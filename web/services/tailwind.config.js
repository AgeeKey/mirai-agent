/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Стандартные цвета shadcn/ui
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Цветовая схема Mirai
        'mirai-dark': '#0B1622',
        'mirai-primary': '#00E2FF',
        'mirai-secondary': '#A076F9',
        'mirai-accent': '#FF6BC1',
        'mirai-success': '#36EABE',
        'mirai-warning': '#FFB800',
        'mirai-error': '#FF3A76',
        'mirai-panel': '#133D5A',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        'neon-primary': '0 0 20px rgba(0, 226, 255, 0.5)',
        'neon-secondary': '0 0 20px rgba(160, 118, 249, 0.5)',
        'neon-accent': '0 0 20px rgba(255, 107, 193, 0.5)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.37)',
        'cyber': '0 0 30px rgba(0, 226, 255, 0.3)',
      },
      backdropBlur: {
        'mirai': '16px',
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
        "holographic-shift": {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        "pulse-neon": {
          '0%, 100%': { 
            boxShadow: '0 0 0 0 rgba(0, 226, 255, 0.7)'
          },
          '50%': { 
            boxShadow: '0 0 0 20px rgba(0, 226, 255, 0)'
          },
        },
        "sakura-fall": {
          '0%': { 
            transform: 'translateY(-100vh) rotate(0deg)',
            opacity: '0'
          },
          '10%': { opacity: '0.7' },
          '90%': { opacity: '0.7' },
          '100%': { 
            transform: 'translateY(100vh) rotate(360deg)',
            opacity: '0'
          },
        },
        "cyber-scan": {
          '0%': { top: '0%', opacity: '0' },
          '5%': { opacity: '1' },
          '95%': { opacity: '1' },
          '100%': { top: '100%', opacity: '0' },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "holographic": "holographic-shift 3s ease infinite",
        "pulse-neon": "pulse-neon 2s ease-in-out infinite",
        "sakura": "sakura-fall linear infinite",
        "cyber-scan": "cyber-scan 3s linear infinite",
      },
    },
  },
  plugins: [],
}