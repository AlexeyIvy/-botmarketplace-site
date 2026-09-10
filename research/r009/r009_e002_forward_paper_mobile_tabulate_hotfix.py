"""Android/Pydroid launcher for frozen R009-E002 forward paper with environment-only tabulate dependency fix."""
from pathlib import Path
import importlib
import subprocess
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "R009_E002_FORWARD"
ENGINE_COMMIT = "b82b5bb3cd71f6f3ba5efc796684e221c29917e7"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r009/r009_e002_forward_paper.py"
)
ENGINE_FILE = OUTDIR / "r009_e002_forward_paper_v0_1.py"


def ensure_tabulate():
    try:
        importlib.import_module("tabulate")
        print("tabulate: already installed")
        return
    except ImportError:
        print("tabulate: missing; installing environment dependency only...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
    importlib.invalidate_caches()
    importlib.import_module("tabulate")
    print("tabulate: installed")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R009-E002 FORWARD PAPER TRACKER — TABULATE ENV HOTFIX")
    print("Frozen economic engine commit:", ENGINE_COMMIT)
    print("Persistent results folder:", OUTDIR)
    print("No strategy parameter, source, inception, accounting or forward clock is changed.")
    print("=" * 72)

    ensure_tabulate()

    req = Request(ENGINE_URL, headers={"User-Agent": "r009-forward-mobile-tabulate-hotfix/0.1"})
    with urlopen(req, timeout=60) as resp:
        ENGINE_FILE.write_bytes(resp.read())

    source = ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("TRACKER FINISHED")
    print("Forward folder:", OUTDIR)
    print("You may omit the .py engine copy when uploading results.")


if __name__ == "__main__":
    main()
