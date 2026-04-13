# Backtest 調試工具 - 快速開始

## 概述

`scripts/debug_backtest.sh` 是一個便利的 Shell 包裝腳本，用於快速運行 backtest 調試工具，驗證回測計算並導出原始數據。

---

## 安裝

腳本已位於 `/scripts/debug_backtest.sh`，已設為可執行。

或手動設置：
```bash
chmod +x scripts/debug_backtest.sh
```

---

## 快速使用

### 基本用法

```bash
# 單個 ETF - 默認過去 2 年
./scripts/debug_backtest.sh VTI

# 多個符號 - 等權
./scripts/debug_backtest.sh VTI BND

# 自定義日期
./scripts/debug_backtest.sh VTI -s 2020-01-01 -e 2024-01-01

# 自定義權重
./scripts/debug_backtest.sh VTI BND -w "70 30" -s 2020-01-01 -e 2024-01-01

# 台灣股票
./scripts/debug_backtest.sh 0050.TW 0056.TW -w "60 40"

# 全球 60/40 資產配置
./scripts/debug_backtest.sh VTI BND -w "60 40" -s 2018-01-01 -e 2024-01-01
```

---

## 選項說明

| 選項 | 說明 | 示例 |
|------|------|------|
| `-s, --start` | 回測起始日期 | `-s 2020-01-01` |
| `-e, --end` | 回測結束日期 | `-e 2024-01-01` |
| `-w, --weights` | 權重列表（空格分隔） | `-w "70 30"` |
| `-h, --help` | 顯示幫助信息 | `-h` |

**注**: 
- 起始日期默認為當前日期前 2 年
- 結束日期默認為當前日期
- 若未指定權重，自動使用等權分配

---

## 輸出文件

所有文件生成到 `temp/` 目錄：

### 1. 原始數據 CSV
```
backtest_raw_data_2022.csv
backtest_raw_data_2023.csv
backtest_raw_data_2024.csv
```

**列**:
- `date` — 交易日期
- `{symbol}_close` — 各符號收盤價
- `{symbol}_return` — 各符號日收益率
- `portfolio_return` — 加權組合日收益率
- `portfolio_value` — 累積組合價值

### 2. 組合價值曲線
```
backtest_portfolio_value.csv
```

**列**:
- `date` — 交易日期
- `portfolio_value` — 累積投資價值

### 3. 驗證報告

#### JSON 格式
```
backtest_validation_report.json
```

內容:
```json
{
  "metadata": {
    "symbols": ["VTI", "BND"],
    "weights": [0.7, 0.3],
    "start_date": "2022-01-01",
    "end_date": "2024-01-01"
  },
  "metrics": {
    "total_return": 0.2534,
    "annualized_return": 0.1197,
    "volatility": 0.0812,
    "sharpe_ratio": 1.4756,
    "max_drawdown": -0.2103,
    "cagr": 0.1197
  },
  "validation": {
    "data_completeness": 1.0,
    "price_anomalies": 0,
    "calculation_verified": true
  }
}
```

#### 文本格式
```
backtest_validation_report.txt
```

易讀的報告格式，包含所有指標和數據驗證結果。

---

## 常見使用場景

### 場景 1: 驗證回測計算

驗證回測引擎是否正確計算了 Sharpe Ratio 和 Max Drawdown：

```bash
./scripts/debug_backtest.sh VTI BND -w "60 40" -s 2020-01-01 -e 2024-01-01
```

檢查輸出報告中的 `sharpe_ratio` 和 `max_drawdown` 是否符合預期。

### 場景 2: 分析單一符號

查看單一 ETF 的年度表現：

```bash
./scripts/debug_backtest.sh VTI -s 2020-01-01 -e 2024-01-01
```

查看 `backtest_raw_data_*.csv` 中每年的收益率變化。

### 場景 3: 台灣股票vs美股

對比台灣 ETF 與美股 ETF 的組合表現：

```bash
./scripts/debug_backtest.sh 0050.TW VTI -w "50 50" -s 2022-01-01 -e 2024-01-01
```

### 場景 4: 長期回測

評估 30 年的長期複利效果：

```bash
./scripts/debug_backtest.sh VTI BND -w "70 30" -s 1994-01-01 -e 2024-01-01
```

---

## 示例输出

### 執行命令
```bash
$ ./scripts/debug_backtest.sh VTI BND -w "70 30" -s 2022-01-01 -e 2024-01-01
```

