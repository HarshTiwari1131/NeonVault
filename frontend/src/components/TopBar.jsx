import { useState, useRef, useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  Bell, 
  User, 
  Settings,
  Menu,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  Folder,
  Brain,
  Shield
} from 'lucide-react'
import { toggleSidebar, clearNotifications, addNotification } from '../store/slices/appSlice'
import { apiService } from '../utils/api'

const TopBar = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { notifications, systemStatus, currentOperation, progress, isBusy } = useSelector(state => state.app)
  const [searchQuery, setSearchQuery] = useState('')
  const [showNotifications, setShowNotifications] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [showSearchResults, setShowSearchResults] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const searchRef = useRef(null)

  const getSystemStatusColor = () => {
    if (systemStatus.backend && systemStatus.database) {
      return 'text-success'
    } else if (systemStatus.backend) {
      return 'text-warning'
    } else {
      return 'text-error'
    }
  }

  const getSystemStatusIcon = () => {
    if (systemStatus.backend && systemStatus.database) {
      return <CheckCircle className="w-4 h-4" />
    } else if (systemStatus.backend) {
      return <AlertTriangle className="w-4 h-4" />
    } else {
      return <XCircle className="w-4 h-4" />
    }
  }

  // Close search results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSearchResults(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Perform search when query changes
  useEffect(() => {
    const searchFiles = async () => {
      if (searchQuery.trim().length >= 2) {
        setIsSearching(true)
        try {
          // Simulate AI-powered search results
          const mockResults = [
            {
              id: 1,
              type: 'file',
              title: `Files containing "${searchQuery}"`,
              description: 'Search through your organized files',
              icon: FileText,
              action: () => navigate('/files', { state: { searchQuery } })
            },
            {
              id: 2,
              type: 'scan',
              title: 'Deep Scan & Clean',
              description: 'Scan and organize files matching your query',
              icon: Zap,
              action: () => navigate('/scan', { state: { searchQuery } })
            },
            {
              id: 3,
              type: 'ml',
              title: 'ML Model Analysis',
              description: 'Analyze files using machine learning',
              icon: Brain,
              action: () => navigate('/ml-model')
            },
            {
              id: 4,
              type: 'security',
              title: 'Security Scan',
              description: 'Check for threats and malware',
              icon: Shield,
              action: () => navigate('/quarantine')
            }
          ]
          
          // Filter results based on query
          const filteredResults = mockResults.filter(result => 
            result.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            result.description.toLowerCase().includes(searchQuery.toLowerCase())
          )
          
          setSearchResults(filteredResults)
          setShowSearchResults(true)
        } catch (error) {
          console.error('Search error:', error)
          dispatch(addNotification({
            type: 'error',
            message: 'Search failed. Please try again.'
          }))
        } finally {
          setIsSearching(false)
        }
      } else {
        setSearchResults([])
        setShowSearchResults(false)
      }
    }

    const debounceTimer = setTimeout(searchFiles, 300)
    return () => clearTimeout(debounceTimer)
  }, [searchQuery, navigate, dispatch])

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim() && searchResults.length > 0) {
      // Execute the first search result action
      searchResults[0].action()
      setSearchQuery('')
      setShowSearchResults(false)
    }
  }

  const handleSearchResultClick = (result) => {
    result.action()
    setSearchQuery('')
    setShowSearchResults(false)
  }

  const handleSettingsClick = () => {
    navigate('/settings')
  }

  return (
    <header className="bg-panel-dark/80 backdrop-blur-sm border-b border-border p-4 z-[60]">
      <div className="flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          {/* Mobile Menu Button */}
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="lg:hidden p-2 hover:bg-border rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* AI Search Bar */}
          <div ref={searchRef} className="relative">
            <form onSubmit={handleSearch} className="relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="AI-powered search..."
                  className="
                    pl-10 pr-4 py-2 w-80 bg-border/50 border border-border 
                    rounded-lg focus:outline-none focus:border-neon-green 
                    focus:ring-2 focus:ring-neon-green/20 transition-all
                    text-text-light placeholder-text-muted
                  "
                />
                {(searchQuery || isSearching) && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2"
                  >
                    {isSearching ? (
                      <Zap className="w-4 h-4 text-neon-green animate-spin" />
                    ) : (
                      <Zap className="w-4 h-4 text-neon-green animate-pulse" />
                    )}
                  </motion.div>
                )}
              </div>
            </form>

            {/* Search Results Dropdown */}
            <AnimatePresence>
              {showSearchResults && searchResults.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  className="absolute top-full mt-2 w-full bg-panel-dark border border-border rounded-lg shadow-lg overflow-hidden z-50"
                >
                  <div className="p-2 border-b border-border">
                    <div className="flex items-center space-x-2">
                      <Zap className="w-4 h-4 text-neon-green" />
                      <span className="text-sm text-text-muted">AI Search Results</span>
                    </div>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {searchResults.map((result) => (
                      <button
                        key={result.id}
                        onClick={() => handleSearchResultClick(result)}
                        className="w-full p-3 hover:bg-border/20 transition-colors text-left flex items-center space-x-3"
                      >
                        <result.icon className="w-5 h-5 text-neon-green flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-text-light">
                            {result.title}
                          </div>
                          <div className="text-xs text-text-muted">
                            {result.description}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="p-2 border-t border-border text-center">
                    <span className="text-xs text-text-muted">
                      Press Enter to select first result
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Current Operation Status */}
          {isBusy && currentOperation && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-2 px-3 py-2 bg-neon-green/10 border border-neon-green/20 rounded-lg"
            >
              <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse" />
              <span className="text-sm text-neon-green capitalize">
                {currentOperation} ({progress}%)
              </span>
            </motion.div>
          )}
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-4">
          {/* System Status */}
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-1 ${getSystemStatusColor()}`}>
              {getSystemStatusIcon()}
              <span className="text-sm font-medium">System</span>
            </div>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 hover:bg-border rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-neon-green text-bg-dark text-xs rounded-full flex items-center justify-center font-bold">
                  {notifications.length > 9 ? '9+' : notifications.length}
                </span>
              )}
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                className="absolute right-0 top-full mt-2 w-80 bg-panel-dark border border-border rounded-lg shadow-lg overflow-hidden z-50"
              >
                <div className="p-3 border-b border-border flex items-center justify-between">
                  <h3 className="font-semibold">Notifications</h3>
                  {notifications.length > 0 && (
                    <button
                      onClick={() => dispatch(clearNotifications())}
                      className="text-sm text-neon-green hover:text-neon-green/80 transition-colors"
                    >
                      Clear All
                    </button>
                  )}
                </div>

                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-text-muted">
                      No notifications
                    </div>
                  ) : (
                    notifications.slice(0, 5).map((notification) => (
                      <div
                        key={notification.id}
                        className="p-3 border-b border-border/50 hover:bg-border/20 transition-colors"
                      >
                        <div className="flex items-start space-x-3">
                          <div className={`
                            w-2 h-2 rounded-full mt-2 flex-shrink-0
                            ${notification.type === 'success' ? 'bg-success' : 
                              notification.type === 'warning' ? 'bg-warning' : 
                              notification.type === 'error' ? 'bg-error' : 'bg-neon-blue'}
                          `} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-text-light">
                              {notification.message}
                            </p>
                            <p className="text-xs text-text-muted mt-1">
                              {new Date(notification.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </div>

          {/* User Avatar */}
          <div className="relative">
            <button className="flex items-center space-x-2 p-2 hover:bg-border rounded-lg transition-colors">
              <div className="w-8 h-8 bg-gradient-to-br from-neon-green to-neon-blue rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="hidden md:block text-sm font-medium">Admin</span>
            </button>
          </div>

          {/* Settings */}
          <button className="p-2 hover:bg-border rounded-lg transition-colors" onClick={handleSettingsClick}>
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {isBusy && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3"
        >
          <div className="w-full bg-border rounded-full h-1">
            <motion.div
              className="bg-gradient-to-r from-neon-green to-neon-blue h-1 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </motion.div>
      )}
    </header>
  )
}

export default TopBar