import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, 
  Download, 
  Share2, 
  Trash2, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye
} from 'lucide-react'
import { formatFileSize, getFileIcon, getCategoryColor, getThreatLevelColor } from '../utils/api'

const FileCard = ({ 
  file, 
  isSelected = false, 
  onSelect, 
  onDownload, 
  onShare, 
  onDelete,
  onPreview,
  showActions = true,
  className = ''
}) => {
  const [isHovered, setIsHovered] = useState(false)

  const getStatusIcon = () => {
    if (file.threat_level && file.threat_level !== 'none') {
      return <AlertTriangle className="w-4 h-4 text-error" />
    }
    if (file.is_organized) {
      return <CheckCircle className="w-4 h-4 text-success" />
    }
    if (file.is_processing) {
      return <Clock className="w-4 h-4 text-warning animate-pulse" />
    }
    return null
  }

  const getCardBorderClass = () => {
    if (isSelected) return 'border-neon-green shadow-neon-green'
    if (file.threat_level === 'high') return 'border-error'
    if (file.threat_level === 'medium') return 'border-warning'
    if (isHovered) return 'border-neon-green/50'
    return 'border-border'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown'
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ y: -2 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={`
        relative group glassmorphism rounded-xl p-4 cursor-pointer
        border-2 transition-all duration-300 hover:shadow-lg
        ${getCardBorderClass()} ${className}
      `}
      onClick={() => onSelect && onSelect(file)}
    >
      {/* Selection Checkbox */}
      {onSelect && (
        <div className="absolute top-3 left-3 z-10">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: isSelected || isHovered ? 1 : 0 }}
            className={`
              w-5 h-5 rounded border-2 flex items-center justify-center
              ${isSelected 
                ? 'bg-neon-green border-neon-green' 
                : 'border-border bg-panel-dark/50'
              }
            `}
          >
            {isSelected && (
              <CheckCircle className="w-3 h-3 text-bg-dark" />
            )}
          </motion.div>
        </div>
      )}

      {/* File Icon and Status */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">
            {getFileIcon(file.extension, file.category)}
          </div>
          <div className="flex-1 min-w-0">
            <h3
              className="font-semibold text-text-light truncate max-w-full overflow-hidden whitespace-nowrap block"
              title={file.name}
              style={{ maxWidth: '180px', minWidth: 0 }}
            >
              {file.name}
            </h3>
            <div className="flex items-center space-x-2 mt-1">
              {file.category && (
                <span className={`text-xs px-2 py-1 rounded-full bg-panel-dark/50 ${getCategoryColor(file.category)}`}>
                  {file.category}
                </span>
              )}
              {file.confidence && (
                <span className="text-xs text-text-muted">
                  {Math.round(file.confidence * 100)}% confident
                </span>
              )}
            </div>
          </div>
        </div>
        
        {getStatusIcon()}
      </div>

      {/* File Details */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-text-muted">Size:</span>
          <span className="text-text-light">{formatFileSize(file.size)}</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-text-muted">Modified:</span>
          <span className="text-text-light">{formatDate(file.modified_time)}</span>
        </div>

        {file.mime_type && (
          <div className="flex justify-between text-sm">
            <span className="text-text-muted">Type:</span>
            <span className="text-text-light text-xs truncate max-w-[120px] overflow-hidden block" title={file.mime_type}>
              {file.mime_type}
            </span>
          </div>
        )}

        {file.entropy !== undefined && file.entropy > 7 && (
          <div className="flex justify-between text-sm">
            <span className="text-text-muted">Entropy:</span>
            <span className="text-warning text-xs">High ({file.entropy.toFixed(1)})</span>
          </div>
        )}
      </div>

      {/* Threat Warning */}
      {file.threat_level && file.threat_level !== 'none' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`
            mt-3 p-2 rounded-lg border flex items-center space-x-2
            ${file.threat_level === 'high' 
              ? 'bg-error/10 border-error/30 text-error' 
              : 'bg-warning/10 border-warning/30 text-warning'
            }
          `}
        >
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <div className="text-xs">
            <div className="font-medium">
              {file.threat_level.toUpperCase()} THREAT
            </div>
            {file.threat_name && (
              <div className="opacity-80">{file.threat_name}</div>
            )}
          </div>
        </motion.div>
      )}

      {/* Actions */}
      <AnimatePresence>
        {showActions && (isHovered || isSelected) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-4 right-4 flex items-center space-x-2"
          >
            {onPreview && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onPreview(file)
                }}
                className="p-2 bg-panel-dark/80 hover:bg-neon-blue/20 border border-border hover:border-neon-blue/50 rounded-lg transition-all duration-200"
                title="Preview"
              >
                <Eye className="w-4 h-4 text-neon-blue" />
              </button>
            )}
            
            {onShare && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onShare(file)
                }}
                className="p-2 bg-panel-dark/80 hover:bg-neon-green/20 border border-border hover:border-neon-green/50 rounded-lg transition-all duration-200"
                title="Share"
              >
                <Share2 className="w-4 h-4 text-neon-green" />
              </button>
            )}
            
            {onDownload && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDownload(file)
                }}
                className="p-2 bg-panel-dark/80 hover:bg-neon-blue/20 border border-border hover:border-neon-blue/50 rounded-lg transition-all duration-200"
                title="Download"
              >
                <Download className="w-4 h-4 text-neon-blue" />
              </button>
            )}
            
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(file)
                }}
                className="p-2 bg-panel-dark/80 hover:bg-error/20 border border-border hover:border-error/50 rounded-lg transition-all duration-200"
                title="Delete"
              >
                <Trash2 className="w-4 h-4 text-error" />
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Scan Line Effect for Processing */}
      {file.is_processing && (
        <div className="absolute inset-0 overflow-hidden rounded-xl">
          <motion.div
            className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-transparent via-neon-green to-transparent"
            animate={{
              x: ['-100%', '400px']
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'linear'
            }}
          />
        </div>
      )}
    </motion.div>
  )
}

export default FileCard