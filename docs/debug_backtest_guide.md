# Backtest 調試工具使用指南

## 概述

`debug_backtest.py` 是一個強大的調試工具，用於驗證回測引擎的計算正確性並導出詳細的數據報告。

## 功能特性

✅ **數據驗證** — 從 Yahoo Finance 獲取並驗證歷史數據  
✅ **日期對齊** — 自動處理不同市場的節假日  
✅ **性能計算** — 計算 CAGR、波動率、最大回撤、夏普比例等  
✅ **數據導出** — 導出每年的原始數據到 CSV  
✅ **詳細報告** — 生成 JSON 和文本格式的驗證報告  
✅ **組合追蹤** — 導出組合價值曲線和每日回撤數據  

## 安裝依賴

```bash
cd backend
pip install -r requirements.txt
```

確保已安裝的主要包：
- `yfinance` — 從 Yahoo Finance 獲取數據
- `pandas` — 數據處理
- `numpy` — 數值計算

## 基本使用

### 單個符號

```bash
python tests/debug_backtest.py \
  --symbols VTI \
  --start 2020-01-01 \
  --end 2024-01-01
```

### 多個符號（等權）

```bash
python tests/debug_backtest.py \
  --symbols VTI BND SPY \
  --start 2020-01-01 \
  --end 2024-01-01
```

### 多個符號（自定義權重）

```bash
python tests/debug_backtest.py \
  --symbols VTI BND \
  --weights 70 30 \
  --start 2020-01-01 \
  --end 2024-01-01
```

### 台灣股票和 ETF

```bash
python tests/debug_backtest.py \
  --symbols 0050.TW 0056.TW \
  --weights 60 40 \
  --start 2022-01-01 \
  --end 2024-01-01
```

### 混合資產（股票 + 期貨）

```bash
python tests/debug_backtest.py \
  --symbols VTI GC=F \
  --weights 80 20 \
  --start 2020-01-01 \
  --end 2024-01-01
```

## 輸出檔案

工具會在 `/temp` 目錄下生成以下檔案：

### 1. 年度原始數據

**檔案**: `backtest_raw_data_YYYY.csv`

包含每年的完整價格和收益率數據：

```
date,VTI,BND,VTI_daily_return,BND_daily_return
2020-01-02,125.45,82.30,NaN,NaN
2020-01-03,126.12,82.50,0.00532,0.00241
...
```

### 2. 組合價值曲線

**檔案**: `backtest_portfolio_value.csv`

組合的詳細績效數據：

```
date,portfolio_value,cumulative_return,daily_return,drawdown
2020-01-02,100000.00,0.00,NaN,NaN
2020-01-03,100532.50,0.00533,0.00533,-0.00012
```

**欄位說明**：
- `portfolio_value` — 組合的總價值
- `cumulative_return` — 累積回報率
- `daily_return` — 每日回報率
- `drawdown` — 從峰值的回撤百分比

### 3. 驗證報告（JSON）

**檔案**: `backtest_validation_report.json`

完整的驗證報告（機器可讀格式）：

```json
{
  "price_validation": {
    "symbols": ["VTI", "BND"],
    "total_rows": 1000,
    "date_range": {
      "start": "2020-01-01",
      "end": "2024-01-01"
    }
  },
  "portfolio_metrics": {
    "total_return": 0.85,
    "cagr": 0.163,
    "annual_volatility": 0.087,
    "max_drawdown": -0.28,
    "sharpe_ratio": 1.45,
    "trading_days": 1000,
    "years": 4.0
  },
  "annual_returns": {
    "2020": 0.12,
    "2021": 0.28,
    "2022": -0.18,
    "2023": 0.24
  },
  "symbol_statistics": {
    "VTI": {
      "total_return": 1.02,
      "annual_return": 0.20,
      "volatility": 0.15,
      "min_daily_return": -0.08,
      "max_daily_return": 0.09,
      "weight": 0.7
    },
    "BND": {
      "total_return": 0.15,
      "annual_return": 0.035,
      "volatility": 0.04,
      "min_daily_return": -0.03,
      "max_daily_return": 0.02,
      "weight": 0.3
    }
  }
}
```

### 4. 驗證報告（文本）

**檔案**: `backtest_validation_report.txt`

人類可讀的驗證報告：

```
================================================================================
回測調試驗證報告
================================================================================

📊 價格數據驗證
----------------------------------------
符號: VTI, BND
總行數: 1000
日期範圍: 2020-01-01 至 2024-01-01

📈 組合績效指標
----------------------------------------
總回報: 85.00%
年化回報 (CAGR): 16.30%
年波動率: 8.70%
最大回撤: -28.00%
夏普比例: 1.45
交易天數: 1000
年數: 4.00

📅 按年回報率
----------------------------------------
2020: 12.00%
2021: 28.00%
2022: -18.00%
2023: 24.00%

📊 各符號統計
----------------------------------------

VTI (權重: 70.0%)
  總回報: 102.00%
  年化回報: 20.00%
  波動率: 15.00%
  最小日收益: -8.00%
  最大日收益: 9.00%

BND (權重: 30.0%)
  總回報: 15.00%
  年化回報: 3.50%
  波動率: 4.00%
  最小日收益: -3.00%
  最大日收益: 2.00%

================================================================================
```

