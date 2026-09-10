"""Android/Pydroid launcher for frozen R003-X001 Bybit structural replication."""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD=Path("/storage/emulated/0/Download")
WORKSPACE=DOWNLOAD/"R003_X001_BYBIT"
ENGINE_COMMIT="c411a1a92f5682f2a5af33871c22064311c4cb86"
ENGINE_URL=("https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"+ENGINE_COMMIT+"/research/r003/r003_x001_bybit_structural_replication.py")
ENGINE_FILE=WORKSPACE/"r003_x001_bybit_structural_replication_v0_1.py"


def main():
    WORKSPACE.mkdir(parents=True,exist_ok=True)
    print("="*72)
    print("R003-X001 BYBIT STRUCTURAL FUNDING REPLICATION")
    print("Frozen engine commit:",ENGINE_COMMIT)
    print("Persistent workspace:",WORKSPACE)
    print("If Android stops the process, run this same launcher again; downloaded pages resume from checkpoints.")
    print("="*72)
    req=Request(ENGINE_URL,headers={"User-Agent":"r003-x001-bybit-mobile/0.1"})
    with urlopen(req,timeout=60) as r: ENGINE_FILE.write_bytes(r.read())
    source=ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv=[str(ENGINE_FILE),"--workspace",str(WORKSPACE)]
    ns={"__name__":"__main__","__file__":str(ENGINE_FILE)}
    exec(compile(source,str(ENGINE_FILE),"exec"),ns)
    print("\nRUN FINISHED")
    print("Upload the 8 result files from:",WORKSPACE/"results")
    print("Do not upload checkpoint, snapshot, instrument-info or .py files.")

if __name__=="__main__": main()
