"""Android/Pydroid launcher for frozen R009-G002 pathwise discrete replay."""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "R009_G002_PATHWISE_DISCRETE"
ENGINE_COMMIT = "ea713a8899673733692659a44ce397b96cd3d4c5"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r009/r009_g002_pathwise_discrete_replay.py"
)
ENGINE_FILE = OUTDIR / "r009_g002_pathwise_discrete_replay_v0_1.py"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R009-G002 PATHWISE DISCRETE REPLAY")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Output folder:", OUTDIR)
    print("Implementation diagnostic only; R009 rules are unchanged.")
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r009-g002-mobile/0.1"})
    with urlopen(req, timeout=60) as r:
        ENGINE_FILE.write_bytes(r.read())

    source = ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Upload the 5 result files from:")
    print(OUTDIR)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
