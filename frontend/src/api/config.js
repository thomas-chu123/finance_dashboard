/**
 * API 配置 - 所有 API 調用的中心配置
 */

// 從環境變數讀取後端基礎 URL
// 開發環境：http://127.0.0.1:8005
// 生產環境：https://webhook.skynetapp.org
const getBackendBaseUrl = () => {
  // 優先級：
  // 1. 環境變數（前端構建時設定）
  // 2. localStorage（運行時可變）
  // 3. window.location.origin（同源）
  
  if (import.meta.env.MODE === 'development') {
    return 'http://127.0.0.1:8005'
  }
  
  // 生產環境使用 window.location.origin（CORS 更安全）
  return window.location.origin
}

export const API_BASE_URL = getBackendBaseUrl()

console.log(`[API Config] API Base URL: ${API_BASE_URL}`)
