from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import re
import shlex
import socket
import stat
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-B15-P1-NONPRICE-IDENTITY-INVENTORY-PROBE-V0.1"
PASS = "B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS"
REVIEW = "B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_REVIEW"

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-b15-p1-canonical-route-universe-identity-freeze-protocol-v0.1.md"
SECURITY = ROOT / "docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md"
CAPABILITY_PASS = ROOT / "docs/research/sc001-b15-p1-readonly-capability-pass-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-b15-p1-canonical-identity-inventory-probe-freeze-v0.1.json"
ENV_FILE = Path("/home/botmarket/.config/sc001/b15-p1.env")

DEFAULT_OUT_ROOT = Path("/home/botmarket/sc001_data/B15_P1_IDENTITY_INVENTORY_V01")
TIMEOUT = 30
MAX_JSON = 16_000_000
RECV_WINDOW = "5000"
MATURE_DAYS = 90
DELISTING_LOOKBACK_DAYS = 180
ANNOUNCEMENT_PAGE_LIMIT = 50
ANNOUNCEMENT_MAX_PAGES = 30


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso_ms(dt: datetime | None = None) -> str:
    now = dt or utc_now()
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def load_json_file(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def require_freeze() -> dict:
    fr = load_json_file(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_V01":
        fail("freeze status mismatch")
    checks = {
        "runner_git_blob_sha": git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha": git_blob(PROTOCOL),
        "security_contract_git_blob_sha": git_blob(SECURITY),
        "capability_pass_git_blob_sha": git_blob(CAPABILITY_PASS),
    }
    for key, value in checks.items():
        if fr.get(key) != value:
            fail(f"freeze identity mismatch: {key}")
    if fr.get("maturity_days") != MATURE_DAYS:
        fail("maturity_days freeze mismatch")
    return fr


def parse_env(path: Path) -> dict[str, str]:
    if not path.exists():
        fail(f"credential file missing: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        fail(f"credential file mode must be 0600, got {oct(mode)}")
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            fail("malformed credential env line")
        key, value = line.split("=", 1)
        parts = shlex.split(value, posix=True)
        if len(parts) != 1:
            fail(f"malformed credential value for {key}")
        out[key] = parts[0]
    required = (
        "SC001_B15_OKX_API_KEY",
        "SC001_B15_OKX_API_SECRET",
        "SC001_B15_OKX_PASSPHRASE",
        "SC001_B15_OKX_BASE_URL",
        "SC001_B15_BYBIT_API_KEY",
        "SC001_B15_BYBIT_API_SECRET",
        "SC001_B15_BYBIT_BASE_URL",
    )
    for key in required:
        if not out.get(key):
            fail(f"missing credential variable: {key}")
    return out


_ORIG_GETADDRINFO = socket.getaddrinfo


def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    rows = _ORIG_GETADDRINFO(host, port, socket.AF_INET, type, proto, flags)
    if not rows:
        fail(f"no IPv4 address resolved for {host}")
    return rows


socket.getaddrinfo = ipv4_only_getaddrinfo


class SafeHTTPError(RuntimeError):
    def __init__(self, status: int, url: str, body: str):
        self.status = status
        self.url = url
        self.body = body
        super().__init__(f"HTTP {status} for {url}")


def http_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(
        url,
        headers=headers or {
            "User-Agent": "BotMarketplace-SC001-B15-P1-IdentityProbe/0.1",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read(MAX_JSON + 1)
            status = int(getattr(resp, "status", 200))
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_JSON + 1)
        body = raw.decode("utf-8", "replace")
        raise SafeHTTPError(int(exc.code), url, body[:4000]) from None
    if status != 200:
        fail(f"HTTP status {status}: {url}")
    if len(raw) > MAX_JSON:
        fail("JSON response cap exceeded")
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        fail("JSON object response expected")
    return obj


def okx_private(base: str, key: str, secret: str, passphrase: str, path: str) -> dict:
    ts = utc_iso_ms()
    prehash = ts + "GET" + path
    sig = base64.b64encode(
        hmac.new(secret.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    headers = {
        "User-Agent": "BotMarketplace-SC001-B15-P1-IdentityProbe/0.1",
        "Accept": "application/json",
        "OK-ACCESS-KEY": key,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
    }
    return http_json(base + path, headers)


def bybit_private(
    base: str, key: str, secret: str, path: str, query: str = ""
) -> dict:
    ts = str(int(time.time() * 1000))
    payload = ts + key + RECV_WINDOW + query
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    headers = {
        "User-Agent": "BotMarketplace-SC001-B15-P1-IdentityProbe/0.1",
        "Accept": "application/json",
        "X-BAPI-API-KEY": key,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
        "X-BAPI-SIGN": sig,
    }
    url = base + path + ("?" + query if query else "")
    return http_json(url, headers)


def ensure_read_only(cfg: dict[str, str]) -> dict:
    okx_base = cfg["SC001_B15_OKX_BASE_URL"].rstrip("/")
    bybit_base = cfg["SC001_B15_BYBIT_BASE_URL"].rstrip("/")

    okx_cfg = okx_private(
        okx_base,
        cfg["SC001_B15_OKX_API_KEY"],
        cfg["SC001_B15_OKX_API_SECRET"],
        cfg["SC001_B15_OKX_PASSPHRASE"],
        "/api/v5/account/config",
    )
    if str(okx_cfg.get("code")) != "0":
        fail(f"OKX account/config code={okx_cfg.get('code')} msg={okx_cfg.get('msg')}")
    rows = okx_cfg.get("data") or []
    if len(rows) != 1:
        fail("OKX account config row mismatch")
    perms = {
        x.strip()
        for x in str(rows[0].get("perm") or "").split(",")
        if x.strip()
    }
    if perms != {"read_only"}:
        fail(f"OKX permission is not exactly read_only: {sorted(perms)}")

    bybit_cfg = bybit_private(
        bybit_base,
        cfg["SC001_B15_BYBIT_API_KEY"],
        cfg["SC001_B15_BYBIT_API_SECRET"],
        "/v5/user/query-api",
    )
    if int(bybit_cfg.get("retCode", -1)) != 0:
        fail(
            f"Bybit query-api retCode={bybit_cfg.get('retCode')} "
            f"msg={bybit_cfg.get('retMsg')}"
        )
    result = bybit_cfg.get("result") or {}
    if int(result.get("readOnly", -1)) != 1:
        fail(f"Bybit key is not read-only: {result.get('readOnly')}")
    wallet = (result.get("permissions") or {}).get("Wallet") or []
    if "Withdraw" in wallet:
        fail("Bybit read-only capability invariant violated: Withdraw token present")

    return {
        "okx_permission": "read_only",
        "bybit_readOnly": 1,
        "bybit_withdraw_token_present": False,
    }


def fetch_okx_sources(cfg: dict[str, str]) -> tuple[dict, dict]:
    base = cfg["SC001_B15_OKX_BASE_URL"].rstrip("/")
    instruments = http_json(base + "/api/v5/public/instruments?instType=SPOT")
    if str(instruments.get("code")) != "0":
        fail(
            f"OKX public instruments code={instruments.get('code')} "
            f"msg={instruments.get('msg')}"
        )
    currencies = okx_private(
        base,
        cfg["SC001_B15_OKX_API_KEY"],
        cfg["SC001_B15_OKX_API_SECRET"],
        cfg["SC001_B15_OKX_PASSPHRASE"],
        "/api/v5/asset/currencies",
    )
    if str(currencies.get("code")) != "0":
        fail(
            f"OKX currencies code={currencies.get('code')} "
            f"msg={currencies.get('msg')}"
        )
    return instruments, currencies


def fetch_bybit_sources(cfg: dict[str, str]) -> tuple[dict, dict]:
    base = cfg["SC001_B15_BYBIT_BASE_URL"].rstrip("/")
    instruments = http_json(base + "/v5/market/instruments-info?category=spot")
    if int(instruments.get("retCode", -1)) != 0:
        fail(
            f"Bybit spot instruments retCode={instruments.get('retCode')} "
            f"msg={instruments.get('retMsg')}"
        )
    coin_info = bybit_private(
        base,
        cfg["SC001_B15_BYBIT_API_KEY"],
        cfg["SC001_B15_BYBIT_API_SECRET"],
        "/v5/asset/coin/query-info",
    )
    if int(coin_info.get("retCode", -1)) != 0:
        fail(
            f"Bybit coin-info retCode={coin_info.get('retCode')} "
            f"msg={coin_info.get('retMsg')}"
        )
    return instruments, coin_info


def fetch_bybit_announcements(
    base: str, type_key: str, tag: str | None = None
) -> list[dict]:
    out: list[dict] = []
    total: int | None = None
    for page in range(1, ANNOUNCEMENT_MAX_PAGES + 1):
        params = {
            "locale": "en-US",
            "type": type_key,
            "page": str(page),
            "limit": str(ANNOUNCEMENT_PAGE_LIMIT),
        }
        if tag:
            params["tag"] = tag
        url = base + "/v5/announcements/index?" + urllib.parse.urlencode(params)
        obj = http_json(url)
        if int(obj.get("retCode", -1)) != 0:
            fail(
                f"Bybit announcements retCode={obj.get('retCode')} "
                f"msg={obj.get('retMsg')}"
            )
        result = obj.get("result") or {}
        rows = result.get("list") or []
        if total is None:
            total = int(result.get("total") or 0)
        if not rows:
            break
        out.extend(row for row in rows if isinstance(row, dict))
        if total is not None and len(out) >= total:
            break
        if len(rows) < ANNOUNCEMENT_PAGE_LIMIT:
            break
    if (
        total is not None
        and len(out) < total
        and len(out) >= ANNOUNCEMENT_PAGE_LIMIT * ANNOUNCEMENT_MAX_PAGES
    ):
        fail(
            f"Bybit announcement collection truncated for type={type_key} tag={tag}: "
            f"collected={len(out)} total={total}"
        )
    return out


def as_int_ms(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        x = int(str(value))
    except Exception:
        return None
    return x if x > 0 else None


def okx_continuous_anchor_ms(row: dict) -> int | None:
    return as_int_ms(row.get("contTdSwTime")) or as_int_ms(row.get("listTime"))


def is_okx_primary_market(row: dict) -> bool:
    return (
        str(row.get("instType") or "") == "SPOT"
        and str(row.get("quoteCcy") or "").upper() == "USDT"
        and str(row.get("state") or "") == "live"
        and str(row.get("instCategory") or "") == "1"
        and bool(str(row.get("baseCcy") or "").strip())
        and not bool(str(row.get("expTime") or "").strip())
    )


def is_bybit_primary_market(row: dict) -> bool:
    return (
        str(row.get("quoteCoin") or "").upper() == "USDT"
        and str(row.get("status") or "") == "Trading"
        and str(row.get("stTag") or "") == "0"
        and str(row.get("symbolType") or "") == ""
        and bool(str(row.get("baseCoin") or "").strip())
    )


def structural_exclusion_hints(base: str) -> list[str]:
    b = base.upper()
    out: list[str] = []
    stable_exact = {
        "USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDD", "USDE", "USDS",
        "PYUSD", "USDP", "GUSD", "BUSD", "USD1", "RLUSD", "EURC", "EURS",
    }
    if b in stable_exact or re.match(
        r"^(?:USD|EUR|GBP|JPY|CHF|AUD|CAD|HKD|SGD)[A-Z0-9]{0,6}$", b
    ):
        out.append("STABLECOIN_OR_FIATLIKE_BASE")
    if re.search(r"(?:2L|2S|3L|3S|5L|5S|BULL|BEAR|UP|DOWN)$", b):
        out.append("LEVERAGED_TOKEN_STYLE_BASE")
    return out


def announcement_time_ms(row: dict) -> int | None:
    return (
        as_int_ms(row.get("publishTime"))
        or as_int_ms(row.get("dateTimestamp"))
        or as_int_ms(row.get("startDateTimestamp"))
        or as_int_ms(row.get("startDataTimestamp"))
    )


def announcement_safe_view(rows: list[dict], cutoff_ms: int | None = None) -> list[dict]:
    out = []
    for row in rows:
        ts = announcement_time_ms(row)
        if cutoff_ms is not None and ts is not None and ts < cutoff_ms:
            continue
        typ = row.get("type") or {}
        out.append(
            {
                "title": str(row.get("title") or ""),
                "type_key": str(typ.get("key") or "") if isinstance(typ, dict) else "",
                "tags": list(row.get("tags") or []),
                "url": str(row.get("url") or ""),
                "publish_time_ms": ts,
            }
        )
    return out


def ticker_hits(base: str, rows: list[dict], cutoff_ms: int) -> list[dict]:
    pat = re.compile(rf"(?<![A-Z0-9]){re.escape(base.upper())}(?![A-Z0-9])")
    hits = []
    for row in rows:
        ts = announcement_time_ms(row)
        if ts is None or ts < cutoff_ms:
            continue
        hay = (
            str(row.get("title") or "") + " " + str(row.get("description") or "")
        ).upper()
        if pat.search(hay):
            typ = row.get("type") or {}
            hits.append(
                {
                    "title": str(row.get("title") or ""),
                    "type_key": str(typ.get("key") or "") if isinstance(typ, dict) else "",
                    "tags": list(row.get("tags") or []),
                    "url": str(row.get("url") or ""),
                    "publish_time_ms": ts,
                }
            )
    return hits


def normalize_okx_markets(raw: dict, freeze_ms: int) -> list[dict]:
    rows = raw.get("data") or []
    out = []
    maturity_cutoff = freeze_ms - MATURE_DAYS * 86400 * 1000
    for row in rows:
        if not isinstance(row, dict):
            continue
        base = str(row.get("baseCcy") or "").upper()
        quote = str(row.get("quoteCcy") or "").upper()
        if quote != "USDT":
            continue
        anchor = okx_continuous_anchor_ms(row)
        out.append(
            {
                "instId": str(row.get("instId") or ""),
                "base": base,
                "quote": quote,
                "state": str(row.get("state") or ""),
                "instCategory": str(row.get("instCategory") or ""),
                "listTime": as_int_ms(row.get("listTime")),
                "contTdSwTime": as_int_ms(row.get("contTdSwTime")),
                "continuous_anchor_ms": anchor,
                "mature_90d": bool(anchor is not None and anchor <= maturity_cutoff),
                "expTime": as_int_ms(row.get("expTime")),
                "primary_market_gate": is_okx_primary_market(row),
            }
        )
    return sorted(out, key=lambda x: (x["base"], x["instId"]))


def normalize_bybit_markets(raw: dict) -> list[dict]:
    rows = (raw.get("result") or {}).get("list") or []
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        quote = str(row.get("quoteCoin") or "").upper()
        if quote != "USDT":
            continue
        out.append(
            {
                "symbol": str(row.get("symbol") or ""),
                "symbolId": row.get("symbolId"),
                "base": str(row.get("baseCoin") or "").upper(),
                "quote": quote,
                "status": str(row.get("status") or ""),
                "symbolType": str(row.get("symbolType") or ""),
                "stTag": str(row.get("stTag") or ""),
                "primary_market_gate": is_bybit_primary_market(row),
            }
        )
    return sorted(out, key=lambda x: (x["base"], x["symbol"]))


def identity_view_okx_chains(raw: dict, include_coins: set[str]) -> list[dict]:
    rows = raw.get("data") or []
    out = []
    required = {"ccy", "chain", "canDep", "canWd"}
    for row in rows:
        if not isinstance(row, dict) or not required.issubset(row):
            fail("OKX currencies schema drift: required identity/status fields missing")
        ccy = str(row.get("ccy") or "").upper()
        if ccy not in include_coins:
            continue
        chain = str(row.get("chain") or "")
        prefix = ccy + "-"
        alias = chain[len(prefix):] if chain.upper().startswith(prefix) else chain
        out.append(
            {
                "coin": ccy,
                "chain_raw": chain,
                "chain_alias_without_coin_prefix": alias,
                "contract_address_raw": str(row.get("ctAddr") or ""),
                "mainNet": row.get("mainNet"),
            }
        )
    return sorted(out, key=lambda x: (x["coin"], x["chain_raw"]))


def identity_view_bybit_chains(raw: dict, include_coins: set[str]) -> list[dict]:
    rows = (raw.get("result") or {}).get("rows") or []
    out = []
    required = {"chain", "chainType", "chainDeposit", "chainWithdraw", "contractAddress"}
    for coin_row in rows:
        if not isinstance(coin_row, dict):
            fail("Bybit coin-info schema drift: coin row not object")
        coin = str(coin_row.get("coin") or "").upper()
        if coin not in include_coins:
            continue
        chains = coin_row.get("chains") or []
        for ch in chains:
            if not isinstance(ch, dict) or not required.issubset(ch):
                fail("Bybit coin-info schema drift: required identity/status fields missing")
            out.append(
                {
                    "coin": coin,
                    "chain_raw": str(ch.get("chain") or ""),
                    "chainType": str(ch.get("chainType") or ""),
                    "contract_address_raw": str(ch.get("contractAddress") or ""),
                }
            )
    return sorted(out, key=lambda x: (x["coin"], x["chain_raw"], x["chainType"]))


def build_chain_alias_census(okx_chains: list[dict], bybit_chains: list[dict]) -> dict:
    def census(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
        counts: dict[tuple[str, ...], set[str]] = {}
        for row in rows:
            key = tuple(str(row.get(f) or "") for f in fields)
            counts.setdefault(key, set()).add(str(row.get("coin") or ""))
        out = []
        for key, coins in counts.items():
            item = {field: value for field, value in zip(fields, key)}
            item["asset_count"] = len(coins)
            item["sample_assets"] = sorted(coins)[:20]
            out.append(item)
        return sorted(out, key=lambda x: tuple(str(x.get(f) or "") for f in fields))

    return {
        "okx": census(okx_chains, ("chain_raw", "chain_alias_without_coin_prefix")),
        "bybit": census(bybit_chains, ("chain_raw", "chainType")),
    }


def build_common_candidates(
    okx_markets: list[dict],
    bybit_markets: list[dict],
    okx_chains: list[dict],
    bybit_chains: list[dict],
    new_listing_rows: list[dict],
    delisting_rows: list[dict],
    freeze_ms: int,
) -> list[dict]:
    okx_by_base = {
        r["base"]: r for r in okx_markets if r["primary_market_gate"]
    }
    bybit_by_base = {
        r["base"]: r for r in bybit_markets if r["primary_market_gate"]
    }
    okx_chain_by_coin: dict[str, list[dict]] = {}
    for row in okx_chains:
        okx_chain_by_coin.setdefault(row["coin"], []).append(row)
    bybit_chain_by_coin: dict[str, list[dict]] = {}
    for row in bybit_chains:
        bybit_chain_by_coin.setdefault(row["coin"], []).append(row)

    listing_cutoff = freeze_ms - MATURE_DAYS * 86400 * 1000
    delist_cutoff = freeze_ms - DELISTING_LOOKBACK_DAYS * 86400 * 1000

    out = []
    for base in sorted(set(okx_by_base) & set(bybit_by_base)):
        okx = okx_by_base[base]
        bybit = bybit_by_base[base]
        out.append(
            {
                "base": base,
                "okx_instId": okx["instId"],
                "bybit_symbol": bybit["symbol"],
                "okx_mature_90d": okx["mature_90d"],
                "recent_bybit_new_listing_hits": ticker_hits(
                    base, new_listing_rows, listing_cutoff
                ),
                "recent_bybit_spot_delisting_hits": ticker_hits(
                    base, delisting_rows, delist_cutoff
                ),
                "structural_exclusion_hints": structural_exclusion_hints(base),
                "okx_chain_aliases": [
                    {
                        "chain_raw": x["chain_raw"],
                        "alias": x["chain_alias_without_coin_prefix"],
                        "contract_address_raw": x["contract_address_raw"],
                        "mainNet": x["mainNet"],
                    }
                    for x in okx_chain_by_coin.get(base, [])
                ],
                "bybit_chain_aliases": [
                    {
                        "chain_raw": x["chain_raw"],
                        "chainType": x["chainType"],
                        "contract_address_raw": x["contract_address_raw"],
                    }
                    for x in bybit_chain_by_coin.get(base, [])
                ],
            }
        )
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(data, encoding="utf-8")


def safe_http_error_summary(exc: SafeHTTPError) -> str:
    try:
        obj = json.loads(exc.body)
        if isinstance(obj, dict):
            safe = {
                k: obj.get(k)
                for k in ("code", "msg", "retCode", "retMsg")
                if k in obj
            }
            if safe:
                return json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        pass
    return exc.body[:500].replace("\n", " ").replace("\r", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    args = ap.parse_args()

    started = utc_now()
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.out_root) / run_id
    freeze_ms = int(started.timestamp() * 1000)

    try:
        require_freeze()
        cfg = parse_env(ENV_FILE)
        permissions = ensure_read_only(cfg)

        okx_instruments, okx_currencies = fetch_okx_sources(cfg)
        bybit_instruments, bybit_coin_info = fetch_bybit_sources(cfg)

        bybit_base = cfg["SC001_B15_BYBIT_BASE_URL"].rstrip("/")
        bybit_new = fetch_bybit_announcements(
            bybit_base, "new_crypto", "Spot Listings"
        )
        bybit_delist = fetch_bybit_announcements(
            bybit_base, "delistings", "Spot"
        )

        okx_markets = normalize_okx_markets(okx_instruments, freeze_ms)
        bybit_markets = normalize_bybit_markets(bybit_instruments)

        okx_primary = {
            r["base"] for r in okx_markets if r["primary_market_gate"]
        }
        bybit_primary = {
            r["base"] for r in bybit_markets if r["primary_market_gate"]
        }
        include_coins = (okx_primary & bybit_primary) | {"USDT"}

        okx_chains = identity_view_okx_chains(okx_currencies, include_coins)
        bybit_chains = identity_view_bybit_chains(bybit_coin_info, include_coins)

        candidates = build_common_candidates(
            okx_markets,
            bybit_markets,
            okx_chains,
            bybit_chains,
            bybit_new,
            bybit_delist,
            freeze_ms,
        )
        alias_census = build_chain_alias_census(okx_chains, bybit_chains)

        raw_dir = run_dir / "raw"
        safe_dir = run_dir / "safe"

        write_json(raw_dir / "okx_spot_instruments.json", okx_instruments)
        write_json(raw_dir / "okx_currencies.json", okx_currencies)
        write_json(raw_dir / "bybit_spot_instruments.json", bybit_instruments)
        write_json(raw_dir / "bybit_coin_info.json", bybit_coin_info)
        write_json(raw_dir / "bybit_new_crypto_spot_listings.json", bybit_new)
        write_json(raw_dir / "bybit_spot_delistings.json", bybit_delist)

        write_json(safe_dir / "okx_spot_usdt_markets.json", okx_markets)
        write_json(safe_dir / "bybit_spot_usdt_markets.json", bybit_markets)
        write_json(safe_dir / "okx_chain_identity_view.json", okx_chains)
        write_json(safe_dir / "bybit_chain_identity_view.json", bybit_chains)
        write_json(safe_dir / "common_base_candidates.json", candidates)
        write_json(safe_dir / "chain_alias_census.json", alias_census)

        listing_cutoff = freeze_ms - MATURE_DAYS * 86400 * 1000
        delist_cutoff = freeze_ms - DELISTING_LOOKBACK_DAYS * 86400 * 1000
        write_json(
            safe_dir / "recent_bybit_new_crypto_spot_listings.json",
            announcement_safe_view(bybit_new, listing_cutoff),
        )
        write_json(
            safe_dir / "recent_bybit_spot_delistings.json",
            announcement_safe_view(bybit_delist, delist_cutoff),
        )

        files = sorted(
            [p for p in run_dir.rglob("*.json") if p.name != "run_manifest.json"]
        )
        hashes = {
            str(p.relative_to(run_dir)): sha256_file(p)
            for p in files
        }

        summary = {
            "stage": STAGE,
            "status": PASS,
            "run_id": run_id,
            "started_utc": utc_iso_ms(started),
            "maturity_days": MATURE_DAYS,
            "transport_family": "IPv4-only",
            "permissions": permissions,
            "price_endpoints_called": False,
            "order_endpoints_called": False,
            "transfer_endpoints_called": False,
            "withdraw_endpoints_called": False,
            "secret_values_printed": False,
            "okx_spot_usdt_rows": len(okx_markets),
            "okx_primary_market_bases": len(okx_primary),
            "bybit_spot_usdt_rows": len(bybit_markets),
            "bybit_primary_market_bases": len(bybit_primary),
            "common_primary_base_candidates": len(candidates),
            "identity_view_okx_chain_rows": len(okx_chains),
            "identity_view_bybit_chain_rows": len(bybit_chains),
            "bybit_new_listing_rows_collected": len(bybit_new),
            "bybit_delisting_rows_collected": len(bybit_delist),
            "output_hashes_sha256": hashes,
            "next_state": "NETWORK_ALIAS_AND_NATIVE_IDENTITY_REVIEW",
        }
        write_json(run_dir / "run_manifest.json", summary)

        print(PASS)
        print("run_dir =", run_dir)
        print("common_primary_base_candidates =", len(candidates))
        print("okx_identity_chain_rows =", len(okx_chains))
        print("bybit_identity_chain_rows =", len(bybit_chains))
        print("safe_chain_alias_census =", safe_dir / "chain_alias_census.json")
        print("safe_common_candidates =", safe_dir / "common_base_candidates.json")
        print("price/order/transfer/withdraw endpoints called = False")
        print("secret_values_printed = False")
        return 0

    except SafeHTTPError as exc:
        print(REVIEW)
        print("http_status =", exc.status)
        print("safe_body =", safe_http_error_summary(exc))
        print("transport_family = IPv4-only")
        print("price/order/transfer/withdraw endpoints called = False")
        print("secret_values_printed = False")
        return 2
    except Exception as exc:
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        print("transport_family = IPv4-only")
        print("price/order/transfer/withdraw endpoints called = False")
        print("secret_values_printed = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
