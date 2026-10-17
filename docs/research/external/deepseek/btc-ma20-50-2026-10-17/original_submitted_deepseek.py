import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ccxt
import warnings
warnings.filterwarnings('ignore')

# 1. ЗАГРУЗКА ДАННЫХ И ЧЕТКОЕ ОПРЕДЕЛЕНИЕ ДАТ
exchange = ccxt.kucoin()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=1000)
btc_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'], unit='ms')
btc_df.set_index('timestamp', inplace=True)
btc_df.rename(columns={'open': 'Open', 'close': 'Close'}, inplace=True)

# Сохраняем исходные данные в CSV
btc_df.to_csv('btc_raw_data.csv')
print(f"Исходные данные: с {btc_df.index[0].date()} по {btc_df.index[-1].date()} (всего {len(btc_df)} дней)")

# Разделение: 70% Train, 30% Test
split_idx = int(len(btc_df) * 0.7)
train_df = btc_df.iloc[:split_idx].copy()
test_df = btc_df.iloc[split_idx:].copy()

print(f"Train (обучение): с {train_df.index[0].date()} по {train_df.index[-1].date()} ({len(train_df)} дней)")
print(f"Test (экзамен): с {test_df.index[0].date()} по {test_df.index[-1].date()} ({len(test_df)} дней)")
print(f"Примечание: Первые 50 дней теста уходят на прогрев MA50. Активная торговля начинается с {test_df.index[50].date()}.\n")

# 2. ИСПРАВЛЕННЫЙ EVENT-DRIVEN БЭКТЕСТ
def run_audited_backtest(df, fast_w=20, slow_w=50, fee=0.001, initial_capital=10000):
    df['MA_Fast'] = df['Close'].rolling(window=fast_w).mean()
    df['MA_Slow'] = df['Close'].rolling(window=slow_w).mean()
    
    capital = initial_capital
    position = 0 # 1 = Long, -1 = Short
    position_size = 0 
    entry_price = 0
    entry_time = None
    entry_fee_paid = 0
    
    equity_curve = []
    dates = []
    trades_log = []
    
    start_idx = slow_w # Прогрев
    
    for i in range(start_idx, len(df)):
        current_close = df['Close'].iloc[i]
        
        # 1. Считаем Equity (Текущий капитал)
        if position == 1:
            unrealized = (current_close - entry_price) * position_size
        elif position == -1:
            unrealized = (entry_price - current_close) * position_size
        else:
            unrealized = 0
        
        current_equity = capital + unrealized
        equity_curve.append(current_equity)
        dates.append(df.index[i])
        
        if i == len(df) - 1: 
            break # Последний день
            
        # 2. Сигнал на закрытии дня i
        signal = 0
        if df['MA_Fast'].iloc[i] > df['MA_Slow'].iloc[i]:
            signal = 1
        elif df['MA_Fast'].iloc[i] < df['MA_Slow'].iloc[i]:
            signal = -1
            
        # 3. Исполнение на открытии дня i+1
        next_open = df['Open'].iloc[i+1]
        next_time = df.index[i+1]
        
        if signal != 0 and signal != position:
            # Закрываем старую позицию
            if position != 0:
                close_pnl = (next_open - entry_price) * position_size if position == 1 else (entry_price - next_open) * position_size
                exit_fee_paid = abs(position_size) * next_open * fee
                
                # Чистый PnL сделки
                net_trade_pnl = close_pnl - entry_fee_paid - exit_fee_paid
                capital += close_pnl - exit_fee_paid 
                
                trades_log.append({
                    'Type': 'LONG' if position == 1 else 'SHORT',
                    'Entry_Time': entry_time, 'Entry_Price': entry_price,
                    'Exit_Time': next_time, 'Exit_Price': next_open,
                    'Entry_Fee': entry_fee_paid, 'Exit_Fee': exit_fee_paid,
                    'Net_PnL': net_trade_pnl,
                    'Position_Size': position_size
                })
                position = 0
                position_size = 0
                entry_fee_paid = 0
                
            # Открываем новую позицию
            if signal != 0:
                pos_value = capital * 1.0 
                position_size = pos_value / next_open
                entry_price = next_open
                entry_time = next_time
                position = signal
                
                entry_fee_paid = pos_value * fee
                capital -= entry_fee_paid

    # Закрываем позицию в конце теста
    if position != 0:
        last_close = df['Close'].iloc[-1]
        close_pnl = (last_close - entry_price) * position_size if position == 1 else (entry_price - last_close) * position_size
        exit_fee_paid = abs(position_size) * last_close * fee
        net_trade_pnl = close_pnl - entry_fee_paid - exit_fee_paid
        
        capital += close_pnl - exit_fee_paid
        trades_log.append({
            'Type': 'LONG' if position == 1 else 'SHORT',
            'Entry_Time': entry_time, 'Entry_Price': entry_price,
            'Exit_Time': 'End of Test', 'Exit_Price': last_close,
            'Entry_Fee': entry_fee_paid, 'Exit_Fee': exit_fee_paid,
            'Net_PnL': net_trade_pnl,
            'Position_Size': position_size
        })
        equity_curve[-1] = capital

    return capital, dates, equity_curve, pd.DataFrame(trades_log)

# Запуск и сохранение
final_cap, dates, eq_curve, trades_df = run_audited_backtest(test_df)
trades_df.to_csv('trades_log.csv', index=False)

# 3. СВЕРКА КАПИТАЛА И ВЫВОД
print("--- СВЕРКА КАПИТАЛА ---")
sum_net_pnl = trades_df['Net_PnL'].sum()
print(f"Начальный капитал: ${10000:.2f}")
print(f"Сумма чистых PnL всех сделок: ${sum_net_pnl:.2f}")
print(f"Ожидаемый конечный капитал: ${10000 + sum_net_pnl:.2f}")
print(f"Фактический конечный капитал: ${final_cap:.2f}")
print(f"Сверка: {'УСПЕХ' if abs((10000 + sum_net_pnl) - final_cap) < 0.01 else 'ОШИБКА'}\n")

print("--- ЖУРНАЛ СДЕЛОК ---")
print(trades_df[['Type', 'Entry_Time', 'Exit_Time', 'Net_PnL']].to_string(index=False))

# 4. ГРАФИК
bh_equity = [10000 * (test_df['Close'].iloc[50+i] / test_df['Close'].iloc[50]) for i in range(len(eq_curve))]

plt.figure(figsize=(12, 6))
plt.plot(dates, eq_curve, label='Стратегия (Long/Short)', color='purple', linewidth=2)
plt.plot(dates, bh_equity, label='Buy & Hold (BTC)', color='orange', linestyle='--')
plt.axhline(10000, color='red', linestyle=':', label='Старт ($10,000)')
plt.title('Кривая капитала (включая прогрев) vs Buy & Hold')
plt.xlabel('Дата')
plt.ylabel('Капитал ($)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
