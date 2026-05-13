import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# INDIAN LARGE-CAP BACKTEST: SMA 200 + RSI 10 Strategy
# DETAILED TRADE-BY-TRADE ANALYSIS
# ============================================================================

class IndianLargeCapBacktest:
    def __init__(self, symbols, start_date, end_date, initial_capital, position_size):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.trades = []
        
    def fetch_data(self):
        """Fetch daily OHLC data for all symbols"""
        print("📥 Fetching historical data...")
        self.data = {}
        for symbol in self.symbols:
            ticker = f"{symbol}.NS"
            try:
                df = yf.download(ticker, start=self.start_date, end=self.end_date, 
                                progress=False, interval='1d')
                self.data[symbol] = df.copy()
                print(f"✓ {symbol}: {len(df)} candles loaded")
            except Exception as e:
                print(f"✗ {symbol}: Failed to load - {e}")
        
    def calculate_indicators(self):
        """Calculate SMA 200 and RSI 10 for all symbols"""
        print("\n📊 Calculating indicators...")
        for symbol in self.data.keys():
            df = self.data[symbol]
            
            # SMA 200
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            # RSI 10
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=10).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=10).mean()
            rs = gain / loss
            df['RSI10'] = 100 - (100 / (1 + rs))
            
            # Swing Low (10-period for stop loss)
            df['SwingLow'] = df['Low'].rolling(window=10).min()
            
            self.data[symbol] = df.copy()
            print(f"✓ {symbol}: Indicators calculated")
    
    def backtest_symbol(self, symbol):
        """Run backtest logic for a single symbol"""
        df = self.data[symbol].dropna()
        symbol_trades = []
        
        active_trade = None
        entry_rsi = None
        entry_date = None
        entry_sma = None
        days_held = 0
        
        for i in range(1, len(df)):
            current_date = df.index[i]
            
            current_price = df.iloc[i]['Close']
            current_sma = df.iloc[i]['SMA200']
            current_rsi = df.iloc[i]['RSI10']
            prev_rsi = df.iloc[i-1]['RSI10']
            swing_low = df.iloc[i-1]['SwingLow']
            
            # ===== TREND FILTER =====
            in_uptrend = current_price > current_sma
            
            # ===== EXIT CONDITIONS =====
            if active_trade:
                days_held += 1
                
                # Exit Condition 1: RSI crosses above 40
                if prev_rsi <= 40 and current_rsi > 40:
                    exit_price = df.iloc[i+1]['Open'] if i+1 < len(df) else current_price
                    profit = (exit_price - active_trade['entry_price']) * active_trade['quantity']
                    symbol_trades.append({
                        'Trade #': len(symbol_trades) + 1,
                        'Symbol': symbol,
                        'Entry Date': entry_date.strftime('%Y-%m-%d'),
                        'Entry Price': round(active_trade['entry_price'], 2),
                        'Entry RSI': round(entry_rsi, 2),
                        'Entry SMA200': round(entry_sma, 2),
                        'Exit Date': (df.index[i+1] if i+1 < len(df) else current_date).strftime('%Y-%m-%d'),
                        'Exit Price': round(exit_price, 2),
                        'Exit RSI': round(current_rsi, 2),
                        'Quantity': round(active_trade['quantity'], 2),
                        'Days Held': days_held,
                        'Stop Loss': round(active_trade['stop_loss'], 2),
                        'Exit Reason': 'RSI > 40',
                        'Profit/Loss': round(profit, 2),
                        'Return %': round((profit / active_trade['entry_price'] / active_trade['quantity']) * 100, 2),
                        'Trade Status': '✓ WIN' if profit > 0 else '✗ LOSS'
                    })
                    active_trade = None
                    days_held = 0
                
                # Exit Condition 2: 10 days without RSI > 40
                elif days_held == 11:
                    exit_price = df.iloc[i+1]['Open'] if i+1 < len(df) else current_price
                    profit = (exit_price - active_trade['entry_price']) * active_trade['quantity']
                    symbol_trades.append({
                        'Trade #': len(symbol_trades) + 1,
                        'Symbol': symbol,
                        'Entry Date': entry_date.strftime('%Y-%m-%d'),
                        'Entry Price': round(active_trade['entry_price'], 2),
                        'Entry RSI': round(entry_rsi, 2),
                        'Entry SMA200': round(entry_sma, 2),
                        'Exit Date': (df.index[i+1] if i+1 < len(df) else current_date).strftime('%Y-%m-%d'),
                        'Exit Price': round(exit_price, 2),
                        'Exit RSI': round(current_rsi, 2),
                        'Quantity': round(active_trade['quantity'], 2),
                        'Days Held': days_held,
                        'Stop Loss': round(active_trade['stop_loss'], 2),
                        'Exit Reason': '11 Days Hold',
                        'Profit/Loss': round(profit, 2),
                        'Return %': round((profit / active_trade['entry_price'] / active_trade['quantity']) * 100, 2),
                        'Trade Status': '✓ WIN' if profit > 0 else '✗ LOSS'
                    })
                    active_trade = None
                    days_held = 0
                
                # Stop Loss hit
                elif current_price < active_trade['stop_loss']:
                    exit_price = active_trade['stop_loss']
                    profit = (exit_price - active_trade['entry_price']) * active_trade['quantity']
                    symbol_trades.append({
                        'Trade #': len(symbol_trades) + 1,
                        'Symbol': symbol,
                        'Entry Date': entry_date.strftime('%Y-%m-%d'),
                        'Entry Price': round(active_trade['entry_price'], 2),
                        'Entry RSI': round(entry_rsi, 2),
                        'Entry SMA200': round(entry_sma, 2),
                        'Exit Date': current_date.strftime('%Y-%m-%d'),
                        'Exit Price': round(exit_price, 2),
                        'Exit RSI': round(current_rsi, 2),
                        'Quantity': round(active_trade['quantity'], 2),
                        'Days Held': days_held,
                        'Stop Loss': round(active_trade['stop_loss'], 2),
                        'Exit Reason': 'Stop Loss',
                        'Profit/Loss': round(profit, 2),
                        'Return %': round((profit / active_trade['entry_price'] / active_trade['quantity']) * 100, 2),
                        'Trade Status': '✓ WIN' if profit > 0 else '✗ LOSS'
                    })
                    active_trade = None
                    days_held = 0
            
            # ===== ENTRY CONDITIONS =====
            if not active_trade and in_uptrend:
                # Entry signal: RSI < 30
                if prev_rsi >= 30 and current_rsi < 30:
                    entry_price = df.iloc[i+1]['Open'] if i+1 < len(df) else current_price
                    stop_loss = swing_low * 0.995
                    quantity = self.position_size / entry_price
                    
                    active_trade = {
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'quantity': quantity
                    }
                    entry_rsi = current_rsi
                    entry_sma = current_sma
                    entry_date = df.index[i+1] if i+1 < len(df) else current_date
                    days_held = 0
        
        return symbol_trades
    
    def run_backtest(self):
        """Run complete backtest across all symbols"""
        print("\n🚀 Running backtest...\n")
        
        all_trades = []
        for symbol in self.symbols:
            if symbol in self.data:
                trades = self.backtest_symbol(symbol)
                all_trades.extend(trades)
        
        self.trades_df = pd.DataFrame(all_trades)
        return self.trades_df
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        if len(self.trades_df) == 0:
            print("\n⚠️ No trades generated!")
            return None
        
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df['Profit/Loss'] > 0])
        losing_trades = len(self.trades_df[self.trades_df['Profit/Loss'] < 0])
        
        total_pnl = self.trades_df['Profit/Loss'].sum()
        avg_return = self.trades_df['Return %'].mean()
        max_loss = self.trades_df['Profit/Loss'].min()
        max_gain = self.trades_df['Profit/Loss'].max()
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        winning_sum = self.trades_df[self.trades_df['Profit/Loss'] > 0]['Profit/Loss'].sum()
        losing_sum = abs(self.trades_df[self.trades_df['Profit/Loss'] < 0]['Profit/Loss'].sum())
        profit_factor = winning_sum / losing_sum if losing_sum > 0 else np.inf
        
        final_capital = self.initial_capital + total_pnl
        total_return = (total_pnl / self.initial_capital) * 100
        
        print("\n" + "="*100)
        print("📈 BACKTEST SUMMARY: Indian Large-Cap SMA200 + RSI10 Strategy")
        print("="*100)
        print(f"\n📊 TRADE STATISTICS:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Winning Trades: {winning_trades} ✓")
        print(f"  Losing Trades: {losing_trades} ✗")
        print(f"  Win Rate: {win_rate:.2f}%")
        print(f"\n💰 P&L METRICS:")
        print(f"  Initial Capital: ₹{self.initial_capital:,.2f}")
        print(f"  Total P&L: ₹{total_pnl:,.2f}")
        print(f"  Final Capital: ₹{final_capital:,.2f}")
        print(f"  Total Return: {total_return:.2f}%")
        print(f"  Avg Return per Trade: {avg_return:.2f}%")
        print(f"\n📉 RISK METRICS:")
        print(f"  Max Gain: ₹{max_gain:,.2f}")
        print(f"  Max Loss: ₹{max_loss:,.2f}")
        print(f"  Profit Factor: {profit_factor:.2f}")
        print(f"\n" + "="*100)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'final_capital': final_capital
        }
    
    def print_detailed_trades(self):
        """Print EACH AND EVERY TRADE in detail"""
        if len(self.trades_df) == 0:
            print("\n⚠️ No trades to display")
            return
        
        print("\n\n" + "="*120)
        print("📋 DETAILED TRADE-BY-TRADE ANALYSIS - ALL TRADES")
        print("="*120 + "\n")
        
        for idx, trade in self.trades_df.iterrows():
            trade_num = idx + 1
            total_trades = len(self.trades_df)
            
            # Color coding for status
            status = trade['Trade Status']
            
            print(f"\n{'─'*120}")
            print(f"TRADE #{trade_num} of {total_trades} {status}")
            print(f"{'─'*120}")
            
            print(f"Stock Symbol:          {trade['Symbol']}")
            print(f"Trade Status:          {status}")
            
            print(f"\n📍 ENTRY DETAILS:")
            print(f"   Entry Date:         {trade['Entry Date']}")
            print(f"   Entry Price:        ₹{trade['Entry Price']:.2f}")
            print(f"   Entry RSI(10):      {trade['Entry RSI']:.2f}")
            print(f"   Entry SMA(200):     ₹{trade['Entry SMA200']:.2f}")
            print(f"   Trend:              Price (₹{trade['Entry Price']:.2f}) > SMA200 (₹{trade['Entry SMA200']:.2f}) ✓ UPTREND")
            print(f"   Signal:             RSI dropped below 30 to {trade['Entry RSI']:.2f} ✓")
            
            print(f"\n📍 EXIT DETAILS:")
            print(f"   Exit Date:          {trade['Exit Date']}")
            print(f"   Exit Price:         ₹{trade['Exit Price']:.2f}")
            print(f"   Exit RSI(10):       {trade['Exit RSI']:.2f}")
            print(f"   Exit Reason:        {trade['Exit Reason']}")
            print(f"   Days Held:          {trade['Days Held']} days")
            
            if trade['Exit Reason'] == 'RSI > 40':
                print(f"   Exit Trigger:       RSI crossed above 40 to {trade['Exit RSI']:.2f}")
            elif trade['Exit Reason'] == 'Stop Loss':
                print(f"   Exit Trigger:       Price hit Stop Loss at ₹{trade['Stop Loss']:.2f}")
            elif trade['Exit Reason'] == '11 Days Hold':
                print(f"   Exit Trigger:       Held for 11 days (max hold period)")
            
            print(f"\n💰 POSITION DETAILS:")
            print(f"   Position Size:      ₹{self.position_size:.2f}")
            print(f"   Quantity Bought:    {trade['Quantity']:.2f} shares")
            print(f"   Stop Loss Level:    ₹{trade['Stop Loss']:.2f}")
            
            print(f"\n📊 P&L ANALYSIS:")
            print(f"   Entry Cost:         ���{trade['Entry Price'] * trade['Quantity']:.2f}")
            print(f"   Exit Value:         ₹{trade['Exit Price'] * trade['Quantity']:.2f}")
            print(f"   Profit/Loss:        ₹{trade['Profit/Loss']:.2f}")
            print(f"   Return %:           {trade['Return %']:.2f}%")
            print(f"   Status:             {status}")

# ============================================================================
# RUN BACKTEST
# ============================================================================

if __name__ == "__main__":
    symbols = ['TCS', 'RELIANCE', 'HDFCBANK', 'INFY']
    start_date = '2023-01-01'
    end_date = '2026-05-13'
    initial_capital = 100000
    position_size = 10000
    
    backtest = IndianLargeCapBacktest(symbols, start_date, end_date, 
                                      initial_capital, position_size)
    
    # Execute backtest
    backtest.fetch_data()
    backtest.calculate_indicators()
    trades_df = backtest.run_backtest()
    metrics = backtest.calculate_metrics()
    
    # Print EACH AND EVERY TRADE IN DETAIL
    backtest.print_detailed_trades()
    
    # Save results
    trades_df.to_csv('backtest_results.csv', index=False)
    print("\n\n" + "="*120)
    print("✅ Results saved to backtest_results.csv")
    print("="*120)
