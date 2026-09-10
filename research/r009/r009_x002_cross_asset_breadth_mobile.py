"""Android/Pydroid launcher for frozen R009-X002 cross-asset breadth panel."""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD=Path("/storage/emulated/0/Download")
WORKSPACE=DOWNLOAD/"R009_X002_BREADTH"
ENGINE_COMMIT="9e5c28428ba62bdae8eda80db364fa6c65b3d34c"
ENGINE_URL=("https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"+ENGINE_COMMIT+"/research/r009/r009_x002_cross_asset_breadth_panel.py")
ENGINE_FILE=WORKSPACE/"r009_x002_cross_asset_breadth_panel_v0_1.py"

def main():
    WORKSPACE.mkdir(parents=True,exist_ok=True)
    print("="*72)
    print("R009-X002 FIXED CROSS-ASSET BREADTH PANEL")
    print("Frozen engine commit:",ENGINE_COMMIT)
    print("Persistent workspace:",WORKSPACE)
    print("If Android stops the process, run the same launcher again; cached pages and cutoff are reused.")
    print("="*72)
    req=Request(ENGINE_URL,headers={"User-Agent":"r009-x002-breadth-mobile/0.1"})
    with urlopen(req,timeout=60) as r: ENGINE_FILE.write_bytes(r.read())
    source=ENGINE_FILE.read_text(encoding="utf-8")
    sys.argv=[str(ENGINE_FILE),"--workspace",str(WORKSPACE)]
    ns={"__name__":"__main__","__file__":str(ENGINE_FILE)}
    exec(compile(source,str(ENGINE_FILE),"exec"),ns)
    print("\nRUN FINISHED")
    print("Upload the 8 result files from:",WORKSPACE/"results")
    print("Do not upload _cache, snapshot.json or the .py engine copy.")

if __name__=="__main__": main()
