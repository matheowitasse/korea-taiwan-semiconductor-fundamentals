"""Download 1-minute bars from Interactive Brokers (run at home, with IB Gateway open and logged in).

Nothing here touches your password: you log in to IB Gateway yourself; this script only connects to the Gateway
running on your own computer (127.0.0.1). Use a Read-Only API setting in the Gateway so no order can ever be sent.

Setup (once):
  1. Client Portal: enable KRX (and US / Japan) market data subscriptions.
  2. IB Gateway -> Configure -> Settings -> API -> Settings:
     tick "Enable ActiveX and Socket Clients" and "Read-Only API"; Trusted IPs = 127.0.0.1.
     Port: 4001 = live account, 4002 = paper account.
  3. In the project venv:  pip install ib_async

Usage (from the project folder):
  python src/ibkr_download_minutes.py find "SK hynix"      # look up the exact IBKR contract for a company
  python src/ibkr_download_minutes.py probe                # how far back 1-minute data goes, per stock (run this first)
  python src/ibkr_download_minutes.py download             # download everything since START (resumable)
  python src/ibkr_download_minutes.py download --only 000660 NVDA

Options: --port 4002 (paper account), --start 2023-01-01
Output: data/raw/ibkr/<exchange>_<symbol>.parquet (UTC timestamps, regular trading hours only)
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from ib_async import IB, Stock, util

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "ibkr"

# symbol, exchange, currency, primary exchange (for SMART-routed US stocks)
# Korean and Japanese symbols follow IBKR's local-code convention; if one fails, use `find` and fix it here.
UNIVERSE = [
    # US signal side
    ("SOXX", "SMART", "USD", "NASDAQ"),
    ("NVDA", "SMART", "USD", "NASDAQ"),
    ("MU", "SMART", "USD", "NASDAQ"),
    # Korea
    ("005930", "KRX", "KRW", None),  # Samsung Electronics
    ("000660", "KRX", "KRW", None),  # SK Hynix
    ("042700", "KRX", "KRW", None),  # Hanmi Semiconductor
    ("000990", "KRX", "KRW", None),  # DB HiTek
    ("058470", "KRX", "KRW", None),  # Leeno Industrial
    ("095340", "KRX", "KRW", None),  # ISC
    ("240810", "KRX", "KRW", None),  # Wonik IPS
    ("036930", "KRX", "KRW", None),  # Jusung Engineering
    ("084370", "KRX", "KRW", None),  # Eugene Technology
    ("403870", "KRX", "KRW", None),  # HPSP
    # Japan
    ("8035", "TSEJ", "JPY", None),  # Tokyo Electron
    ("6857", "TSEJ", "JPY", None),  # Advantest
    ("6146", "TSEJ", "JPY", None),  # Disco
    ("6920", "TSEJ", "JPY", None),  # Lasertec
    ("7735", "TSEJ", "JPY", None),  # Screen Holdings
]
# Taiwan: IBKR access to Taiwan-listed stocks may not be available for your account — check with `find "TSMC"`.

CHUNK = "5 D"          # ~390 bars per day -> 5 days stays under IBKR's ~2,000 bars per request
PAUSE_SECONDS = 3.0    # stay well inside IBKR pacing limits


def connect(port: int) -> IB:
    ib = IB()
    ib.connect("127.0.0.1", port, clientId=17, readonly=True, timeout=20)
    return ib


def make_contract(ib: IB, symbol: str, exchange: str, currency: str, primary: str | None) -> Stock | None:
    c = Stock(symbol, exchange, currency, primaryExchange=primary) if primary else Stock(symbol, exchange, currency)
    qualified = ib.qualifyContracts(c)
    if not qualified:
        print(f"  !! could not find {symbol} on {exchange} — try: python src/ibkr_download_minutes.py find \"<company name>\"")
        return None
    return qualified[0]


def cmd_find(ib: IB, pattern: str) -> None:
    for d in ib.reqMatchingSymbols(pattern):
        c = d.contract
        print(f"{c.symbol:10s} {c.secType:5s} {c.primaryExchange:8s} {c.currency:4s} {c.description if hasattr(c, 'description') else ''}")


def cmd_probe(ib: IB, universe) -> None:
    for sym, exch, cur, prim in universe:
        c = make_contract(ib, sym, exch, cur, prim)
        if c is None:
            continue
        head = ib.reqHeadTimeStamp(c, whatToShow="TRADES", useRTH=True, formatDate=2)
        print(f"{sym:8s} {exch:6s} earliest data: {head}")
        ib.sleep(PAUSE_SECONDS)


def cmd_download(ib: IB, universe, start: datetime) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sym, exch, cur, prim in universe:
        c = make_contract(ib, sym, exch, cur, prim)
        if c is None:
            continue
        path = OUT / f"{exch}_{sym}.parquet"
        existing = pd.read_parquet(path) if path.exists() else pd.DataFrame()
        head = ib.reqHeadTimeStamp(c, whatToShow="TRADES", useRTH=True, formatDate=2)
        floor = max(start, head) if isinstance(head, datetime) else start

        # Resume: continue backwards from the oldest bar already saved, or from now
        end = existing["date"].min().to_pydatetime() if len(existing) else datetime.now(timezone.utc)
        chunks = [existing] if len(existing) else []
        print(f"{sym} ({exch}): downloading back to {floor.date()}, starting from {end:%Y-%m-%d}")
        while end > floor:
            bars = ib.reqHistoricalData(c, endDateTime=end, durationStr=CHUNK, barSizeSetting="1 min",
                                        whatToShow="TRADES", useRTH=True, formatDate=2, timeout=120)
            if not bars:
                end -= timedelta(days=7)  # holiday week or gap: step back and keep going
                ib.sleep(PAUSE_SECONDS)
                continue
            df = util.df(bars)
            chunks.append(df)
            end = df["date"].min().to_pydatetime()
            pd.concat(chunks).drop_duplicates("date").sort_values("date").to_parquet(path)  # save as we go
            print(f"  {sym}: back to {end:%Y-%m-%d}, {sum(len(x) for x in chunks):,} bars")
            ib.sleep(PAUSE_SECONDS)
        print(f"{sym}: done -> {path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["find", "probe", "download"])
    ap.add_argument("pattern", nargs="?", help="company name for `find`")
    ap.add_argument("--port", type=int, default=4001)
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--only", nargs="*", help="limit to these symbols")
    args = ap.parse_args()

    universe = [u for u in UNIVERSE if not args.only or u[0] in args.only]
    ib = connect(args.port)
    try:
        if args.command == "find":
            if not args.pattern:
                sys.exit('usage: find "company name"')
            cmd_find(ib, args.pattern)
        elif args.command == "probe":
            cmd_probe(ib, universe)
        else:
            start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
            cmd_download(ib, universe, start)
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
