"""Android/Pydroid launcher for frozen R009-E001 mechanism screen."""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "1240a9b9c399a7f7e1e5f6af7ecb33a00de365fa"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r009/r009_e001_trend_gated_dry_powder.py"
)


def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R009_E001_RUN_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)
    engine = outdir / "r009_e001_trend_gated_dry_powder_v0_1.py"

    print("=" * 72)
    print("R009-E001 TREND-GATED DRY-POWDER BARBELL")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Results folder:", outdir)
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r009-research-mobile/0.1"})
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    source = engine.read_text(encoding="utf-8")
    sys.argv = [str(engine), "--outdir", str(outdir)]
    ns = {"__name__": "__main__", "__file__": str(engine)}
    exec(compile(source, str(engine), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Upload all 10 result files from:")
    print(outdir)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
