# Q26b — the borrow-fee bound

The borrow fee is the only cost input in Q26 that cannot be looked up: commissions and the securities
transaction tax are published, half-spreads are estimated from public prices (Corwin-Schultz), and impact is a
model. So instead of assuming a better number, we report how large the fee would have to be to overturn the
conclusion. Everything else is held at the Q26 settings; the fee is swept from 0% to 60% a year.

## Bounds on the Korean long-short, 2023-01 onwards

```
 fund_usd_m  net_bp_at_3%  fee_net_zero_%  fee_t_below_2_%  fee_alpha_zero_%  fee_alpha_t_below_2_%
        1.0        313.95           40.67            13.44             29.07                  10.76
       10.0        249.75           32.97             6.21             21.63                   4.26
       50.0        -35.56            0.00             0.00              0.00                   0.00
```

Columns: the fee at which the net monthly return crosses zero, at which its Newey-West t crosses 2, and the
same two for the risk-adjusted alpha (market, size and momentum controls).

## Reading

The point estimate is robust to the assumption: borrow would have to cost tens of per cent a year, which is
deep special-rate territory, before the net spread disappears at a small fund size. Statistical significance is
the fragile part -- the t-statistic falls below 2 at a far lower fee, so the confidence in the after-cost result,
not the after-cost result itself, is what the borrow assumption buys.

Borrow fees for the actual short-leg names can be observed directly from a broker's stock-loan quotes, or
historically from Markit Securities Finance (WRDS). Until then these bounds stand in for the missing input.
