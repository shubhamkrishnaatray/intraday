# Indian Large-Cap Backtest Strategy
## SMA 200 + RSI 10 Trading Strategy

### 📊 Strategy Overview

This backtest tests a trend-following strategy on Indian large-cap stocks using two key indicators:

**Indicators:**
- SMA 200 (Simple Moving Average)
- RSI 10 (Relative Strength Index)

### 📋 Strategy Rules

#### 1. **Trend Filter**
- **Bullish**: When Price > SMA 200 → Only take BUY trades
- **Bearish**: When Price < SMA 200 → Stay in CASH (no trades)

#### 2. **Entry Condition**
- RSI(10) drops below 30 in an uptrend (healthy pullback signal)
- Entry: Market order on next day's open

#### 3. **Stop Loss**
- Place stop loss slightly below the recent swing low (10-period)
- Multiplier: 0.5% below swing low

#### 4. **Exit Conditions**
- **Exit 1**: RSI(10) crosses above 40 → Exit on next day's open
- **Exit 2**: If RSI hasn't crossed 40 in 10 days → Force exit on Day 11 open

#### 5. **Position Sizing**
- Fixed position size: ₹10,000 per trade
- No shorting allowed (Long trades only)

---

### 📈 Backtest Parameters

| Parameter | Value |
|-----------|-------|
| **Assets** | TCS, Reliance, HDFC Bank, Infosys |
| **Timeframe** | Daily |
| **Period** | 2023-01-01 to 2026-05-13 |
| **Initial Capital** | ₹1,00,000 |
| **Position Size** | ₹10,000 per trade |
| **Market** | NSE (India) |

---

### 🚀 How to Run

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Run Backtest
```bash
python backtest_strategy.py
```

#### 3. Output Files
- Console output with performance metrics
- `backtest_results.csv` - Detailed trade log

---

### 📊 Output Metrics

The backtest generates the following metrics:

**Trade Statistics:**
- Total Trades
- Winning Trades
- Losing Trades
- Win Rate (%)

**P&L Metrics:**
- Initial Capital
- Total Profit/Loss
- Final Capital
- Total Return (%)
- Average Return per Trade

**Risk Metrics:**
- Maximum Gain
- Maximum Loss
- Profit Factor

---

### 📝 Trade Log Columns

| Column | Description |
|--------|-------------|
| Symbol | Stock ticker |
| Entry Date | Trade entry date |
| Entry Price | Entry price (₹) |
| Exit Date | Trade exit date |
| Exit Price | Exit price (₹) |
| Quantity | Number of shares |
| Exit Reason | Why trade was exited (RSI>40, 11 Days, Stop Loss) |
| Profit/Loss | P&L in ₹ |
| Return % | Return percentage |

---

### 🔧 Customization

You can modify the following in `backtest_strategy.py`:

```python
symbols = ['TCS', 'RELIANCE', 'HDFCBANK', 'INFY']  # Change stocks
start_date = '2023-01-01'                           # Change start date
end_date = '2026-05-13'                             # Change end date
initial_capital = 100000                            # Change capital
position_size = 10000                               # Change position size
```

---

### ⚠️ Disclaimer

This backtest is for educational purposes only. Past performance does not guarantee future results. Always consult a financial advisor before trading with real capital.

---

### 📞 Support

For issues or questions, please open a GitHub issue.
