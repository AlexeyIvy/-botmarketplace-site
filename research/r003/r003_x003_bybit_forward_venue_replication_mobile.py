"""Android/Pydroid launcher for frozen R003-X003 Bybit forward venue replication."""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "R003_X003_BYBIT_FORWARD"
ENGINE_COMMIT = "2ef343190a672a2099654ec91da88c4bef201b9f"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r003/r003_x003_bybit_forward_venue_replication.py"
)
ENGINE_FILE = OUTDIR / "r003_x003_bybit_forward_venue_replication_v0_1.py"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R003-X003 BYBIT FORWARD VENUE REPLICATION")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Fixed decision boundary: 2026-09-10 16:00:00 UTC")
    print("Persistent output folder:", OUTDIR)
    print("Binance R003-E003 is separate and remains unchanged.")
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r003-x003-bybit-mobile/0.1"})
    with urlopen(req, timeout=60) as resp:
        ENGINE_FILE.write_bytes(resp.read())

    source = ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Re-run the same launcher later to extend the same fixed forward record.")
    print("Upload result files from:", OUTDIR)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
