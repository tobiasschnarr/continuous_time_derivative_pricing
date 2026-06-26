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


def black_scholes_put(S0, K, r, sigma, T):
    """
    Price a European put option using the Black-Scholes formula.
    """
    d1 = (
        np.log(S0 / K)
        + (r + 0.5 * sigma**2) * T
    ) / (
        sigma * np.sqrt(T)
    )

    d2 = d1 - sigma * np.sqrt(T)

    put_price = (
        K * np.exp(-r * T) * norm.cdf(-d2)
        - S0 * norm.cdf(-d1)
    )

    return put_price


def evaluate_put_insurance_strategy(
    S_T,
    put_budget_fraction,
    strike_moneyness,
    S0,
    initial_capital,
    r,
    sigma_pricing,
    T,
):
    """
    Evaluate a put-insurance strategy for a given terminal stock distribution.
    """
    K = strike_moneyness * S0

    put_price = black_scholes_put(
        S0=S0,
        K=K,
        r=r,
        sigma=sigma_pricing,
        T=T,
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

    put_leg = (
        n_puts
        * np.maximum(K - S_T, 0)
    )

    terminal_wealth = (
        equity_leg
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
    }
