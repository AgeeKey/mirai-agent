import './globals.css'
import '../styles/mirai-theme.css'

export const metadata = { 
  title: "Mirai Agent - AI Trading Platform",
  description: "Autonomous trading system with anime-style interface",
  manifest: '/manifest.json',
  themeColor: '#0b1220',
  icons: {
    icon: '/icon-192.png',
    apple: '/icon-192.png'
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="bg-mirai-dark text-white font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
