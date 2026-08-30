/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        hospital: {
          dark: '#0B132B',
          surface: '#111D3E',
          card: '#1C2951',
          border: '#283868',
        },
        acuity: {
          l1: '#EF4444', // Resuscitation (Red)
          l2: '#F97316', // Emergent (Orange)
          l3: '#F59E0B', // Urgent (Amber)
          l4: '#10B981', // Less Urgent (Emerald)
          l5: '#3B82F6', // Non-Urgent (Blue)
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      }
    },
  },
  plugins: [],
}
