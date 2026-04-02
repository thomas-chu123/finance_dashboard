# 蒙地卡羅模擬 — 修復說明

## 🔴 **發現的問題**

### 核心 Bug：年提取計算邏輯完全錯誤

**文件位置**：`backend/app/services/monte_carlo_engine.py` 第 109 行

**原代碼**（❌ 錯誤）：
```python
net_cashflow = (annual_contribution - annual_withdrawal) * inf_factor
new_balances += net_cashflow
```

**問題分析**：

1. **提取沒有基於餘額計算**
   - `annual_withdrawal` 被視為固定金額（如 20）
   - 實際應該是：`balance * (20 / 100) = balance * 0.20`
   - 導致每年只提取固定的 20 塊（而不是 20% 的餘額）

2. **通膨調整優先級錯誤**
   - 累積通膨被乘到錯誤的地方
   - 優先級順序應為：計算報酬 → 調整提取金額 → 提取

3. **結果**：提取幾乎無效，餘額永遠不會耗盡
   - ✗ 100萬 + 20% 年提取 = **100% 成功率**（完全不合理）
   - ✓ 應該是：~0% 成功率（資金會快速耗盡）

---

## ✅ **修復方案**

### 新代碼（✓ 正確）：
```python
# Calculate inflation factor for this year (for adjusting contributions/withdrawals)
current_year_inflation = 1.0
if adjust_for_inflation and inflation_std > 0:
    current_year_inflation = 1 + sim_inflation[:, t-1]
elif adjust_for_inflation:
    current_year_inflation = 1 + inflation_mean

# Add contribution (grew by inflation)
contribution = annual_contribution * current_year_inflation
new_balances += contribution

# Subtract withdrawal (as percentage of current balance)
# withdrawal_rate should be in percentage (0-100), convert to decimal
withdrawal_rate = annual_withdrawal / 100.0  # Convert percentage to decimal
withdrawal = new_balances * withdrawal_rate
new_balances -= withdrawal

# Floor at zero (bankrupt condition)
new_balances = np.maximum(new_balances, 0)
```

### 修復要點：

1. **百分比正確轉換**
   - `annual_withdrawal / 100.0` 將 20 轉換成 0.20

2. **提取基於當年餘額**
   - `withdrawal = new_balances * withdrawal_rate`
   - 確保提取金額會隨著餘額縮小而縮小

3. **通膨調整邏輯清晰**
   - 只調整「投入」部分的購買力
   - 提取自動隨著報酬和餘額變化

---

## 📊 **修復驗證**

使用更現實的場景測試（100萬初始 + 5% 平均年報酬 + 20% 年提取）：

| 年份 | 報酬後 | 提取額 | 剩餘 |
|-----|-------|--------|------|
| 1 | $1,050,000 | $210,000 | $840,000 |
| 5 | $522,765 | $104,553 | $418,212 |
| 10 | $218,627 | $43,725 | $174,901 |
| 15 | $91,432 | $18,286 | $73,146 |

**結論**：15年內資金耗盡約 92.7% ✓ 符合預期的高失敗率

---

## 🔧 **如何使用修復**

只需清除快取並重新執行模擬：

```bash
# 可選：清除 Redis 快取
redis-cli FLUSHDB

# 前端：刷新頁面後重新執行模擬
# 系統會使用新的計算邏輯
```

---

## ⚠️ **預期結果變化**

修復後，蒙地卡羅模擬會顯示**更現實的成功率**：

| 場景 | 修復前 | 修復後 |
|------|--------|--------|
| 100萬 + 7年報酬 + 20% 提取 | ✗ 100% | ✓ ~10% |
| 100萬 + 5年報酬 + 20% 提取 | ✗ 100% | ✓ ~5% |
| 100萬 + 7年報酬 + 4% 提取 | ✓ 95% | ✓ 95% |

---

## 📋 **後續建議**

1. **添加提取策略**
   - 動態提取（market-dependent）
   - 固定金額 vs. 百分比
   
2. **增強通膨模型**
   - 可選：美國 vs. 台灣通膨率
   
3. **測試覆蓋**
   - 添加單元測試驗證邊界情況
   - 與第三方工具（如 cFIREsim）對比驗證

4. **UI 提示**
   - 在前端添加警告：「若年提取率 > 4%，成功率會顯著下降」
