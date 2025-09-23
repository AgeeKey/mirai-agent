# AI Mirai Frontend

Современный веб-интерфейс для автономной торговой платформы AI Mirai, построенный на Next.js 15 с TypeScript и Tailwind CSS.

## 🚀 Функциональность

### Основные страницы
- **Главная страница** (`/`) - Лендинг с информацией о платформе
- **Регистрация** (`/register`) - Создание нового аккаунта
- **Вход** (`/login`) - Авторизация пользователей
- **Dashboard** (`/dashboard`) - Личный кабинет с торговой аналитикой

### Ключевые компоненты
- **WebSocket Manager** - Реальное время соединение с торговым сервером
- **Notification System** - Система уведомлений о сделках и сигналах
- **System Status** - Мониторинг статуса всех сервисов
- **API Client** - Интеграция с backend REST API

## 🛠 Технологический стек

- **Next.js 15.5.3** - React framework с App Router
- **React 19** - UI библиотека
- **TypeScript** - Статическая типизация
- **Tailwind CSS 3.4** - Utility-first CSS framework
- **Framer Motion** - Анимации и transitions
- **Heroicons** - SVG иконки
- **Headless UI** - Unstyled UI компоненты

## 🏗️ Архитектура

```
src/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Trading dashboard
│   ├── login/            # Login page
│   ├── register/         # Registration page
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Home page
├── components/           # Reusable components
│   ├── ApiClient.tsx     # API integration
│   ├── NotificationManager.tsx
│   ├── SystemStatus.tsx
│   └── WebSocketManager.tsx
└── globals.css          # Global styles
```

## ⚙️ Конфигурация

### Environment Variables
```bash
NEXT_PUBLIC_API_BASE=https://aimirai.online
NEXT_PUBLIC_SITE_URL=https://aimirai.info
```

### Next.js Configuration
- Automatic API rewrites to backend server
- HTTPS redirect and security headers via nginx
- WebSocket proxy support
- Optimized font loading

## 🔗 Интеграция

### Backend API Endpoints
- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /portfolio/stats` - Portfolio statistics
- `GET /portfolio/positions` - Active positions
- `GET /trading/signals` - AI trading signals
- `POST /trading/status` - Trading on/off
- `GET /health` - System health check

### WebSocket Events
- `signal` - New AI trading signal
- `trade_executed` - Trade confirmation
- `portfolio_update` - Portfolio changes
- `system_status` - System state changes

## 🎨 UI/UX Features

### Design System
- **Dark theme** с градиентами purple/blue/green
- **Responsive design** для всех устройств
- **Modern animations** с Framer Motion
- **Accessible components** с Headless UI

### Real-time Features
- Live trading clock
- Real-time portfolio updates
- WebSocket connection status
- System health monitoring
- Push notifications

## 🚀 Развертывание

### Production Setup
```bash
# Build optimized version
npm run build

# Start production server
npm start
```

### SSL & Security
- HTTPS через Let's Encrypt certificates
- Security headers (HSTS, CSP, etc.)
- CORS configuration для API
- Rate limiting через nginx

## 🔧 Разработка

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Build Commands
```bash
npm run dev      # Development server (port 3000)
npm run build    # Production build
npm run start    # Production server
npm run lint     # ESLint check
```

## 📱 Responsive Breakpoints

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px
- **Large**: > 1280px

## 🔐 Security

### Frontend Security
- Content Security Policy headers
- XSS protection
- CSRF token handling
- Secure cookie settings
- Input validation

### API Security
- JWT token authentication
- Request timeout handling
- Error boundary protection
- Secure storage practices

## 📊 Performance

### Optimizations
- Server-side rendering (SSR)
- Static generation где возможно
- Automatic code splitting
- Image optimization
- Font preloading
- CSS optimization

### Monitoring
- Real-time error tracking
- Performance metrics
- User interaction analytics
- API response monitoring

## 🎯 Future Roadmap

### Planned Features
- **Trading Charts** - Interactive price charts
- **Advanced Analytics** - Detailed trading reports  
- **Mobile App** - React Native version
- **Multi-language** - Internationalization
- **Dark/Light Theme** - Theme switcher
- **Telegram Integration** - Bot commands

### Technical Improvements
- Progressive Web App (PWA)
- Service Worker для offline
- GraphQL integration
- Real-time collaboration
- Advanced caching strategies

## 🤝 Contributing

При разработке следуйте установленным паттернам:
- TypeScript для всех компонентов
- Tailwind CSS для стилей
- Framer Motion для анимаций
- Responsive design обязателен
- Accessibility guidelines

## 📄 License

© 2025 AI Mirai. Все права защищены.
