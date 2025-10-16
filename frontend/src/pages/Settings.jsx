import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Wrench, KeyRound, Volume2 } from 'lucide-react'
import { apiService } from '../utils/api'
import { useDispatch } from 'react-redux'
import { addNotification } from '../store/slices/appSlice'

const Settings = () => {
  const dispatch = useDispatch()
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(false)
  const [apiKeys, setApiKeys] = useState({ virustotal_api_key: '', clamav_host: '', clamav_port: 3310 })
  const [notifications, setNotifications] = useState({ speech_enabled: true, email_notifications: false, desktop_notifications: true, recipient_email: '' })

  const load = async () => {
    setLoading(true)
    try {
      const res = await apiService.getSettings()
      const s = res.data.settings || {}
      setSettings(s)
      setApiKeys({
        virustotal_api_key: s.api_keys?.virustotal_api_key || '',
        clamav_host: s.api_keys?.clamav_host || 'localhost',
        clamav_port: s.api_keys?.clamav_port || 3310,
      })
      setNotifications(s.notifications || notifications)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const saveSetting = async (key, value) => {
    try {
      await apiService.updateSetting({ key, value })
      dispatch(addNotification({ type: 'success', message: `Updated ${key}` }))
      await load()
    } catch (e) {
      dispatch(addNotification({ type: 'error', message: e.response?.data?.detail || 'Update failed' }))
    }
  }

  const saveApiKeys = async () => {
    try {
      const res = await apiService.updateApiKeys(apiKeys)
      dispatch(addNotification({ type: 'success', message: res.data.message }))
    } catch {
      dispatch(addNotification({ type: 'error', message: 'Failed to update API keys' }))
    }
  }

  const saveNotifications = async () => {
    try {
      await apiService.updateNotificationSettings(notifications)
      dispatch(addNotification({ type: 'success', message: 'Notification settings updated' }))
    } catch {
      dispatch(addNotification({ type: 'error', message: 'Failed to update notifications' }))
    }
  }

  const testSpeech = async () => {
    try {
      const res = await apiService.testSpeechNotification()
      dispatch(addNotification({ type: res.data.success ? 'success' : 'info', message: res.data.message }))
    } catch {}
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2"><Wrench className="w-6 h-6 text-neon-green" /> Settings & System</h1>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={load} className="px-4 py-2 bg-border/30 border border-border rounded-lg">Reload</motion.button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glassmorphism rounded-xl p-4 space-y-3">
          <h2 className="text-lg font-semibold flex items-center gap-2"><KeyRound className="w-5 h-5" /> API Keys</h2>
          <label className="block text-sm text-text-muted">VirusTotal API Key</label>
          <input value={apiKeys.virustotal_api_key} onChange={e => setApiKeys({ ...apiKeys, virustotal_api_key: e.target.value })} className="w-full px-3 py-2 rounded bg-border/20 border border-border" />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-text-muted">ClamAV Host</label>
              <input value={apiKeys.clamav_host} onChange={e => setApiKeys({ ...apiKeys, clamav_host: e.target.value })} className="w-full px-3 py-2 rounded bg-border/20 border border-border" />
            </div>
            <div>
              <label className="block text-sm text-text-muted">ClamAV Port</label>
              <input type="number" value={apiKeys.clamav_port} onChange={e => setApiKeys({ ...apiKeys, clamav_port: Number(e.target.value) })} className="w-full px-3 py-2 rounded bg-border/20 border border-border" />
            </div>
          </div>
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={saveApiKeys} className="px-4 py-2 bg-neon-green/20 border border-neon-green/40 rounded-lg text-neon-green">Save API Keys</motion.button>
        </div>

        <div className="glassmorphism rounded-xl p-4 space-y-3">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Volume2 className="w-5 h-5" /> Notifications</h2>
          <label className="flex items-center gap-2"><input type="checkbox" checked={notifications.speech_enabled} onChange={e => setNotifications({ ...notifications, speech_enabled: e.target.checked })} /> Speech notifications</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={notifications.desktop_notifications} onChange={e => setNotifications({ ...notifications, desktop_notifications: e.target.checked })} /> Desktop notifications</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={notifications.email_notifications} onChange={e => setNotifications({ ...notifications, email_notifications: e.target.checked })} /> Email notifications</label>
          
          {notifications.email_notifications && (
            <div className="pl-6">
              <label className="block text-sm text-text-muted">Recipient Email</label>
              <input 
                type="email"
                value={notifications.recipient_email || ''} 
                onChange={e => setNotifications({ ...notifications, recipient_email: e.target.value })} 
                placeholder="your.email@example.com"
                className="w-full px-3 py-2 rounded bg-border/20 border border-border" 
              />
            </div>
          )}

          <div className="flex gap-2">
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={saveNotifications} className="px-4 py-2 bg-border/30 border border-border rounded-lg">Save</motion.button>
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={testSpeech} className="px-4 py-2 bg-neon-blue/20 border border-neon-blue/40 rounded-lg text-neon-blue">Test Speech</motion.button>
          </div>
        </div>
      </div>

      {settings && (
        <div className="glassmorphism rounded-xl p-4 space-y-3">
          <h2 className="text-lg font-semibold">Quick Toggles</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            <button onClick={() => saveSetting('organization.dry_run_by_default', !(settings.organization?.dry_run_by_default))} className="p-3 rounded bg-border/20 border border-border text-left">
              <div className="text-sm text-text-muted">Dry Run by Default</div>
              <div className="font-semibold">{settings.organization?.dry_run_by_default ? 'On' : 'Off'}</div>
            </button>
            <button onClick={() => saveSetting('scanning.auto_quarantine', !(settings.scanning?.auto_quarantine))} className="p-3 rounded bg-border/20 border border-border text-left">
              <div className="text-sm text-text-muted">Auto Quarantine</div>
              <div className="font-semibold">{settings.scanning?.auto_quarantine ? 'On' : 'Off'}</div>
            </button>
            <button onClick={() => saveSetting('ml_model.feature_extraction_enabled', !(settings.ml_model?.feature_extraction_enabled))} className="p-3 rounded bg-border/20 border border-border text-left">
              <div className="text-sm text-text-muted">Feature Extraction</div>
              <div className="font-semibold">{settings.ml_model?.feature_extraction_enabled ? 'On' : 'Off'}</div>
            </button>
            <button onClick={() => saveSetting('ui.compact_mode', !(settings.ui?.compact_mode))} className="p-3 rounded bg-border/20 border border-border text-left">
              <div className="text-sm text-text-muted">Compact Mode</div>
              <div className="font-semibold">{settings.ui?.compact_mode ? 'On' : 'Off'}</div>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings
