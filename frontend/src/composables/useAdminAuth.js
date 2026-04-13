import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import * as adminApi from '../api/admin-api'

/**
 * 管理員認證 Composable
 * 提供管理員權限檢查和認證相關邏輯
 */
export const useAdminAuth = () => {
  const auth = useAuthStore()
  
  const isAdmin = computed(() => auth.isAdmin)
  
  const hasAdminPermission = computed(() => {
    return auth.isAdmin && auth.token
  })
  
  const checkAdminAccess = () => {
    if (!isAdmin.value) {
      throw new Error('無管理員權限')
    }
    return true
  }
  
  const initializeAdminAPI = () => {
    if (auth.token) {
      adminApi.setAuthToken(auth.token)
    }
  }
  
  const clearAdminAPI = () => {
    adminApi.setAuthToken(null)
  }
  
  return {
    isAdmin,
    hasAdminPermission,
    checkAdminAccess,
    initializeAdminAPI,
    clearAdminAPI,
  }
}

export default {
  useAdminAuth,
}