## 計算指標說明

### CAGR（複合年成長率）
年化回報率，是衡量投資長期績效的標準指標。

### Annual Volatility（年波動率）
年化標準差，衡量投資的風險程度。

### Max Drawdown（最大回撤）
從峰值到谷值的最大損失百分比。

### Sharpe Ratio（夏普比例）
風險調整後的回報率，計算公式：
```
Sharpe = (年回報 - 無風險利率) / 年波動率
```

## 調試工作流程

1. **確認數據正確性**
   - 檢查 `backtest_raw_data_YYYY.csv` 中的價格數據
   - 驗證日期範圍和行數

2. **檢查每日回報**
   - 在 CSV 中手動驗證幾個日收益率的計算
   - 確保沒有 NaN 或異常值

3. **驗證性能指標**
   - 比較 `backtest_validation_report.txt` 中的 CAGR 和波動率
   - 與外部工具（如 Excel、Google Sheets）對比

4. **檢查組合構建**
   - 驗證權重是否正確應用
   - 檢查組合價值曲線是否合理

5. **分析年度表現**
   - 查看各年的回報率分佈
   - 識別異常的市場年份

## 常見問題

### Q: 為什麼有些年份的數據行數不同？

**A**: 不同市場有不同的交易日曆。該工具使用 `ffill()` 和 `bfill()` 自動填充，處理跨市場的節假日差異。

### Q: 如何處理 NaN（缺失數據）？

**A**: 工具自動使用前向填充（ffill）和後向填充（bfill）來處理缺失值。如果仍有 NaN，這表示該期間無交易數據。

### Q: 是否支援台灣股票？

**A**: 是的！支援所有 Yahoo Finance 支援的符號，包括：
- 台灣 ETF：`0050.TW`、`0056.TW` 等
- 台灣指數：`^TWII`（台指）
- 匯率：`TWD=X`

### Q: 能否比較不同時間段的回報？

**A**: 可以！只需用不同的 `--start` 和 `--end` 日期執行工具，生成新的報告進行對比。

### Q: 夏普比例的無風險利率是多少？

**A**: 目前固定設定為 2%（年化）。可在代碼中修改 `RISK_FREE_RATE` 常數。

## 進階用法

### 調試特定符號組合

```bash
# 測試全球 60/40 資產配置
python tests/debug_backtest.py \
  --symbols VTI BND \
  --weights 60 40 \
  --start 2018-01-01 \
  --end 2024-01-01
```

### 測試高風險組合

```bash
# 純股票、高成長組合
python tests/debug_backtest.py \
  --symbols QQQ VTI \
  --weights 50 50 \
  --start 2020-01-01 \
  --end 2024-01-01
```

### 測試另類資產

```bash
# 股票 + 黃金 + 原油組合
python tests/debug_backtest.py \
  --symbols VTI GC=F CL=F \
  --weights 60 20 20 \
  --start 2019-01-01 \
  --end 2024-01-01
```

## 故障排除

### 錯誤：「No data available」

- 檢查符號是否正確（區分大小寫）
- 驗證日期範圍是否有效
- 確認 Yahoo Finance 中該符號有數據

### 錯誤：「模塊未找到」

```bash
# 確保在 backend 目錄安裝依賴
cd backend
pip install -r requirements.txt
```

### 輸出檔案為空

- 檢查 `/temp` 目錄是否存在且可寫
- 查看日誌輸出以了解詳細錯誤信息

## 範例分析

### 分析 COVID-19 疫情期間的表現

```bash
python tests/debug_backtest.py \
  --symbols VTI BND \
  --weights 70 30 \
  --start 2019-01-01 \
  --end 2021-12-31
```

檢查 `backtest_validation_report.txt` 中 2020 年的回報率（應該是負數，然後 2021 年強勁反彈）。

### 比較 2022 年熊市影響

```bash
python tests/debug_backtest.py \
  --symbols VTI BND QQQ \
  --weights 60 30 10 \
  --start 2022-01-01 \
  --end 2022-12-31
```

觀察 `drawdown` 欄位，看最大回撤的時機和幅度。

## 貢獻

歡迎提出改進建議！如需新增功能：
- 支援更多數據源
- 新增績效指標
- 改進數據導出格式

---

**最後更新**: 2026-04-13  
**作者**: Finance Dashboard 開發團隊
