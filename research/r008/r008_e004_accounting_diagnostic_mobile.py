"""Android/Pydroid launcher for frozen R008-E004 accounting diagnostic audit."""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "e9ab9310f77af124287022881ec8222eb04599bf"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r008/r008_e004_accounting_diagnostic.py"
)


def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R008_E004_RUN_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)
    engine = outdir / "r008_e004_accounting_diagnostic_v0_1.py"

    print("=" * 72)
    print("R008-E004 ACCOUNTING & EVENT-DIAGNOSTIC AUDIT")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Results folder:", outdir)
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r008-research-mobile/0.4"})
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
