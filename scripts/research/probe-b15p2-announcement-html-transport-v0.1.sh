#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

OUT_DIR="/home/botmarket/sc001_data/SC001_B15P2_ANNOUNCEMENT_TRANSPORT_PROBE"
OUT="$OUT_DIR/announcement_html_transport_probe_v0_1.json"
DOG_URL="https://announcements.bybit.com/en-US/article/delisting-of-dogusdt-perpetual-contract-blt9ee6b6807b7ba01f/"
TON_URL="https://announcements.bybit.com/en-US/article/delisting-of-tonusdt-perpetual-contract-bltd27f1f00e6b0f5ed/"
API_URL="https://api.bybit.com/v5/announcements/index?locale=en-US&type=delistings&limit=1"
BROWSER_UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"
BOT_UA="BotMarketplace-SC001-B15P2-TransportProbe/0.1"

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || { echo "PROBE_REVIEW reason=must_run_as_root"; exit 2; }
}

need_tools() {
  local cmd
  for cmd in curl python3 getent install chown chmod date; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "PROBE_REVIEW reason=missing_tool:$cmd"; exit 2; }
  done
}

curl_probe() {
  local label="$1" family="$2" ua="$3" url="$4"
  local result rc
  set +e
  result="$(
    curl -sS -L "$family" \
      --proto '=https' --proto-redir '=https' \
      --connect-timeout 5 --max-time 15 \
      -A "$ua" -H 'Accept: text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8' \
      -o /dev/null \
      -w '{"http_code":"%{http_code}","remote_ip":"%{remote_ip}","remote_port":"%{remote_port}","time_namelookup":"%{time_namelookup}","time_connect":"%{time_connect}","time_appconnect":"%{time_appconnect}","time_starttransfer":"%{time_starttransfer}","time_total":"%{time_total}","ssl_verify_result":"%{ssl_verify_result}","url_effective":"%{url_effective}"}' \
      "$url" 2>&1
  )"
  rc="$?"
  set -e
  python3 - "$label" "$rc" "$result" <<'PY'
import json,sys
label,rc,raw=sys.argv[1],int(sys.argv[2]),sys.argv[3]
obj={"label":label,"curl_exit_code":rc}
try:
    start=raw.rfind('{"http_code"')
    if start>=0:
        prefix=raw[:start].strip()
        data=json.loads(raw[start:])
        obj.update(data)
        if prefix:
            obj["stderr_or_prefix"]=prefix
    else:
        obj["stderr_or_prefix"]=raw
except Exception as exc:
    obj["parse_error"]=f"{type(exc).__name__}: {exc}"
    obj["raw"]=raw
print(json.dumps(obj,sort_keys=True))
PY
}

python_urllib_probe() {
  python3 - "$DOG_URL" <<'PY'
import json,ssl,socket,sys,time,urllib.request,urllib.error
url=sys.argv[1]
out={"label":"python_urllib_dog_default","url":url}
t0=time.monotonic()
try:
    req=urllib.request.Request(url,headers={
        "User-Agent":"BotMarketplace-SC001-B15P2-TransportProbe/0.1",
        "Accept":"text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(req,timeout=10) as resp:
        out["status"]=getattr(resp,"status",None)
        out["final_url"]=resp.geturl()
        chunk=resp.read(4096)
        out["read_bytes"]=len(chunk)
        out["content_type"]=resp.headers.get("Content-Type")
    out["ok"]=True
except Exception as exc:
    out["ok"]=False
    out["error_type"]=type(exc).__name__
    out["error_message"]=str(exc)
out["elapsed_seconds"]=round(time.monotonic()-t0,3)
print(json.dumps(out,sort_keys=True))
PY
}

main() {
  need_root
  need_tools
  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"

  local tmp="$OUT.tmp"
  {
    echo '{'
    printf '"schema":"sc001.b15p2_announcement_html_transport_probe.v0.1",\n'
    printf '"date":"2026-09-28",\n'
    printf '"price_accessed":false,\n'
    printf '"basis_accessed":false,\n'
    printf '"returns_accessed":false,\n'
    printf '"pnl_accessed":false,\n'
    printf '"dns":{\n'
    printf '"announcements_ahostsv4":'
    getent ahostsv4 announcements.bybit.com 2>/dev/null | awk '{print $1}' | sort -u | python3 -c 'import json,sys; print(json.dumps([x.strip() for x in sys.stdin if x.strip()]))'
    printf ',"announcements_ahostsv6":'
    getent ahostsv6 announcements.bybit.com 2>/dev/null | awk '{print $1}' | sort -u | python3 -c 'import json,sys; print(json.dumps([x.strip() for x in sys.stdin if x.strip()]))'
    printf ',"api_ahostsv4":'
    getent ahostsv4 api.bybit.com 2>/dev/null | awk '{print $1}' | sort -u | python3 -c 'import json,sys; print(json.dumps([x.strip() for x in sys.stdin if x.strip()]))'
    printf ',"api_ahostsv6":'
    getent ahostsv6 api.bybit.com 2>/dev/null | awk '{print $1}' | sort -u | python3 -c 'import json,sys; print(json.dumps([x.strip() for x in sys.stdin if x.strip()]))'
    printf '},\n"probes":[\n'

    curl_probe "curl_ipv4_dog_browser_ua" "-4" "$BROWSER_UA" "$DOG_URL"
    echo ','
    curl_probe "curl_ipv6_dog_browser_ua" "-6" "$BROWSER_UA" "$DOG_URL"
    echo ','
    curl_probe "curl_ipv4_dog_bot_ua" "-4" "$BOT_UA" "$DOG_URL"
    echo ','
    curl_probe "curl_ipv4_ton_browser_ua" "-4" "$BROWSER_UA" "$TON_URL"
    echo ','
    curl_probe "curl_ipv4_announcement_api_control" "-4" "$BOT_UA" "$API_URL"
    echo ','
    python_urllib_probe
    echo
    printf ']\n}\n'
  } > "$tmp"

  python3 - "$tmp" "$OUT" <<'PY'
import json,sys
from pathlib import Path
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
obj=json.loads(src.read_text(encoding="utf-8"))
dst.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
  rm -f "$tmp"
  chown botmarket:botmarket "$OUT"
  chmod 0640 "$OUT"

  python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_COMPLETE")
for p in obj["probes"]:
    print(
        p.get("label"),
        "curl_rc="+str(p.get("curl_exit_code")) if "curl_exit_code" in p else "ok="+str(p.get("ok")),
        "http="+str(p.get("http_code")),
        "remote_ip="+str(p.get("remote_ip")),
        "ttfb="+str(p.get("time_starttransfer")),
        "total="+str(p.get("time_total") or p.get("elapsed_seconds")),
        "error="+str(p.get("stderr_or_prefix") or p.get("error_message")),
    )
print("price/basis/returns/PnL=CLOSED")
print("report =",sys.argv[1])
PY
}

main "$@"
