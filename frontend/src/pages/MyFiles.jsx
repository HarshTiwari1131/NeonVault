import { useState, useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FolderOpen, 
  Upload, 
  Grid3X3, 
  List,
  Filter,
  Search,
  Download,
  Trash2,
  Eye,
  MoreHorizontal
} from 'lucide-react'
import FileCard from '../components/FileCard'
import { useDropzone } from 'react-dropzone'
import { setScannedFiles, setViewMode, setFilters } from '../store/slices/fileSlice'
import { addNotification } from '../store/slices/appSlice'
import { apiService } from '../utils/api'

const MyFiles = () => {
  const dispatch = useDispatch()
  const { scannedFiles, viewMode, filters, selectedFiles } = useSelector(state => state.files)
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)
  const [isDownloading, setIsDownloading] = useState(false)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      // Handle file upload
      console.log('Files dropped:', acceptedFiles)
      dispatch(addNotification({
        type: 'info',
        message: `${acceptedFiles.length} files ready for processing`
      }))
    },
    noClick: true
  })

  const filteredFiles = scannedFiles.filter(file => {
    // Search
    if (searchQuery && !file.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    // Category
    if (filters.category !== 'all' && file.category !== filters.category) {
      return false
    }
    // Size
    if (filters.size !== 'all') {
      if (filters.size === 'small' && file.size >= 1024 * 1024) return false;
      if (filters.size === 'medium' && (file.size < 1024 * 1024 || file.size > 10 * 1024 * 1024)) return false;
      if (filters.size === 'large' && file.size <= 10 * 1024 * 1024) return false;
    }
    // Date
    if (filters.date !== 'all' && file.modified_time) {
      const fileDate = new Date(file.modified_time);
      const now = new Date();
      if (filters.date === 'today') {
        if (fileDate.toDateString() !== now.toDateString()) return false;
      } else if (filters.date === 'week') {
        const weekAgo = new Date(now);
        weekAgo.setDate(now.getDate() - 7);
        if (fileDate < weekAgo) return false;
      } else if (filters.date === 'month') {
        if (fileDate.getMonth() !== now.getMonth() || fileDate.getFullYear() !== now.getFullYear()) return false;
      } else if (filters.date === 'year') {
        if (fileDate.getFullYear() !== now.getFullYear()) return false;
      }
    }
    // Threat
    if (filters.threat !== 'all') {
      if (filters.threat === 'clean' && file.threat_level && file.threat_level !== 'none') return false;
      if (filters.threat === 'suspicious' && file.threat_level !== 'medium') return false;
      if (filters.threat === 'threats' && file.threat_level !== 'high') return false;
    }
    return true;
  });

  // Backend-connected file actions
  const handleFileAction = async (file, action) => {
    try {
      if (action === 'Preview') {
        setPreviewFile(file)
        dispatch(addNotification({ type: 'info', message: `Previewing ${file.name}` }))
      } else if (action === 'Download') {
        setIsDownloading(true)
        // Download endpoint (assume /api/files/download?path=...)
        const url = `/api/files/download?path=${encodeURIComponent(file.path)}`
        const response = await fetch(url)
        if (!response.ok) throw new Error('Download failed')
        const blob = await response.blob()
        const link = document.createElement('a')
        link.href = window.URL.createObjectURL(blob)
        link.download = file.name
        document.body.appendChild(link)
        link.click()
        link.remove()
        dispatch(addNotification({ type: 'success', message: `Downloaded ${file.name}` }))
      } else if (action === 'Share') {
        // Copy file path to clipboard as a simple share
        await navigator.clipboard.writeText(file.path)
        dispatch(addNotification({ type: 'success', message: `File path copied to clipboard` }))
      } else if (action === 'Delete') {
        // Call backend delete API for this file
        await apiService.deleteFiles({ folder_path: file.path, rules: {}, dry_run: false, permanent: true })
        dispatch(addNotification({ type: 'success', message: `Deleted ${file.name}` }))
      }
    } catch (err) {
      dispatch(addNotification({ type: 'error', message: `${action} failed: ${err.message}` }))
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient mb-2">My Files</h1>
          <p className="text-text-muted">Manage and organize your files</p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* View Toggle */}
          <div className="flex items-center bg-border/20 rounded-lg p-1">
            <button
              onClick={() => dispatch(setViewMode('grid'))}
              className={`p-2 rounded transition-colors ${
                viewMode === 'grid' ? 'bg-neon-green/20 text-neon-green' : 'text-text-muted hover:text-text-light'
              }`}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => dispatch(setViewMode('list'))}
              className={`p-2 rounded transition-colors ${
                viewMode === 'list' ? 'bg-neon-green/20 text-neon-green' : 'text-text-muted hover:text-text-light'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Filter Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2 hover:bg-border rounded-lg transition-colors"
          >
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files..."
            className="w-full pl-10 pr-4 py-3 bg-border/20 border border-border rounded-lg focus:outline-none focus:border-neon-green focus:ring-2 focus:ring-neon-green/20 transition-all"
          />
        </div>

        {/* Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="glassmorphism rounded-xl p-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-light mb-2">Category</label>
                  <select
                    value={filters.category}
                    onChange={(e) => dispatch(setFilters({ category: e.target.value }))}
                    className="w-full bg-border/20 border border-border rounded-lg px-3 py-2 text-text-light focus:outline-none focus:border-neon-green"
                  >
                    <option value="all">All Categories</option>
                    <option value="images">Images</option>
                    <option value="videos">Videos</option>
                    <option value="documents">Documents</option>
                    <option value="audio">Audio</option>
                    <option value="archives">Archives</option>
                    <option value="code">Code</option>
                    <option value="others">Others</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-light mb-2">Size</label>
                  <select
                    value={filters.size}
                    onChange={(e) => dispatch(setFilters({ size: e.target.value }))}
                    className="w-full bg-border/20 border border-border rounded-lg px-3 py-2 text-text-light focus:outline-none focus:border-neon-green"
                  >
                    <option value="all">All Sizes</option>
                    <option value="small">Small (&lt; 1MB)</option>
                    <option value="medium">Medium (1-10MB)</option>
                    <option value="large">Large (&gt; 10MB)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-light mb-2">Date</label>
                  <select
                    value={filters.date}
                    onChange={(e) => dispatch(setFilters({ date: e.target.value }))}
                    className="w-full bg-border/20 border border-border rounded-lg px-3 py-2 text-text-light focus:outline-none focus:border-neon-green"
                  >
                    <option value="all">All Dates</option>
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="year">This Year</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-light mb-2">Threat Level</label>
                  <select
                    value={filters.threat}
                    onChange={(e) => dispatch(setFilters({ threat: e.target.value }))}
                    className="w-full bg-border/20 border border-border rounded-lg px-3 py-2 text-text-light focus:outline-none focus:border-neon-green"
                  >
                    <option value="all">All Files</option>
                    <option value="clean">Clean Files</option>
                    <option value="suspicious">Suspicious</option>
                    <option value="threats">Threats Only</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Upload Zone */}
      {scannedFiles.length === 0 && (
        <motion.div
          {...getRootProps()}
          className={`
            glassmorphism rounded-xl p-12 text-center cursor-pointer transition-all duration-300
            ${isDragActive ? 'border-neon-green bg-neon-green/5' : 'border-border hover:border-neon-green/50'}
            border-2 border-dashed
          `}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <input {...getInputProps()} />
          <Upload className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-text-light mb-2">
            {isDragActive ? 'Drop files here' : 'Upload or Scan Files'}
          </h3>
          <p className="text-text-muted mb-6">
            Drag and drop files here, or click to select files for scanning and organization
          </p>
          <div className="flex items-center justify-center space-x-4">
            <button className="px-6 py-3 bg-neon-green/20 border border-neon-green/30 rounded-lg text-neon-green hover:bg-neon-green/30 transition-colors">
              Select Files
            </button>
            <button className="px-6 py-3 bg-neon-blue/20 border border-neon-blue/30 rounded-lg text-neon-blue hover:bg-neon-blue/30 transition-colors">
              Scan Folder
            </button>
          </div>
        </motion.div>
      )}

      {/* Files Grid/List */}
      {filteredFiles.length > 0 && (
        <div className="space-y-4">
          {/* Stats Bar */}
          <div className="flex items-center justify-between text-sm text-text-muted">
            <span>{filteredFiles.length} files found</span>
            {selectedFiles.length > 0 && (
              <div className="flex items-center space-x-4">
                <span>{selectedFiles.length} selected</span>
                <div className="flex items-center space-x-2">
                  <button className="p-1 hover:bg-border rounded text-neon-blue">
                    <Download className="w-4 h-4" />
                  </button>
                  <button className="p-1 hover:bg-border rounded text-error">
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <button className="p-1 hover:bg-border rounded text-text-muted">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Files Display */}
          <motion.div
            layout
            className={
              viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'
                : 'space-y-4'
            }
          >
            <AnimatePresence>
              {filteredFiles.map((file, index) => (
                <FileCard
                  key={file.path || index}
                  file={file}
                  isSelected={selectedFiles.includes(file.path)}
                  onSelect={(file) => {
                    // Toggle file selection
                    console.log('File selected:', file.name)
                  }}
                  onDownload={(file) => handleFileAction(file, 'Download')}
                  onShare={(file) => handleFileAction(file, 'Share')}
                  onDelete={(file) => handleFileAction(file, 'Delete')}
                  onPreview={(file) => handleFileAction(file, 'Preview')}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        </div>
      )}

      {/* Empty State */}
      {scannedFiles.length > 0 && filteredFiles.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-text-light mb-2">No files match your filters</h3>
          <p className="text-text-muted">Try adjusting your search or filter criteria</p>
        </div>
      )}
      {/* Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-panel p-6 rounded-xl shadow-xl max-w-lg w-full relative min-w-[320px]">
            <button className="absolute top-2 right-2 text-text-muted hover:text-error" onClick={() => setPreviewFile(null)}>&times;</button>
            <h2 className="text-xl font-bold mb-2 truncate max-w-full overflow-hidden" title={previewFile.name}>Preview: {previewFile.name || 'No name'}</h2>
            <div className="text-sm text-text-light break-all space-y-1">
              <div><b>Path:</b> {previewFile.path || 'N/A'}</div>
              <div><b>Type:</b> {previewFile.mime_type || 'N/A'}</div>
              <div><b>Size:</b> {previewFile.size !== undefined ? formatFileSize(previewFile.size) : 'N/A'}</div>
              <div><b>Modified:</b> {previewFile.modified_time || 'N/A'}</div>
              <div><b>Category:</b> {previewFile.category || 'N/A'}</div>
              <div><b>Entropy:</b> {previewFile.entropy !== undefined ? previewFile.entropy : 'N/A'}</div>
            </div>
            <div className="mt-4 flex justify-end">
              <button className="px-4 py-2 bg-border rounded-lg hover:bg-error/20" onClick={() => setPreviewFile(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MyFiles