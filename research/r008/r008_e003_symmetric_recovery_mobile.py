"""Android/Pydroid launcher for frozen R008-E003 symmetric recovery screen."""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "243fdf7e68ab150936b7fa461182c770a9a4e974"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r008/r008_e003_symmetric_recovery.py"
)


def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R008_E003_RUN_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)
    engine = outdir / "r008_e003_symmetric_recovery_v0_1.py"

    print("=" * 72)
    print("R008-E003 SYMMETRIC RECOVERY-RELEASE MOBILE LAUNCHER")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Results folder:", outdir)
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r008-research-mobile/0.3"})
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    source = engine.read_text(encoding="utf-8")
    sys.argv = [str(engine), "--outdir", str(outdir)]
    ns = {"__name__": "__main__", "__file__": str(engine)}
    exec(compile(source, str(engine), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Upload all result files from:")
    print(outdir)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
