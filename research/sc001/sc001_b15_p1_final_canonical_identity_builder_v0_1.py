from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN="20260920T210446Z"
ART=ROOT/"docs/research/artifacts/b15-p1-identity-inventory"/RUN
NET=ROOT/"docs/research/sc001-b15-p1-canonical-network-registry-v0.1.json"
NATIVE=ROOT/"docs/research/sc001-b15-p1-native-asset-registry-v0.1.json"
FREEZE=ROOT/"docs/research/sc001-b15-p1-final-canonical-identity-builder-freeze-v0.1.json"
OUT=ROOT/"docs/research/artifacts/b15-p1-canonical-freeze"/RUN
PASS="B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS"
REVIEW="B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW"

def fail(s): raise RuntimeError(s)
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def blob(p): return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()
def canon_contract(v,rule):
    v=str(v or "")
    if rule.startswith("evm_"):
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}",v): return None
        return v.lower()
    return v if v else None
def strict_recent_listing(base,hits):
    b=re.escape(base)
    pats=[re.compile(rf"\bto\s+list\b.*\({b}\)\s+on\s+spot\b",re.I),
          re.compile(rf"\bnew\s+listing\s*:\s*{b}/USDT\b",re.I)]
    return [h for h in hits if any(p.search(str(h.get("title") or "")) for p in pats)]
def main():
    fr=load(FREEZE)
    checks={"runner_git_blob_sha":blob(Path(__file__).resolve()),"network_registry_git_blob_sha":blob(NET),"native_registry_git_blob_sha":blob(NATIVE)}
    for k,v in checks.items():
        if fr.get(k)!=v: fail(f"freeze mismatch: {k}")
    cands=load(ART/"common_base_candidates.json"); okx=load(ART/"okx_chain_identity_view.json"); byb=load(ART/"bybit_chain_identity_view.json")
    net=load(NET); nat=load(NATIVE)
    native={(x["network_uid"],x["native_asset"]) for x in nat["rows"]}
    omap={}; bmap={}
    for n in net["networks"]:
        for a in n["okx_aliases"]: omap[a]=n
        for a in n["bybit_chain_codes"]: bmap.setdefault(a,[]).append(n)
    stable={"PYUSD","RLUSD","USD1","USDC","USDS","USDT"}
    admitted=[]; reviews=[]; excluded=[]; routes=[]
    for c in cands:
        coin=c["base"]; reasons=[]
        if coin in stable: excluded.append({"asset":coin,"reasons":["STABLECOIN_OR_FIATLIKE_BASE"]}); continue
        if not c.get("okx_mature_90d"): excluded.append({"asset":coin,"reasons":["OKX_LT_90D_MATURE"]}); continue
        if strict_recent_listing(coin,c.get("recent_bybit_new_listing_hits") or []):
            excluded.append({"asset":coin,"reasons":["BYBIT_EXPLICIT_RECENT_SPOT_LISTING_LT_90D"]}); continue
        ors=[x for x in okx if x["coin"]==coin]; brs=[x for x in byb if x["coin"]==coin]
        matched=[]
        unresolved=False
        for o in ors:
            on=omap.get(o["chain_alias_without_coin_prefix"])
            if not on: unresolved=True; continue
            candidates=[n for n in bmap.get("",[]) if False]
            for b in brs:
                bn=[n for n in bmap.get(b["chain_raw"],[]) if n["network_uid"]==on["network_uid"]]
                if not bn: continue
                n=bn[0]
                allowed={x.strip() for x in n["bybit_chain_types"]}
                if str(b.get("chainType") or "").strip() not in allowed: unresolved=True; continue
                oc=str(o.get("contract_address_raw") or ""); bc=str(b.get("contract_address_raw") or "")
                if not oc and not bc:
                    if (n["network_uid"],coin) not in native: unresolved=True; continue
                    kind="native"; ident="native:"+coin
                elif bool(oc)!=bool(bc): unresolved=True; continue
                else:
                    a=canon_contract(oc,n["contract_rule"]); z=canon_contract(bc,n["contract_rule"])
                    if not a or not z or a!=z: unresolved=True; continue
                    kind="token"; ident=a
                matched.append({"asset":coin,"network_uid":n["network_uid"],"kind":kind,"representation_identity":ident,
                    "okx_chain":o["chain_raw"],"bybit_chain":b["chain_raw"],"bybit_chainType":b["chainType"]})
        uniq={ (x["network_uid"],x["kind"],x["representation_identity"]):x for x in matched}
        matched=list(uniq.values())
        if not matched:
            reviews.append({"asset":coin,"reasons":["NO_PROVEN_COMMON_REPRESENTATION"]}); continue
        # Fail closed: any observed alias not covered by registry can be an alternative route.
        if unresolved:
            reviews.append({"asset":coin,"reasons":["UNRESOLVED_OBSERVED_ROUTE_OR_IDENTITY"],"proven_representations":matched}); continue
        admitted.append({"asset":coin,"representations":matched})
        for m in matched:
            routes.append({**m,"direction":"OKX_TO_BYBIT"})
            routes.append({**m,"direction":"BYBIT_TO_OKX"})
    # Quote graph is independently required and may remain REVIEW.
    q_or=[x for x in okx if x["coin"]=="USDT"]; q_br=[x for x in byb if x["coin"]=="USDT"]
    quote=[]; quote_review=False
    for o in q_or:
        n=omap.get(o["chain_alias_without_coin_prefix"])
        if not n: quote_review=True; continue
        found=False
        for b in q_br:
            if not any(x["network_uid"]==n["network_uid"] for x in bmap.get(b["chain_raw"],[])): continue
            oc=canon_contract(o["contract_address_raw"],n["contract_rule"]); bc=canon_contract(b["contract_address_raw"],n["contract_rule"])
            if oc and bc and oc==bc:
                found=True; quote.append({"asset":"USDT","network_uid":n["network_uid"],"representation_identity":oc,"okx_chain":o["chain_raw"],"bybit_chain":b["chain_raw"]})
        if not found: quote_review=True
    OUT.mkdir(parents=True,exist_ok=True)
    for name,obj in [("ADMITTED.json",admitted),("IDENTITY_REVIEW.json",reviews),("EXCLUDED.json",excluded),("directed_route_graph.json",routes),("usdt_quote_rebalance_graph.json",quote)]:
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    status=PASS if not reviews and not quote_review else REVIEW
    summary={"status":status,"source_run":RUN,"admitted_assets":len(admitted),"identity_review_assets":len(reviews),"excluded_assets":len(excluded),"directed_edges":len(routes),"quote_routes":len(quote),"quote_review":quote_review,
      "price_data_used":False,"transfer_status_used_for_selection":False}
    (OUT/"final_builder_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(status)
    for k,v in summary.items(): print(k,"=",v)
    return 0 if status==PASS else 3
if __name__=="__main__": raise SystemExit(main())
