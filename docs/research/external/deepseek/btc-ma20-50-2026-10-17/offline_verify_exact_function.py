#!/usr/bin/env python3
"""Independent offline adapter; not part of the submitted DeepSeek source.

Only the exact original function definition and original bh_equity assignment
are compiled from the supplied script. Imports, ccxt, data acquisition, plotting,
and original CSV writes are never executed. Frozen inputs are read-only.
"""
import argparse
import ast
import csv
import hashlib
import json
import math
import platform
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir',type=Path,default=HERE)
parser.add_argument('--output-dir',type=Path,default=HERE/'verified_outputs')
args=parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=True)
source_file=HERE/'original_submitted_deepseek.py'
raw_file=args.input_dir/'btc_raw_data.csv'
log_file=args.input_dir/'trades_log.csv'
assert args.output_dir.resolve()!=args.input_dir.resolve(), 'Never write into the input directory'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

before={p.name:sha(p) for p in [source_file,raw_file,log_file]}
expected={
    'original_submitted_deepseek.py':'8b11ef920cae01bfce066bb0b861d8f9d37328d7409a28b41d285140d6419bf6',
    'btc_raw_data.csv':'513892e2c85ef927c92f81725fb385932e0fc450397de8fb3900876c7463ae46',
    'trades_log.csv':'f8a139e454e6bc66e2543460a5ba0dc0d56ffc5761fec76a730e2ecac34dd627',
}
assert before==expected, {'unexpected_input_hashes':before}
source=source_file.read_text()
tree=ast.parse(source,filename=source_file.name)
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run_audited_backtest']
assert len(functions)==1
func_node=functions[0]
func_text=ast.get_source_segment(source,func_node)
# AST subtree is taken intact; the original function is not reconstructed or rewritten.
module=ast.Module(body=[func_node],type_ignores=[])
namespace={'pd':pd}
exec(compile(module,source_file.name,'exec'),namespace)
btc_df=pd.read_csv(raw_file,index_col='timestamp',parse_dates=True,float_precision='round_trip')
split_idx=int(len(btc_df)*0.7)
train_df=btc_df.iloc[:split_idx].copy()
test_df=btc_df.iloc[split_idx:].copy()
final_cap,dates,eq_curve,trades_df=namespace['run_audited_backtest'](test_df)

