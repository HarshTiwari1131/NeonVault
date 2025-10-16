import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for long operations
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error(`API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data)
    return Promise.reject(error)
  }
)

// API Service Methods
export const apiService = {
  // Health check
  healthCheck: () => api.get('/api/health'),

  // Status
  getStatus: () => api.get('/api/status'),

  // File scanning
  scanFolder: (data) => api.post('/api/scan', data),
  getScanProgress: () => api.get('/api/scan/progress'),
  getLastScanResults: () => api.get('/api/scan/results'),
  getScanStats: () => api.get('/api/scan/stats'),

  // File organization
  organizeFiles: (data) => api.post('/api/organize', data),
  getOrganizeCategories: () => api.get('/api/organize/categories'),
  getOrganizeHistory: (limit = 50) => api.get(`/api/organize/history?limit=${limit}`),

  // File deletion
  deleteFiles: (data) => api.post('/api/delete', data),
  previewDeletion: (params) => api.get('/api/delete/preview', { params }),
  getDeletionRules: () => api.get('/api/delete/rules'),

  // Virus scanning
  virusScan: (data) => api.post('/api/virus-scan', data),
  getQuarantinedFiles: () => api.get('/api/quarantine'),
  quarantineAction: (data) => api.post('/api/quarantine/action', data),
  getThreatSummary: () => api.get('/api/scan/threats/summary'),

  // ML operations
  trainMLModel: (data) => api.post('/api/ml/train', data),
  predictFileCategory: (data) => api.post('/api/ml/predict', data),
  getModelInfo: () => api.get('/api/ml/model/info'),
  reloadModel: () => api.post('/api/ml/model/reload'),
  getModelPerformance: () => api.get('/api/ml/model/performance'),
  detectAnomaly: (data) => api.post('/api/ml/anomaly/detect', data),

  // Logs
  getLogs: (params) => api.get('/api/logs', { params }),
  getLogLevels: () => api.get('/api/logs/levels'),
  getLogActions: () => api.get('/api/logs/actions'),
  clearLogs: (olderThanDays) => api.delete(`/api/logs/clear?older_than_days=${olderThanDays}`),
  getLogStats: () => api.get('/api/logs/stats'),

  // Settings
  getSettings: () => api.get('/api/settings'),
  updateSetting: (data) => api.post('/api/settings/update', data),
  updateApiKeys: (data) => api.post('/api/settings/api-keys', data),
  updateNotificationSettings: (data) => api.post('/api/settings/notifications', data),
  testSpeechNotification: () => api.get('/api/settings/test-speech'),
  getSystemInfo: () => api.get('/api/settings/system-info'),
  resetSettings: () => api.post('/api/settings/reset'),
}

// Utility functions
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const formatDuration = (seconds) => {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

export const getFileIcon = (extension, category) => {
  const ext = extension?.toLowerCase()
  
  // Category-based icons
  if (category) {
    const categoryIcons = {
      images: '🖼️',
      videos: '🎥',
      audio: '🎵',
      documents: '📄',
      archives: '📦',
      code: '💻',
      spreadsheets: '📊',
      presentations: '📊',
      executables: '⚙️',
      others: '📄'
    }
    return categoryIcons[category] || '📄'
  }

  // Extension-based icons
  const extensionIcons = {
    '.pdf': '📕',
    '.doc': '📘',
    '.docx': '📘',
    '.txt': '📄',
    '.jpg': '🖼️',
    '.jpeg': '🖼️',
    '.png': '🖼️',
    '.gif': '🖼️',
    '.mp4': '🎥',
    '.avi': '🎥',
    '.mkv': '🎥',
    '.mp3': '🎵',
    '.wav': '🎵',
    '.zip': '📦',
    '.rar': '📦',
    '.py': '🐍',
    '.js': '📜',
    '.html': '🌐',
    '.css': '🎨',
    '.exe': '⚙️',
  }

  return extensionIcons[ext] || '📄'
}

export const getThreatLevelColor = (level) => {
  const colors = {
    low: 'text-neon-green',
    medium: 'text-warning',
    high: 'text-error',
    critical: 'text-red-600'
  }
  return colors[level] || 'text-text-muted'
}

export const getCategoryColor = (category) => {
  const colors = {
    images: 'text-purple-400',
    videos: 'text-red-400',
    audio: 'text-pink-400',
    documents: 'text-blue-400',
    archives: 'text-yellow-400',
    code: 'text-green-400',
    spreadsheets: 'text-teal-400',
    presentations: 'text-orange-400',
    executables: 'text-red-500',
    others: 'text-gray-400'
  }
  return colors[category] || 'text-text-muted'
}

export default api