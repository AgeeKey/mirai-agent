import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  ChartBarIcon, 
  BookOpenIcon, 
  PresentationChartLineIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline'

const Navigation = () => {
  const location = useLocation()
  
  const navigation = [
    { name: 'Дашборд', href: '/', icon: HomeIcon },
    { name: 'Торговля', href: '/trading', icon: ChartBarIcon },
    { name: 'Дневник', href: '/diary', icon: BookOpenIcon },
    { name: 'Аналитика', href: '/analytics', icon: PresentationChartLineIcon },
  ]

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <CpuChipIcon className="h-8 w-8 text-mirai-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">Mirai</span>
              <span className="ml-1 text-sm text-gray-500">Trading Platform</span>
            </div>
            
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      isActive
                        ? 'border-mirai-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>
          
          <div className="flex items-center">
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Online</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation