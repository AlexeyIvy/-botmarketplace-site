"""Pydroid/Android launcher for the frozen R002 wide-universe engine v0.1."""

from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
CSV = DOWNLOAD / "r002_binance_full_universe_daily.csv"
STATE = DOWNLOAD / "r002_binance_full_universe_state.json"
ENGINE = DOWNLOAD / "r002_wide_universe_point_in_time_finalists_v0_1.py"

# Pin the exact pre-result engine commit. Do not switch this launcher to main
# after seeing results; any future engine change must be a new explicit version.
ENGINE_COMMIT = "9275d50e321dd24f5eabe83cc20dd340cfda6350"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r002/wide_universe_point_in_time_finalists.py"
)


def main():
    if not CSV.exists():
        raise FileNotFoundError(f"Missing dataset: {CSV}")
    if not STATE.exists():
        raise FileNotFoundError(f"Missing state file: {STATE}")

    print("Downloading frozen wide-universe engine:")
    print(ENGINE_COMMIT)
    req = Request(ENGINE_URL, headers={"User-Agent": "r002-research-mobile/0.1"})
    with urlopen(req, timeout=60) as resp:
        ENGINE.write_bytes(resp.read())

    source = ENGINE.read_text(encoding="utf-8")
    sys.argv = [str(ENGINE), str(CSV), "--state", str(STATE)]
    namespace = {"__name__": "__main__", "__file__": str(ENGINE)}
    exec(compile(source, str(ENGINE), "exec"), namespace)


if __name__ == "__main__":
    main()
