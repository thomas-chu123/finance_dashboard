import { ref, computed } from 'vue'
import { useAdminStore } from '../stores/admin'
import * as adminApi from '../api/admin-api'

/**
 * 用戶管理 Composable
 * 提供用戶相關的邏輯和狀態管理
 */
export const useAdminUsers = () => {
  const admin = useAdminStore()
  
  const searchQuery = ref('')
  const filteredUsers = computed(() => {
    if (!searchQuery.value) return admin.users
    const q = searchQuery.value.toLowerCase()
    return admin.users.filter(u => 
      u.display_name?.toLowerCase().includes(q) || 
      u.email?.toLowerCase().includes(q)
    )
  })
  
  const editingUser = ref(null)
  const showEditModal = ref(false)
  const showDeleteModal = ref(false)
  const showPasswordModal = ref(false)
  
  const openEditModal = (user) => {
    editingUser.value = { ...user }
    showEditModal.value = true
  }
  
  const closeEditModal = () => {
    showEditModal.value = false
    editingUser.value = null
  }
  
  const openDeleteModal = (user) => {
    editingUser.value = { ...user }
    showDeleteModal.value = true
  }
  
  const closeDeleteModal = () => {
    showDeleteModal.value = false
    editingUser.value = null
  }
  
  const openPasswordModal = (user) => {
    editingUser.value = { ...user }
    showPasswordModal.value = true
  }
  
  const closePasswordModal = () => {
    showPasswordModal.value = false
    editingUser.value = null
  }
  
  const refreshUsers = async () => {
    await admin.loadUsers(0, 50)
  }
  
  const deleteUser = async () => {
    if (!editingUser.value) return
    const success = await admin.deleteUserAPI(editingUser.value.id)
    if (success) {
      closeDeleteModal()
    }
    return success
  }
  
  const resetPassword = async (newPassword) => {
    if (!editingUser.value) return
    const success = await admin.resetPasswordAPI(editingUser.value.id, newPassword)
    if (success) {
      closePasswordModal()
    }
    return success
  }
  
  const updateUser = (updates) => {
    if (!editingUser.value) return
    admin.updateUserLocal(editingUser.value.id, updates)
    closeEditModal()
  }
  
  return {
    users: computed(() => admin.users),
    filteredUsers,
    searchQuery,
    editingUser,
    showEditModal,
    showDeleteModal,
    showPasswordModal,
    loading: computed(() => admin.loading),
    error: computed(() => admin.error),
    
    refreshUsers,
    openEditModal,
    closeEditModal,
    openDeleteModal,
    closeDeleteModal,
    openPasswordModal,
    closePasswordModal,
    deleteUser,
    resetPassword,
    updateUser,
  }
}

/**
 * Scheduler 管理 Composable
 */
export const useAdminScheduler = () => {
  const admin = useAdminStore()
  
  const selectedJob = ref(null)
  const showJobDetail = ref(false)
  const showJobHistory = ref(false)
  const jobHistory = ref([])
  
  const openJobDetail = (job) => {
    selectedJob.value = { ...job }
    showJobDetail.value = true
  }
  
  const closeJobDetail = () => {
    showJobDetail.value = false
    selectedJob.value = null
  }
  
  const openJobHistory = async (jobId) => {
    try {
      jobHistory.value = await adminApi.fetchSchedulerJobHistory(jobId)
      showJobHistory.value = true
    } catch (err) {
      console.error('加載任務歷史失敗:', err)
    }
  }
  
  const closeJobHistory = () => {
    showJobHistory.value = false
    jobHistory.value = []
  }
  
  const refreshJobs = async () => {
    await admin.loadSchedulerJobs()
  }
  
  const pauseJob = async (jobId) => {
    return await admin.pauseJobAPI(jobId)
  }
  
  const resumeJob = async (jobId) => {
    return await admin.resumeJobAPI(jobId)
  }
  
  const executeJob = async (jobId) => {
    return await admin.executeJobAPI(jobId)
  }
  
  return {
    jobs: computed(() => admin.schedulerJobs),
    selectedJob,
    jobHistory,
    showJobDetail,
    showJobHistory,
    loading: computed(() => admin.loading),
    error: computed(() => admin.error),
    
    openJobDetail,
    closeJobDetail,
    openJobHistory,
    closeJobHistory,
    refreshJobs,
    pauseJob,
    resumeJob,
    executeJob,
  }
}

/**
 * 日誌管理 Composable
 */
export const useAdminLogs = () => {
  const admin = useAdminStore()
  
  const auditFilter = ref('')
  const systemLevelFilter = ref('')
  
  const filteredAuditLogs = computed(() => {
    if (!auditFilter.value) return admin.auditLogs
    const q = auditFilter.value.toLowerCase()
    return admin.auditLogs.filter(log => 
      log.action?.toLowerCase().includes(q) ||
      log.user_id?.toLowerCase().includes(q)
    )
  })
  
  const filteredSystemLogs = computed(() => {
    if (!systemLevelFilter.value) return admin.systemLogs
    return admin.systemLogs.filter(log => log.level === systemLevelFilter.value)
  })
  
  const refreshAuditLogs = async () => {
    await admin.loadAuditLogs(0, 50)
  }
  
  const refreshSystemLogs = async () => {
    if (systemLevelFilter.value) {
      await admin.loadSystemLogs(systemLevelFilter.value)
    } else {
      await admin.loadSystemLogs()
    }
  }
  
  const refreshBackendLogs = async () => {
    await admin.loadBackendLogs(100)
  }
  
  return {
    auditLogs: computed(() => admin.auditLogs),
    systemLogs: computed(() => admin.systemLogs),
    backendLogs: computed(() => admin.backendLogs),
    filteredAuditLogs,
    filteredSystemLogs,
    auditFilter,
    systemLevelFilter,
    loading: computed(() => admin.loading),
    error: computed(() => admin.error),
    
    refreshAuditLogs,
    refreshSystemLogs,
    refreshBackendLogs,
  }
}

/**
 * 統計 Composable
 */
export const useAdminStats = () => {
  const admin = useAdminStore()
  
  const refreshStats = async () => {
    await admin.loadStats()
  }
  
  return {
    statsOverview: computed(() => admin.statsOverview),
    userStats: computed(() => admin.userStats),
    alertStats: computed(() => admin.alertStats),
    loading: computed(() => admin.loading),
    error: computed(() => admin.error),
    
    refreshStats,
  }
}

export default {
  useAdminUsers,
  useAdminScheduler,
  useAdminLogs,
  useAdminStats,
}
