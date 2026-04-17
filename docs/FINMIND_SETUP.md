# FinMind API 配置指南

## 🎯 目標

設置 FinMind API token，使台灣 ETF 回測使用本地數據源而不是 Yahoo Finance，從而：
- ✅ 避免拆股信息延遲問題
- ✅ 確保股息調整準確（特別是高股息 ETF 如 0056）
- ✅ 獲得最新的台灣股票/ETF 數據

## 📋 前置要求

- 完成項目初始設置
- 網絡連接到 FinMind 服務

## 🚀 設置步驟

### Step 1：申請 FinMind API Token

1. **訪問 FinMind 官網**
   ```
   https://finmindtrade.com
   ```

2. **註冊帳戶或登入**
   - 如無帳戶，點擊「註冊」
   - 填寫必要信息完成註冊
   - 或使用 Google/GitHub 快速登入

3. **申請 API Token**
   - 登入後進入「設置」或「API」菜單
   - 點擊「申請 API Token」或「Generate Token」
   - 查看並複製生成的 token
   - Token 通常為 32-64 字符的字符串

### Step 2：配置本地環境

#### 方式 A：編輯 `.env` 文件（推薦永久配置）

```bash
# 打開項目根目錄的 .env 文件
# (Linux/macOS)
vim .env

# (Windows - 用文本編輯器打開)
notepad .env
```

找到以下行：
```ini
FinMind_API=your_finmind_api_token
```

替換為你的實際 token：
```ini
FinMind_API=<paste_your_token_here>
```

**示例**：
```ini
FinMind_API=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567
```

#### 方式 B：設置環境變數（臨時會話）

```bash
# Linux/macOS - 臨時設置（僅當前終端會話）
export FinMind_API="your_token_here"

# Windows PowerShell
$env:FinMind_API="your_token_here"

# Windows CMD
set FinMind_API=your_token_here
```

### Step 3：驗證配置

#### 使用 Python 驗證

```bash
python3 << 'VERIFY'
import os

token = os.getenv('FinMind_API')

if token and token != 'your_finmind_api_token':
    print("✅ FinMind_API token 已正確設置")
    print(f"   Token 前 20 字符：{token[:20]}...")
else:
    print("❌ FinMind_API token 未設置或為默認值")
    print("   請按照上述步驟設置 token")
VERIFY
```

#### 測試 API 連接

```bash
python3 << 'TEST'
import os
import requests

token = os.getenv('FinMind_API')

if not token or token == 'your_finmind_api_token':
    print("❌ 請先設置 FinMind_API token")
    exit(1)

print("測試 FinMind API 連接...")

try:
    response = requests.get(
        "https://api.finmindtrade.com/api/v4/data",
        params={
            "dataset": "TaiwanStockPriceAdj",
            "data_id": "0052",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "token": token
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == 200:
            print("✅ 連接成功！")
            print(f"   獲得 {len(data['data'])} 筆交易日數據")
        else:
            print(f"⚠️  API 返回異常：{data.get('msg')}")
    else:
        print(f"❌ 連接失敗 (HTTP {response.status_code})")
        
except Exception as e:
    print(f"❌ 連接錯誤：{e}")
TEST
```

## ✅ 驗證 FinMind 正在使用

當設置正確後，在回測時會看到如下日誌：

```
[MarketData] Using FinMind adjusted prices for: 0052.TW
[MarketData] FinMind fetched 252 days for 0052.TW (0.45s)
```

而不是：

```
[MarketData] yfinance fetched 252 days for 0052.TW (adjusted=True, 2.34s)
```

## 📊 數據源優先級

| 優先級 | 數據源 | 適用資產 | 特點 |
|--------|--------|----------|------|
| 1️⃣ | FinMind | 台灣股票/ETF | ✅ 本地、及時、準確 |
| 2️⃣ | yfinance | 其他資產、美股 | ⚠️ 國際數據、可能延遲 |
| 3️⃣ | 監控層 | 所有來源 | 🔍 拆股延遲檢測告警 |

## 🐛 故障排除

### 問題 1：Token 不被識別

**症狀**：依然使用 yfinance 而不是 FinMind

**原因**：
- `.env` 文件未被正確加載
- 環境變數未正確設置

**解決**：
```bash
# 驗證 .env 文件存在
ls -la .env

# 驗證 token 已設置
python3 -c "import os; print(os.getenv('FinMind_API'))"

# 如果未顯示 token，重啟終端或重新啟動應用
```

### 問題 2：FinMind API 返回 401 錯誤

**症狀**：日誌中出現 `401: Unauthorized`

**原因**：
- Token 無效或已過期
- Token 複製時帶了額外空格

**解決**：
1. 重新訪問 FinMind 官網確認 token
2. 確保 `.env` 中沒有前後空格：
   ```ini
   ❌ FinMind_API= abc123...  (有空格)
   ✅ FinMind_API=abc123...   (無空格)
   ```

### 問題 3：連接超時

**症狀**：`Timeout connecting to api.finmindtrade.com`

**原因**：
- 網絡連接問題
- FinMind 服務暫時不可用

**解決**：
- 檢查網絡連接
- 稍候后重試
- 確認 FinMind 服務狀態

## 📚 相關資源

- **FinMind 官網**：https://finmindtrade.com
- **FinMind API 文檔**：https://finmindtrade.com/docs
- **項目 .env 示例**：`backend/.env.example`
- **FinMind 遷移評估**：`docs/finmind_migration_impact.md`

## 🎓 技術背景

### 為什麼需要 FinMind？

台灣 ETF（如 0050、0052、0056）存在以下問題：
1. **拆股延遲**：Yahoo Finance 更新拆股信息有延遲（可能數週）
2. **股息調整**：高股息 ETF（0056）的配息調整容易出錯

**FinMind 優勢**：
- 台灣本地數據源，拆股信息及時
- `TaiwanStockPriceAdj` 數據集已自動處理所有調整
- 避免 Yahoo Finance 的延遲問題

### 數據調整方式

| 調整類型 | 說明 | FinMind | yfinance |
|---------|------|---------|----------|
| **股息** | 除息日價格調整 | ✅ 及時 | ✅ 及時 |
| **拆股** | 拆股日全部歷史調整 | ✅ 及時 | ⚠️ 可能延遲 |

## ❓ 常見問題

### Q：沒有 FinMind token 怎麼辦？

**A**：系統會自動回退到 Yahoo Finance。但建議申請 token 以獲得更準確的台灣 ETF 數據。

### Q：FinMind token 免費嗎？

**A**：FinMind 提供免費和付費 API token。免費版本對大多數用戶足夠。詳見 FinMind 官網。

### Q：如何修改已設置的 token？

**A**：編輯 `.env` 文件中的 `FinMind_API` 值，然後重啟應用。

### Q：Token 會被提交到 Git 嗎？

**A**：不會。`.env` 文件已添加到 `.gitignore`，不會被提交。

## 📞 支持

如遇問題，請：
1. 檢查日誌中的錯誤信息
2. 參考上述故障排除部分
3. 訪問 FinMind 官方支持

---

**更新日期**：2026-04-17  
**FinMind 遷移版本**：Phase 2
