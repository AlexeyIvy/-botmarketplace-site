"""One-tap Android/Pydroid runner for the two frozen forward trackers.

This orchestration layer does NOT change either research engine or inception.
It runs the already-frozen R009 and R003 mobile launchers sequentially so they
remain operationally independent and easier to audit on a phone.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import traceback

DOWNLOAD = Path("/storage/emulated/0/Download")
BUNDLE_DIR = DOWNLOAD / "FORWARD_BUNDLE"
STATUS_FILE = BUNDLE_DIR / "forward_bundle_status.txt"

R009_LAUNCHER_COMMIT = "6579bc0720e52ded057607420132640d5a5d49ac"
R009_PATH = "research/r009/r009_e002_forward_paper_mobile.py"

R003_LAUNCHER_COMMIT = "8367b239795f345d97b09fc9ab957aa3f3d31e57"
R003_PATH = "research/r003/r003_e003_forward_paper_mobile_v0_2.py"

BASE = "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site"


def fetch_text(commit: str, path: str) -> str:
    url = f"{BASE}/{commit}/{path}"
    req = Request(url, headers={"User-Agent": "botmarketplace-forward-bundle/0.1"})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def run_launcher(name: str, commit: str, path: str) -> tuple[bool, str]:
    print("\n" + "=" * 78)
    print(f"START {name}")
    print("Pinned launcher commit:", commit)
    print("=" * 78)
    try:
        source = fetch_text(commit, path)
        local = BUNDLE_DIR / Path(path).name
        local.write_text(source, encoding="utf-8")
        ns = {"__name__": "__main__", "__file__": str(local)}
        exec(compile(source, str(local), "exec"), ns)
        print(f"{name}: OK")
        return True, "OK"
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        print(f"{name}: FAILED -> {msg}")
        traceback.print_exc()
        return False, msg


def main() -> None:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)

    print("BOTMARKETPLACE FORWARD BUNDLE")
    print("UTC start:", started.isoformat())
    print("R009 and R003 remain separate frozen experiments.")
    print("They are run sequentially to reduce Android memory/network contention.")

    results = []
    results.append(("R009-E002",) + run_launcher("R009-E002", R009_LAUNCHER_COMMIT, R009_PATH))
    results.append(("R003-E003",) + run_launcher("R003-E003", R003_LAUNCHER_COMMIT, R003_PATH))

    finished = datetime.now(timezone.utc)
    lines = [
        "BotMarketplace forward bundle status",
        f"started_utc={started.isoformat()}",
        f"finished_utc={finished.isoformat()}",
        f"r009_launcher_commit={R009_LAUNCHER_COMMIT}",
        f"r003_launcher_commit={R003_LAUNCHER_COMMIT}",
    ]
    for name, ok, msg in results:
        lines.append(f"{name}={'OK' if ok else 'FAILED'} | {msg}")
    STATUS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n" + "=" * 78)
    print("BUNDLE FINISHED")
    for name, ok, msg in results:
        print(f"{name}: {'OK' if ok else 'FAILED'}")
    print("Status file:", STATUS_FILE)
    print("R009 results stay in /Download/R009_E002_FORWARD")
    print("R003 results stay in /Download/R003_E003_FORWARD")
    print("=" * 78)


if __name__ == "__main__":
    main()
