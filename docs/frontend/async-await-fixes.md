# 前端異步操作修復報告

## 問題描述

投資總覽（Dashboard）只有在手動按下 refresh 按鈕才會顯示引用的報價，但當用戶在不同頁面之間切換時，數據會消失。

## 根本原因

Vue 3 生命週期中的 `onMounted` 鉤子中存在未 await 的異步操作。這導致父組件的初始化工作（例如加載用戶資料）在子組件渲染之前未完成，結果子組件使用到空值或默認值。

### 數據流問題圖

```
LayoutView.onMounted()
  ├─ auth.fetchProfile() [ASYNC, NO AWAIT] ❌
  └─ (異步操作在後台繼續)

DashboardView.onMounted()
  ├─ await trackingStore.fetchAll() ✓
  ├─ await trackingStore.fetchAlertLogs() ✓
  └─ await fetchQuotes()
      └─ 使用: auth.profile?.dashboard_quotes
         ├─ 如果 profile 還在加載 → null
         └─ 使用 DEFAULT_SYMBOLS 作為備用

用戶導航離開 → 組件卸載
用戶返回 Dashboard → 組件重新掛載
  ├─ 如果 profile 還在加載 → 報價消失
  └─ 時序競賽導致間歇性數據丟失
```

## 修復方案

### 1. **LayoutView.vue** (主要問題)

**文件**: `frontend/src/views/LayoutView.vue` (第 162-167 行)

**修復前**:
```javascript
onMounted(() => {
  auth.fetchProfile()  // ❌ NO AWAIT
})
```

**修復後**:
```javascript
onMounted(async () => {
  try {
    await auth.fetchProfile()
    console.log('[LayoutView] Profile loaded successfully:', auth.profile?.display_name)
  } catch (error) {
    console.error('[LayoutView] Failed to load profile:', error)
  }
})
```

**改變內容**:
- ✅ 添加 `async` 關鍵字到 onMounted
- ✅ 添加 `await` 等待 fetchProfile() 完成
- ✅ 添加 try/catch 錯誤處理
- ✅ 添加調試日誌

### 2. **OptimizeView.vue** (類似問題)

**文件**: `frontend/src/views/OptimizeView.vue` (第 467-469 行)

**修復前**:
```javascript
onMounted(() => {
  loadSymbols()  // ❌ NO AWAIT
})
```

**修復後**:
```javascript
onMounted(async () => {
  try {
    await loadSymbols()
    console.log('[OptimizeView] Symbols loaded successfully')
  } catch (error) {
    console.error('[OptimizeView] Failed to load symbols:', error)
  }
})
```

**改變內容**:
- ✅ 添加 `async` 關鍵字到 onMounted
- ✅ 添加 `await` 等待 loadSymbols() 完成
- ✅ 添加 try/catch 錯誤處理
- ✅ 添加調試日誌

### 3. **DashboardView.vue** (已正確)

**文件**: `frontend/src/views/DashboardView.vue` (第 421-427 行)

✅ 狀態: **已正確實現** - 無需更改

```javascript
onMounted(async () => {
  await trackingStore.fetchAll()
  await trackingStore.fetchAlertLogs()
  await fetchQuotes()
  quotesTimer = setInterval(fetchQuotes, 60_000)
})

onUnmounted(() => {
  if (quotesTimer) clearInterval(quotesTimer)
})
```

**已正確實現的內容**:
- ✅ 所有異步操作都被 await
- ✅ 計時器在卸載時被清除
- ✅ 無內存洩漏風險

## 修復驗證結果

已檢查所有 `onMounted` 調用:

| 文件 | 狀態 | 備註 |
|------|------|------|
| UsersView.vue | ✅ | 已正確使用 async/await |
| LayoutView.vue | ✅ FIXED | 添加 await fetchProfile() |
| LineView.vue | ✅ | 已正確使用 async/await |
| DashboardView.vue | ✅ | 已正確使用 async/await |
| TrackingView.vue | ✅ | 已正確使用 async/await |
| BacktestView.vue | ✅ | 已正確使用 async/await |
| OptimizeView.vue | ✅ FIXED | 添加 await loadSymbols() |
| RSIChart.vue | ✅ | 無異步操作 |

## 預期改進

修復後應該獲得以下改進:

1. ✅ **數據持久性**: Dashboard 報價在頁面導航時保持可見
2. ✅ **消除競賽條件**: 用戶資料和符號在子組件需要時已完全加載
3. ✅ **更好的錯誤處理**: try/catch 捕獲加載失敗
4. ✅ **改進的調試**: 添加了控制台日誌用於故障排査
5. ✅ **無內存洩漏**: 計時器在組件卸載時正確清除

## 測試建議

### 手動測試步驟

1. **測試 Dashboard 報價持久性**
   - 訪問投資總覽（Dashboard）
   - 驗證報價是否出現（無需手動刷新）
   - 切換到其他頁面（追蹤、回測等）
   - 返回 Dashboard - 報價應該仍然可見

2. **測試 OptimizeView 符號加載**
   - 訪問優化頁面
   - 驗證符號列表是否加載
   - 檢查控制台是否有日誌消息

3. **檢查控制台日誌**
   - 打開瀏覽器開發者工具控制台
   - 應該看到 `[LayoutView] Profile loaded successfully`
   - 應該看到 `[OptimizeView] Symbols loaded successfully`
   - 不應該有錯誤消息

4. **驗證頁面導航**
   - 在 Dashboard ↔ Tracking ↔ Backtest 之間切換
   - 確保每次都加載正確的數據
   - 沒有數據閃爍或消失

## 相關配置

### key async 方法需要 await

**auth.js - fetchProfile()**
```javascript
async fetchProfile() {
  if (!this.token) return
  try {
    const res = await axios.get(`${API_BASE}/api/users/me?_t=${Date.now()}`, { 
      headers: this.headers 
    })
    this.profile = res.data
  } catch (e) {
    console.error('Profile fetch failed', e)
  }
}
```

**OptimizeView.vue - loadSymbols()**
```javascript
async function loadSymbols() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest/symbols`, { 
      headers: auth.headers 
    })
    // ... 設置符號列表
  } catch (e) { 
    console.error('Symbol load failed', e) 
  }
}
```

## 相關模式

此修復遵循與 TrackingView.vue 相同的模式，該模式已在之前的會話中成功修復。

關鍵模式:
- ✅ 在 onMounted 中添加 async
- ✅ 為所有異步操作添加 await
- ✅ 添加 try/catch 錯誤處理
- ✅ 添加控制台日誌用於調試
- ✅ 在 onUnmounted 中清除計時器

## 文件修改總結

```
修改的文件: 2
  - frontend/src/views/LayoutView.vue (4 行更改)
  - frontend/src/views/OptimizeView.vue (4 行更改)

檢查的文件: 8
  - 6 個已正確
  - 1 個無需更改（無異步操作）
  - 2 個已修復
```

## 2025-01 會話記錄

- **發現日期**: 2025-01-30
- **問題**: 投資總覽報價在頁面導航時消失
- **根本原因**: LayoutView.onMounted 缺少 await fetchProfile()
- **修復時間**: ~10 分鐘
- **測試狀態**: ⏳ 待手動驗證
