---
goal: 實現 RSI 技術指標與複合觸發條件的警報系統
version: 1.0
date_created: 2026-03-23
last_updated: 2026-03-23
owner: Finance Dashboard Team
status: 'Planned'
tags: ['feature', 'technical-analysis', 'alerts', 'tracking']
---

# RSI 指標與複合觸發條件警報系統實現計劃

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

## 簡介

本計劃旨在增強指數追蹤管理系統的警報觸發能力。當前系統僅支持基於價格的單一觸發條件，本計劃將添加：
1. **RSI (相對強度指數) 指標** 的自動計算與追蹤
2. **複合觸發條件** 支持：RSI 單獨、價格單獨、或兩者同時符合
3. **每週 RSI** 的計算邏輯（基於7天數據）

---

## 1. 需求與約束

### 功能需求
- **REQ-001**: 每週 RSI 計算：基於過去7個交易日的收盤價
- **REQ-002**: 支持 RSI 範圍設定 (例：RSI < 30 超賣，RSI > 70 超買)
- **REQ-003**: 支持三種觸發模式：
  - 模式A：僅限價格觸發
  - 模式B：僅限 RSI 觸發
  - 模式C：價格 AND RSI 同時觸發
- **REQ-004**: RSI 值實時計算與儲存，用於警報檢測
- **REQ-005**: 前端支持切換觸發條件模式

### 技術約束
- **CON-001**: yfinance 不提供 RSI，需自行計算
- **CON-002**: RSI 計算需要至少 14 個數據點（傳統 RSI 週期）
- **CON-003**: 需要支持台股與美股數據源
- **CON-004**: 需向後相容現有警報系統

### 安全與性能
- **SEC-001**: RSI 計算需限制週期範圍防止過度計算
- **PAT-001**: 使用現有 Redis 快取層存儲 RSI 值
- **GUD-001**: 遵循 Conventional Commits 規範

---

## 2. 實現步驟

### Phase 1: 後端 RSI 計算與儲存基礎設施

**GOAL-001**: 建立 RSI 計算引擎與數據模型擴展

| Task       | 描述                                                 | 完成 | 日期 |
|-----------|------------------------------------------------------|------|------|
| TASK-001  | 在 `app/services/technical_indicators.py` 中實現 RSI 計算函數 | ☐    |      |
| TASK-002  | 擴展 Pydantic 模型支持 RSI 觸發參數 (TrackingCreate/Update) | ☐    |      |
| TASK-003  | 在 Supabase 中添加 RSI 相關列到 tracked_indices 表 | ☐    |      |
| TASK-004  | 建立 RSI 計算與快取服務（確保不重複計算） | ☐    |      |
| TASK-005  | 編寫 RSI 計算單元測試（邊界情況：數據不足、NaN 處理） | ☐    |      |

### Phase 2: 警報檢測引擎改造

**GOAL-002**: 實現複合條件警報檢測邏輯

| Task       | 描述                                                 | 完成 | 日期 |
|-----------|------------------------------------------------------|------|------|
| TASK-006  | 重構 `app/routers/market.py` 中的警報檢測邏輯 | ☐    |      |
| TASK-007  | 實現 `_check_rsi_condition()` 函數 | ☐    |      |
| TASK-008  | 實現 `_check_price_condition()` 函數 | ☐    |      |
| TASK-009  | 實現 `_evaluate_trigger_conditions()` 複合邏輯函數 | ☐    |      |
| TASK-010  | 更新定時警報檢測任務（scheduler）以調用新邏輯 | ☐    |      |
| TASK-011  | 編寫端到端警報觸發測試 | ☐    |      |

### Phase 3: API 端點與路由擴展

**GOAL-003**: 暴露 RSI 相關 API 端點

| Task       | 描述                                                 | 完成 | 日期 |
|-----------|------------------------------------------------------|------|------|
| TASK-012  | `POST /api/tracking` - 支持 RSI 參數創建追蹤項目 | ☐    |      |
| TASK-013  | `PUT /api/tracking/{id}` - 支持更新 RSI 觸發條件 | ☐    |      |
| TASK-014  | `GET /api/tracking/{id}/rsi-data` - 獲取最新 RSI 值 | ☐    |      |
| TASK-015  | 更新追蹤列表返回值以包含 RSI、trigger_mode 等 | ☐    |      |
| TASK-016  | 更新測試警報端點以驗證複合條件邏輯 | ☐    |      |

### Phase 4: 前端 UI 與交互

**GOAL-004**: 前端支持 RSI 觸發條件配置

| Task       | 描述                                                 | 完成 | 日期 |
|-----------|------------------------------------------------------|------|------|
| TASK-017  | 更新 `TrackingCreate` 模型以支持 RSI 參數 | ☐    |      |
| TASK-018  | 修改新增/編輯模態框支持觸發模式選擇（價格/RSI/兩者） | ☐    |      |
| TASK-019  | 在追蹤列表中顯示「觸發模式」列（含當前 RSI 值） | ☐    |      |
| TASK-020  | 新增「RSI 設置面板」用於設定超買/超賣閾值 | ☐    |      |
| TASK-021  | 編寫前端組件集成測試 | ☐    |      |

