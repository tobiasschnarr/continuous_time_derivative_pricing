import numpy as np
from datetime import timedelta


def nelson_siegel_svensson_model(T, beta0, beta1, beta2, beta3, tau1, tau2):
    """
    Nelson-Siegel-Svensson zero rate curve.

    T is measured in years. Bundesbank parameters are given in percent,
    so the output is converted to decimal rates.
    """
    T = np.asarray(T)

    term1 = (1 - np.exp(-T / tau1)) / (T / tau1)
    term2 = term1 - np.exp(-T / tau1)
    term3 = (1 - np.exp(-T / tau2)) / (T / tau2) - np.exp(-T / tau2)

    r_t = beta0 + beta1 * term1 + beta2 * term2 + beta3 * term3
    return r_t / 100


def zero_to_short(R, dt):
    """
    Convert zero rates into one-step short rates.
    """
    f = np.empty_like(R)
    f[0] = R[0]
    f[1:] = (
        R[1:] * np.arange(1, len(R)) * dt
        - R[:-1] * np.arange(len(R) - 1) * dt
    ) / dt
    return f


def idx_of(date, today, params):
    """
    Convert a calendar date to the corresponding trading-step index.
    """
    return int(np.ceil((date - today).days * params["STEPS_PER_DAY"]))


def price_express_certificate_one_day(spot, sigma, val_date, r_vec, params):
    """
    Value the UniCredit ASML Express Plus Certificate using a binomial tree.

    Product logic:
    - early redemption condition is checked on the observation dates;
    - payment is made on the corresponding redemption/payment date;
    - final payoff is determined on the final observation date;
    - final cash/physical redemption is settled on the maturity/payment date;
    - no separate coupons are modelled, since the certificate is not interest-bearing.
    """
    dt = 1 / params["TRADING_DAYS"]

    # Tree ends at the final observation date, because the ASML price relevant
    # for the final payoff is fixed there.
    n_steps = idx_of(params["FINAL_OBS_DATE"], val_date, params)

    if n_steps <= 2:
        return np.nan

    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u

    # Map early observation dates to tree indices
    obs_idx = {}

    for obs_date, pay_date, level, redemption_amount in zip(
        params["OBS_DATES"],
        params["EARLY_REDEMPTION_DATES"],
        params["LEVELS"],
        params["EARLY_REDEMPTION_AMOUNTS"],
    ):
        i_obs = idx_of(obs_date, val_date, params)

        if 0 <= i_obs < n_steps:
            gap_years = max((pay_date - obs_date).days / 365, 0)

            obs_idx[i_obs] = {
                "level": level,
                "amount": redemption_amount,
                "gap_years": gap_years,
            }

    # Stock tree until final observation date
    stock = [[0.0] * (i + 1) for i in range(n_steps + 1)]

    for i in range(n_steps + 1):
        for j in range(i + 1):
            stock[i][j] = spot * (u ** j) * (d ** (i - j))

    # Value tree
    value = [[0.0] * (i + 1) for i in range(n_steps + 1)]

    # Final payoff determined at final observation date.
    # Payment occurs on maturity date, so discount over the short settlement gap.
    final_gap_years = max(
        (params["MATURITY"] - params["FINAL_OBS_DATE"]).days / 365,
        0,
    )

    # Use the final short rate as approximation for the short settlement gap.
    r_final = r_vec[min(n_steps - 1, len(r_vec) - 1)]
    final_gap_discount = np.exp(-r_final * final_gap_years)

    for j, ST in enumerate(stock[-1]):
        if ST >= params["BARRIER"]:
            payoff = params["MAX_AMOUNT"]
        elif ST >= params["BASIS_PRICE"]:
            payoff = params["NOMINAL"]
        else:
            payoff = params["SHARES"] * ST

        value[-1][j] = payoff * final_gap_discount

    # Backward induction
    for i in range(n_steps - 1, -1, -1):
        r_i = r_vec[min(i, len(r_vec) - 1)]
        disc_i = np.exp(-r_i * dt)
        q_i = (np.exp(r_i * dt) - d) / (u - d)

        if not np.isfinite(q_i) or q_i < 0 or q_i > 1:
            raise ValueError(
                f"Invalid risk-neutral probability q={q_i:.4f} at step {i}. "
                f"r={r_i:.6f}, sigma={sigma:.6f}, u={u:.6f}, d={d:.6f}"
            )

        for j in range(i + 1):
            continuation = disc_i * (
                q_i * value[i + 1][j + 1]
                + (1 - q_i) * value[i + 1][j]
            )

            if i in obs_idx and stock[i][j] >= obs_idx[i]["level"]:
                # If early redemption happens, payment is made a few days later.
                gap_discount = np.exp(-r_i * obs_idx[i]["gap_years"])
                node_value = obs_idx[i]["amount"] * gap_discount
            else:
                node_value = continuation

            value[i][j] = node_value

    return value[0][0]


