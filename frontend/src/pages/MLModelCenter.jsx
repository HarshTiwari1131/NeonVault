import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BrainCircuit, RefreshCw, Info } from 'lucide-react'
import { apiService } from '../utils/api'
import { useDispatch } from 'react-redux'
import { addNotification } from '../store/slices/appSlice'

const MLModelCenter = () => {
  const dispatch = useDispatch()
  const [modelInfo, setModelInfo] = useState(null)
  const [training, setTraining] = useState(false)
  const [dataSource, setDataSource] = useState('last_scan')
  const [folderPath, setFolderPath] = useState('')
  const [minFiles, setMinFiles] = useState(10)

  const loadInfo = async () => {
    try {
      const res = await apiService.getModelInfo()
      const info = res.data.model_info || res.data
      
      // If model exists but shows as not trained, try to reload it
      if (!info.trained && info.model_path) {
        try {
          await apiService.reloadModel()
          // Reload info after model reload
          const reloadedRes = await apiService.getModelInfo()
          setModelInfo(reloadedRes.data.model_info || reloadedRes.data)
        } catch (reloadError) {
          setModelInfo(info)
        }
      } else {
        setModelInfo(info)
      }
    } catch (error) {
      console.error('Failed to load model info:', error)
      dispatch(addNotification({ 
        type: 'warning', 
        message: 'Could not load model information. Model may not be trained yet.' 
      }))
    }
  }

  useEffect(() => { loadInfo() }, [])

  const train = async () => {
    setTraining(true)
    try {
      const res = await apiService.trainMLModel({ 
        data_source: dataSource, 
        folder_path: folderPath || undefined, 
        min_files: Number(minFiles) 
      })
      
      dispatch(addNotification({ 
        type: 'success', 
        message: res.data.message || 'Training completed successfully!' 
      }))
      
      // Wait a moment then reload model info
      setTimeout(async () => {
        await loadInfo()
      }, 1000)
      
    } catch (e) {
      const errorMessage = e.response?.data?.detail || e.message || 'Training failed'
      dispatch(addNotification({ 
        type: 'error', 
        message: `Training failed: ${errorMessage}` 
      }))
      console.error('Training error:', e.response?.data || e.message)
    } finally {
      setTraining(false)
    }
  }

  const reload = async () => {
    try {
      const res = await apiService.reloadModel()
      dispatch(addNotification({ type: res.data.success ? 'success' : 'error', message: res.data.message }))
      await loadInfo()
    } catch {}
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2"><BrainCircuit className="w-6 h-6 text-neon-green" /> ML Model Center</h1>
        <div className="space-x-2">
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={reload} className="px-4 py-2 bg-border/30 border border-border rounded-lg inline-flex items-center gap-2"><RefreshCw className="w-4 h-4" />Reload Model</motion.button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glassmorphism rounded-xl p-4 space-y-3 lg:col-span-1">
          <h2 className="text-lg font-semibold">Train Model</h2>
          <label className="block text-sm text-text-muted">Data Source</label>
          <select value={dataSource} onChange={e => setDataSource(e.target.value)} className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border">
            <option value="last_scan">Last Scan</option>
            <option value="folder_path">Folder Path</option>
            <option value="database">Database</option>
          </select>
          {dataSource === 'folder_path' && (
            <>
              <label className="block text-sm text-text-muted pt-1">Folder Path</label>
              <input value={folderPath} onChange={e => setFolderPath(e.target.value)} placeholder="C:\\Users\\You\\Documents" className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border" />
            </>
          )}
          <label className="block text-sm text-text-muted pt-1">Minimum Files</label>
          <input type="number" value={minFiles} onChange={e => setMinFiles(e.target.value)} className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border" />
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} disabled={training} onClick={train} className="w-full mt-2 px-4 py-2 bg-neon-green/20 border border-neon-green/40 rounded-lg text-neon-green">{training ? 'Training…' : 'Start Training'}</motion.button>
        </div>

        <div className="glassmorphism rounded-xl p-4 space-y-3 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2"><Info className="w-5 h-5" /> Model Info</h2>
          </div>
          {!modelInfo ? (
            <div className="text-text-muted">No model info available.</div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3 rounded bg-border/20 border border-border">
                <div className="text-sm text-text-muted">Trained</div>
                <div className="font-semibold flex items-center gap-2">
                  {modelInfo.trained ? (
                    <>
                      <span className="w-2 h-2 bg-neon-green rounded-full"></span>
                      Yes
                    </>
                  ) : (
                    <>
                      <span className="w-2 h-2 bg-error rounded-full"></span>
                      No
                    </>
                  )}
                </div>
              </div>
              <div className="p-3 rounded bg-border/20 border border-border">
                <div className="text-sm text-text-muted">Accuracy</div>
                <div className="font-semibold">{`${(((modelInfo.metadata?.accuracy ?? 0) * 100).toFixed(1))}%`}</div>
              </div>
              <div className="p-3 rounded bg-border/20 border border-border">
                <div className="text-sm text-text-muted">Features</div>
                <div className="font-semibold">{modelInfo.feature_count || modelInfo.metadata?.features_count || 0}</div>
              </div>
              <div className="p-3 rounded bg-border/20 border border-border">
                <div className="text-sm text-text-muted">Training samples</div>
                <div className="font-semibold">{modelInfo.metadata?.training_samples || 0}</div>
              </div>
              <div className="p-3 rounded bg-border/20 border border-border md:col-span-2">
                <div className="text-sm text-text-muted">Model path</div>
                <div className="font-semibold truncate text-xs" title={modelInfo.model_path || 'backend/ml_model/model.pkl'}>
                  {modelInfo.model_path || 'backend/ml_model/model.pkl'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MLModelCenter
