import { motion } from 'framer-motion'

const ProgressRing = ({ 
  progress = 0, 
  size = 120, 
  strokeWidth = 8, 
  className = '',
  showPercentage = true,
  color = 'neon-green',
  children 
}) => {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const strokeDasharray = `${circumference} ${circumference}`
  const strokeDashoffset = circumference - (progress / 100) * circumference

  const colorClasses = {
    'neon-green': 'stroke-neon-green',
    'neon-blue': 'stroke-neon-blue', 
    'warning': 'stroke-warning',
    'error': 'stroke-error',
    'success': 'stroke-success'
  }

  const glowClasses = {
    'neon-green': 'drop-shadow-[0_0_8px_rgba(74,222,128,0.6)]',
    'neon-blue': 'drop-shadow-[0_0_8px_rgba(59,130,246,0.6)]',
    'warning': 'drop-shadow-[0_0_8px_rgba(245,158,11,0.6)]',
    'error': 'drop-shadow-[0_0_8px_rgba(239,68,68,0.6)]',
    'success': 'drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]'
  }

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
      >
        {/* Background Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="text-border opacity-30"
        />
        
        {/* Progress Circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={circumference}
          strokeLinecap="round"
          className={`${colorClasses[color]} ${glowClasses[color]} transition-all duration-300`}
          animate={{
            strokeDashoffset: strokeDashoffset
          }}
          transition={{
            duration: 0.8,
            ease: "easeInOut"
          }}
        />
      </svg>
      
      {/* Center Content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children || (showPercentage && (
          <div className="text-center">
            <div className={`text-2xl font-bold ${colorClasses[color].replace('stroke-', 'text-')}`}>
              {Math.round(progress)}%
            </div>
            <div className="text-xs text-text-muted mt-1">
              Complete
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ProgressRing