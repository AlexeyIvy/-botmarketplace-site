"""Pydroid/Android launcher for the frozen R002 wide-universe engine v0.1.

Each execution creates its own timestamped folder inside Android Download and
places the pinned engine copy plus every result file from that run there.
The large input CSV/state files remain in Download and are not duplicated.
"""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
CSV = DOWNLOAD / "r002_binance_full_universe_daily.csv"
STATE = DOWNLOAD / "r002_binance_full_universe_state.json"

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

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R002_WIDE_UNIVERSE_RUN_{run_id}"
    outdir.mkdir(parents=True, exist_ok=False)

    engine = outdir / "r002_wide_universe_point_in_time_finalists_v0_1.py"

    print("=" * 72)
    print("R002 WIDE-UNIVERSE MOBILE LAUNCHER")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("All files from this run will be saved in:")
    print(outdir)
    print("=" * 72)
    print()

    print("Downloading frozen wide-universe engine...")
    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "r002-research-mobile/0.2"},
    )
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    source = engine.read_text(encoding="utf-8")

    sys.argv = [
        str(engine),
        str(CSV),
        "--state",
        str(STATE),
        "--outdir",
        str(outdir),
    ]

    namespace = {
        "__name__": "__main__",
        "__file__": str(engine),
    }
    exec(compile(source, str(engine), "exec"), namespace)

    print()
    print("=" * 72)
    print("RUN FINISHED")
    print("Open this folder and upload its result files to ChatGPT:")
    print(outdir)
    print("=" * 72)


if __name__ == "__main__":
    main()
