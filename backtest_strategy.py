import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# INDIAN LARGE-CAP BACKTEST: SMA 200 + RSI 10 Strategy
# ============================================================================

class IndianLargeCapBacktest:
    def __init__(self, symbols, start_date, end_date, initial_capital, position_size):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.trades = []
        self.portfolio_value = []
        
    def fetch_data(self):
        """Fetch daily OHLC data for all symbols"""
        print("📥 Fetching historical data...")
        self.data = {}
        for symbol in self.symbols:
            # Add .NS suffix for NSE stocks
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
        days_held = 0
        
        for i in range(1, len(df)):
            current_date = df.index[i]
            prev_date = df.index[i-1]
            
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
                        'Symbol': symbol,
                        'Entry Date': entry_date,
                        'Entry Price': active_trade['entry_price'],
                        'Exit Date': df.index[i+1] if i+1 < len(df) else current_date,
                        'Exit Price': exit_price,
                        'Quantity': active_trade['quantity'],
                        'Exit Reason': 'RSI > 40',
                        'Profit/Loss': profit,
                        'Return %': (profit / active_trade['entry_price'] / active_trade['quantity']) * 100
                    })
                    active_trade = None
                    entry_rsi = None
                    days_held = 0
                
                # Exit Condition 2: 10 days without RSI > 40
                elif days_held == 11:
                    exit_price = df.iloc[i+1]['Open'] if i+1 < len(df) else current_price
                    profit = (exit_price - active_trade['entry_price']) * active_trade['quantity']
                    symbol_trades.append({
                        'Symbol': symbol,
                        'Entry Date': entry_date,
                        'Entry Price': active_trade['entry_price'],
                        'Exit Date': df.index[i+1] if i+1 < len(df) else current_date,
                        'Exit Price': exit_price,
                        'Quantity': active_trade['quantity'],
                        'Exit Reason': '11 Days Hold',
                        'Profit/Loss': profit,
                        'Return %': (profit / active_trade['entry_price'] / active_trade['quantity']) * 100
                    })
                    active_trade = None
                    entry_rsi = None
                    days_held = 0
                
                # Stop Loss hit
                elif current_price < active_trade['stop_loss']:
                    exit_price = active_trade['stop_loss']
                    profit = (exit_price - active_trade['entry_price']) * active_trade['quantity']
                    symbol_trades.append({
                        'Symbol': symbol,
                        'Entry Date': entry_date,
                        'Entry Price': active_trade['entry_price'],
                        'Exit Date': current_date,
                        'Exit Price': exit_price,
                        'Quantity': active_trade['quantity'],
                        'Exit Reason': 'Stop Loss',
                        'Profit/Loss': profit,
                        'Return %': (profit / active_trade['entry_price'] / active_trade['quantity']) * 100
                    })
                    active_trade = None
                    entry_rsi = None
                    days_held = 0
            
            # ===== ENTRY CONDITIONS =====
            if not active_trade and in_uptrend:
                # Entry signal: RSI < 30
                if prev_rsi >= 30 and current_rsi < 30:
                    entry_price = df.iloc[i+1]['Open'] if i+1 < len(df) else current_price
                    stop_loss = swing_low * 0.995  # 0.5% below swing low
                    quantity = self.position_size / entry_price
                    
                    active_trade = {
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'quantity': quantity
                    }
                    entry_rsi = current_rsi
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
            return
        
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df['Profit/Loss'] > 0])
        losing_trades = len(self.trades_df[self.trades_df['Profit/Loss'] < 0])
        
        total_pnl = self.trades_df['Profit/Loss'].sum()
        avg_return = self.trades_df['Return %'].mean()
        max_loss = self.trades_df['Profit/Loss'].min()
        max_gain = self.trades_df['Profit/Loss'].max()
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        profit_factor = abs(self.trades_df[self.trades_df['Profit/Loss'] > 0]['Profit/Loss'].sum() / 
                           self.trades_df[self.trades_df['Profit/Loss'] < 0]['Profit/Loss'].sum()) \
                       if len(self.trades_df[self.trades_df['Profit/Loss'] < 0]) > 0 else np.inf
        
        final_capital = self.initial_capital + total_pnl
        total_return = (total_pnl / self.initial_capital) * 100
        
        print("="*70)
        print("📈 BACKTEST RESULTS: Indian Large-Cap SMA200 + RSI10 Strategy")
        print("="*70)
        print(f"\n📊 TRADE STATISTICS:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Winning Trades: {winning_trades}")
        print(f"  Losing Trades: {losing_trades}")
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
        print(f"\n" + "="*70)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'final_capital': final_capital
        }
    
    def print_trades(self, limit=20):
        """Print recent trades"""
        if len(self.trades_df) == 0:
            print("\n⚠️ No trades to display")
            return
        
        print(f"\n📋 TRADE LOG (Last {limit} trades):\n")
        display_df = self.trades_df.tail(limit).copy()
        display_df['Entry Date'] = pd.to_datetime(display_df['Entry Date']).dt.strftime('%Y-%m-%d')
        display_df['Exit Date'] = pd.to_datetime(display_df['Exit Date']).dt.strftime('%Y-%m-%d')
        
        print(display_df.to_string(index=False))

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
    backtest.print_trades(limit=30)
    
    # Save results
    trades_df.to_csv('backtest_results.csv', index=False)
    print("\n✅ Results saved to backtest_results.csv")