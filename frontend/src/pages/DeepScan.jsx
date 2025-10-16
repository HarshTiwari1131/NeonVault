import { useEffect, useMemo, useState, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FolderOpen, PlayCircle, PauseCircle, ScanLine, Settings2, CheckCircle2, AlertTriangle } from 'lucide-react'
import { apiService, formatFileSize, formatDuration } from '../utils/api'
import ProgressRing from '../components/ProgressRing'
import { useDispatch } from 'react-redux'
import { addNotification } from '../store/slices/appSlice'

const scanModes = [
  { key: 'custom', label: 'Custom Scan' },
  { key: 'normal', label: 'Normal Scan' },
  { key: 'full', label: 'Full Scan' },
]

const DeepScan = () => {
  const dispatch = useDispatch()
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const quick = params.get('quick')
  const folderParam = params.get('folder')
  const [targetPath, setTargetPath] = useState(folderParam ? decodeURIComponent(folderParam) : '')
  const [scanMode, setScanMode] = useState('custom')
  const [recursive, setRecursive] = useState(true)
  const [dryRun, setDryRun] = useState(true)
  const [hashCompare, setHashCompare] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [progress, setProgress] = useState({ progress: 0, message: '', is_busy: false })
  const [results, setResults] = useState(null)
  const [rules, setRules] = useState({ extensions: ['.tmp', '.log'], older_than_days: 30, size_below_kb: 1024 })
  const [rulePresets, setRulePresets] = useState([])
  const [preview, setPreview] = useState(null)
  // Organize state
  const [isOrganizing, setIsOrganizing] = useState(false)
  const [orgSourcePath, setOrgSourcePath] = useState('')
  const [orgTargetBase, setOrgTargetBase] = useState('organized')
  const [orgUseML, setOrgUseML] = useState(true)
  const [orgDatedFolders, setOrgDatedFolders] = useState(false)
  const [orgResults, setOrgResults] = useState(null)
  // Organize progress
  const [orgProgress, setOrgProgress] = useState({ progress: 0, message: '', is_busy: false })
  const [orgPolling, setOrgPolling] = useState(false)
  const orgPollRef = useRef(null)

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const res = await apiService.getStatus();
        if (!res?.data) return;

        const { current_operation, is_busy } = res.data;

        if (current_operation === 'organizing') {
          setIsOrganizing(is_busy);
          setOrgProgress(res.data);
          if (!is_busy) {
            setOrgPolling(false);
            if (orgPollRef.current) clearInterval(orgPollRef.current);
          }
        } else if (current_operation === 'scanning') {
          setIsScanning(is_busy);
          setProgress(res.data);
        } else {
          if (isOrganizing && !is_busy) {
             setIsOrganizing(false);
             setOrgPolling(false);
             if (orgPollRef.current) clearInterval(orgPollRef.current);
             setOrgProgress(prev => ({ ...prev, progress: 100, is_busy: false, message: 'Organization complete' }));
          }
        }
      } catch (error) {
        console.error("Error polling status:", error);
      }
    };

    const intervalId = setInterval(pollStatus, 1000);
    orgPollRef.current = intervalId;

    return () => clearInterval(intervalId);
  }, [isOrganizing]);

  // Cleanup organize polling on unmount
  useEffect(() => {
    return () => {
      if (orgPollRef.current) {
        clearInterval(orgPollRef.current);
      }
    };
  }, [])

  // Auto-start scan if quick param is present and folder is set
  useEffect(() => {
    if (quick && folderParam && !isScanning && !results) {
      startScan()
    }
    // eslint-disable-next-line
  }, [quick, folderParam])

  const startScan = async () => {
    if (!targetPath) {
      dispatch(addNotification({ type: 'error', message: 'Please enter a target folder path' }))
      return
    }
    setIsScanning(true)
    setResults(null)
    try {
      const res = await apiService.scanFolder({ folder_path: targetPath, recursive })
      setResults(res.data.results)
      dispatch(addNotification({ type: 'success', message: 'Scan completed' }))
    } catch (e) {
      dispatch(addNotification({ type: 'error', message: 'Scan failed. Check logs.' }))
    } finally {
      setIsScanning(false)
    }
  }

  const quickScanNow = async () => {
    // Quick action: reuse startScan with current options
    await startScan()
  }

  const createNewRule = () => {
    // Save current rules as a preset locally (basic UX)
    const preset = {
      id: Date.now(),
      ...rules,
    }
    setRulePresets(prev => [preset, ...prev].slice(0, 5)) // keep last 5
    dispatch(addNotification({ type: 'success', message: 'Rule saved' }))
  }


  const pollOrganizeStatus = () => {
    setOrgPolling(true);
  };

  const runOrganize = async () => {
    const source = orgSourcePath || targetPath;
    if (!source) {
      dispatch(addNotification({ type: 'error', message: 'Enter a source Folder Path for organization' }));
      return;
    }
    setIsOrganizing(true);
    setOrgResults(null);
    setOrgProgress({ progress: 0, message: 'Starting organization...', is_busy: true });
    pollOrganizeStatus();
    try {
      const res = await apiService.organizeFiles({
        folder_path: source,
        destination_base: orgTargetBase || 'organized',
        dry_run: true,
        use_ml: orgUseML,
        create_dated_folders: orgDatedFolders,
      });
      setOrgResults(res.data);
      dispatch(addNotification({ type: res.data.success ? 'success' : 'info', message: res.data.message }));
    } catch (e) {
      dispatch(addNotification({ type: 'error', message: 'Organization preview failed' }));
    } finally {
      setIsOrganizing(false);
      setOrgPolling(false);
      if (orgPollRef.current) clearInterval(orgPollRef.current);
    }
  };

  const previewOrganize = async () => {
    // Explicit preview with dry_run=true
    await runOrganize()
  }

  const applyOrganize = async () => {
    const source = orgSourcePath || targetPath;
    if (!source) {
      dispatch(addNotification({ type: 'error', message: 'Enter a source Folder Path for organization' }));
      return;
    }
    setIsOrganizing(true);
    setOrgProgress({ progress: 0, message: 'Starting organization...', is_busy: true });
    pollOrganizeStatus();
    try {
      const res = await apiService.organizeFiles({
        folder_path: source,
        destination_base: orgTargetBase || 'organized',
        dry_run: false,
        use_ml: orgUseML,
        create_dated_folders: orgDatedFolders,
      });
      setOrgResults(res.data);
      dispatch(addNotification({ type: res.data.success ? 'success' : 'error', message: res.data.message }));
    } catch (e) {
      dispatch(addNotification({ type: 'error', message: 'Organization failed to apply' }));
    } finally {
      setIsOrganizing(false);
      setOrgPolling(false);
      if (orgPollRef.current) clearInterval(orgPollRef.current);
    }
  };

  const runPreviewDeletion = async () => {
    if (!targetPath) return
    try {
      const res = await apiService.previewDeletion({ folder_path: targetPath, extensions: rules.extensions.join(','), older_than_days: rules.older_than_days, size_below_kb: rules.size_below_kb })
      setPreview(res.data.preview)
      dispatch(addNotification({ type: 'info', message: `Preview: ${res.data.preview.files_to_delete} files match` }))
    } catch {
      dispatch(addNotification({ type: 'error', message: 'Preview failed' }))
    }
  }

  const runDeletion = async () => {
    if (!targetPath) return
    try {
      const res = await apiService.deleteFiles({ folder_path: targetPath, rules, dry_run: dryRun, permanent: !dryRun })
      dispatch(addNotification({ type: 'success', message: res.data.message }))
    } catch {
      dispatch(addNotification({ type: 'error', message: 'Deletion failed' }))
    }
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      {/* Column 1: Deep Scan Box and Configuration */}
      <div className="xl:col-span-1 space-y-4">
        {/* Deep Scan & Clean Main Box */}
        <div className="glassmorphism rounded-xl p-6 border border-neon-green/30">
          <div className="text-center mb-4">
            <h2 className="text-2xl font-bold text-neon-green mb-1">Deep Scan & Clean</h2>
          </div>

          {/* Scan Mode Tabs */}
          <div className="flex space-x-1 mb-4 bg-border/20 rounded-lg p-1">
            {scanModes.map((mode) => (
              <button
                key={mode.key}
                className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  scanMode === mode.key 
                    ? 'bg-neon-green text-bg-dark' 
                    : 'text-text-light hover:bg-border/30'
                }`}
                onClick={() => setScanMode(mode.key)}
              >
                {mode.label}
              </button>
            ))}
          </div>

          {/* Folder Path */}
          <div className="mb-4">
            <label className="block text-sm text-text-muted mb-2">Folder Path</label>
            <input 
              value={targetPath} 
              onChange={(e) => setTargetPath(e.target.value)} 
              placeholder="C:\\Users\\You\\Downloads" 
              className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border focus:outline-none focus:border-neon-green" 
            />
          </div>

          {/* Start Deep Scan Button */}
          <motion.button 
            whileHover={{ scale: 1.02 }} 
            whileTap={{ scale: 0.98 }} 
            onClick={startScan} 
            disabled={isScanning}
            className="w-full px-4 py-3 bg-neon-green text-bg-dark font-bold rounded-lg flex items-center justify-center space-x-2 mb-4 hover:bg-neon-green/90 disabled:opacity-50"
          >
            <PlayCircle className="w-5 h-5" />
            <span>Start Deep Scan</span>
          </motion.button>

          {/* Scan Configuration */}
          <div className="space-y-3 pt-3 border-t border-border/30">
            <h3 className="text-sm font-semibold text-text-light">Scan Configuration</h3>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-light">Dry Run Mode</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={dryRun} 
                  onChange={(e) => setDryRun(e.target.checked)} 
                  className="sr-only peer" 
                />
                <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-light">Hash Comparison (Duplicates)</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={hashCompare} 
                  onChange={(e) => setHashCompare(e.target.checked)} 
                  className="sr-only peer" 
                />
                <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-light">Recursive</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={recursive} 
                  onChange={(e) => setRecursive(e.target.checked)} 
                  className="sr-only peer" 
                />
                <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
              </label>
            </div>
          </div>
        </div>

          {/* Organize Files - Full Box */}
          <div className="glassmorphism rounded-xl p-6 border border-neon-green/30">
            <div className="text-center mb-4">
              <h2 className="text-2xl font-bold text-neon-green mb-1">Organize Files</h2>
            </div>

            {/* Source Folder Path */}
            <div className="mb-3">
              <label className="block text-sm text-text-muted mb-2">Folder Path</label>
              <input 
                value={orgSourcePath}
                onChange={(e) => setOrgSourcePath(e.target.value)}
                placeholder="E:\\"
                className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border focus:outline-none focus:border-neon-green" 
              />
              {!orgSourcePath && targetPath && (
                <button className="mt-2 text-xs text-neon-blue hover:underline" onClick={() => setOrgSourcePath(targetPath)}>
                  Use Deep Scan folder: {targetPath}
                </button>
              )}
            </div>

            {/* Target Base Path */}
            <div className="mb-4">
              <label className="block text-sm text-text-muted mb-2">Target Base (organized to)</label>
              <input 
                value={orgTargetBase}
                onChange={(e) => setOrgTargetBase(e.target.value)}
                placeholder="E:\\Organized or 'organized'"
                className="w-full px-3 py-2 rounded-lg bg-border/20 border border-border focus:outline-none focus:border-neon-green" 
              />
            </div>

            {/* Actions */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <motion.button 
                whileHover={{ scale: 1.02 }} 
                whileTap={{ scale: 0.98 }} 
                onClick={previewOrganize}
                disabled={isOrganizing}
                className="w-full px-4 py-3 bg-border/40 border border-border rounded-lg flex items-center justify-center space-x-2 hover:bg-border/60 disabled:opacity-50"
              >
                <PlayCircle className="w-5 h-5 text-neon-blue" />
                <span>Preview Organization</span>
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.02 }} 
                whileTap={{ scale: 0.98 }} 
                onClick={applyOrganize}
                disabled={isOrganizing}
                className="w-full px-4 py-3 bg-neon-green text-bg-dark font-bold rounded-lg flex items-center justify-center space-x-2 hover:bg-neon-green/90 disabled:opacity-50"
              >
                <PlayCircle className="w-5 h-5" />
                <span>Start Organization</span>
              </motion.button>
            </div>

            {/* Organize Configuration */}
            <div className="space-y-3 pt-3 border-t border-border/30">
              <h3 className="text-sm font-semibold text-text-light">Organize Configuration</h3>

              <div className="flex items-center justify-between">
                <span className="text-sm text-text-light">Use ML Predictions</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={orgUseML} 
                    onChange={(e) => setOrgUseML(e.target.checked)} 
                    className="sr-only peer" 
                  />
                  <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-text-light">Create Dated Folders (YYYY-MM)</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={orgDatedFolders} 
                    onChange={(e) => setOrgDatedFolders(e.target.checked)} 
                    className="sr-only peer" 
                  />
                  <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
                </label>
              </div>

              {(isOrganizing || orgPolling) && (
                <div className="flex items-center space-x-2 text-sm text-text-muted">
                  <div className="w-4 h-4 rounded-full border-2 border-neon-green border-t-transparent animate-spin" />
                  <span>{orgProgress.message || 'Organizing… check progress on the right'}</span>
                </div>
              )}
            </div>
          </div>

          {/* Rule Management & Preview */}
        <div className="glassmorphism rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-3 text-neon-blue">Rule Management & Preview</h2>
          <div className="space-y-3">
            {/* Organization Rules Toggle */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-neon-green rounded-full"></div>
                <span className="text-sm">Organization Rules</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
              </label>
            </div>

            {/* Deletion Rules */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-text-light">Deletion Rules</h3>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-muted">Enable temp rules</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rules.extensions.includes('.tmp') || rules.extensions.includes('.log')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRules(r => ({ ...r, extensions: Array.from(new Set([...(r.extensions||[]), '.tmp', '.log'])) }))
                      } else {
                        setRules(r => ({ ...r, extensions: (r.extensions||[]).filter(x => x !== '.tmp' && x !== '.log') }))
                      }
                    }}
                    className="sr-only peer"
                  />
                  <div className="relative w-11 h-6 bg-border/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-green"></div>
                </label>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-3">
              <div>
                <label className="block text-xs text-text-muted mb-1">Extensions (comma-separated)</label>
                <input
                  value={(rules.extensions||[]).join(', ')}
                  onChange={(e) => setRules(r => ({ ...r, extensions: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))}
                  placeholder=".tmp, .log, .cache"
                  className="w-full px-2 py-1 rounded bg-border/20 border border-border text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Size below</label>
                <select
                  value={rules.size_below_kb}
                  onChange={(e) => setRules(r => ({ ...r, size_below_kb: Number(e.target.value) }))}
                  className="w-full px-2 py-1 rounded bg-border/20 border border-border text-sm"
                >
                  <option value={51200}>50MB</option>
                  <option value={10240}>10MB</option>
                  <option value={2048}>2MB</option>
                  <option value={1024}>1MB</option>
                  <option value={512}>512KB</option>
                  <option value={100}>100KB</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-text-muted mb-1">Older than (days)</label>
                <input
                  type="number"
                  value={rules.older_than_days}
                  onChange={(e) => setRules(r => ({ ...r, older_than_days: Math.max(0, Number(e.target.value||0)) }))}
                  className="w-full px-2 py-1 rounded bg-border/20 border border-border text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Size below (KB)</label>
                <input
                  type="number"
                  value={rules.size_below_kb}
                  onChange={(e) => setRules(r => ({ ...r, size_below_kb: Math.max(0, Number(e.target.value||0)) }))}
                  className="w-full px-2 py-1 rounded bg-border/20 border border-border text-sm"
                />
              </div>
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={runPreviewDeletion} className="px-4 py-2 bg-border/30 border border-border rounded-lg text-sm">Preview</motion.button>
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={runDeletion} className="px-4 py-2 bg-error/20 border border-error/40 rounded-lg text-error text-sm">Run Clean</motion.button>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex space-x-2">
          <motion.button 
            whileHover={{ scale: 1.02 }} 
            whileTap={{ scale: 0.98 }} 
            onClick={quickScanNow}
            disabled={isScanning}
            className="flex-1 px-4 py-2 bg-neon-green/20 border border-neon-green/40 rounded-lg text-neon-green text-sm font-medium disabled:opacity-50"
          >
            Quick Scan Now
          </motion.button>
          <motion.button 
            whileHover={{ scale: 1.02 }} 
            whileTap={{ scale: 0.98 }} 
            onClick={createNewRule}
            className="flex-1 px-4 py-2 bg-neon-blue/20 border border-neon-blue/40 rounded-lg text-neon-blue text-sm font-medium"
          >
            Create New Rule
          </motion.button>
        </div>

        {/* Optional: Show last saved rules */}
        {rulePresets.length > 0 && (
          <div className="glassmorphism rounded-xl p-4">
            <h3 className="text-sm font-medium text-text-light mb-2">Saved Rules (recent)</h3>
            <div className="space-y-2 text-xs text-text-muted">
              {rulePresets.map(p => (
                <div key={p.id} className="flex items-center justify-between border border-border/30 rounded px-2 py-1">
                  <span>Ext: {(p.extensions||[]).join(', ') || '—'} • Older: {p.older_than_days}d • Size: {p.size_below_kb}KB</span>
                  <button
                    className="text-neon-blue hover:underline"
                    onClick={() => setRules({ extensions: p.extensions||[], older_than_days: p.older_than_days, size_below_kb: p.size_below_kb })}
                  >Load</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

  {/* Column 2-3: Results Table */}
      <div className="xl:col-span-2 space-y-4">
        {/* Progress Bar: Scan or Organize */}
        {(isScanning || isOrganizing || orgPolling) && (
          <div className="glassmorphism rounded-xl p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">
                {isScanning ? (progress.message || 'Scanning...') : (orgProgress.message || 'Organizing...')}
              </span>
              <span className="text-sm text-text-muted">
                {isScanning ? (progress.progress || 0) : (orgProgress.progress || 0)}%
              </span>
            </div>
            <div className="w-full bg-border/30 rounded-full h-2">
              <div
                className="bg-neon-green h-2 rounded-full transition-all duration-300"
                style={{ width: `${isScanning ? (progress.progress || 0) : (orgProgress.progress || 0)}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Scan Results Preview (Deep Scan / Delete Preview) */}
        {(results || preview) && (
          <div className="glassmorphism rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Scan Results Preview (Dry Run):</h2>
              {results && (
                <div className="text-sm text-text-muted">
                  {results.total_files} files • {formatFileSize(results.total_size)} • {formatDuration(results.scan_duration)}
                </div>
              )}
            </div>
            
            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-text-muted">
                    <th className="px-3 py-2 text-left">File Name</th>
                    <th className="px-3 py-2 text-left">Action</th>
                    <th className="px-3 py-2 text-left">Action</th>
                    <th className="px-3 py-2 text-left">Action</th>
                    <th className="px-3 py-2 text-left">Predicted Category</th>
                    <th className="px-3 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Sample rows matching the image */}
                  <tr className="border-b border-border/30 hover:bg-border/10">
                    <td className="px-3 py-2">report.docx</td>
                    <td className="px-3 py-2">→</td>
                    <td className="px-3 py-2 text-neon-blue">Move to /Docs</td>
                    <td className="px-3 py-2">1W</td>
                    <td className="px-3 py-2">Document</td>
                    <td className="px-3 py-2 text-neon-green">OK</td>
                  </tr>
                  <tr className="border-b border-border/30 hover:bg-border/10">
                    <td className="px-3 py-2">report.docx</td>
                    <td className="px-3 py-2">→</td>
                    <td className="px-3 py-2 text-warning">Exists Skip (Size)</td>
                    <td className="px-3 py-2">1W</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2 text-neon-green">OK</td>
                  </tr>
                  <tr className="border-b border-border/30 hover:bg-border/10">
                    <td className="px-3 py-2">temp.tmp</td>
                    <td className="px-3 py-2">→</td>
                    <td className="px-3 py-2 text-error">Delete</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2 text-warning">Pending Deletion (Rule)</td>
                  </tr>
                  <tr className="border-b border-border/30 hover:bg-border/10">
                    <td className="px-3 py-2">temp.tmp</td>
                    <td className="px-3 py-2">→</td>
                    <td className="px-3 py-2 text-error">Delete</td>
                    <td className="px-3 py-2">6W</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2 text-neon-green">OK</td>
                  </tr>
                  <tr className="border-b border-border/30 hover:bg-border/10">
                    <td className="px-3 py-2">Sure.bom (KB)</td>
                    <td className="px-3 py-2">→</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2">-</td>
                    <td className="px-3 py-2">-</td>
                  </tr>

                  {/* Dynamic results from actual scan */}
                  {results?.files?.slice(0, 5).map((file, idx) => (
                    <tr key={`result-${idx}`} className="border-b border-border/30 hover:bg-border/10">
                      <td className="px-3 py-2 truncate max-w-xs">{file.name}</td>
                      <td className="px-3 py-2">→</td>
                      <td className="px-3 py-2 text-neon-blue">{file.action || 'Scan'}</td>
                      <td className="px-3 py-2">-</td>
                      <td className="px-3 py-2">{file.category || 'Unknown'}</td>
                      <td className="px-3 py-2 text-neon-green">OK</td>
                    </tr>
                  ))}

                  {/* Dynamic preview from deletion preview */}
                  {preview?.files?.slice(0, 3).map((file, idx) => (
                    <tr key={`preview-${idx}`} className="border-b border-border/30 hover:bg-border/10">
                      <td className="px-3 py-2 truncate max-w-xs">{file.name}</td>
                      <td className="px-3 py-2">→</td>
                      <td className="px-3 py-2 text-error">Delete</td>
                      <td className="px-3 py-2">-</td>
                      <td className="px-3 py-2">-</td>
                      <td className="px-3 py-2 text-warning">Preview</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Show message if no results */}
            {!results && !preview && (
              <div className="text-center py-8 text-text-muted">
                <ScanLine className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No scan results yet. Start a scan to see file analysis here.</p>
              </div>
            )}
          </div>
        )}

        {/* Organization Preview/Changes */}
        {orgResults && (
          <div className="glassmorphism rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">
                {orgResults?.results?.dry_run ? 'Organization Preview' : 'Organization Changes Applied'}
              </h2>
              <div className="text-sm text-text-muted">
                {orgResults?.results?.moved_count || 0} planned • {orgResults?.results?.failed_count || 0} failed • {formatDuration(orgResults?.duration || 0)}
              </div>
            </div>

            {/* Summary badges */}
            <div className="flex flex-wrap gap-2 mb-3 text-xs">
              <span className="px-2 py-1 rounded bg-border/30 border border-border">Source: {orgResults?.results?.source_folder}</span>
              <span className="px-2 py-1 rounded bg-border/30 border border-border">Target: {orgResults?.results?.destination_base}</span>
              <span className="px-2 py-1 rounded bg-border/30 border border-border">Mode: {orgResults?.results?.dry_run ? 'Preview' : 'Apply'}</span>
            </div>

            {/* Operations Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-text-muted">
                    <th className="px-3 py-2 text-left">Source</th>
                    <th className="px-3 py-2 text-left"></th>
                    <th className="px-3 py-2 text-left">Destination</th>
                    <th className="px-3 py-2 text-left">Category</th>
                    <th className="px-3 py-2 text-left">Confidence</th>
                    <th className="px-3 py-2 text-left">Method</th>
                    <th className="px-3 py-2 text-left">Dry Run</th>
                  </tr>
                </thead>
                <tbody>
                  {(orgResults?.results?.operations || []).map((op, idx) => (
                    <tr key={`op-${idx}`} className="border-b border-border/30 hover:bg-border/10">
                      <td className="px-3 py-2 truncate max-w-xs" title={op.source}>{op.source}</td>
                      <td className="px-3 py-2">→</td>
                      <td className="px-3 py-2 truncate max-w-xs" title={op.destination}>{op.destination}</td>
                      <td className="px-3 py-2 capitalize">{op.category}</td>
                      <td className="px-3 py-2">{typeof op.confidence === 'number' ? `${(op.confidence * 100).toFixed(0)}%` : '-'}</td>
                      <td className="px-3 py-2">{op.method}</td>
                      <td className="px-3 py-2">{op.dry_run ? 'Yes' : 'No'}</td>
                    </tr>
                  ))}
                  {(!orgResults?.results?.operations || orgResults.results.operations.length === 0) && (
                    <tr>
                      <td className="px-3 py-6 text-center text-text-muted" colSpan={7}>No operations to display</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Default state when no scan */}
        {!isScanning && !results && !preview && !orgResults && (
          <div className="glassmorphism rounded-xl p-8 text-center">
            <FolderOpen className="w-16 h-16 text-text-muted mx-auto mb-4 opacity-50" />
            <h2 className="text-xl font-semibold mb-2">Ready for Deep Scan</h2>
            <p className="text-text-muted mb-4">Configure your scan settings and click "Start Deep Scan" to begin analyzing your files.</p>
            <div className="flex items-center justify-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-text-muted">
                <div className="w-2 h-2 bg-neon-green rounded-full"></div>
                <span>Custom Scan Selected</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-text-muted">
                <div className="w-2 h-2 bg-neon-blue rounded-full"></div>
                <span>Rules Configured</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DeepScan
