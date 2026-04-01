import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as adminApi from '../api/admin-api'

export const useAdminStore = defineStore('admin', () => {
  // State
  const users = ref([])
  const schedulerJobs = ref([])
  const auditLogs = ref([])
  const systemLogs = ref([])
  const backendLogs = ref('')
  const statsOverview = ref({})
  const userStats = ref({})
  const alertStats = ref({})
  
  const loading = ref(false)
  const error = ref(null)
  
  // Computed
  const totalUsers = computed(() => users.value.length)
  const adminUsers = computed(() => users.value.filter(u => u.is_admin))
  const enabledJobs = computed(() => schedulerJobs.value.filter(j => j.is_enabled))
  
  // User Management
  const loadUsers = async (skip = 0, limit = 50) => {
    loading.value = true
    error.value = null
    try {
      users.value = await adminApi.fetchUsers(skip, limit)
    } catch (err) {
      error.value = err.message
      console.error('加載用戶列表失敗:', err)
    } finally {
      loading.value = false
    }
  }
  
  const addUser = (user) => {
    const exists = users.value.find(u => u.id === user.id)
    if (!exists) {
      users.value.push(user)
    }
  }
  
  const updateUserLocal = (userId, updates) => {
    const user = users.value.find(u => u.id === userId)
    if (user) {
      Object.assign(user, updates)
    }
  }
  
  const removeUser = (userId) => {
    users.value = users.value.filter(u => u.id !== userId)
  }
  
  const deleteUserAPI = async (userId) => {
    error.value = null
    try {
      await adminApi.deleteUser(userId)
      removeUser(userId)
      return true
    } catch (err) {
      error.value = err.message
      console.error('刪除用戶失敗:', err)
      return false
    }
  }
  
  const resetPasswordAPI = async (userId, newPassword) => {
    error.value = null
    try {
      await adminApi.resetPassword(userId, newPassword)
      return true
    } catch (err) {
      error.value = err.message
      console.error('重設密碼失敗:', err)
      return false
    }
  }
  
  // Scheduler Management
  const loadSchedulerJobs = async () => {
    loading.value = true
    error.value = null
    try {
      schedulerJobs.value = await adminApi.fetchSchedulerJobs()
    } catch (err) {
      error.value = err.message
      console.error('加載 scheduler 任務失敗:', err)
    } finally {
      loading.value = false
    }
  }
  
  const pauseJobAPI = async (jobId) => {
    error.value = null
    try {
      await adminApi.pauseSchedulerJob(jobId)
      const job = schedulerJobs.value.find(j => j.job_id === jobId)
      if (job) job.is_enabled = false
      return true
    } catch (err) {
      error.value = err.message
      console.error('暫停任務失敗:', err)
      return false
    }
  }
  
  const resumeJobAPI = async (jobId) => {
    error.value = null
    try {
      await adminApi.resumeSchedulerJob(jobId)
      const job = schedulerJobs.value.find(j => j.job_id === jobId)
      if (job) job.is_enabled = true
      return true
    } catch (err) {
      error.value = err.message
      console.error('恢復任務失敗:', err)
      return false
    }
  }
  
  const executeJobAPI = async (jobId) => {
    error.value = null
    try {
      await adminApi.executeSchedulerJob(jobId)
      return true
    } catch (err) {
      error.value = err.message
      console.error('執行任務失敗:', err)
      return false
    }
  }
  
  // Logs
  const loadAuditLogs = async (skip = 0, limit = 50) => {
    loading.value = true
    error.value = null
    try {
      auditLogs.value = await adminApi.fetchAuditLogs(skip, limit)
    } catch (err) {
      error.value = err.message
      console.error('加載審計日誌失敗:', err)
    } finally {
      loading.value = false
    }
  }
  
  const loadSystemLogs = async (level = null) => {
    loading.value = true
    error.value = null
    try {
      systemLogs.value = await adminApi.fetchSystemLogs(level)
    } catch (err) {
      error.value = err.message
      console.error('加載系統日誌失敗:', err)
    } finally {
      loading.value = false
    }
  }
  
  const loadBackendLogs = async (lines = 100) => {
    loading.value = true
    error.value = null
    try {
      const result = await adminApi.fetchBackendLogs(lines)
      // 處理兩種可能的返回格式
      if (typeof result === 'string') {
        backendLogs.value = result
      } else if (result && typeof result === 'object') {
        backendLogs.value = result.logs || result
      } else {
        backendLogs.value = String(result)
      }
    } catch (err) {
      error.value = err.message
      console.error('加載後端日誌失敗:', err)
      backendLogs.value = ''
    } finally {
      loading.value = false
    }
  }
  
  // Stats
  const loadStats = async () => {
    loading.value = true
    error.value = null
    try {
      const [overview, userStat, alertStat] = await Promise.all([
        adminApi.fetchStatsOverview(),
        adminApi.fetchUserStats(),
        adminApi.fetchAlertStats(),
      ])
      statsOverview.value = overview
      userStats.value = userStat
      alertStats.value = alertStat
    } catch (err) {
      error.value = err.message
      console.error('加載統計失敗:', err)
    } finally {
      loading.value = false
    }
  }
  
  // Reset
  const resetStore = () => {
    users.value = []
    schedulerJobs.value = []
    auditLogs.value = []
    systemLogs.value = []
    backendLogs.value = ''
    statsOverview.value = {}
    userStats.value = {}
    alertStats.value = {}
    loading.value = false
    error.value = null
  }
  
  return {
    // State
    users,
    schedulerJobs,
    auditLogs,
    systemLogs,
    backendLogs,
    statsOverview,
    userStats,
    alertStats,
    loading,
    error,
    
    // Computed
    totalUsers,
    adminUsers,
    enabledJobs,
    
    // Methods
    loadUsers,
    addUser,
    updateUserLocal,
    removeUser,
    deleteUserAPI,
    resetPasswordAPI,
    
    loadSchedulerJobs,
    pauseJobAPI,
    resumeJobAPI,
    executeJobAPI,
    
    loadAuditLogs,
    loadSystemLogs,
    loadBackendLogs,
    
    loadStats,
    resetStore,
  }
})