# Execute the exact original graph benchmark expression, without executing plots.
bh_nodes=[node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bh_equity' for t in node.targets)]
assert len(bh_nodes)==1
bh_node=bh_nodes[0]
bh_scope={'test_df':test_df,'eq_curve':eq_curve}
exec(compile(ast.Module(body=[bh_node],type_ignores=[]),source_file.name,'exec'),bh_scope)
bh_equity=bh_scope['bh_equity']

numeric=['Entry_Price','Exit_Price','Entry_Fee','Exit_Fee','Net_PnL','Position_Size']
original=list(csv.DictReader(log_file.open()))
actual=trades_df.to_dict('records')

def normalize_date(value):
    return 'End of Test' if value=='End of Test' else pd.Timestamp(value).strftime('%Y-%m-%d')

comparisons=[]
assert len(actual)==len(original)
for idx,(a,b) in enumerate(zip(actual,original),1):
    deltas={key:float(a[key])-float(b[key]) for key in numeric}
    text_matches=a['Type']==b['Type'] and all(normalize_date(a[key])==normalize_date(b[key]) for key in ['Entry_Time','Exit_Time'])
    comparisons.append({'trade':idx,'numeric_deltas':deltas,'type_and_dates_match':bool(text_matches)})
assert all(c['type_and_dates_match'] and all(abs(d)<=1e-10 for d in c['numeric_deltas'].values()) for c in comparisons)

curve=pd.DataFrame({'date':dates,'strategy_equity':eq_curve,'buy_hold_gross_equity':bh_equity})
curve['strategy_drawdown']=curve['strategy_equity']/curve['strategy_equity'].cummax()-1
trough_idx=int(curve['strategy_drawdown'].argmin())
peak_idx=int(curve.loc[:trough_idx,'strategy_equity'].argmax())
net_pnl=float(trades_df['Net_PnL'].sum())
recon=10000+net_pnl-float(final_cap)
assert abs(recon)<1e-10
assert len(dates)==250 and dates[0]==test_df.index[50]
assert eq_curve[-1]==final_cap
# Exclude only the provisional last row, preserving the original split and rules.
closed_cap,closed_dates,closed_eq,closed_trades=namespace['run_audited_backtest'](test_df.iloc[:-1].copy())
assert len(closed_dates)==249
assert abs(float(closed_cap)-12492.466961355964)<1e-6

# Frozen-input structural checks do not authenticate the exchange source.
assert len(btc_df)==1000 and btc_df.index.is_unique and btc_df.index.is_monotonic_increasing
assert (btc_df.index.to_series().diff().dropna()==pd.Timedelta(days=1)).all()
for column in ['Open','high','low','Close','volume']:
    assert all(math.isfinite(value) and value>0 for value in btc_df[column])
assert ((btc_df['low']<=btc_df['Open']) & (btc_df['Open']<=btc_df['high'])).all()
assert ((btc_df['low']<=btc_df['Close']) & (btc_df['Close']<=btc_df['high'])).all()

start=float(test_df['Close'].iloc[50]);end=float(test_df['Close'].iloc[-1]);fee=.001
cost_bh=10000-10000*fee+10000/start*(end-start)-10000/start*end*fee
# Train is created and printed in the original script but never passed to the strategy.
train_load_sites=[{'line':n.lineno,'context':type(n.ctx).__name__} for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id=='train_df']
report={
    'verification_type':'Exact supplied function and exact supplied benchmark expression, run offline on frozen user-supplied CSV; not a fresh market data acquisition or new out-of-sample test.',
    'source_provenance_file':'source_provenance.json',
    'source_and_input_sha256':before,
    'function_source_sha256':hashlib.sha256(func_text.encode()).hexdigest(),
    'function_source_lines':{'start':func_node.lineno,'end':func_node.end_lineno},
    'benchmark_expression':ast.get_source_segment(source,bh_node),
    'executed_source_nodes':['run_audited_backtest function definition','bh_equity assignment'],
    'original_fetch_imports_csv_writes_and_plotting_executed':False,
    'runtime':{'python':platform.python_version(),'pandas':pd.__version__},
    'periods':{'raw_rows':len(btc_df),'raw_start':str(btc_df.index[0].date()),'raw_end':str(btc_df.index[-1].date()),
        'train_rows':len(train_df),'train_start':str(train_df.index[0].date()),'train_end':str(train_df.index[-1].date()),
        'test_rows':len(test_df),'test_start':str(test_df.index[0].date()),'test_end':str(test_df.index[-1].date()),
        'equity_observations':len(dates),'equity_start':str(dates[0].date()),'equity_end':str(dates[-1].date()),
        'first_execution':str(trades_df.iloc[0]['Entry_Time'].date())},
    'results':{'initial_capital':10000,'final_capital':float(final_cap),'return_percent':(float(final_cap)/10000-1)*100,
        'sum_net_pnl':net_pnl,'capital_reconciliation_difference':recon,'trade_count':len(trades_df),
        'total_entry_and_exit_fees':float(trades_df['Entry_Fee'].sum()+trades_df['Exit_Fee'].sum()),
        'last_equity_includes_terminal_exit_fee':bool(eq_curve[-1]==final_cap),
        'daily_close_max_drawdown_percent':float(curve['strategy_drawdown'].min()*100),
        'max_drawdown_peak_date':str(dates[peak_idx].date()),'max_drawdown_trough_date':str(dates[trough_idx].date()),
        'last_trade_share_of_net_pnl_percent':float(trades_df.iloc[-1]['Net_PnL']/net_pnl*100)},
    'benchmark':{'original_graph_start_date':str(dates[0].date()),'original_graph_start_price':start,
        'original_graph_last_close':end,'original_graph_final_gross_equity':float(bh_equity[-1]),
        'original_graph_gross_return_percent':(float(bh_equity[-1])/10000-1)*100,
        'commission_in_original_benchmark':False,
        'separately_computed_same_engine_cost_return_percent':(cost_bh/10000-1)*100,
        'same_engine_cost_convention':'0.1% entry and exit; quantity calculated before entry fee, matching original strategy.'},
    'supplied_trade_log_comparison':comparisons,
    'max_numeric_trade_difference':max(abs(d) for c in comparisons for d in c['numeric_deltas'].values()),
    'input_structural_checks':{'unique_ascending_daily_dates':True,'finite_positive_ohlcv':True,'ohlc_bounds':True},
    'exclude_last_provisional_row_diagnostic':{
        'original_split_rows_kept':split_idx,
        'test_rows':len(test_df)-1,
        'test_end':str(test_df.index[-2].date()),
        'final_capital':float(closed_cap),
        'return_percent':(float(closed_cap)/10000-1)*100,
        'equity_observations':len(closed_dates),
        'trade_count':len(closed_trades),
        'interpretation':'Same frozen input minus only 2026-10-17; original 700-row split and function unchanged; sensitivity diagnostic, not a new holdout.'},
    'code_review':{
        'train_df_usage':'Created and printed only; no model fitting, optimization or parameter selection using train_df in this script.',
        'train_df_name_sites':train_load_sites,
        'warmup_graph_title':'Original title says including warm-up, but both plotted series begin at test index 50; the preceding 50 rows are not plotted.',
        'first_signal_vs_execution':'February 10 is first recorded equity and signal date; February 11 is first next-open execution.',
        'signal_timing':'Trailing rolling averages through close i; executions at Open i+1. No signal look-ahead detected in this function.',
        'terminal_candle':'Final input row is 2026-10-17, the current UTC day at verification. No completed-candle filter; terminal result remains provisional.',
        'short_costs':'Shorts are simulated from spot OHLC; no borrow costs, funding, spread, slippage or execution capacity model.',
        'size_cost_convention':'Position notional uses capital before subtracting entry commission; exact verification preserves this convention.',
        'validation_limit':'Six trades and a matching accounting identity establish reproducibility on this file, not robustness, live profitability, or untouched out-of-sample selection.'},
}
after={p.name:sha(p) for p in [source_file,raw_file,log_file]}
assert after==before
report['original_source_and_inputs_unchanged']=True
trades_df.to_csv(args.output_dir/'exact_function_trades.csv',index=False)
curve.to_csv(args.output_dir/'exact_function_equity_and_benchmark.csv',index=False)
(args.output_dir/'verification_results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
output_hashes={p.name:sha(p) for p in sorted(args.output_dir.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'}
(args.output_dir/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in output_hashes.items()))
print(json.dumps(report,indent=2,ensure_ascii=False))
print('OUTPUT_SHA256',json.dumps(output_hashes,indent=2))