### Phase 5: 整合與部署準備

**GOAL-005**: 完整測試與部署準備

| Task       | 描述                                                 | 完成 | 日期 |
|-----------|------------------------------------------------------|------|------|
| TASK-022  | 執行回歸測試（確保現有警報功能不受損） | ☐    |      |
| TASK-023  | 性能測試：RSI 計算對大量符號的影響 | ☐    |      |
| TASK-024  | 撰寫 `/docs/rsi-alerts-guide.md` 使用文檔 | ☐    |      |
| TASK-025  | 撰寫遷移腳本（為舊數據添加 RSI 相關列） | ☐    |      |
| TASK-026  | 準備 Git commit messages 與 PR 說明 | ☐    |      |

---

## 3. 可選方案

- **ALT-001**: 使用 `pandas-ta` 庫計算 RSI (vs 手動實現)
  - 優點：經過驗證的算法、支援多指標
  - 缺點：增加依賴、需要額外學習曲線
  
- **ALT-002**: 使用外部 API 檢索 RSI (vs 本地計算)
  - 優點：減少計算負擔
  - 缺點：增加延遲、API 依賴、成本
  
- **ALT-003**: 支持自定義 RSI 週期 (vs 固定 14 天)
  - 優點：更靈活
  - 缺點：複雜度增加、UI 設計困難

---

## 4. 依賴關係

- **DEP-001**: 後端基礎設施（Phase 1）必須於 Phase 2 之前完成
- **DEP-002**: API 端點（Phase 3）依賴 Phase 1 的模型擴展
- **DEP-003**: 前端（Phase 4）依賴 Phase 3 的 API 完成
- **DEP-004**: pandas、numpy 庫已在 requirements.txt 中，可用於計算

---

## 5. 受影響的檔案

### 後端
- **FILE-001**: `backend/app/services/technical_indicators.py` (新建)
- **FILE-002**: `backend/app/models/__init__.py` - 擴展 TrackingCreate/Update
- **FILE-003**: `backend/app/routers/market.py` - 警報檢測邏輯
- **FILE-004**: `backend/app/routers/tracking.py` - 追蹤管理端點
- **FILE-005**: `backend/app/database.py` - Supabase 遷移準備
- **FILE-006**: `docs/line_setup.sql` - 新增 SQL 遷移

### 前端
- **FILE-007**: `frontend/src/views/TrackingView.vue` - UI 更新
- **FILE-008**: `frontend/src/stores/tracking.js` - 狀態管理
- **FILE-009**: `frontend/src/api/tracking.js` (新建) - API 客戶端

### 文檔
- **FILE-010**: `docs/rsi-alerts-guide.md` (新建) - 使用指南

---

## 6. 測試策略

### 單元測試
- **TEST-001**: RSI 計算準確性（vs 已知數據點）
- **TEST-002**: 邊界情況：數據不足、異常值、NaN 處理
- **TEST-003**: 價格觸發條件邏輯
- **TEST-004**: RSI 觸發條件邏輯
- **TEST-005**: 複合觸發邏輯（AND 操作）

### 整合測試
- **TEST-006**: 完整警報流程（數據 → RSI 計算 → 條件檢測 → 通知發送）
- **TEST-007**: 多種資產類型（台股、美股、ETF）
- **TEST-008**: 快取層功能性

### UI 測試
- **TEST-009**: 模態框觸發模式選擇
- **TEST-010**: RSI 值實時更新顯示
- **TEST-011**: 編輯現有追蹤項目以切換觸發模式

---

## 7. 風險與假設

### 風險
- **RISK-001**: RSI 計算對性能的影響（大量符號情況）
  - 緩解：使用 Redis 快取、非同步排程計算
  
- **RISK-002**: 舊數據遷移失敗導致現有追蹤失效
  - 緩解：編寫回滾腳本、備份數據
  
- **RISK-003**: 使用者混淆新觸發模式 UI
  - 緩解：提供清晰說明文檔、教程視頻

### 假設
- **ASSUMPTION-001**: yfinance 持續提供 OHLCV 數據
- **ASSUMPTION-002**: 使用者網路連線穩定，足以支持實時 RSI 計算
- **ASSUMPTION-003**: 14 天 RSI 週期是業界標準，無需自定義

---

## 8. 相關文檔與參考

- [yfinance Documentation](https://yfinance.readthedocs.io/)
- [RSI 指標計算原理](https://www.investopedia.com/terms/r/rsi.asp)
- [pandas 技術分析教程](https://pandas.pydata.org/docs/)
- 項目文檔：`/docs/backend/backend.md`、`/docs/frontend/frontend.md`
