import React from 'react';
import { useTheme } from '../context/ThemeContext';

const StatCard = ({ title, value, icon, color }) => {
  const { theme } = useTheme();
  const colors = {
    blue: 'bg-blue-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
    green: 'bg-green-500'
  };

  return (
    <div className={`p-6 rounded-xl shadow-lg ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {title}
          </p>
          <p className={`text-3xl font-bold mt-2 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
            {value}
          </p>
        </div>
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          {React.cloneElement(icon, { className: 'w-6 h-6 text-white' })}
        </div>
      </div>
    </div>
  );
};

export default StatCard;