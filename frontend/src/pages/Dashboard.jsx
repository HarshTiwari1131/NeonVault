import { useState, useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity,
  HardDrive,
  Shield,
  Brain,
  Zap,
  TrendingUp,
  FileText,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'
import ProgressRing from '../components/ProgressRing'
import { apiService } from '../utils/api'
import { setLastScanResults, updateStats } from '../store/slices/fileSlice'
import { setMlModelStatus, addNotification } from '../store/slices/appSlice'

const Dashboard = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { lastScanResults, stats } = useSelector(state => state.files)
  const { mlModelStatus, systemStatus } = useSelector(state => state.app)
  const [systemStats, setSystemStats] = useState(null)
  const [threatSummary, setThreatSummary] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setIsLoading(true)
      
      // Load various dashboard data in parallel
      const [
        statusResponse,
        scanStatsResponse,
        threatResponse,
        systemInfoResponse
      ] = await Promise.allSettled([
        apiService.getStatus(),
        apiService.getScanStats(),
        apiService.getThreatSummary(),
        apiService.getSystemInfo()
      ])

      // Handle status response
      if (statusResponse.status === 'fulfilled') {
        const data = statusResponse.value.data
        if (data.last_scan_results) {
          dispatch(setLastScanResults(data.last_scan_results))
        }
        if (data.ml_model_status) {
          dispatch(setMlModelStatus(data.ml_model_status))
        }
      }

      // Handle scan stats
      if (scanStatsResponse.status === 'fulfilled') {
        const data = scanStatsResponse.value.data
        if (data.stats) {
          dispatch(updateStats(data.stats))
        }
      }

      // Handle threat summary
      if (threatResponse.status === 'fulfilled') {
        setThreatSummary(threatResponse.value.data.summary)
      }

      // Handle system info
      if (systemInfoResponse.status === 'fulfilled') {
        setSystemStats(systemInfoResponse.value.data)
      }

    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      dispatch(addNotification({
        type: 'error',
        message: 'Failed to load dashboard data'
      }))
    } finally {
      setIsLoading(false)
    }
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num?.toString() || '0'
  }

  const getHealthScore = () => {
    let score = 0
    if (systemStatus.backend) score += 25
    if (systemStatus.database) score += 25
    if (mlModelStatus.trained) score += 25
    if (!threatSummary?.total_quarantined || threatSummary.total_quarantined === 0) score += 25
    return score
  }

  // Quick Actions handlers
  const handleQuickScan = () => {
    navigate('/scan')
  }

  const handleOrganizeFiles = () => {
    navigate('/files')
  }

  const handleTrainModel = () => {
    navigate('/ml-model')
  }

  const handleStartNewScan = () => {
    navigate('/scan')
  }

  const handleTrainModelFromML = () => {
    navigate('/ml-model')
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="holographic-pulse w-16 h-16 rounded-full mx-auto mb-4" />
          <p className="text-text-muted">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-gradient mb-2">
          System Overview
        </h1>
        <p className="text-text-muted">
          Monitor your file organization and security status
        </p>
      </motion.div>

      {/* Top Stats Grid */}
      <motion.div 
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {/* System Health */}
        <div className="glassmorphism rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-light">System Health</h3>
            <Activity className="w-5 h-5 text-neon-green" />
          </div>
          <div className="flex items-center justify-center">
            <ProgressRing
              progress={getHealthScore()}
              size={80}
              strokeWidth={6}
              color="neon-green"
            />
          </div>
        </div>

        {/* Files Processed */}
        <div className="glassmorphism rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-light">Files Processed</h3>
            <FileText className="w-5 h-5 text-neon-blue" />
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-neon-blue mb-1">
              {formatNumber(lastScanResults?.total_files || stats.totalFiles)}
            </div>
            <div className="text-sm text-text-muted">
              Last 30 days
            </div>
          </div>
        </div>

        {/* Storage Analyzed */}
        <div className="glassmorphism rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-light">Storage Analyzed</h3>
            <HardDrive className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400 mb-1">
              {(lastScanResults?.storage_analyzed_percent || 0).toFixed(1)}%
            </div>
            <div className="text-sm text-text-muted">
              Disk Usage
            </div>
          </div>
        </div>

        {/* Threats Detected */}
        <div className="glassmorphism rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-light">Threats</h3>
            <Shield className="w-5 h-5 text-error" />
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-error mb-1">
              {threatSummary?.total_quarantined || 0}
            </div>
            <div className="text-sm text-text-muted">
              Quarantined
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - 2/3 width */}
        <div className="lg:col-span-2 space-y-6">
          {/* Last Scan Results */}
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-text-light">Recent Scan Activity</h3>
              <Zap className="w-5 h-5 text-neon-green" />
            </div>

            {lastScanResults ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-border/20 rounded-lg">
                    <div className="text-2xl font-bold text-neon-green">
                      {lastScanResults.total_files}
                    </div>
                    <div className="text-sm text-text-muted">Files Found</div>
                  </div>
                  <div className="text-center p-3 bg-border/20 rounded-lg">
                    <div className="text-2xl font-bold text-neon-blue">
                      {Object.keys(lastScanResults.categories || {}).length}
                    </div>
                    <div className="text-sm text-text-muted">Categories</div>
                  </div>
                  <div className="text-center p-3 bg-border/20 rounded-lg">
                    <div className="text-2xl font-bold text-purple-400">
                      {lastScanResults.total_size_formatted}
                    </div>
                    <div className="text-sm text-text-muted">Total Size</div>
                  </div>
                  <div className="text-center p-3 bg-border/20 rounded-lg">
                    <div className="text-2xl font-bold text-warning">
                      {lastScanResults.scan_duration?.toFixed(1)}s
                    </div>
                    <div className="text-sm text-text-muted">Duration</div>
                  </div>
                </div>

                {/* Category Breakdown */}
                {lastScanResults.categories && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-text-light">File Categories</h4>
                    <div className="space-y-2">
                      {Object.entries(lastScanResults.categories).map(([category, data]) => (
                        <div key={category} className="flex items-center justify-between">
                          <span className="text-sm capitalize text-text-light">{category}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-text-muted">{data.count} files</span>
                            <div className="w-20 h-2 bg-border rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-neon-green rounded-full"
                                style={{ 
                                  width: `${(data.count / lastScanResults.total_files) * 100}%` 
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Zap className="w-12 h-12 text-text-muted mx-auto mb-4" />
                <p className="text-text-muted">No recent scan data available</p>
                <button 
                  onClick={handleStartNewScan}
                  className="mt-4 px-4 py-2 bg-neon-green/20 border border-neon-green/30 rounded-lg text-neon-green hover:bg-neon-green/30 transition-colors hover:scale-105 transform transition-all duration-200"
                >
                  Start New Scan
                </button>
              </div>
            )}
          </motion.div>

          {/* ML Model Performance */}
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-text-light">ML Model Status</h3>
              <Brain className="w-5 h-5 text-neon-blue" />
            </div>

            {mlModelStatus.trained ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <ProgressRing
                    progress={mlModelStatus.accuracy * 100}
                    size={80}
                    strokeWidth={6}
                    color="neon-blue"
                  />
                  <div className="mt-2 text-sm text-text-muted">Accuracy</div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-text-muted">Training Samples:</span>
                    <span className="text-text-light">{mlModelStatus.trainingsamples || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Features:</span>
                    <span className="text-text-light">{mlModelStatus.featuresCount || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Version:</span>
                    <span className="text-text-light">{mlModelStatus.modelVersion}</span>
                  </div>
                </div>
                <div className="text-center">
                  <CheckCircle className="w-12 h-12 text-success mx-auto mb-2" />
                  <div className="text-sm text-success font-medium">Model Ready</div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Brain className="w-12 h-12 text-text-muted mx-auto mb-4" />
                <p className="text-text-muted mb-4">ML Model not trained</p>
                <button 
                  onClick={handleTrainModelFromML}
                  className="px-4 py-2 bg-neon-blue/20 border border-neon-blue/30 rounded-lg text-neon-blue hover:bg-neon-blue/30 transition-colors hover:scale-105 transform transition-all duration-200"
                >
                  Train Model
                </button>
              </div>
            )}
          </motion.div>
        </div>

        {/* Right Column - 1/3 width */}
        <div className="space-y-6">
          {/* System Status */}
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <h3 className="text-lg font-semibold text-text-light mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Backend API</span>
                <div className="flex items-center space-x-2">
                  {systemStatus.backend ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-success" />
                      <span className="text-success text-sm">Online</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4 text-error" />
                      <span className="text-error text-sm">Offline</span>
                    </>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Database</span>
                <div className="flex items-center space-x-2">
                  {systemStatus.database ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-success" />
                      <span className="text-success text-sm">Connected</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4 text-error" />
                      <span className="text-error text-sm">Disconnected</span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-text-muted">ML Model</span>
                <div className="flex items-center space-x-2">
                  {mlModelStatus.trained ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-success" />
                      <span className="text-success text-sm">Ready</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4 text-warning" />
                      <span className="text-warning text-sm">Not Trained</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Quick Actions */}
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <h3 className="text-lg font-semibold text-text-light mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button 
                onClick={handleQuickScan}
                className="w-full p-3 bg-neon-green/10 hover:bg-neon-green/20 border border-neon-green/30 rounded-lg text-neon-green transition-colors flex items-center space-x-3 hover:scale-105 transform transition-all duration-200"
              >
                <Zap className="w-5 h-5" />
                <span>Quick Scan</span>
              </button>
              
              <button 
                onClick={handleOrganizeFiles}
                className="w-full p-3 bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/30 rounded-lg text-neon-blue transition-colors flex items-center space-x-3 hover:scale-105 transform transition-all duration-200"
              >
                <TrendingUp className="w-5 h-5" />
                <span>Organize Files</span>
              </button>
              
              <button 
                onClick={handleTrainModel}
                className="w-full p-3 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-400 transition-colors flex items-center space-x-3 hover:scale-105 transform transition-all duration-200"
              >
                <Brain className="w-5 h-5" />
                <span>Train ML Model</span>
              </button>
            </div>
          </motion.div>

          {/* Recent Activity */}
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <h3 className="text-lg font-semibold text-text-light mb-4">Recent Activity</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center space-x-3 p-2 bg-border/20 rounded-lg">
                <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse" />
                <span className="text-text-light">System started</span>
                <span className="text-text-muted ml-auto">2m ago</span>
              </div>
              
              {lastScanResults && (
                <div className="flex items-center space-x-3 p-2 bg-border/20 rounded-lg">
                  <div className="w-2 h-2 bg-neon-blue rounded-full" />
                  <span className="text-text-light">Scan completed</span>
                  <span className="text-text-muted ml-auto">5m ago</span>
                </div>
              )}
              
              <div className="flex items-center space-x-3 p-2 bg-border/20 rounded-lg">
                <div className="w-2 h-2 bg-text-muted rounded-full" />
                <span className="text-text-light">Settings updated</span>
                <span className="text-text-muted ml-auto">1h ago</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

export default Dashboard