# Admin Panel - 前端技術文檔

## 目錄

- [概述](#概述)
- [架構設計](#架構設計)
- [組件結構](#組件結構)
- [狀態管理](#狀態管理)
- [API 整合](#api-整合)
- [樣式系統](#樣式系統)
- [測試指南](#測試指南)

---

## 概述

Admin Panel 前端提供完整的管理介面，基於 **Vue 3 Composition API** 和 **Pinia 狀態管理**。

### 核心特性

- ✅ 響應式用戶管理表格
- ✅ 實時統計儀表板
- ✅ 彩色日誌查看器（ANSI 轉 HTML）
- ✅ 時程表任務監控
- ✅ 暗色主題優化

---

## 架構設計

### 目錄結構

```
frontend/src/
├── App.vue                      # 應用根組件
├── main.js                      # 入口點
├── api/
│   ├── admin-api.js            # Admin API 客戶端（25+ endpoints）
│   ├── auth.js
│   └── market.js
├── components/
│   ├── LogViewer.vue           # 日誌查看器（彩色 ANSI）
│   ├── AdminModals/            # 5 個模態框
│   └── ...
├── views/
│   ├── AdminPanelView.vue      # 儀表板
│   ├── AdminUsersView.vue      # 用戶管理
│   ├── AdminLogsView.vue       # 日誌查看
│   ├── AdminSchedulerView.vue  # Scheduler 管理
│   └── AdminStatsView.vue      # 統計監控
├── stores/
│   ├── admin.js                # Admin Pinia store
│   ├── auth.js
│   └── market.js
└── router/
    └── index.js                # 路由配置
```

### 數據流架構

```
┌──────────────────┐
│   Vue Component  │
├──────────────────┤
│  Pinia Store     │ (admin.js)
│ (loadUsers, ...) │
├──────────────────┤
│  API Client      │ (admin-api.js)
│ (setAuthToken)   │
├──────────────────┤
│   HTTP Request   │ (Axios)
├──────────────────┤
│  FastAPI Backend │ (/api/admin/*)
└──────────────────┘
```

---

## 組件結構

### AdminPanelView.vue - 儀表板

```vue
<template>
  <div class="admin-panel">
    <!-- 頭部導航 -->
    <header class="admin-header">
      <h1>管理者面板</h1>
    </header>
    
    <!-- 4 個導航卡片 -->
    <div class="nav-grid">
      <NavigationCard
        title="用戶管理"
        icon="👥"
        to="/admin/users"
      />
      <NavigationCard
        title="日誌查看"
        icon="📋"
        to="/admin/logs"
      />
      <NavigationCard
        title="統計監控"
        icon="📊"
        to="/admin/stats"
      />
      <NavigationCard
        title="Scheduler 管理"
        icon="⏰"
        to="/admin/scheduler"
      />
    </div>
  </div>
</template>
```

### AdminUsersView.vue - 用戶管理

```vue
<script setup>
import { ref, computed } from 'vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()
const searchQuery = ref('')

// 表格數據
const filteredUsers = computed(() => {
  return adminStore.users.filter(user =>
    user.email.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 操作
const handleDeleteUser = async (userId) => {
  await adminStore.deleteUser(userId)
}

const handleToggleAdmin = async (userId) => {
  await adminStore.toggleAdminStatus(userId)
}
</script>

<template>
  <div class="users-view">
    <!-- 搜尋欄 -->
    <input
      v-model="searchQuery"
      type="text"
      placeholder="搜尋用戶..."
      class="search-input"
    />
    
    <!-- 用戶表格 -->
    <table class="users-table">
      <thead>
        <tr>
          <th>Email</th>
          <th>名稱</th>
          <th>管理員</th>
          <th>建立日期</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in filteredUsers" :key="user.id">
          <td>{{ user.email }}</td>
          <td>{{ user.display_name || '未設置' }}</td>
          <td>
            <toggle-switch
              :value="user.is_admin"
              @change="handleToggleAdmin(user.id)"
            />
          </td>
          <td>{{ formatDate(user.created_at) }}</td>
          <td class="actions">
            <button @click="editUser(user)">編輯</button>
            <button @click="handleDeleteUser(user.id)">刪除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.users-view {
  padding: 20px;
}

.search-input {
  width: 100%;
  padding: 10px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th {
  background: var(--bg-secondary);
  padding: 12px;
  text-align: left;
  border-bottom: 2px solid var(--border-color);
}

.users-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
}

.actions button {
  margin-right: 8px;
  padding: 4px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.actions button:hover {
  opacity: 0.8;
}
</style>
```

### LogViewer.vue - 日誌查看器（核心組件）

這是最重要的組件，負責將 **ANSI 顏色碼轉換為 HTML**。

```vue
<script setup>
import { AnsiToHtml } from 'ansi-to-html'

const props = defineProps({
  logs: {
    type: [String, Array],
    default: ''
  },
  searchQuery: {
    type: String,
    default: ''
  }
})

// ANSI 轉 HTML 配置
const ansiConverter = new AnsiToHtml({
  fg: '#ffffff',  // 白色文本
  bg: '#000000',  // 黑色背景
  colors: {
    0: '#808080',   // 黑 → 灰
    1: '#ff4444',   // 紅
    2: '#44ff44',   // 綠
    3: '#ffff00',   // 黃
    4: '#4444ff',   // 藍
    5: '#ff44ff',   // 品紅
    6: '#44ffff',   // 青
    7: '#ffffff',   // 白
    8: '#808080',   // 亮黑
    9: '#ff8888',   // 亮紅
    10: '#88ff88',  // 亮綠
    11: '#ffff88',  // 亮黃
    12: '#8888ff',  // 亮藍
    13: '#ff88ff',  // 亮品紅
    14: '#88ffff',  // 亮青
    15: '#ffffff'   // 亮白
  }
})

const convertAnsiToHtml = (text) => {
  if (!text) return ''
  
  // 將日誌字符串轉換為 HTML
  const html = ansiConverter.toHtml(text)
  
  // 搜尋高亮（如果有）
  if (props.searchQuery) {
    const regex = new RegExp(props.searchQuery, 'gi')
    return html.replace(regex, match =>
      `<mark style="background: yellow; color: black">${match}</mark>`
    )
  }
  
  return html
}
</script>

<template>
  <div class="log-viewer">
    <!-- 日誌容器 -->
    <div class="log-container" v-html="convertAnsiToHtml(logs)"></div>
  </div>
</template>

<style scoped>
.log-viewer {
  width: 100%;
  height: 600px;
  overflow: auto;
}

.log-container {
  background: #000000;  /* 純黑背景 */
  color: #ffffff;       /* 白色文本 */
  padding: 15px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  border: 1px solid #333333;
  border-radius: 4px;
}

.log-container :deep(mark) {
  background: #ffff00;
  color: #000000;
  padding: 2px;
  border-radius: 2px;
}

/* 不同顏色的 SPAN 標籤 */
.log-container :deep(span[style*="color"]) {
  font-weight: 500;
}
</style>
```

### AdminStatsView.vue - 統計監控

```vue
<script setup>
import { onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()

onMounted(() => {
  adminStore.loadStats()
})
</script>

<template>
  <div class="stats-view">
    <div class="stats-grid">
      <!-- 總用戶數 -->
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <h3>總用戶數</h3>
          <p class="stat-value">{{ adminStore.stats.total_users_count || 0 }}</p>
        </div>
      </div>
      
      <!-- 活躍用戶 -->
      <div class="stat-card">
        <div class="stat-icon">🟢</div>
        <div class="stat-content">
          <h3>活躍用戶</h3>
          <p class="stat-value">{{ adminStore.stats.active_users_count || 0 }}</p>
        </div>
      </div>
      
      <!-- 追蹤指數 -->
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <h3>追蹤指數</h3>
          <p class="stat-value">{{ adminStore.stats.tracked_indices_count || 0 }}</p>
        </div>
      </div>
      
      <!-- 發送警報 -->
      <div class="stat-card">
        <div class="stat-icon">🚨</div>
        <div class="stat-content">
          <h3>已發送警報</h3>
          <p class="stat-value">{{ adminStore.stats.alerts_sent_count || 0 }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-view {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.stat-icon {
  font-size: 32px;
  margin-right: 15px;
}

.stat-content h3 {
  margin: 0 0 5px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.stat-value {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-color);
}
</style>
```

---

## 狀態管理 (Pinia Store)

### admin.js - Admin Store

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminAPI } from '@/api/admin-api'

export const useAdminStore = defineStore('admin', () => {
  // 狀態
  const users = ref([])
  const stats = ref({})
  const auditLogs = ref([])
  const systemLogs = ref([])
  const schedulerJobs = ref([])
  const loading = ref(false)
  const error = ref(null)

  // 計算屬性
  const userCount = computed(() => users.value.length)
  const adminCount = computed(() => 
    users.value.filter(u => u.is_admin).length
  )

  // 操作
  const loadUsers = async (skip = 0, limit = 20) => {
    loading.value = true
    try {
      users.value = await adminAPI.getUsers(skip, limit)
      error.value = null
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const deleteUser = async (userId) => {
    await adminAPI.deleteUser(userId)
    await loadUsers()
  }

  const toggleAdminStatus = async (userId) => {
    await adminAPI.toggleAdminStatus(userId)
    await loadUsers()
  }

  const loadStats = async () => {
    try {
      stats.value = await adminAPI.getSystemStats()
    } catch (e) {
      error.value = e.message
    }
  }

  const loadAuditLogs = async (skip = 0, limit = 50) => {
    try {
      auditLogs.value = await adminAPI.getAuditLogs(skip, limit)
    } catch (e) {
      error.value = e.message
    }
  }

  return {
    // 狀態
    users,
    stats,
    auditLogs,
    systemLogs,
    schedulerJobs,
    loading,
    error,
    
    // 計算屬性
    userCount,
    adminCount,
    
    // 操作
    loadUsers,
    deleteUser,
    toggleAdminStatus,
    loadStats,
    loadAuditLogs
  }
})
```

---

## API 整合

### admin-api.js - API 客戶端

```javascript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
})

class AdminAPIClient {
  // JWT 認證
  setAuthToken(token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  // 用戶管理
  async getUsers(skip = 0, limit = 20) {
    const response = await apiClient.get('/api/admin/users', {
      params: { skip, limit }
    })
    return response.data
  }

  async deleteUser(userId) {
    await apiClient.delete(`/api/admin/users/${userId}`)
  }

  async updateUser(userId, data) {
    const response = await apiClient.put(
      `/api/admin/users/${userId}`,
      data
    )
    return response.data
  }

  async toggleAdminStatus(userId) {
    const response = await apiClient.put(
      `/api/admin/users/${userId}/admin`
    )
    return response.data
  }

  // 統計
  async getSystemStats() {
    const response = await apiClient.get('/api/admin/stats/overview')
    return response.data
  }

  async getUserStats() {
    const response = await apiClient.get('/api/admin/stats/users')
    return response.data
  }

  async getAlertStats() {
    const response = await apiClient.get('/api/admin/stats/alerts')
    return response.data
  }

  // 日誌
  async getAuditLogs(skip = 0, limit = 50, action = null) {
    const params = { skip, limit }
    if (action) params.action = action
    
    const response = await apiClient.get('/api/admin/logs/audit', { params })
    return response.data
  }

  async getSystemLogs(skip = 0, limit = 100, level = null, environment = null) {
    const params = { skip, limit }
    if (level) params.level = level
    if (environment) params.environment = environment
    
    const response = await apiClient.get('/api/admin/logs/system', { params })
    return response.data
  }

  async getBackendLogs(lines = 100) {
    const response = await apiClient.get('/api/admin/logs/backend', {
      params: { lines }
    })
    return response.data
  }

  // 更多 25+ 端點...
}

export const adminAPI = new AdminAPIClient()
```

---

## 樣式系統

### TailwindCSS 配置

```javascript
// tailwind.config.js
export default {
  theme: {
    colors: {
      primary: 'var(--primary-color)',
      bg: {
        primary: 'var(--bg-primary)',
        secondary: 'var(--bg-secondary)'
      }
    }
  }
}
```

### CSS 變數（深色主題）

```css
:root {
  --primary-color: #3b82f6;    /* 藍色 */
  --bg-primary: #1e1e2e;        /* 深灰 */
  --bg-secondary: #2a2a3e;      /* 更深灰 */
  --text-primary: #ffffff;      /* 白色 */
  --text-secondary: #a0aec0;    /* 淺灰 */
  --border-color: #414156;      /* 邊框灰 */
}

/* LogViewer 專用 */
.log-container {
  background: #000000;          /* 純黑 */
  color: #ffffff;               /* 純白 */
}
```

---

## 測試指南

### 執行前端組件測試

```bash
cd frontend
npm run test:unit
```

### 測試 LogViewer 組件

```javascript
// LogViewer.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LogViewer from '@/components/LogViewer.vue'

describe('LogViewer', () => {
  it('converts ANSI codes to HTML', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: '\x1b[31mERROR\x1b[0m: Something failed'
      }
    })
    
    expect(wrapper.html()).toContain('color: #ff4444')
  })

  it('filters logs by search query', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: 'INFO: Connection established\nERROR: Connection failed',
        searchQuery: 'ERROR'
      }
    })
    
    expect(wrapper.html()).toContain('mark')
  })
})
```

---

## 相關資源

- [後端文檔](./admin-panel.md)
- [部署指南](./deploy.md)
- [Vue 3 文檔](https://vuejs.org/)
- [Pinia 文檔](https://pinia.vuejs.org/)