def error_metrics(model, market):
    """
    Calculate error metrics for model prices versus market prices.
    """
    diff = model - market
    abs_diff = np.abs(diff)
    pct_diff = diff / market

    return {
        "ME": diff.mean(),
        "MAE": abs_diff.mean(),
        "RMSE": np.sqrt((diff ** 2).mean()),
        "MPE": pct_diff.mean() * 100,
        "90%-|e|": np.quantile(abs_diff, 0.90),
        "R²": 1 - diff.var() / market.var(),
    }


def price_and_greeks(
    spot,
    sigma,
    val_date,
    r_vec,
    params,
    spot_bump_pct=0.01,
    vega_bump=0.01,
):
    """
    Calculate price and main Greeks by finite differences.

    Delta and Gamma are based on a symmetric spot bump.
    Vega is scaled to a one volatility-point change.
    """
    spot_bump = spot * spot_bump_pct

    price = price_express_certificate_one_day(
        spot=spot,
        sigma=sigma,
        val_date=val_date,
        r_vec=r_vec,
        params=params,
    )

    price_up = price_express_certificate_one_day(
        spot=spot + spot_bump,
        sigma=sigma,
        val_date=val_date,
        r_vec=r_vec,
        params=params,
    )

    price_down = price_express_certificate_one_day(
        spot=spot - spot_bump,
        sigma=sigma,
        val_date=val_date,
        r_vec=r_vec,
        params=params,
    )

    delta = (price_up - price_down) / (2 * spot_bump)

    gamma = (
        price_up
        - 2 * price
        + price_down
    ) / (spot_bump ** 2)

    price_vol_up = price_express_certificate_one_day(
        spot=spot,
        sigma=sigma + vega_bump,
        val_date=val_date,
        r_vec=r_vec,
        params=params,
    )

    price_vol_down = price_express_certificate_one_day(
        spot=spot,
        sigma=max(sigma - vega_bump, 1e-6),
        val_date=val_date,
        r_vec=r_vec,
        params=params,
    )

    # Vega per 1 volatility point, e.g. sigma + 0.01
    vega = (price_vol_up - price_vol_down) / (2 * vega_bump) / 100

    return price, delta, gamma, vega


def price_and_extended_greeks(
    spot,
    sigma,
    val_date,
    r_vec,
    params,
    spot_bump_pct=0.005,
    vega_bump=0.005,
    rho_bump=0.0001,
):
    """
    Compute price, Delta, Gamma, Vega, Rho, and one-day Theta
    using central finite differences.

    Scaling:
    - Vega: EUR per one volatility percentage point.
    - Rho: EUR per one interest-rate percentage point.
    - Theta: EUR change over one additional trading day.
    """
    spot_bump = spot * spot_bump_pct

    price = price_express_certificate_one_day(
        spot, sigma, val_date, r_vec, params
    )

    # Delta and Gamma
    price_spot_up = price_express_certificate_one_day(
        spot + spot_bump, sigma, val_date, r_vec, params
    )
    price_spot_down = price_express_certificate_one_day(
        spot - spot_bump, sigma, val_date, r_vec, params
    )

    delta = (price_spot_up - price_spot_down) / (2 * spot_bump)

    gamma = (
        price_spot_up - 2 * price + price_spot_down
    ) / (spot_bump ** 2)

    # Vega: per one volatility percentage point
    price_vol_up = price_express_certificate_one_day(
        spot, sigma + vega_bump, val_date, r_vec, params
    )
    price_vol_down = price_express_certificate_one_day(
        spot,
        max(sigma - vega_bump, 1e-8),
        val_date,
        r_vec,
        params,
    )

    vega = (
        (price_vol_up - price_vol_down)
        / (2 * vega_bump)
        / 100
    )

    # Rho: parallel shift of the complete short-rate curve,
    # reported per one interest-rate percentage point
    price_rate_up = price_express_certificate_one_day(
        spot, sigma, val_date, r_vec + rho_bump, params
    )
    price_rate_down = price_express_certificate_one_day(
        spot, sigma, val_date, r_vec - rho_bump, params
    )

    rho = (
        (price_rate_up - price_rate_down)
        / (2 * rho_bump)
        / 100
    )

    # Theta: value change after one trading day.
    # Remove the first one-step rate because one tree step has elapsed.
    next_val_date = val_date + timedelta(days=1)
    next_r_vec = r_vec[1:]

    next_day_price = price_express_certificate_one_day(
        spot,
        sigma,
        next_val_date,
        next_r_vec,
        params,
    )

    theta = next_day_price - price

    return price, delta, gamma, vega, rho, theta