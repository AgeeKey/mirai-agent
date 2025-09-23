import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Mirai - Автономная торговая платформа",
  description: "Инновационная AI-платформа для автономной торговли на криптовалютных биржах с интеллектуальным управлением рисками",
  keywords: "криптотрейдинг, автономный AI, торговые боты, Binance, управление рисками",
  authors: [{ name: "AI Mirai Team" }],
  openGraph: {
    title: "AI Mirai - Автономная торговая платформа",
    description: "Инновационная AI-платформа для автономной торговли",
    url: "https://aimirai.info",
    siteName: "AI Mirai",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white`}
      >
        <div id="__next">
          {children}
        </div>
      </body>
    </html>
  );
}
