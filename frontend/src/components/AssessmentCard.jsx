import React from 'react';
import { Download, Calendar, Clock } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const AssessmentCard = ({ prediction, onDownload }) => {
  const { theme } = useTheme();
  const date = new Date(prediction.created_at);
  const patientName = prediction.patient_details?.name || 'Unknown Patient';

  return (
    <div className={`p-4 rounded-lg border ${
      theme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
              {patientName}
            </span>
            <span
              className="px-3 py-1 rounded-full text-sm font-semibold text-white"
              style={{ backgroundColor: prediction.risk_color }}
            >
              {prediction.risk_level}
            </span>
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              {prediction.probability}% probability
            </span>
          </div>
          <div className={`flex items-center gap-4 text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {date.toLocaleDateString()}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {date.toLocaleTimeString()}
            </span>
          </div>
        </div>
        <button
          onClick={onDownload}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          <Download className="w-4 h-4" />
          Download
        </button>
      </div>
    </div>
  );
};

export default AssessmentCard;