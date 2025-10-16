import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  currentFolder: '',
  scannedFiles: [],
  organizedFiles: [],
  quarantinedFiles: [],
  lastScanResults: null,
  selectedFiles: [],
  viewMode: 'grid', // 'grid' or 'list'
  sortBy: 'name', // 'name', 'size', 'date', 'type'
  sortOrder: 'asc', // 'asc' or 'desc'
  filters: {
    category: 'all',
    size: 'all',
    date: 'all',
    threat: 'all'
  },
  uploadProgress: {},
  stats: {
    totalFiles: 0,
    totalSize: 0,
    categoryCounts: {},
    threatCounts: {}
  }
}

const fileSlice = createSlice({
  name: 'files',
  initialState,
  reducers: {
    setCurrentFolder: (state, action) => {
      state.currentFolder = action.payload
    },
    setScannedFiles: (state, action) => {
      state.scannedFiles = action.payload
    },
    addScannedFiles: (state, action) => {
      state.scannedFiles.push(...action.payload)
    },
    updateScannedFile: (state, action) => {
      const { index, updates } = action.payload
      if (state.scannedFiles[index]) {
        state.scannedFiles[index] = { ...state.scannedFiles[index], ...updates }
      }
    },
    setOrganizedFiles: (state, action) => {
      state.organizedFiles = action.payload
    },
    addOrganizedFile: (state, action) => {
      state.organizedFiles.push(action.payload)
    },
    setQuarantinedFiles: (state, action) => {
      state.quarantinedFiles = action.payload
    },
    addQuarantinedFile: (state, action) => {
      state.quarantinedFiles.push(action.payload)
    },
    removeQuarantinedFile: (state, action) => {
      state.quarantinedFiles = state.quarantinedFiles.filter(
        file => file.id !== action.payload
      )
    },
    setLastScanResults: (state, action) => {
      state.lastScanResults = action.payload
      if (action.payload?.files) {
        state.scannedFiles = action.payload.files
      }
    },
    setSelectedFiles: (state, action) => {
      state.selectedFiles = action.payload
    },
    toggleFileSelection: (state, action) => {
      const fileId = action.payload
      const isSelected = state.selectedFiles.includes(fileId)
      if (isSelected) {
        state.selectedFiles = state.selectedFiles.filter(id => id !== fileId)
      } else {
        state.selectedFiles.push(fileId)
      }
    },
    clearSelectedFiles: (state) => {
      state.selectedFiles = []
    },
    setViewMode: (state, action) => {
      state.viewMode = action.payload
    },
    setSortBy: (state, action) => {
      state.sortBy = action.payload
    },
    setSortOrder: (state, action) => {
      state.sortOrder = action.payload
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {
        category: 'all',
        size: 'all', 
        date: 'all',
        threat: 'all'
      }
    },
    setUploadProgress: (state, action) => {
      const { fileId, progress } = action.payload
      state.uploadProgress[fileId] = progress
    },
    clearUploadProgress: (state, action) => {
      const fileId = action.payload
      delete state.uploadProgress[fileId]
    },
    updateStats: (state, action) => {
      state.stats = { ...state.stats, ...action.payload }
    },
    resetFileState: (state) => {
      return initialState
    }
  },
})

export const {
  setCurrentFolder,
  setScannedFiles,
  addScannedFiles,
  updateScannedFile,
  setOrganizedFiles,
  addOrganizedFile,
  setQuarantinedFiles,
  addQuarantinedFile,
  removeQuarantinedFile,
  setLastScanResults,
  setSelectedFiles,
  toggleFileSelection,
  clearSelectedFiles,
  setViewMode,
  setSortBy,
  setSortOrder,
  setFilters,
  clearFilters,
  setUploadProgress,
  clearUploadProgress,
  updateStats,
  resetFileState
} = fileSlice.actions

export default fileSlice.reducer