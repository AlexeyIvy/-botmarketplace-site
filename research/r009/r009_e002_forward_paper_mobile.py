"""Android/Pydroid launcher for frozen R009-E002 forward paper tracker."""

from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "b82b5bb3cd71f6f3ba5efc796684e221c29917e7"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r009/r009_e002_forward_paper.py"
)


def main():
    outdir = DOWNLOAD / "R009_E002_FORWARD"
    outdir.mkdir(parents=True, exist_ok=True)
    engine = outdir / "r009_e002_forward_paper_v0_1.py"

    print("=" * 72)
    print("R009-E002 FORWARD PAPER TRACKER")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Persistent results folder:", outdir)
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r009-forward-mobile/0.1"})
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    source = engine.read_text(encoding="utf-8")
    sys.argv = [str(engine), "--outdir", str(outdir)]
    ns = {"__name__": "__main__", "__file__": str(engine)}
    exec(compile(source, str(engine), "exec"), ns)

    print()
    print("TRACKER FINISHED")
    print("Forward folder:")
    print(outdir)
    print("You may omit the .py engine copy when uploading results.")


if __name__ == "__main__":
    main()
