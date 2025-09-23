'use client';

import { useEffect, useRef } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PortfolioData {
  labels: string[];
  datasets: {
    data: number[];
    backgroundColor: string[];
    borderColor: string[];
    borderWidth: number;
  }[];
}

interface PortfolioDistributionProps {
  data?: PortfolioData;
  title?: string;
  size?: number;
}

const PortfolioDistribution: React.FC<PortfolioDistributionProps> = ({
  data,
  title = 'Portfolio Distribution',
  size = 300
}) => {
  // Данные портфеля по умолчанию
  const defaultData: PortfolioData = {
    labels: ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'Cash'],
    datasets: [
      {
        data: [35, 25, 15, 10, 8, 7],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',   // Blue for BTC
          'rgba(34, 197, 94, 0.8)',    // Green for ETH
          'rgba(168, 85, 247, 0.8)',   // Purple for SOL
          'rgba(239, 68, 68, 0.8)',    // Red for ADA
          'rgba(251, 146, 60, 0.8)',   // Orange for DOT
          'rgba(156, 163, 175, 0.8)'   // Gray for Cash
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(34, 197, 94, 1)',
          'rgba(168, 85, 247, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(251, 146, 60, 1)',
          'rgba(156, 163, 175, 1)'
        ],
        borderWidth: 2
      }
    ]
  };

  const chartData = data || defaultData;

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: '#9ca3af',
          font: {
            size: 12
          },
          padding: 15,
          usePointStyle: true,
          generateLabels: function(chart: any) {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              return data.labels.map((label: string, index: number) => {
                const percentage = data.datasets[0].data[index];
                return {
                  text: `${label}: ${percentage}%`,
                  fillStyle: data.datasets[0].backgroundColor[index],
                  strokeStyle: data.datasets[0].borderColor[index],
                  lineWidth: 2,
                  pointStyle: 'circle',
                  hidden: false,
                  index: index
                };
              });
            }
            return [];
          }
        }
      },
      title: {
        display: true,
        text: title,
        color: '#f3f4f6',
        font: {
          size: 16,
          weight: 'bold' as const
        },
        padding: {
          bottom: 20
        }
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: '#f3f4f6',
        bodyColor: '#d1d5db',
        borderColor: '#374151',
        borderWidth: 1,
        cornerRadius: 8,
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed;
            return `${label}: ${value}% of portfolio`;
          }
        }
      }
    },
    cutout: '60%', // Создает эффект пончика
    animation: {
      animateRotate: true,
      animateScale: true,
      duration: 1000,
      easing: 'easeInOutQuart'
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
      <div style={{ height: size, position: 'relative' }}>
        <Doughnut data={chartData} options={options} />
        
        {/* Центральный текст */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              $105.8K
            </div>
            <div className="text-sm text-gray-400">
              Total Value
            </div>
          </div>
        </div>
      </div>
      
      {/* Дополнительная статистика */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-lg font-semibold text-green-400">+5.8%</div>
          <div className="text-xs text-gray-400">24h Change</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-blue-400">7</div>
          <div className="text-xs text-gray-400">Assets</div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioDistribution;