"""Android/Pydroid launcher for frozen R009-G001 capital granularity snapshot."""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD=Path("/storage/emulated/0/Download")
OUTDIR=DOWNLOAD/"R009_G001_CAPITAL_GRANULARITY"
ENGINE_COMMIT="cede11a1eac65f4bdff2ad485dab62c9f2a5e367"
ENGINE_URL=("https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"+ENGINE_COMMIT+"/research/r009/r009_g001_capital_granularity_snapshot.py")
ENGINE_FILE=OUTDIR/"r009_g001_capital_granularity_snapshot_v0_1.py"


def main():
    OUTDIR.mkdir(parents=True,exist_ok=True)
    print("="*72)
    print("R009-G001 CAPITAL GRANULARITY SNAPSHOT")
    print("Frozen engine commit:",ENGINE_COMMIT)
    print("Output folder:",OUTDIR)
    print("="*72)
    req=Request(ENGINE_URL,headers={"User-Agent":"r009-g001-mobile/0.1"})
    with urlopen(req,timeout=60) as r: ENGINE_FILE.write_bytes(r.read())
    source=ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv=[str(ENGINE_FILE),"--outdir",str(OUTDIR)]
    ns={"__name__":"__main__","__file__":str(ENGINE_FILE)}
    exec(compile(source,str(ENGINE_FILE),"exec"),ns)
    print("\nRUN FINISHED")
    print("Upload these 5 result files from:",OUTDIR)
    print("Omit the .py engine copy.")

if __name__=="__main__": main()
