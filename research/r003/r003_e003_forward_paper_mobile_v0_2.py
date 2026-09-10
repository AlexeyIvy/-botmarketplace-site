"""Android/Pydroid launcher for frozen R003-E003 forward paper tracker v0.2."""

from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "R003_E003_FORWARD"
ENGINE_COMMIT = "cfc001400008ee4d63a27ad6821dda5cb9354f3e"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r003/r003_e003_forward_paper_v0_2.py"
)
ENGINE_FILE = OUTDIR / "r003_e003_forward_paper_v0_2.py"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R003-E003 FORWARD PAPER TRACKER v0.2")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Persistent output folder:", OUTDIR)
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r003-forward-mobile/0.3"})
    with urlopen(req, timeout=60) as resp:
        ENGINE_FILE.write_bytes(resp.read())

    source = ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Re-run this same launcher whenever you want to refresh the forward record.")
    print("Upload the result files from:")
    print(OUTDIR)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
