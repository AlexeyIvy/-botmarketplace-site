"""Pydroid launcher for frozen R002 availability/domain audit v0.1."""

from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
AUDIT_COMMIT = "b4f77bb9f60843185fb78708b3b107e81511ca18"
AUDIT_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + AUDIT_COMMIT
    + "/research/r002/binance_availability_domain_audit_mobile.py"
)
LOCAL = DOWNLOAD / "r002_availability_domain_audit_v0_1.py"


def main():
    print("R002 availability/domain audit")
    print("Frozen audit commit:", AUDIT_COMMIT)
    req = Request(AUDIT_URL, headers={"User-Agent": "r002-research-mobile/0.1"})
    with urlopen(req, timeout=60) as resp:
        LOCAL.write_bytes(resp.read())
    source = LOCAL.read_text(encoding="utf-8")
    namespace = {"__name__": "__main__", "__file__": str(LOCAL)}
    sys.argv = [str(LOCAL)]
    exec(compile(source, str(LOCAL), "exec"), namespace)


if __name__ == "__main__":
    main()
