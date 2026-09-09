"""R008-E003 symmetric recovery-release redesign screen v0.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r008-v0.2-symmetric-recovery-protocol-v0.1"
SOURCE_URL = (
    "https://api.blockchain.info/charts/market-price"
    "?timespan=all&format=json&sampled=false"
)

BASE = 0.10
TRANCHE = 0.025
THRESH = (-0.20, -0.35, -0.50, -0.65)
FEES = (0.0005, 0.0010, 0.0025, 0.0050)
BASE_FEE = 0.0010
DAYS_PER_YEAR = 365.25
EPS = 1e-12

PRIMARY_START = pd.Timestamp("2013-01-01")
PRE2020_END = pd.Timestamp("2019-12-31")
REPLAY_START = pd.Timestamp("2020-01-01")
LATE_START = pd.Timestamp("2023-01-01")
MIN_ONE_DAY_GAP_SHARE = 0.98
MAX_ALLOWED_GAP_DAYS = 7


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_source() -> tuple[bytes, dict]:
    req = Request(SOURCE_URL, headers={"User-Agent": "botmarketplace-r008-e003/0.1"})
    with urlopen(req, timeout=90) as resp:
        raw = resp.read()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("values"), list) or not obj["values"]:
        raise ValueError("Unexpected Blockchain.com response schema")
    return raw, obj


def clean_source(obj: dict) -> tuple[pd.DataFrame, int]:
    rows = []
    for item in obj["values"]:
        if isinstance(item, dict):
            rows.append({"x": item.get("x"), "price": item.get("y")})
    x = pd.DataFrame(rows)
    if x.empty:
        raise ValueError("No parseable source rows")
    x["date"] = pd.to_datetime(
        pd.to_numeric(x["x"], errors="coerce"), unit="s", utc=True, errors="coerce"
    ).dt.tz_convert(None).dt.normalize()
    x["price"] = pd.to_numeric(x["price"], errors="coerce")
    x = x.dropna(subset=["date", "price"])
    x = x[x["price"] > 0].sort_values("date")
    dup = int(x["date"].duplicated().sum())
    x = x.drop_duplicates("date", keep="last")[["date", "price"]].reset_index(drop=True)
    if len(x) < 1000:
        raise ValueError(f"Long-history source unexpectedly short: {len(x)}")
    return x, dup


def audit_source(raw_obj: dict, clean: pd.DataFrame, duplicate_count: int) -> dict:
    dates = clean["date"]
    gaps = dates.diff().dt.days.dropna()
    primary = clean[clean["date"] >= PRIMARY_START].copy()
    pgaps = primary["date"].diff().dt.days.dropna()
    one_day_share = float((pgaps == 1).mean()) if len(pgaps) else 0.0
    max_gap = int(pgaps.max()) if len(pgaps) else 0
    long_gaps = int((pgaps > 1).sum()) if len(pgaps) else 0
    missing_days = int((pgaps[pgaps > 1] - 1).sum()) if len(pgaps) else 0
    passed = (
        len(primary) >= 1000
        and one_day_share >= MIN_ONE_DAY_GAP_SHARE
        and max_gap <= MAX_ALLOWED_GAP_DAYS
    )
    return {
        "status": "PASS" if passed else "DATA_REDESIGN",
        "source_url": SOURCE_URL,
        "source_name": raw_obj.get("name"),
        "source_unit": raw_obj.get("unit"),
        "source_period": raw_obj.get("period"),
        "raw_values": len(raw_obj.get("values", [])),
        "clean_rows": len(clean),
        "clean_start": clean["date"].iloc[0].date().isoformat(),
        "clean_end": clean["date"].iloc[-1].date().isoformat(),
        "duplicate_raw_dates_before_dedup": duplicate_count,
        "all_history_max_gap_days": int(gaps.max()) if len(gaps) else 0,
        "primary_start": PRIMARY_START.date().isoformat(),
        "primary_rows": len(primary),
        "primary_one_day_gap_share": one_day_share,
        "primary_long_gap_events_gt1d": long_gaps,
        "primary_missing_calendar_days": missing_days,
        "primary_max_gap_days": max_gap,
        "gate_min_one_day_share": MIN_ONE_DAY_GAP_SHARE,
        "gate_max_gap_days": MAX_ALLOWED_GAP_DAYS,
    }


def target_v02(dd: float) -> float:
    if dd <= -0.65 + EPS:
        return 0.20
    if dd <= -0.50 + EPS:
        return 0.175
    if dd <= -0.35 + EPS:
        return 0.15
    if dd <= -0.20 + EPS:
        return 0.125
    return 0.10


def build_states(price: pd.Series):
    idx = price.index
    peak = float(price.iloc[0])
    peak_date = idx[0]
    sticky = [False] * 4
    active_event = None
    event_no = 1
    state_rows = []
    done_events = []

    for i, (date, raw) in enumerate(price.items()):
        p = float(raw)
        new_ath = (i == 0 or p > peak + EPS)
        if new_ath:
            if i > 0 and active_event is not None:
                active_event["reset_date"] = date
                active_event["status"] = "CLOSED"
                done_events.append(active_event)
                active_event = None
            peak = p
            peak_date = date
            sticky = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            newly_crossed = []
            for j, threshold in enumerate(THRESH):
                if dd <= threshold + EPS and not sticky[j]:
                    sticky[j] = True
                    newly_crossed.append(j)
            if newly_crossed:
                if active_event is None:
                    active_event = {
                        "event_id": event_no,
                        "prior_peak_date": peak_date,
                        "prior_peak_price": peak,
                        "first_breach_date": date,
                        "reset_date": pd.NaT,
                        "status": "OPEN",
                        "max_drawdown": dd,
                        "max_drawdown_date": date,
                        "breach_20_date": pd.NaT,
                        "breach_35_date": pd.NaT,
                        "breach_50_date": pd.NaT,
                        "breach_65_date": pd.NaT,
                    }
                    event_no += 1
                for j in newly_crossed:
                    key = f"breach_{(20, 35, 50, 65)[j]}_date"
                    if pd.isna(active_event[key]):
                        active_event[key] = date
            if active_event is not None and dd < float(active_event["max_drawdown"]):
                active_event["max_drawdown"] = dd
                active_event["max_drawdown_date"] = date

        v01_target = BASE + TRANCHE * sum(sticky)
        v02_target = target_v02(dd)
        state_rows.append({
            "date": date,
            "price": p,
            "running_peak_price": peak,
            "running_peak_date": peak_date,
            "drawdown": dd,
            "new_ath": bool(new_ath),
            "event_id": active_event["event_id"] if active_event else np.nan,
            "v01_active_tranches": int(sum(sticky)),
            "r008_v01_target": v01_target,
            "r008_v02_target": v02_target,
            "v02_active_tranches": int(round((v02_target - BASE) / TRANCHE)),
        })

    if active_event is not None:
        active_event["status"] = "OPEN_CENSORED"
        done_events.append(active_event)

    state = pd.DataFrame(state_rows).set_index("date")
    events = pd.DataFrame(done_events)
    return state, events


def simulate(price: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    target = target.reindex(price.index).astype(float)
    r = price.pct_change(fill_method=None).fillna(0.0)
    held = target.shift(1).fillna(0.0)
    dturn = target.diff().abs()
    dturn.iloc[0] = abs(float(target.iloc[0]))
    turn = dturn.shift(1).fillna(0.0)
    gross = held * r
    cost = fee * turn
    net = gross - cost
    eq = (1 + net).cumprod()
    return pd.DataFrame({
        "btc_return": r,
        "target_weight": target,
        "held_weight": held,
        "turnover": turn,
        "gross_return": gross,
        "fee_cost": cost,
        "net_return": net,
        "equity": eq,
    }, index=price.index)


def longest_dd(eq: pd.Series) -> int:
    peak = eq.cummax()
    under = eq < peak - 1e-15
    start = None
    best = 0
    for date, flag in under.items():
        if flag and start is None:
            start = date
        elif not flag and start is not None:
            best = max(best, (date - start).days)
            start = None
    if start is not None:
        best = max(best, (eq.index[-1] - start).days)
    return int(best)


def period_return(r: pd.Series, freq: str) -> pd.Series:
    return (1 + r).groupby(r.index.to_period(freq)).prod() - 1


def slice_sim(sim: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp | None = None):
    x = sim[sim.index >= start]
    if end is not None:
        x = x[x.index <= end]
    return x


def metrics(name: str, fee: float, sim: pd.DataFrame, slice_name: str,
            start: pd.Timestamp, end: pd.Timestamp | None = None) -> dict | None:
    x = slice_sim(sim, start, end)
    if len(x) < 2:
        return None
    r = x["net_return"]
    eq = (1 + r).cumprod()
    years = (eq.index[-1] - eq.index[0]).days / DAYS_PER_YEAR
    cagr = float(eq.iloc[-1] ** (1 / years) - 1) if years > 0 else np.nan
    dd = float((eq / eq.cummax() - 1).min())
    vol = float(r.std() * math.sqrt(365))
    yr = period_return(r, "Y")
    qr = period_return(r, "Q")
    mo = period_return(r, "M")
    roll = (eq / eq.shift(365) - 1).dropna()
    return {
        "strategy": name,
        "fee_bps": fee * 10000,
        "slice": slice_name,
        "start": eq.index[0].date().isoformat(),
        "end": eq.index[-1].date().isoformat(),
        "observations": len(eq),
        "cagr": cagr,
        "ending_multiple": float(eq.iloc[-1]),
        "annualized_vol": vol,
        "max_drawdown": dd,
        "calmar": cagr / abs(dd) if dd < 0 else np.nan,
        "worst_calendar_year": float(yr.min()) if len(yr) else np.nan,
        "worst_calendar_year_label": str(yr.idxmin()) if len(yr) else "",
        "worst_calendar_quarter": float(qr.min()) if len(qr) else np.nan,
        "worst_calendar_quarter_label": str(qr.idxmin()) if len(qr) else "",
        "worst_month": float(mo.min()) if len(mo) else np.nan,
        "worst_month_label": str(mo.idxmin()) if len(mo) else "",
        "worst_rolling_12m": float(roll.min()) if len(roll) else np.nan,
        "longest_drawdown_days": longest_dd(eq),
        "average_btc_exposure": float(x["held_weight"].mean()),
        "max_btc_exposure": float(x["held_weight"].max()),
        "turnover": float(x["turnover"].sum()),
        "fee_drag_simple": float(x["fee_cost"].sum()),
    }


def next_date(idx: pd.DatetimeIndex, date: pd.Timestamp):
    pos = idx.searchsorted(date, side="right")
    return None if pos >= len(idx) else idx[pos]


def event_group(first_breach: pd.Timestamp) -> str:
    if first_breach < PRIMARY_START:
        return "BEFORE_PRIMARY"
    if first_breach <= PRE2020_END:
        return "PRE_2020_NEW"
    return "REPLAY_2020"


def build_transitions(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strat, col in (("R008_V02", "r008_v02_target"), ("R008_V01", "r008_v01_target")):
        s = state[col]
        prev = s.shift(1)
        mask = prev.notna() & (s.sub(prev).abs() > 1e-12)
        for date in s.index[mask]:
            a = float(prev.loc[date]); b = float(s.loc[date]); d = b - a
            rows.append({
                "date": date.date().isoformat(),
                "strategy": strat,
                "from_target": a,
                "to_target": b,
                "direction": "UP" if d > 0 else "DOWN",
                "absolute_weight_change": abs(d),
                "threshold_units_moved": int(round(abs(d) / TRANCHE)),
                "drawdown": float(state.loc[date, "drawdown"]),
                "event_id": state.loc[date, "event_id"],
            })
    return pd.DataFrame(rows)


def spell_rows(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strat, col in (("R008_V02", "r008_v02_target"), ("R008_V01", "r008_v01_target")):
        s = state[col].eq(0.20)
        start = None
        n = 0
        spell_id = 0
        prev_date = None
        for date, flag in s.items():
            if flag and start is None:
                start = date; n = 1; spell_id += 1
            elif flag:
                n += 1
            elif (not flag) and start is not None:
                end = prev_date
                rows.append({
                    "strategy": strat, "spell_id": spell_id,
                    "start_date": start.date().isoformat(), "end_date": end.date().isoformat(),
                    "observations": n, "calendar_days": (end - start).days + 1,
                })
                start = None; n = 0
            prev_date = date
        if start is not None:
            end = s.index[-1]
            rows.append({
                "strategy": strat, "spell_id": spell_id,
                "start_date": start.date().isoformat(), "end_date": end.date().isoformat(),
                "observations": n, "calendar_days": (end - start).days + 1,
            })
    return pd.DataFrame(rows)


def event_diag(events: pd.DataFrame, sims: dict[str, pd.DataFrame], state: pd.DataFrame,
               transitions: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    idx = state.index
    rows = []
    for _, e in events.iterrows():
        breach = pd.Timestamp(e["first_breach_date"])
        reset = pd.Timestamp(e["reset_date"]) if pd.notna(e["reset_date"]) else None
        start_exec = next_date(idx, breach)
        if start_exec is None:
            continue
        end_exec = next_date(idx, reset) if reset is not None else idx[-1]
        if end_exec is None:
            end_exec = idx[-1]
        deepest = sum(pd.notna(e[f"breach_{p}_date"]) for p in (20,35,50,65))
        row = {
            "event_id": int(e["event_id"]),
            "period_group": event_group(breach),
            "status": e["status"],
            "prior_peak_date": pd.Timestamp(e["prior_peak_date"]).date().isoformat(),
            "first_breach_date": breach.date().isoformat(),
            "start_execution_date": start_exec.date().isoformat(),
            "reset_date": reset.date().isoformat() if reset is not None else "",
            "end_execution_date": end_exec.date().isoformat(),
            "max_drawdown": float(e["max_drawdown"]),
            "max_drawdown_date": pd.Timestamp(e["max_drawdown_date"]).date().isoformat(),
            "deepest_level": int(deepest),
        }
        for p in (20,35,50,65):
            v = e[f"breach_{p}_date"]
            row[f"breach_{p}_date"] = pd.Timestamp(v).date().isoformat() if pd.notna(v) else ""
        for name in ("R008_V02","R008_V01","STATIC10","STATIC15","STATIC20"):
            rr = sims[name].loc[start_exec:end_exec, "net_return"]
            row[f"{name.lower()}_event_return"] = float((1 + rr).prod() - 1)
        row["benefit10"] = row["r008_v02_event_return"] - row["static10_event_return"]
        row["benefit15"] = row["r008_v02_event_return"] - row["static15_event_return"]
        row["benefit20"] = row["r008_v02_event_return"] - row["static20_event_return"]
        row["v02_minus_v01"] = row["r008_v02_event_return"] - row["r008_v01_event_return"]
        t = transitions[(transitions["strategy"] == "R008_V02")]
        if not t.empty:
            td = pd.to_datetime(t["date"])
            mask = (td >= breach) & (td <= (reset if reset is not None else idx[-1]))
            et = t.loc[mask]
            row["v02_transition_count"] = int(len(et))
            row["v02_up_transitions"] = int((et["direction"] == "UP").sum())
            row["v02_down_transitions"] = int((et["direction"] == "DOWN").sum())
            row["v02_threshold_units_moved"] = int(et["threshold_units_moved"].sum())
        else:
            row["v02_transition_count"] = row["v02_up_transitions"] = row["v02_down_transitions"] = 0
            row["v02_threshold_units_moved"] = 0

        ev_state = state.loc[breach:(reset if reset is not None else idx[-1])]
        twenty = ev_state.index[ev_state["r008_v02_target"].eq(0.20)]
        first20 = twenty[0] if len(twenty) else None
        row["first_20pct_target_date"] = first20.date().isoformat() if first20 is not None else ""
        for label, lim in (("to_17_5",0.175),("to_15",0.15),("to_12_5",0.125),("to_10",0.10)):
            days = np.nan
            release_date = ""
            if first20 is not None:
                after = ev_state[ev_state.index > first20]
                hit = after.index[after["r008_v02_target"] <= lim + EPS]
                if len(hit):
                    release_date = hit[0].date().isoformat()
                    days = int((hit[0] - first20).days)
            row[f"first_{label}_date"] = release_date
            row[f"days_{label}"] = days
        rows.append(row)
    return pd.DataFrame(rows)


def severity_summary(ev: pd.DataFrame) -> pd.DataFrame:
    if ev.empty:
        return pd.DataFrame()
    closed = ev[ev["status"] == "CLOSED"].copy()
    rows = []
    for grp_name in ("ALL","PRE_2020_NEW","REPLAY_2020"):
        x = closed if grp_name == "ALL" else closed[closed["period_group"] == grp_name]
        for level, g in x.groupby("deepest_level"):
            pos = g["benefit10"].clip(lower=0)
            total_pos = float(pos.sum())
            largest_share = float(pos.max() / total_pos) if total_pos > 0 else np.nan
            rows.append({
                "period_group": grp_name,
                "deepest_level": int(level),
                "closed_events": len(g),
                "mean_benefit10": float(g["benefit10"].mean()),
                "median_benefit10": float(g["benefit10"].median()),
                "positive_benefit10_fraction": float((g["benefit10"] > 0).mean()),
                "mean_benefit15": float(g["benefit15"].mean()),
                "mean_benefit20": float(g["benefit20"].mean()),
                "mean_v02_minus_v01": float(g["v02_minus_v01"].mean()),
                "largest_positive_benefit10_share_within_level": largest_share,
            })
    return pd.DataFrame(rows)


def occupancy(state: pd.DataFrame, col: str, start: pd.Timestamp, end: pd.Timestamp | None = None) -> dict:
    x = state[state.index >= start]
    if end is not None:
        x = x[x.index <= end]
    vc = x[col].value_counts(normalize=True)
    return {f"share_{int(round(w*1000))/10:g}pct": float(vc.get(w, 0.0)) for w in (0.10,0.125,0.15,0.175,0.20)}


def self_test():
    dds = [0,-.19,-.20,-.34,-.35,-.49,-.50,-.64,-.65,-.70,-.58,-.47,-.31,-.18]
    exp = [.10,.10,.125,.125,.15,.15,.175,.175,.20,.20,.175,.15,.125,.10]
    got = [target_v02(x) for x in dds]
    if [round(x,6) for x in got] != [round(x,6) for x in exp]:
        raise AssertionError((got, exp))
    idx = pd.date_range("2020-01-01", periods=12)
    p = pd.Series([100,110,105,88,80,70,50,35,55,70,90,111], index=idx, dtype=float)
    st, ev = build_states(p)
    if len(ev) != 1 or ev.iloc[0]["status"] != "CLOSED":
        raise AssertionError("event self-test failed")
    if st.loc[idx[7],"r008_v02_target"] != 0.20 or st.loc[idx[9],"r008_v02_target"] >= 0.20:
        raise AssertionError("symmetric recovery self-test failed")


def write_summary(path: Path, m: pd.DataFrame, state: pd.DataFrame, ev: pd.DataFrame,
                  trans: pd.DataFrame, spells: pd.DataFrame, audit: dict):
    base = m[m["fee_bps"] == 10.0]
    L = [
        "# R008-E003 Symmetric Recovery-Release — Raw Engine Output v0.1", "",
        "**Status:** redesign/mechanism screen only; no automatic promotion.", "",
        f"- Data gate: **{audit['status']}**",
        f"- Clean period: **{audit['clean_start']} -> {audit['clean_end']}**",
        "- v0.2: 10% base + current-drawdown 2.5% tranches at -20/-35/-50/-65%, symmetric release",
        "- v0.1 comparator: sticky tranches until new ATH", "- Baseline cost: **10 bps**", "",
        "## Baseline metrics", "",
        "| Strategy | Slice | CAGR | Max DD | Calmar | Avg BTC | Turnover |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in base.itertuples(index=False):
        if r.strategy in ("R008_V02","R008_V01","STATIC10","STATIC15","STATIC20"):
            L.append(f"| {r.strategy} | {r.slice} | {r.cagr:.2%} | {r.max_drawdown:.2%} | {r.calmar:.2f} | {r.average_btc_exposure:.2%} | {r.turnover:.3f} |")
    L += ["", "## Exposure occupancy", ""]
    for label,start,end in (("PRIMARY_LONG",PRIMARY_START,None),("PRE_2020_NEW",PRIMARY_START,PRE2020_END)):
        L.append(f"### {label}")
        for strat,col in (("R008_V02","r008_v02_target"),("R008_V01","r008_v01_target")):
            x = state[state.index >= start]
            if end is not None:
                x = x[x.index <= end]
            share20 = float(x[col].eq(.20).mean())
            avg = float(x[col].mean())
            L.append(f"- {strat}: avg target **{avg:.2%}**, time at 20% **{share20:.1%}**")
    L += ["", "## Churn", ""]
    for strat in ("R008_V02","R008_V01"):
        t = trans[trans["strategy"] == strat]
        L.append(f"- {strat}: transitions **{len(t)}**, up **{int((t.direction=='UP').sum()) if len(t) else 0}**, down **{int((t.direction=='DOWN').sum()) if len(t) else 0}**")
    if not spells.empty:
        L += ["", "## 20% spells", ""]
        for strat,g in spells.groupby("strategy"):
            L.append(f"- {strat}: spells **{len(g)}**, median **{g['calendar_days'].median():.0f}d**, mean **{g['calendar_days'].mean():.1f}d**, max **{g['calendar_days'].max():.0f}d**")
    closed = ev[ev["status"] == "CLOSED"] if not ev.empty else ev
    L += ["", "## Crisis benefit", ""]
    if closed is not None and len(closed):
        L.append(f"- Closed events: **{len(closed)}**")
        L.append(f"- Positive Benefit10 fraction: **{(closed['benefit10']>0).mean():.1%}**")
        pos = closed['benefit10'].clip(lower=0)
        share = float(pos.max()/pos.sum()) if pos.sum()>0 else np.nan
        L.append(f"- Largest single positive Benefit10 share: **{share:.1%}**")
        for level,g in closed.groupby('deepest_level'):
            L.append(f"- Level {int(level)}: mean Benefit10 **{g['benefit10'].mean():.2%}**, mean v0.2-v0.1 **{g['v02_minus_v01'].mean():.2%}**")
    L += ["", "## Important", "",
          "E003 uses history already inspected during redesign. Even a strong result can only be PROMISING; it cannot receive independent historical PASS.", ""]
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir")
    args = ap.parse_args()
    out = Path(args.outdir).expanduser().resolve() if args.outdir else Path.cwd()/f"R008_E003_RUN_{datetime.now():%Y-%m-%d_%H-%M-%S}"
    out.mkdir(parents=True, exist_ok=True)

    print("="*72)
    print("R008-E003 SYMMETRIC RECOVERY-RELEASE v0.1")
    print("="*72)
    print("[1/9] Self-test...")
    self_test(); print("      PASS")

    print("[2/9] Downloading Blockchain.com market-price...")
    raw, obj = download_source()
    raw_path = out/"_r008_e003_source_raw.json"
    raw_path.write_bytes(raw)
    clean, dup = clean_source(obj)
    print("      raw values:", len(obj.get("values", [])), "clean rows:", len(clean))

    print("[3/9] Data audit...")
    audit = audit_source(obj, clean, dup)
    audit["raw_sha256"] = sha256_bytes(raw)
    clean_path = out/"r008_e003_price_clean.csv"
    clean.to_csv(clean_path, index=False)
    audit["clean_csv_sha256"] = sha256_file(clean_path)
    (out/"r008_e003_data_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    if audit["status"] != "PASS":
        run = {"status":"DATA_REDESIGN","engine_version":VERSION,"protocol":PROTOCOL,"data_gate":audit}
        (out/"r008_e003_run_state.json").write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
        print("DATA_REDESIGN; no P&L calculated")
        return

    price = clean.set_index("date")["price"].astype(float)
    print("[4/9] Building v0.1/v0.2 states and events...")
    state, raw_events = build_states(price)
    transitions = build_transitions(state)
    spells = spell_rows(state)
    print("      events:", len(raw_events), "v0.2 transitions:", int((transitions.strategy=="R008_V02").sum()) if len(transitions) else 0)

    targets = {
        "R008_V02": state["r008_v02_target"],
        "R008_V01": state["r008_v01_target"],
        "CASH": pd.Series(0.0, index=price.index),
        "STATIC10": pd.Series(0.10, index=price.index),
        "STATIC15": pd.Series(0.15, index=price.index),
        "STATIC20": pd.Series(0.20, index=price.index),
        "BTC100": pd.Series(1.0, index=price.index),
    }
    slices = {
        "FULL_AVAILABLE": (price.index[0], None),
        "PRIMARY_LONG": (PRIMARY_START, None),
        "PRE_2020_NEW": (PRIMARY_START, PRE2020_END),
        "REPLAY_2020": (REPLAY_START, None),
        "POST_2023": (LATE_START, None),
    }

    print("[5/9] Cost grid + metrics...")
    sims_by_fee = {}; metric_rows = []
    for fee in FEES:
        sims = {name: simulate(price, target, fee) for name,target in targets.items()}
        sims_by_fee[fee] = sims
        for name,sim in sims.items():
            for sl,(start,end) in slices.items():
                row = metrics(name, fee, sim, sl, start, end)
                if row:
                    metric_rows.append(row)
    m = pd.DataFrame(metric_rows)

    print("[6/9] Yearly returns + event diagnostics...")
    base_sims = sims_by_fee[BASE_FEE]
    yearly_rows = []
    for name,sim in base_sims.items():
        for sl,(start,end) in slices.items():
            x = slice_sim(sim,start,end)
            if len(x) < 2:
                continue
            y = period_return(x["net_return"],"Y")
            for p,v in y.items():
                yearly_rows.append({"strategy":name,"slice":sl,"year":int(p.year),"return":float(v)})
    yearly = pd.DataFrame(yearly_rows)
    ev = event_diag(raw_events, base_sims, state, transitions)
    sev = severity_summary(ev)

    print("[7/9] Baseline daily output...")
    daily = state.copy()
    daily["btc_return"] = base_sims["R008_V02"]["btc_return"]
    for name in ("R008_V02","R008_V01","STATIC10","STATIC15","STATIC20","BTC100","CASH"):
        sim = base_sims[name]
        low = name.lower()
        daily[f"{low}_held_weight"] = sim["held_weight"]
        daily[f"{low}_net_return"] = sim["net_return"]
        daily[f"{low}_equity"] = sim["equity"]

    print("[8/9] Writing outputs...")
    m.to_csv(out/"r008_e003_metrics.csv", index=False)
    yearly.to_csv(out/"r008_e003_yearly_returns.csv", index=False)
    state.to_csv(out/"r008_e003_state_daily.csv")
    transitions.to_csv(out/"r008_e003_transitions.csv", index=False)
    spells.to_csv(out/"r008_e003_exposure_spells_20.csv", index=False)
    raw_events.to_csv(out/"r008_e003_crisis_events_raw.csv", index=False)
    ev.to_csv(out/"r008_e003_crisis_event_diagnostics.csv", index=False)
    sev.to_csv(out/"r008_e003_severity_summary.csv", index=False)
    daily.to_csv(out/"r008_e003_baseline_daily.csv")
    write_summary(out/"r008_e003_summary.md", m, state, ev, transitions, spells, audit)

    raw_path.unlink(missing_ok=True)

    occ = {}
    for sl,(start,end) in (("PRIMARY_LONG",(PRIMARY_START,None)),("PRE_2020_NEW",(PRIMARY_START,PRE2020_END))):
        occ[sl] = {
            "R008_V02": occupancy(state,"r008_v02_target",start,end),
            "R008_V01": occupancy(state,"r008_v01_target",start,end),
        }
    run = {
        "status":"PASS",
        "engine_version":VERSION,
        "protocol":PROTOCOL,
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "research_freeze":{
            "base_weight":BASE,"opportunity_reserve":0.10,"tranche_weight":TRANCHE,
            "thresholds":list(THRESH),"v02_release":"same-threshold current-drawdown mapping",
            "hysteresis":False,"cooldown":False,"fee_grid":list(FEES),"baseline_fee":BASE_FEE,
            "cash_return":0.0,
        },
        "source":{
            "url":SOURCE_URL,"raw_sha256":audit["raw_sha256"],"clean_csv_sha256":audit["clean_csv_sha256"],
            "clean_rows":len(clean),"start":audit["clean_start"],"end":audit["clean_end"],
        },
        "data_gate":audit,
        "crisis_events":len(raw_events),
        "closed_crisis_events":int((ev["status"]=="CLOSED").sum()) if len(ev) else 0,
        "v02_transition_count":int((transitions["strategy"]=="R008_V02").sum()) if len(transitions) else 0,
        "v01_transition_count":int((transitions["strategy"]=="R008_V01").sum()) if len(transitions) else 0,
        "occupancy":occ,
        "outputs":[
            "r008_e003_data_audit.json","r008_e003_price_clean.csv","r008_e003_metrics.csv",
            "r008_e003_yearly_returns.csv","r008_e003_state_daily.csv","r008_e003_transitions.csv",
            "r008_e003_exposure_spells_20.csv","r008_e003_crisis_events_raw.csv",
            "r008_e003_crisis_event_diagnostics.csv","r008_e003_severity_summary.csv",
            "r008_e003_baseline_daily.csv","r008_e003_summary.md","r008_e003_run_state.json",
        ],
    }
    (out/"r008_e003_run_state.json").write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[9/9] FINISHED")
    print("Results:", out)


if __name__ == "__main__":
    main()
