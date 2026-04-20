# 部署指南：社群分享功能 (feat_social_share)

## 概述

本功能實現了投組分享快照功能，用戶可生成短連結分享回測/最佳化結果，無需登入即可查看。

**分支**: `feat_social_share`  
**關鍵文件**:
- `docs/migrations/20260420_portfolio_shares.sql` — 數據庫遷移
- `backend/app/routers/shares.py` — API 端點
- `backend/app/utils/share_utils.py` — 短碼生成
- `frontend/src/components/ShareButton.vue` — 前端組件

---

## 部署步驟

### 步驟 1：執行數據庫遷移

⚠️ **必須在所有其他步驟之前執行**

#### 方法 A：Supabase Web UI（推薦）

1. 登入 [Supabase Dashboard](https://supabase.io)
2. 導航至 **SQL Editor**
3. 建立新的 SQL 查詢
4. 複製並貼上 `docs/migrations/20260420_portfolio_shares.sql` 的全部內容
5. 點擊 **執行**

#### 方法 B：Supabase CLI

```bash
# 確保已安裝並登入 Supabase CLI
supabase db push 20260420_portfolio_shares

# 或手動執行 SQL
supabase sql --file docs/migrations/20260420_portfolio_shares.sql
```

#### 方法 C：自動遷移（應用啟動時）

後端 `main.py` 包含遷移檢查。如果表不存在，應用將記錄遷移 SQL 到日誌。您可以複製日誌中的 SQL 並在 Supabase Web UI 中執行。

**檢查遷移狀態**：
```bash
cd backend
python -c "from app.services.migrations import ensure_portfolio_shares_table; ensure_portfolio_shares_table()"
```

---

### 步驟 2：後端部署

```bash
# 拉取最新代碼
git checkout feat_social_share
git pull origin feat_social_share

# 後端無額外依賴需要安裝（已在 requirements.txt 中）
cd backend

# 驗證短碼生成工具
python -c "from app.utils.share_utils import generate_share_key; print(generate_share_key())"
# 預期輸出：xxx-xxx-xxx 格式的 12 字符短碼

# 啟動後端（假設在 8005 port）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

**驗證後端 API**：
```bash
# 查詢 API 文檔
curl -X GET http://127.0.0.1:8005/api/docs

# 嘗試分享端點（需要有效 JWT）
curl -X POST http://127.0.0.1:8005/api/backtest/portfolio/{portfolio_id}/share \
  -H "Authorization: Bearer {YOUR_JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"share_type": "snapshot", "expires_in_days": 30}'
```

---

### 步驟 3：前端部署

```bash
# 拉取最新代碼
cd frontend
git checkout feat_social_share
git pull origin feat_social_share

# 安裝新依賴（html2canvas）
npm install

# 驗證環境變數
cat .env.development
# 確保 VITE_API_BASE_URL 指向後端 API（如 http://127.0.0.1:8005/api）

# 啟動前端開發伺服器（或構建生產版本）
npm run dev
# 或
npm run build
```

**驗證前端路由**：
- 打開 http://127.0.0.1:3100
- 登入帳戶
- 進行回測並點擊結果卡片上的「分享」按鈕
- 驗證分享模態框顯示正確
- 點擊「下一步」並檢查後端是否成功建立分享

---

## 端到端測試

### 測試場景 1：建立分享快照

```bash
# 1. 登入前端並進行回測
# 2. 結果出現後，點擊「分享」按鈕
# 3. 配置分享參數（快照類型、30 天過期、可選描述）
# 4. 點擊「下一步：生成分享」
# 5. 等待進度條完成
# 6. 驗證分享連結顯示（格式：/share/abc-123-xyz）
# 7. 複製連結
```

### 測試場景 2：公開查看分享

```bash
# 1. 打開新的無痕浏覽器標籤或不同瀏覽器
# 2. 訪問分享連結：http://127.0.0.1:3100/share/abc-123-xyz
# 3. 驗證無需登入可以查看
# 4. 驗證顯示投組詳情、回測結果、持倉表
# 5. 測試社群分享按鈕（Twitter、Facebook、LINE、Email）
# 6. 測試「複製分享連結」按鈕
```

### 測試場景 3：TTL 和過期管理

```bash
# 1. 建立過期時間為 1 分鐘的分享（用於測試）
# 修改 frontend/src/components/ShareButton.vue 中的過期時間選項
# 或直接修改 API 響應模擬

# 2. 等待 1 分鐘後嘗試訪問分享連結
# 3. 預期獲得 404 或 "分享已過期" 提示

# 4. 檢查數據庫中過期分享的清理
# SELECT COUNT(*) FROM portfolio_shares WHERE expires_at < NOW();
# 預期應有清理任務刪除過期分享（可在後端排程中實現）
```

### 測試場景 4：RLS 安全性

```bash
# 1. 用戶 A 建立分享快照，獲得短碼 abc-123-xyz
# 2. 用戶 B 嘗試修改或刪除此分享

# 用戶 B 嘗試：
curl -X DELETE http://127.0.0.1:8005/api/backtest/shares/abc-123-xyz \
  -H "Authorization: Bearer {USER_B_JWT_TOKEN}"

# 預期結果：403 Forbidden 或權限錯誤
```

---

## 故障排除

### 問題 1：「表 portfolio_shares 不存在」

**症狀**：後端在 POST `/api/backtest/portfolio/{id}/share` 時返回 500 錯誤

**解決方案**：
1. 驗證遷移是否已執行：
   ```sql
   SELECT EXISTS (
     SELECT 1 FROM information_schema.tables 
     WHERE table_name = 'portfolio_shares'
   );
   ```
2. 如果返回 `false`，執行步驟 1 中的遷移

### 問題 2：「短碼衝突」

**症狀**：建立分享時返回 UNIQUE constraint 錯誤

**解決方案**：
- 這是預期情況（極其罕見）
- 短碼使用 base36 字母數字（36^12 ≈ 3.6e18 種組合）
- 碰撞概率 < 10^-9
- 後端的 `generate_unique_share_key()` 會自動重試

### 問題 3：「無法從社群分享頁面存取數據」

**症狀**：公開分享頁面顯示 404 或空白

**解決方案**：
1. 驗證 RLS 策略是否正確啟用：
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'portfolio_shares';
   ```
2. 確認公開分享時 `is_public = true` 已設置
3. 檢查後端日誌中的 RLS 驗證錯誤

### 問題 4：「html2canvas 在生產環境中未定義」

**症狀**：前端構建或執行時 html2canvas 報錯

**解決方案**：
```bash
# 重新安裝依賴
rm -rf node_modules package-lock.json
npm install

# 或特別安裝 html2canvas
npm install html2canvas@1.4.1
```

---

## 配置檢查清單

- [ ] 後端 `.env` 包含有效 Supabase 認證信息
- [ ] 前端 `.env.development` 和 `.env.production` 設置正確的 `VITE_API_BASE_URL`
- [ ] 數據庫遷移已成功執行（表存在）
- [ ] RLS 策略已啟用
- [ ] 後端在端口 8005 運行（或根據配置調整）
- [ ] 前端在端口 3100 運行（或根據配置調整）
- [ ] 跨域 (CORS) 配置允許前端請求後端
- [ ] JWT 令牌在儲存存儲中正確保存
- [ ] 短碼生成函數能正常工作

---

## 監控和維護

### 查看分享統計

```sql
-- 最受歡迎的分享
SELECT share_key, share_type, view_count, created_at 
FROM portfolio_shares 
ORDER BY view_count DESC 
LIMIT 10;

-- 過期分享統計
SELECT COUNT(*) as expired_count 
FROM portfolio_shares 
WHERE expires_at < NOW();

-- 用戶分享活動
SELECT user_id, COUNT(*) as share_count, MAX(created_at) as latest_share 
FROM portfolio_shares 
GROUP BY user_id 
ORDER BY share_count DESC;
```

### 定期清理過期分享

建議在後端排程中添加清理任務（每小時或每天執行一次）：

```python
# app/scheduler.py 中添加
async def cleanup_expired_shares():
    """Delete shares that have expired"""
    query = """
    DELETE FROM portfolio_shares 
    WHERE expires_at < NOW() AND is_archived = false
    RETURNING id, share_key
    """
    result = await supabase.rpc('execute_sql', {'query': query})
    logger.info(f"Cleaned up {len(result)} expired shares")
```

---

## 性能優化建議

### 快取策略

- 公開分享頁面結果快取 1 小時（Redis）
- 用戶分享列表快取 5 分鐘

```python
# 在 API 路由中實現
from redis import Redis
redis_client = Redis()

@router.get('/share/{share_key}')
async def get_public_share(share_key: str):
    # 先查快取
    cached = redis_client.get(f'share:{share_key}')
    if cached:
        return json.loads(cached)
    
    # 查數據庫
    result = await supabase.table('portfolio_shares').select('*').eq('share_key', share_key).single()
    
    # 存快取
    redis_client.setex(f'share:{share_key}', 3600, json.dumps(result))
    return result
```

### 速率限制

防止濫用（垃圾分享）：

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post('/backtest/portfolio/{portfolio_id}/share')
@limiter.limit('10/hour')  # 每小時 10 個分享
async def create_share(portfolio_id: str, request: Request):
    pass
```

---

## 回滾計劃

如果需要回滾此功能：

```sql
-- 移除 RLS 策略
DROP POLICY "Anyone can view public shares" ON portfolio_shares;
DROP POLICY "Users can manage their own shares" ON portfolio_shares;
DROP POLICY "Users can only create shares for their portfolios" ON portfolio_shares;

-- 移除表
DROP TABLE portfolio_shares;

-- 移除 backtest_portfolios 的新列
ALTER TABLE backtest_portfolios 
DROP COLUMN IF EXISTS is_public,
DROP COLUMN IF EXISTS public_created_at,
DROP COLUMN IF EXISTS share_description,
DROP COLUMN IF EXISTS share_tags;
```

---

## 后续工作

### Phase 2：社群功能

- [ ] 用戶可評論分享快照
- [ ] 按讚和收藏功能
- [ ] 熱門策略排行榜
- [ ] 跟蹤作者功能

### Phase 3：進階分享

- [ ] 嵌入式小工具（網站可嵌入分享快照）
- [ ] 一鍵導入分享策略
- [ ] 分享快照的版本控制
- [ ] 高級隱私設置（限制查看者等）

---

## 聯絡方式

如有問題，請參考：
- 後端文檔：`docs/backend/backend.md`
- 前端文檔：`docs/frontend/frontend.md`
- API 文檔：http://127.0.0.1:8005/api/docs

