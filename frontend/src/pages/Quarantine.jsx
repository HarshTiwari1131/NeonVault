import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ShieldAlert, RotateCcw, Trash2, HardDrive, FolderOpen, File, PlayCircle } from 'lucide-react'
import { apiService, formatFileSize, getThreatLevelColor } from '../utils/api'
import { useDispatch } from 'react-redux'
import { addNotification } from '../store/slices/appSlice'

const Quarantine = () => {
  const dispatch = useDispatch()
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [scanPath, setScanPath] = useState('')
  const [scanMode, setScanMode] = useState('file') // 'file' | 'folder' | 'drive'
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState({ progress: 0, message: '' })
  const [scanResults, setScanResults] = useState(null)

  const loadFiles = async () => {
    setLoading(true)
    try {
      const res = await apiService.getQuarantinedFiles()
      setFiles(res.data.quarantined_files || [])
    } catch (e) {
      dispatch(addNotification({ type: 'error', message: 'Failed to load quarantined files' }))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  const act = async (fileId, action) => {
    try {
      const res = await apiService.quarantineAction({ file_id: fileId, action })
      dispatch(addNotification({ type: 'info', message: res.data.message }))
      loadFiles()
    } catch {
      dispatch(addNotification({ type: 'error', message: 'Action failed' }))
    }
  }

  const startVirusScan = async () => {
    if (!scanPath) {
      dispatch(addNotification({ type: 'error', message: 'Please enter a path to scan' }))
      return
    }
    setScanning(true)
    setScanResults(null)
    try {
      const payload = scanMode === 'file' ? { file_path: scanPath } : { folder_path: scanPath, recursive: true }
      const res = await apiService.virusScan(payload)
      setScanResults(res.data.results)
      dispatch(addNotification({ type: 'success', message: res.data.message }))
    } catch (e) {
      dispatch(addNotification({ type: 'error', message: 'Virus scan failed' }))
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Quarantine & Threats</h1>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={loadFiles} className="px-4 py-2 bg-border/30 border border-border rounded-lg">Refresh</motion.button>
      </div>

      {/* Virus Scan */}
      <div className="glassmorphism rounded-xl p-4">
        <h2 className="text-lg font-semibold mb-3">Virus Scan</h2>
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          <div className="md:col-span-3 flex items-center gap-2">
            <button onClick={() => setScanMode('file')} className={`px-3 py-2 rounded-lg border ${scanMode==='file'?'border-neon-blue text-neon-blue bg-neon-blue/10':'border-border text-text-muted'}`}><File className="w-4 h-4 inline mr-1"/> File</button>
            <button onClick={() => setScanMode('folder')} className={`px-3 py-2 rounded-lg border ${scanMode==='folder'?'border-neon-green text-neon-green bg-neon-green/10':'border-border text-text-muted'}`}><FolderOpen className="w-4 h-4 inline mr-1"/> Folder</button>
            <button onClick={() => setScanMode('drive')} className={`px-3 py-2 rounded-lg border ${scanMode==='drive'?'border-warning text-warning bg-warning/10':'border-border text-text-muted'}`}><HardDrive className="w-4 h-4 inline mr-1"/> Drive</button>
          </div>
          <div className="md:col-span-7">
            <label className="block text-xs text-text-muted mb-1">{scanMode==='file'?'File Path':'Folder/Drive Path'}</label>
            <input value={scanPath} onChange={(e)=>setScanPath(e.target.value)} placeholder={scanMode==='file'?'E:\\file.pdf':'E:\\Downloads'} className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border"/>
          </div>
          <div className="md:col-span-2 flex items-center">
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} disabled={scanning} onClick={startVirusScan} className="w-full px-4 py-2 bg-error/20 border border-error/40 rounded-lg text-error font-medium disabled:opacity-50"><PlayCircle className="w-4 h-4 inline mr-1"/> Scan</motion.button>
          </div>
        </div>
        {scanning && (
          <div className="mt-3 flex items-center gap-3">
            <motion.div className="w-5 h-5 rounded-full border-2 border-error border-t-transparent" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}/>
            <div className="text-sm text-text-muted">Scanning… This can take a while for large folders.</div>
          </div>
        )}
        {scanResults && (
          <div className="mt-4 text-sm">
            <div className="mb-2 text-text-muted">Scanned: {scanResults.files_scanned} • Infected: {scanResults.infected_count}</div>
            <div className="max-h-64 overflow-auto divide-y divide-border/50">
              {scanResults.details?.map((r, i)=> (
                <div key={i} className="py-2 flex items-center justify-between">
                  <div className="truncate max-w-[60%]">{r.file_name || r.file_path}</div>
                  <div className="text-xs {r.is_infected? 'text-error': 'text-neon-green'}">{r.is_infected ? r.threat_name || 'INFECTED' : 'Clean'}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="glassmorphism rounded-xl p-4">
        <div className="grid grid-cols-12 text-sm text-text-muted pb-2 border-b border-border/50">
          <div className="col-span-5">File</div>
          <div className="col-span-2">Threat</div>
          <div className="col-span-2">Method</div>
          <div className="col-span-1">Level</div>
          <div className="col-span-2 text-right">Actions</div>
        </div>
        <div className="divide-y divide-border/50 max-h-[60vh] overflow-auto">
          {files.map((f) => (
            <div key={f.id} className="grid grid-cols-12 py-3 items-center text-sm">
              <div className="col-span-5 truncate">
                <div className="font-medium">{f.file_path?.split('\\').pop() || f.file_path}</div>
                <div className="text-text-muted truncate">{f.original_path}</div>
              </div>
              <div className="col-span-2">
                <div className="font-medium text-error flex items-center space-x-2"><ShieldAlert className="w-4 h-4" /><span>{f.threat_type || 'Unknown'}</span></div>
                <div className="text-xs text-text-muted">{formatFileSize(f.file_size || 0)}</div>
              </div>
              <div className="col-span-2">{f.detection_method}</div>
              <div className={`col-span-1 font-semibold ${getThreatLevelColor(f.threat_level || 'medium')}`}>{f.threat_level || 'medium'}</div>
              <div className="col-span-2 text-right space-x-2">
                <button onClick={() => act(f.id, 'restore')} className="px-3 py-1 rounded bg-neon-blue/20 border border-neon-blue/40 text-neon-blue inline-flex items-center space-x-1"><RotateCcw className="w-4 h-4" /><span>Restore</span></button>
                <button onClick={() => act(f.id, 'delete')} className="px-3 py-1 rounded bg-error/20 border border-error/40 text-error inline-flex items-center space-x-1"><Trash2 className="w-4 h-4" /><span>Delete</span></button>
              </div>
            </div>
          ))}
          {(!files || files.length === 0) && (
            <div className="py-10 text-center text-text-muted">No quarantined files found</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Quarantine
