/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // NeonVault Color Palette
        'bg-dark': '#0D1117',
        'panel-dark': '#161B22',
        'neon-green': '#4ADE80',
        'neon-blue': '#3B82F6',
        'text-light': '#E5E7EB',
        'text-muted': '#9CA3AF',
        'border': '#30363D',
        'border-hover': '#4ADE80',
        'error': '#EF4444',
        'warning': '#F59E0B',
        'success': '#10B981'
      },
      boxShadow: {
        'neon-green': '0 0 20px rgba(74, 222, 128, 0.3)',
        'neon-blue': '0 0 20px rgba(59, 130, 246, 0.3)',
        'glassmorphism': '0 8px 32px rgba(31, 38, 135, 0.37)',
      },
      backdropBlur: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
      },
      animation: {
        'pulse-neon': 'pulse-neon 2s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan-line': 'scan-line 2s linear infinite',
      },
      keyframes: {
        'pulse-neon': {
          '0%': { 
            boxShadow: '0 0 5px rgba(74, 222, 128, 0.5), 0 0 10px rgba(74, 222, 128, 0.5), 0 0 15px rgba(74, 222, 128, 0.5)' 
          },
          '100%': { 
            boxShadow: '0 0 10px rgba(74, 222, 128, 0.8), 0 0 20px rgba(74, 222, 128, 0.8), 0 0 30px rgba(74, 222, 128, 0.8)' 
          },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'glow': {
          '0%': { opacity: '0.5' },
          '100%': { opacity: '1' },
        },
        'scan-line': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(400px)' },
        },
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}