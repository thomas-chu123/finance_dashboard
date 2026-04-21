/**
 * Admin API 客戶端
 * 提供所有後端 /api/admin/* 端點的包裝
 */

import axios from 'axios'
import { API_BASE_URL } from './config'

const API_BASE = API_BASE_URL

const client = axios.create({
  baseURL: `${API_BASE}/api/admin`,
})

// 添加認證令牌攔截器
export const setAuthToken = (token) => {
  if (token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete client.defaults.headers.common['Authorization']
  }
}

// ===================================================================
// 用戶管理 API
// ===================================================================

/**
 * 獲取用戶列表
 * @param {number} skip - 跳過的記錄數
 * @param {number} limit - 返回的記錄限制
 * @returns {Promise<Array>}
 */
export const fetchUsers = async (skip = 0, limit = 50) => {
  const res = await client.get('/users', { params: { skip, limit } })
  return res.data
}

/**
 * 獲取單個用戶詳情
 * @param {string} userId - 用戶 ID
 * @returns {Promise<Object>}
 */
export const fetchUser = async (userId) => {
  const res = await client.get(`/users/${userId}`)
  return res.data
}

/**
 * 更新用戶信息
 * @param {string} userId - 用戶 ID
 * @param {Object} data - 更新數據 (display_name, is_admin)
 * @returns {Promise<Object>}
 */
export const updateUser = async (userId, data) => {
  const res = await client.put(`/users/${userId}`, data)
  return res.data
}

/**
 * 刪除用戶（級聯刪除）
 * @param {string} userId - 用戶 ID
 * @returns {Promise<Object>}
 */
export const deleteUser = async (userId) => {
  const res = await client.delete(`/users/${userId}`)
  return res.data
}

/**
 * 重設用戶密碼
 * @param {string} userId - 用戶 ID
 * @param {string} newPassword - 新密碼
 * @returns {Promise<Object>}
 */
export const resetPassword = async (userId, newPassword) => {
  const res = await client.post(`/users/${userId}/password`, { new_password: newPassword })
  return res.data
}

/**
 * 切換用戶管理員狀態
 * @param {string} userId - 用戶 ID
 * @returns {Promise<Object>}
 */
export const toggleAdminStatus = async (userId) => {
  const res = await client.put(`/users/${userId}/admin`)
  return res.data
}

/**
 * 獲取用戶活動日誌
 * @param {string} userId - 用戶 ID
 * @returns {Promise<Array>}
 */
export const fetchUserActivity = async (userId) => {
  const res = await client.get(`/users/${userId}/activity`)
  return res.data
}

// ===================================================================
// Scheduler 管理 API
// ===================================================================

/**
 * 獲取所有 scheduler 任務
 * @returns {Promise<Array>}
 */
export const fetchSchedulerJobs = async () => {
  const res = await client.get('/scheduler/jobs')
  return res.data
}

/**
 * 獲取單個 scheduler 任務詳情
 * @param {string} jobId - 任務 ID
 * @returns {Promise<Object>}
 */
export const fetchSchedulerJob = async (jobId) => {
  const res = await client.get(`/scheduler/jobs/${jobId}`)
  return res.data
}

/**
 * 暫停 scheduler 任務
 * @param {string} jobId - 任務 ID
 * @returns {Promise<Object>}
 */
export const pauseSchedulerJob = async (jobId) => {
  const res = await client.put(`/scheduler/jobs/${jobId}/pause`)
  return res.data
}

/**
 * 恢復 scheduler 任務
 * @param {string} jobId - 任務 ID
 * @returns {Promise<Object>}
 */
export const resumeSchedulerJob = async (jobId) => {
  const res = await client.put(`/scheduler/jobs/${jobId}/resume`)
  return res.data
}

/**
 * 立即執行 scheduler 任務
 * @param {string} jobId - 任務 ID
 * @returns {Promise<Object>}
 */
export const executeSchedulerJob = async (jobId) => {
  const res = await client.post(`/scheduler/jobs/${jobId}/execute`)
  return res.data
}

/**
 * 獲取 scheduler 任務執行歷史
 * @param {string} jobId - 任務 ID
 * @param {number} limit - 返回的記錄限制
 * @returns {Promise<Array>}
 */
export const fetchSchedulerJobHistory = async (jobId, limit = 50) => {
  const res = await client.get(`/scheduler/jobs/${jobId}/history`, { params: { limit } })
  return res.data
}

// ===================================================================
// 日誌管理 API
// ===================================================================

/**
 * 獲取審計日誌
 * @param {number} skip - 跳過的記錄數
 * @param {number} limit - 返回的記錄限制
 * @returns {Promise<Array>}
 */
export const fetchAuditLogs = async (skip = 0, limit = 50) => {
  const res = await client.get('/logs/audit', { params: { skip, limit } })
  return res.data
}

/**
 * 獲取系統日誌
 * @param {string} level - 日誌級別過濾 (DEBUG, INFO, WARNING, ERROR)
 * @returns {Promise<Array>}
 */
export const fetchSystemLogs = async (level = null) => {
  const params = level ? { level } : {}
  const res = await client.get('/logs/system', { params })
  return res.data
}

/**
 * 獲取後端日誌（文件尾部）
 * @param {number} lines - 返回的行數
 * @returns {Promise<string>}
 */
export const fetchBackendLogs = async (lines = 100) => {
  const res = await client.get('/logs/backend', { params: { lines } })
  return res.data
}

/**
 * 提交前端日誌
 * @param {Object} log - 日誌對象 {level, component, message}
 * @returns {Promise<Object>}
 */
export const submitFrontendLog = async (log) => {
  const res = await client.post('/logs/frontend', log)
  return res.data
}

// ===================================================================
// 統計 API
// ===================================================================

/**
 * 獲取系統概覽統計
 * @returns {Promise<Object>}
 */
export const fetchStatsOverview = async () => {
  const res = await client.get('/stats/overview')
  return res.data
}

/**
 * 獲取用戶統計
 * @returns {Promise<Object>}
 */
export const fetchUserStats = async () => {
  const res = await client.get('/stats/users')
  return res.data
}

/**
 * 獲取警報統計
 * @returns {Promise<Object>}
 */
export const fetchAlertStats = async () => {
  const res = await client.get('/stats/alerts')
  return res.data
}

export default {
  // 用戶管理
  fetchUsers,
  fetchUser,
  updateUser,
  deleteUser,
  resetPassword,
  toggleAdminStatus,
  fetchUserActivity,
  
  // Scheduler
  fetchSchedulerJobs,
  fetchSchedulerJob,
  pauseSchedulerJob,
  resumeSchedulerJob,
  executeSchedulerJob,
  fetchSchedulerJobHistory,
  
  // 日誌
  fetchAuditLogs,
  fetchSystemLogs,
  fetchBackendLogs,
  submitFrontendLog,
  
  // 統計
  fetchStatsOverview,
  fetchUserStats,
  fetchAlertStats,
  
  // 工具
  setAuthToken,
}
