from __future__ import annotations
import json,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path("/work/run/output")
MANIFEST=OUT/"v011_source_invalid_recovery_before_v014_offline_preflight_manifest.json"
WRAPPER=ROOT/"scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.sh"
SPEC=ROOT/"docs/research/sc001-b15-p1-v011-source-invalid-recovery-before-v014-preflight-spec-v0.1.json"
PASS="B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_PASS"
REVIEW="B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_REVIEW"

def write(o):
    OUT.mkdir(parents=True,exist_ok=True)
    MANIFEST.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main():
    checks={}
    try:
        spec=json.loads(SPEC.read_text())
        text=WRAPPER.read_text()
        if spec["wrapper"]["sha256"]!=__import__("hashlib").sha256(WRAPPER.read_bytes()).hexdigest():
            raise RuntimeError("wrapper sha mismatch")
        bash=shutil.which("bash")
        p=subprocess.run([bash,"-n",str(WRAPPER)],capture_output=True,text=True)
        checks["bash_syntax_returncode"]=p.returncode
        if p.returncode: raise RuntimeError(p.stderr or p.stdout)
        blocks=re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)",text,re.S)
        if len(blocks)!=1: raise RuntimeError(f"embedded python count={len(blocks)}")
        compile(blocks[0],"<recovery-heredoc>","exec")
        checks["embedded_python_compile"]=True
        cmds=[]
        for line in text.splitlines():
            s=line.strip()
            if s.startswith("#") or s.startswith("for cmd in "): continue
            cmds += re.findall(r"\bsystemctl\s+([A-Za-z-]+)",line)
        allowed=set(spec["allowed_systemctl_subcommands"])
        if any(c not in allowed for c in cmds): raise RuntimeError(f"bad systemctl {cmds}")
        checks["systemctl_subcommands"]=cmds
        forbidden={
            "start":bool(re.search(r"systemctl\s+start",text)),
            "enable":bool(re.search(r"systemctl\s+enable",text)),
            "restart":bool(re.search(r"systemctl\s+restart",text)),
            "collector_run":"--mode run" in text,
            "snapshot_move":bool(re.search(r"mv\s+[^\n]*\$SNAPSHOT",text)),
            "snapshot_delete":bool(re.search(r"rm\s+[^\n]*\$SNAPSHOT",text)),
            "safe_summary_move":bool(re.search(r"mv\s+[^\n]*\$SAFE_SUMMARY",text)),
            "cap_log_move":bool(re.search(r"mv\s+[^\n]*\$CAP_LOG",text)),
        }
        if any(forbidden.values()): raise RuntimeError(f"forbidden={forbidden}")
        checks["forbidden"]=forbidden
        required=[
            'flock -n 9',
            'EXPECTED_SNAPSHOT_SHA="fc1b4537290451241596e67342a9ab8fa6acd827afd4aeb70b70cee1e24e8e47"',
            '"$OUT_DIR/raw_objects"','"$OUT_DIR/polls"','"$OUT_DIR/normalized"',
            '"$OUT_DIR/events"','"$OUT_DIR/gaps"','"$OUT_DIR/fees"',
            '"$OUT_DIR/invalid"','"$OUT_DIR/daily_manifests"',
            'v022_snapshot_changed_during_recovery',
            'B15P1_V011_SOURCE_INVALID_RECOVERY_PASS'
        ]
        miss=[m for m in required if m not in text]
        if miss: raise RuntimeError(f"missing={miss}")
        write({"schema":"sc001.b15.p1_v011_source_invalid_recovery_before_v014_offline_preflight.v0.1","status":PASS,"checks":checks,"exchange_calls_performed":False,"collector_start_performed":False})
        print(PASS); return 0
    except Exception as e:
        write({"schema":"sc001.b15.p1_v011_source_invalid_recovery_before_v014_offline_preflight.v0.1","status":REVIEW,"error":f"{type(e).__name__}: {e}","checks":checks})
        print(REVIEW); print("error =",e); return 2

if __name__=="__main__":
    raise SystemExit(main())
