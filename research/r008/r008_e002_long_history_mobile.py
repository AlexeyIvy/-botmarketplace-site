"""Pydroid/Android launcher for frozen R008-E002 v0.1."""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "aa84072c2e35ac53442d57a6bf57a51966df68b4"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r008/r008_e002_long_history.py"
)


def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R008_E002_RUN_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    engine = outdir / "r008_e002_long_history_v0_1.py"

    print("=" * 72)
    print("R008-E002 MOBILE LAUNCHER")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Independent source: Blockchain.com market-price history")
    print("All files from this run will be saved in:")
    print(outdir)
    print("=" * 72)
    print()

    print("Downloading frozen R008-E002 engine...")
    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "r008-research-mobile/0.2"},
    )
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    source = engine.read_text(encoding="utf-8")

    sys.argv = [
        str(engine),
        "--outdir",
        str(outdir),
    ]

    namespace = {
        "__name__": "__main__",
        "__file__": str(engine),
    }

    exec(
        compile(source, str(engine), "exec"),
        namespace,
    )

    print()
    print("=" * 72)
    print("RUN FINISHED")
    print("Upload all non-.py result files from:")
    print(outdir)
    print("=" * 72)


if __name__ == "__main__":
    main()
