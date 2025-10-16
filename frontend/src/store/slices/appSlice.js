import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  isLoading: false,
  currentOperation: null,
  progress: 0,
  message: '',
  isBusy: false,
  notifications: [],
  theme: 'neonvault',
  sidebarOpen: true,
  systemStatus: {
    backend: false,
    database: false,
    mlModel: false,
    clamav: false,
  },
  mlModelStatus: {
    trained: false,
    accuracy: 0,
    trainingsamples: 0,
    featuresCount: 0,
    modelVersion: 'unknown'
  }
}

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload
    },
    setCurrentOperation: (state, action) => {
      state.currentOperation = action.payload.operation
      state.progress = action.payload.progress || 0
      state.message = action.payload.message || ''
      state.isBusy = action.payload.isBusy !== undefined ? action.payload.isBusy : state.isBusy
    },
    updateProgress: (state, action) => {
      state.progress = action.payload.progress
      state.message = action.payload.message || state.message
    },
    completeOperation: (state) => {
      state.progress = 100
      state.isBusy = false
      state.currentOperation = null
    },
    addNotification: (state, action) => {
      const notification = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        ...action.payload
      }
      state.notifications.unshift(notification)
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50)
      }
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(
        notification => notification.id !== action.payload
      )
    },
    clearNotifications: (state) => {
      state.notifications = []
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload
    },
    setSystemStatus: (state, action) => {
      state.systemStatus = { ...state.systemStatus, ...action.payload }
    },
    setMlModelStatus: (state, action) => {
      state.mlModelStatus = { ...state.mlModelStatus, ...action.payload }
    },
    setTheme: (state, action) => {
      state.theme = action.payload
    }
  },
})

export const {
  setLoading,
  setCurrentOperation,
  updateProgress,
  completeOperation,
  addNotification,
  removeNotification,
  clearNotifications,
  toggleSidebar,
  setSidebarOpen,
  setSystemStatus,
  setMlModelStatus,
  setTheme
} = appSlice.actions

export default appSlice.reducer