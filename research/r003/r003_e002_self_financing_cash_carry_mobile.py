"""Android/Pydroid launcher for frozen R003-E002 cash-and-carry implementation study."""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "84ab935899b22b8610d7184b192a1b5e8e6df36d"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r003/r003_e002_self_financing_cash_carry.py"
)


def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R003_E002_RUN_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)
    engine = outdir / "r003_e002_self_financing_cash_carry_v0_1.py"

    print("=" * 72)
    print("R003-E002 SELF-FINANCING BTC CASH-AND-CARRY")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Results folder:", outdir)
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r003-research-mobile/0.2"})
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    source = engine.read_text(encoding="utf-8")
    sys.argv = [str(engine), "--outdir", str(outdir)]
    ns = {"__name__": "__main__", "__file__": str(engine)}
    exec(compile(source, str(engine), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Upload the 9 result files from:")
    print(outdir)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
