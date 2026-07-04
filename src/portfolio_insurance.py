import numpy as np
from scipy.stats import kurtosis, norm, skew


def risk_metrics(returns):
    """
    Calculate risk and performance metrics for simulated portfolio returns.
    """
    # 5% left-tail cutoff used for VaR and CVaR
    threshold = np.percentile(returns, 5)
    tail_returns = returns[returns <= threshold]

    return {
        "E[R]": returns.mean(),
        "Sigma": returns.std(),
        "VaR 95%": -threshold,
        "CVaR 95%": -tail_returns.mean(),
        "P(loss)": np.mean(returns < 0),
        "5% quantile": threshold,
        "Skewness": skew(returns),
        "Excess kurtosis": kurtosis(returns, fisher=True),
    }


def terminal_dividend_cash(
    stock_paths,
    n_shares,
    risk_free_rate,
    dividend_yield,
    dt,
):
    """
    Terminal value of dividends from a constant share holding.

    The path matrix contains ex-dividend stock prices. Dividends over each
    interval use the beginning-of-interval stock price and are accumulated at
    the risk-free rate until maturity.
    """
    stock_paths = np.asarray(stock_paths, dtype=float)

    if stock_paths.ndim != 2 or stock_paths.shape[1] < 2:
        raise ValueError("stock_paths must be a 2D array with at least two columns.")

    if not np.all(np.isfinite(stock_paths)):
        raise ValueError("stock_paths must contain only finite values.")

    if np.any(stock_paths < 0):
        raise ValueError("stock_paths must be non-negative.")

    n_shares = np.asarray(n_shares, dtype=float)

    if n_shares.ndim == 0:
        shares = n_shares
    elif n_shares.shape == (stock_paths.shape[0],):
        shares = n_shares[:, None]
    else:
        raise ValueError("n_shares must be scalar or have one value per path.")

    if not np.all(np.isfinite(n_shares)):
        raise ValueError("n_shares must contain only finite values.")

    if np.any(n_shares < 0):
        raise ValueError("n_shares must be non-negative.")

    if not np.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite.")

    if not np.isfinite(dividend_yield) or dividend_yield < 0:
        raise ValueError("dividend_yield must be finite and non-negative.")

    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")

    n_intervals = stock_paths.shape[1] - 1
    dividend_per_share = np.exp(dividend_yield * dt) - 1
    accrual_factors = np.exp(
        risk_free_rate
        * dt
        * np.arange(n_intervals - 1, -1, -1)
    )

    interval_dividends = (
        shares
        * stock_paths[:, :-1]
        * dividend_per_share
    )

    return np.sum(interval_dividends * accrual_factors, axis=1)


def manual_constant_path_dividend_cash(
    stock_price,
    n_shares,
    n_intervals,
    risk_free_rate,
    dividend_yield,
    dt,
):
    """
    Manually compound dividend cash for a constant stock path.
    """
    dividend_cash = 0.0

    for _ in range(n_intervals):
        dividend_cash = (
            dividend_cash
            * np.exp(risk_free_rate * dt)
            + n_shares
            * stock_price
            * (np.exp(dividend_yield * dt) - 1)
        )

    return dividend_cash


def black_scholes_put(S0, K, r, sigma, T, *, dividend_yield):
    """
    Price a European put option using the Black-Scholes formula.
    """
    d1 = (
        np.log(S0 / K)
        + (r - dividend_yield + 0.5 * sigma**2) * T
    ) / (
        sigma * np.sqrt(T)
    )

    d2 = d1 - sigma * np.sqrt(T)

    put_price = (
        K * np.exp(-r * T) * norm.cdf(-d2)
        - S0 * np.exp(-dividend_yield * T) * norm.cdf(-d1)
    )

    return put_price


def evaluate_put_insurance_strategy(
    stock_paths,
    put_budget_fraction,
    strike_moneyness,
    S0,
    initial_capital,
    r,
    sigma_pricing,
    T,
    *,
    dividend_yield,
    dt,
    dividend_cash_per_share=None,
):
    """
    Evaluate a put-insurance strategy for a given stock-price path matrix.
    """
    stock_paths = np.asarray(stock_paths, dtype=float)

    if stock_paths.ndim != 2 or stock_paths.shape[1] < 2:
        raise ValueError("stock_paths must be a 2D array with at least two columns.")

    S_T = stock_paths[:, -1]
    K = strike_moneyness * S0

    put_price = black_scholes_put(
        S0=S0,
        K=K,
        r=r,
        sigma=sigma_pricing,
        T=T,
        dividend_yield=dividend_yield,
    )

    equity_budget = (
        (1 - put_budget_fraction)
        * initial_capital
    )

    # Allocate the non-insurance budget to ASML shares
    n_shares = (
        equity_budget
        / S0
    )

    # Buy put options with the allocated insurance budget
    n_puts = (
        put_budget_fraction
        * initial_capital
        / put_price
    )

    # Terminal wealth across all supplied stock-price outcomes
    equity_leg = (
        n_shares
        * S_T
    )

    if dividend_cash_per_share is None:
        dividend_cash = terminal_dividend_cash(
            stock_paths=stock_paths,
            n_shares=n_shares,
            risk_free_rate=r,
            dividend_yield=dividend_yield,
            dt=dt,
        )
    else:
        dividend_cash_per_share = np.asarray(dividend_cash_per_share, dtype=float)

        if dividend_cash_per_share.shape != S_T.shape:
            raise ValueError("dividend_cash_per_share must have one value per path.")

        if not np.all(np.isfinite(dividend_cash_per_share)):
            raise ValueError("dividend_cash_per_share must contain only finite values.")

        if np.any(dividend_cash_per_share < 0):
            raise ValueError("dividend_cash_per_share must be non-negative.")

        dividend_cash = n_shares * dividend_cash_per_share

    put_leg = (
        n_puts
        * np.maximum(K - S_T, 0)
    )

    terminal_wealth = (
        equity_leg
        + dividend_cash
        + put_leg
    )

    returns = (
        terminal_wealth
        / initial_capital
        - 1
    )

    return returns, {
        "K": K,
        "put_price": put_price,
        "n_shares": n_shares,
        "n_puts": n_puts,
        "avg_dividend_cash": dividend_cash.mean(),
        "avg_dividend_return": dividend_cash.mean() / initial_capital,
    }
