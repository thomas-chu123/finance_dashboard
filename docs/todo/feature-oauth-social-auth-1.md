---
goal: Implement OAuth 2.0 Social Authentication (Google, GitHub, Facebook) for Login/Signup
version: 1.0
date_created: 2026-04-07
status: Planned
---

# 第三方登入整合方案 - OAuth 2.0

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本實現計劃為 Finance Dashboard 添加 OAuth 2.0 支援。

## 核心優勢

- 改善使用者體驗（使用熟悉的社交帳户登入）
- 減少密碼管理負擔
- 加快帳户建立速度
- 提升安全性（由 OAuth 提供商處理）

## 1. 功能需求

- **REQ-001**: 支援 Google OAuth 2.0 認證
- **REQ-002**: 支援 GitHub OAuth 2.0 認證
- **REQ-003**: 支援 Facebook OAuth 2.0 認證
- **REQ-004**: 首次 OAuth 登入時自動建立帳户
- **REQ-005**: OAuth 帳户可關聯到使用相同郵件的現有帳户
- **REQ-006**: 支援 OAuth 帳户解除關聯/刪除
- **REQ-007**: 在使用者設定中顯示 OAuth 提供商資訊

## 2. 安全需求

- **SEC-001**: 驗證 OAuth s- **SEC-001**: 驗證 OAuth s- **SEC-001*02**: 安全儲存 OAuth credentials（使用環境變數）
- **SEC-003**: 所有 OAuth callback 必須使用 HTTPS
- **SEC-004**: 驗證 issued 的 JWT token
- **SEC-005**: 實現 OAuth callback endpoint 的速率限制

## 3. 實現步驟

### Phase 1: 數據庫架構擴展

需要添加 `oauth_providers` 表：

```sql
CREATE TABLE oauth_providers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  provider_email TEXT,
  access_token_encrypted TEXT,
  linked_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  UNIQUE(provider, provider_id),
  UNIQUE(user_id, provider)
);
```

### Phase 2: 後端 OAuth 實現

需要安裝依賴：
- `authlib>=1.2.1`
- `cryptography>=42.0.0`

新建檔案：
- `backend/app/services/oauth_service.py` - OAuth 服務邏輯
- `backend/app/routers/oauth.py` - OAuth API endpoints

### Phase 3: 前端 UI 實現

修改檔案：
- `frontend/src/views/LoginView.vue` - 添加 OAuth 按鈕
- `frontend/src/stores/auth.js` - 添加 OAuth 相關方法

新建檔案：
- `frontend/src/components/OAuthCallback.vue` - OAuth callback 元件
- `frontend/src/composables/useOAuth.js` - OAuth 流程邏輯

### Phase 4: 環境配置

在 `.env` 中添加：

```env
OAUTH_ENABLED=true

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/oauth/callback/google

# GitHub OAuth
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/oauth/callback/github

# Facebook OAuth
FACEBOOK_OAUTH_APP_ID=your_app_id
FACEBOOK_OAUTH_APP_SECRET=your_secret
FACEBOOK_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/oauth/callback/facebook
```

### Phase 5: 測試與驗證

- 單元測試：`tests/unit/test_oauth_service.py`
- 整合測試：`tests/integration/test_oauth_endpoints.py`
- E2E 測試：完整 OAuth 流程

### Phase 6: 文件與部署

- 在 `/docs/deploy/oauth-setup.md` 撰寫設置指南
- 更新 API 文件
- 部署至 staging 和生產環境

## 4. 工作清單

### 後端工作
- [ ] 安裝依賴
- [ ] 創建 oauth_service.py
- [ ] 創建 oauth.py router
- [ ] 修改 config.py、security.py、models/__init__.py、auth.py
- [ ] 創建資料庫遷移

### 前端工作
- [ ] 修改 LoginView.vue
- [ ] 創建 OAuthCallback.vue
- [ ] 創建 useOAuth.js
- [ ] 修改 auth.js store

### 測試工作
- [ ] 編寫單元測試
- [ ] 編寫整合測試
- [ ] 編寫 E2E 測試

## 5. 參考資源

- [OAuth 2.0 授權框架](https://tools.ietf.org/html/rfc6749)
- [Authlib 文件](https://docs.authlib.org/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2/web-server)
- [GitHub OAuth Apps](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [Facebook Login](https://developers.facebook.com/docs/facebook-login/web)

