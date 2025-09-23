'use client';

import { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Регистрируем компоненты Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
    tension?: number;
  }[];
}

interface PerformanceChartProps {
  type: 'line' | 'bar';
  data?: ChartData;
  title?: string;
  height?: number;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({
  type = 'line',
  data,
  title = 'Performance Chart',
  height = 300
}) => {
  // Данные по умолчанию для демонстрации
  const defaultData: ChartData = {
    labels: [
      '6:00', '9:00', '12:00', '15:00', '18:00', '21:00', '24:00'
    ],
    datasets: [
      {
        label: 'Portfolio Value (USDT)',
        data: [100000, 101500, 99800, 102300, 104600, 103200, 105800],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'BTC Price',
        data: [67000, 67200, 66800, 68100, 68500, 67900, 68200],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: false,
        tension: 0.4
      }
    ]
  };

  const chartData = data || defaultData;

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#9ca3af',
          font: {
            size: 12
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
        }
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: '#f3f4f6',
        bodyColor: '#d1d5db',
        borderColor: '#374151',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(55, 65, 81, 0.3)',
          borderColor: '#374151'
        },
        ticks: {
          color: '#9ca3af',
          font: {
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(55, 65, 81, 0.3)',
          borderColor: '#374151'
        },
        ticks: {
          color: '#9ca3af',
          font: {
            size: 11
          },
          callback: function(value: any) {
            return '$' + value.toLocaleString();
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index' as const
    }
  };

  return (
    <div 
      className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
      style={{ height: height + 80 }}
    >
      <div style={{ height }}>
        {type === 'line' ? (
          <Line data={chartData} options={options} />
        ) : (
          <Bar data={chartData} options={options} />
        )}
      </div>
    </div>
  );
};

export default PerformanceChart;