import { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  FolderOpen, 
  Search, 
  Shield, 
  Brain, 
  Settings,
  Zap,
  Plus,
  Menu,
  X
} from 'lucide-react'
import { toggleSidebar } from '../store/slices/appSlice'

const Sidebar = () => {
  const dispatch = useDispatch()
  const { sidebarOpen } = useSelector(state => state.app)
  const location = useLocation()

  const navigationItems = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      description: 'System Overview'
    },
    {
      name: 'My Files',
      path: '/files',
      icon: FolderOpen,
      description: 'File Management'
    },
    {
      name: 'Deep Scan & Clean',
      path: '/scan',
      icon: Search,
      description: 'Advanced Scanning'
    },
    {
      name: 'Quarantine & Threats',
      path: '/quarantine',
      icon: Shield,
      description: 'Security Center'
    },
    {
      name: 'ML Model Center',
      path: '/ml-model',
      icon: Brain,
      description: 'AI Configuration'
    },
    {
      name: 'Settings & Logs',
      path: '/settings',
      icon: Settings,
      description: 'System Settings'
    }
  ]

  const isActivePath = (path) => {
    if (path === '/dashboard' && (location.pathname === '/' || location.pathname === '/dashboard')) {
      return true
    }
    return location.pathname === path
  }

  const handleQuickScan = () => {
  // Prefill quick scan with Downloads folder and trigger scan
  const downloads = encodeURIComponent('C:/Users/' + (window?.process?.env?.USERNAME || 'Public') + '/Downloads');
  window.location.href = `/scan?quick=1&folder=${downloads}`;
  }

  const handleCreateRule = () => {
    // Example: navigate to settings or show a modal (for now, go to settings)
    window.location.href = '/settings';
  }

  return (
    <div>
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => dispatch(toggleSidebar())}
        />
      )}

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          x: sidebarOpen ? 0 : -300,
          opacity: sidebarOpen ? 1 : 0.9
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={`
          fixed lg:relative top-0 left-0 z-50 lg:z-auto
          w-80 h-full bg-panel-dark/90 backdrop-blur-lg
          border-r border-border flex flex-col
          ${sidebarOpen ? 'shadow-2xl lg:shadow-none' : ''}
        `}
      >
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-neon-green to-neon-blue rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gradient">NeonVault</h1>
                <p className="text-xs text-text-muted">File Organizer</p>
              </div>
            </div>
            {/* Mobile Close Button */}
            <button
              onClick={() => dispatch(toggleSidebar())}
              className="lg:hidden p-2 hover:bg-border rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navigationItems.map((item) => {
            const isActive = isActivePath(item.path)
            const Icon = item.icon

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => {
                  // Close mobile sidebar when navigating
                  if (window.innerWidth < 1024) {
                    dispatch(toggleSidebar())
                  }
                }}
                className="block"
              >
                <motion.div
                  whileHover={{ scale: 1.02, x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  className={`
                    relative p-4 rounded-xl transition-all duration-300 group
                    ${isActive 
                      ? 'bg-neon-green/10 border border-neon-green/30' 
                      : 'hover:bg-border/50 border border-transparent hover:border-border'
                    }
                  `}
                >
                  {/* Active Indicator */}
                  {isActive && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-neon-green rounded-r-full" />
                  )}
                  <div className="flex items-center space-x-4">
                    <div className={`
                      p-2 rounded-lg transition-colors
                      ${isActive 
                        ? 'bg-neon-green text-bg-dark' 
                        : 'bg-border/50 text-text-muted group-hover:text-neon-green group-hover:bg-neon-green/20'
                      }
                    `}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h3 className={`
                        font-semibold transition-colors
                        ${isActive ? 'text-neon-green' : 'text-text-light group-hover:text-neon-green'}
                      `}>
                        {item.name}
                      </h3>
                      <p className="text-sm text-text-muted">
                        {item.description}
                      </p>
                    </div>
                  </div>
                  {/* Hover Effect */}
                  <div className={`
                    absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity
                    bg-gradient-to-r from-neon-green/5 to-neon-blue/5
                    ${isActive ? 'opacity-100' : ''}
                  `} />
                </motion.div>
              </Link>
            )
          })}
        </nav>

        {/* Quick Actions */}
        <div className="p-4 border-t border-border space-y-3">
          <h4 className="text-sm font-semibold text-text-muted uppercase tracking-wide">
            Quick Actions
          </h4>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full p-3 bg-neon-green/10 hover:bg-neon-green/20 border border-neon-green/30 rounded-lg transition-all duration-300 group"
            onClick={handleQuickScan}
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-neon-green/20 rounded-lg">
                <Zap className="w-4 h-4 text-neon-green" />
              </div>
              <span className="font-medium text-neon-green">Quick Scan</span>
            </div>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full p-3 bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/30 rounded-lg transition-all duration-300 group"
            onClick={handleCreateRule}
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-neon-blue/20 rounded-lg">
                <Plus className="w-4 h-4 text-neon-blue" />
              </div>
              <span className="font-medium text-neon-blue">Create Rule</span>
            </div>
          </motion.button>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <div className="text-xs text-text-muted text-center">
            <p>Intelligent File Organizer</p>
            <p className="mt-1">v1.0.0 • AI Powered</p>
          </div>
        </div>
      </motion.aside>
    </div>
  )
}

export default Sidebar