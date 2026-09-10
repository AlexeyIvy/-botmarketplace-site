"""Android/Pydroid launcher for frozen R010-E001 prospective shadow-forward."""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "R010_E001_FORWARD"
ENGINE_COMMIT = "5088678bdf480a222f9b2cc276ab3573ec4a3639"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r010/r010_e001_prospective_shadow_forward.py"
)
ENGINE_FILE = OUTDIR / "r010_e001_prospective_shadow_forward_v0_1.py"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R010-E001 PROSPECTIVE SHADOW FORWARD")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Persistent output folder:", OUTDIR)
    print("Fixed forward inception: 2026-09-11 00:00 UTC")
    print("R009-E002 remains unchanged and separate.")
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r010-e001-mobile/0.1"})
    with urlopen(req, timeout=60) as resp:
        ENGINE_FILE.write_bytes(resp.read())

    source = ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Upload the 7 result files from:", OUTDIR)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
