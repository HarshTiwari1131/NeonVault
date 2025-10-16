import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { motion } from 'framer-motion'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import Dashboard from './pages/Dashboard'
import MyFiles from './pages/MyFiles'
import DeepScan from './pages/DeepScan'
import Quarantine from './pages/Quarantine'
import MLModelCenter from './pages/MLModelCenter'
import Settings from './pages/Settings'
import { apiService } from './utils/api'
import { setSystemStatus, setMlModelStatus } from './store/slices/appSlice'

function App() {
  const dispatch = useDispatch()

  useEffect(() => {
    // Check system status on app load
    const checkSystemStatus = async () => {
      try {
        const healthResponse = await apiService.healthCheck()
        const statusResponse = await apiService.getStatus()
        
        dispatch(setSystemStatus({
          backend: healthResponse.status === 200,
          database: true, // Assume database is working if backend is up
        }))
        
        if (statusResponse.data.ml_model_status) {
          dispatch(setMlModelStatus(statusResponse.data.ml_model_status))
        }
      } catch (error) {
        console.error('Failed to check system status:', error)
        dispatch(setSystemStatus({
          backend: false,
          database: false,
        }))
      }
    }

    checkSystemStatus()

    // Set up periodic status checking
    const statusInterval = setInterval(checkSystemStatus, 30000) // Every 30 seconds

    return () => clearInterval(statusInterval)
  }, [dispatch])

  return (
    <div className="h-screen bg-bg-dark text-text-light overflow-hidden">
      <div className="flex h-full">
        {/* Sidebar */}
        <Sidebar />
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {/* Top Bar */}
          <TopBar />
          {/* Main Content */}
          <main className="flex-1 overflow-auto p-6 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/files" element={<MyFiles />} />
                <Route path="/scan" element={<DeepScan />} />
                <Route path="/quarantine" element={<Quarantine />} />
                <Route path="/ml-model" element={<MLModelCenter />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </motion.div>
          </main>
        </div>
      </div>
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-neon-green opacity-10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-neon-blue opacity-10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>
    </div>
  )
}

export default App