### 終端輸出
```
═══════════════════════════════════════════════
Backtest 調試工具
═══════════════════════════════════════════════

配置:
  符號: VTI BND
  權重: 70 30
  日期範圍: 2022-01-01 至 2024-01-01

正在運行調試工具...

[2024-01-15 14:23:45] 開始獲取數據...
✓ VTI: 获取 504 天数据
✓ BND: 获取 504 天数据

[2024-01-15 14:23:47] 開始回測...
✓ 回測完成

[2024-01-15 14:23:48] 開始數據驗證...
✓ 數據完整性: 100.0%
✓ 沒有價格異常
✓ 計算已驗證

✅ 調試完成！
📁 結果已保存到: ./temp/

生成的文件:
  • backtest_raw_data_2022.csv — 每年的原始數據
  • backtest_raw_data_2023.csv — 每年的原始數據
  • backtest_raw_data_2024.csv — 每年的原始數據
  • backtest_portfolio_value.csv — 組合價值曲線
  • backtest_validation_report.json — JSON 格式報告
  • backtest_validation_report.txt — 文本格式報告
```

### 驗證報告示例
```
$ cat temp/backtest_validation_report.txt

════════════════════════════════════════════════
Backtest 驗證報告
════════════════════════════════════════════════

符號: VTI, BND
權重: 70%, 30%
日期範圍: 2022-01-01 至 2024-01-01

════════════════════════════════════════════════
投資回報指標
════════════════════════════════════════════════

總報酬 (Total Return):       25.34%
年化報酬 (Annualized Return): 11.97%
波動度 (Volatility):          8.12%
夏普比例 (Sharpe Ratio):      1.4756
最大回撤 (Max Drawdown):     -21.03%
年複合增長率 (CAGR):         11.97%

════════════════════════════════════════════════
數據驗證
════════════════════════════════════════════════

數據完整性: 100.0% (504 / 504 天)
價格異常:   0 個
計算驗證:   ✓ 通過

════════════════════════════════════════════════
```

---

## 故障排查

### 問題: 「符號未找到」

**原因**: Yahoo Finance 沒有該符號的數據

**解決方案**:
- 檢查符號拼寫（如 `0050.TW` vs `0050.tw`）
- 台灣股票需要 `.TW` 後綴
- 美股不需要後綴（如 `VTI` 不是 `VTI.US`）

```bash
# ✓ 正確
./scripts/debug_backtest.sh 0050.TW VTI

# ✗ 錯誤
./scripts/debug_backtest.sh 0050 VTI.US
```

### 問題: 「日期範圍無效」

**原因**: 起始日期晚於結束日期，或日期格式不正確

**解決方案**:
- 使用 YYYY-MM-DD 格式
- 確保起始日期 < 結束日期

```bash
# ✓ 正確
./scripts/debug_backtest.sh VTI -s 2020-01-01 -e 2024-01-01

# ✗ 錯誤
./scripts/debug_backtest.sh VTI -s 01/01/2020 -e 2024/01/01
```

### 問題: 「權重不相等」

**原因**: 權重總和不等於 1，或權重數量不符

**解決方案**:
- 確保權重總和為 1.0（或在 0-100 之間，工具會自動轉換）
- 權重數量必須等於符號數量

```bash
# ✓ 正確 (總和 = 1.0)
./scripts/debug_backtest.sh VTI BND -w "0.7 0.3"

# ✓ 正確 (總和 = 100)
./scripts/debug_backtest.sh VTI BND -w "70 30"

# ✗ 錯誤 (總和 != 1.0 或 100)
./scripts/debug_backtest.sh VTI BND -w "60 30"
```

### 問題: 「權限被拒絕」

**原因**: 腳本沒有執行權限

**解決方案**:
```bash
chmod +x scripts/debug_backtest.sh
```

### 問題: 「Python 模塊未找到」

**原因**: 後端環境未激活或依賴未安裝

**解決方案**:
```bash
cd backend
pip install -r requirements.txt
cd ..
./scripts/debug_backtest.sh VTI
```

---

## 進階用法

### 直接運行 Python 腳本

如果 Shell 腳本不適用，可以直接使用 Python：

```bash
cd backend
python ../tests/debug_backtest.py \
  --symbols VTI BND \
  --weights 0.7 0.3 \
  --start 2022-01-01 \
  --end 2024-01-01
```

### 整合到 CI/CD

在 GitHub Actions 中運行回測驗證：

```yaml
- name: Verify backtest calculations
  run: |
    ./scripts/debug_backtest.sh VTI BND -w "60 40" -s 2020-01-01 -e 2024-01-01
    if [ -f temp/backtest_validation_report.json ]; then
      cat temp/backtest_validation_report.json
    fi
```

---

## 相關文件

- `tests/debug_backtest.py` — 核心調試工具
- `docs/debug_backtest_guide.md` — 詳細文檔
- `backend/app/services/backtest_engine.py` — 回測引擎
- `temp/` — 結果輸出目錄

---

## 反饋與改進

若腳本出現問題或有改進建議，請：

1. 檢查 `/tests/debug_backtest.py` 中的錯誤信息
2. 查看完整報告：`cat temp/backtest_validation_report.txt`
3. 提供符號、日期範圍和權重信息以便診斷
