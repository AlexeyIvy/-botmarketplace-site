"""Pydroid/Android launcher for frozen R008-E001 v0.1."""

from datetime import datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD=Path("/storage/emulated/0/Download")
CSV=DOWNLOAD/"r002_binance_full_universe_daily.csv"
ENGINE_COMMIT="70700adc936ea59f245a11804f9a576ba4572460"
ENGINE_URL=(
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    +ENGINE_COMMIT+
    "/research/r008/r008_e001_crisis_opportunity.py"
)

def main():
    if not CSV.exists():
        raise FileNotFoundError(f"Missing dataset: {CSV}")
    stamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir=DOWNLOAD/f"R008_E001_RUN_{stamp}"
    outdir.mkdir(parents=True,exist_ok=False)
    engine=outdir/"r008_e001_crisis_opportunity_v0_1.py"

    print("="*72)
    print("R008-E001 MOBILE LAUNCHER")
    print("Frozen engine commit:",ENGINE_COMMIT)
    print("Results folder:",outdir)
    print("="*72)

    req=Request(ENGINE_URL,headers={"User-Agent":"r008-research-mobile/0.1"})
    with urlopen(req,timeout=60) as resp:
        engine.write_bytes(resp.read())

    source=engine.read_text(encoding="utf-8")
    sys.argv=[str(engine),str(CSV),"--outdir",str(outdir)]
    ns={"__name__":"__main__","__file__":str(engine)}
    exec(compile(source,str(engine),"exec"),ns)

    print()
    print("RUN FINISHED")
    print("Upload all result files from:")
    print(outdir)

if __name__=="__main__":
    main()
