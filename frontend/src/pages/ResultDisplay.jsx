
import React from 'react';
import {  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Download } from "lucide-react"; 
import { useTheme } from '../context/ThemeContext';
import Navbar from '../components/Navbar';
import RecommendationSection from '../components/RecommendationSection';

const ResultDisplay = ({ result, formData, onDownload, onBack, onDashboard }) => {
  const { theme } = useTheme();

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <Navbar onNavigate={onDashboard} />
      
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className={`p-8 rounded-xl shadow-lg mb-6 ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
          {/* Patient Name Header */}
          {formData.patientName && (
            <div className="mb-6">
              <h2 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
                Assessment Report for {formData.patientName}
              </h2>
              {formData.patientPhone && (
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  Contact: {formData.patientPhone}
                </p>
              )}
            </div>
          )}
          
          {/* Risk Level */}
          <div className="text-center mb-8">
            <div
              className="inline-block px-8 py-4 rounded-2xl text-white text-3xl font-bold mb-4 shadow-lg"
              style={{ backgroundColor: result.risk_color }}
            >
              {result.risk_level}
            </div>
            <p className={`text-xl ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
              Probability: {result.probability}%
            </p>
          </div>

          {/* Risk Factors Chart */}
          <div className="mb-8">
            <h3 className={`text-xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
              Contributing Risk Factors
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={result.risk_factors}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#e5e7eb'} />
                <XAxis dataKey="factor" stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'} />
                <YAxis stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                    border: `1px solid ${theme === 'dark' ? '#374151' : '#e5e7eb'}`,
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="contribution" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Recommendations */}
          <div className="space-y-6">
            <div className={`p-4 rounded-lg border-2 ${
              result.risk_level === 'High Risk' ? 'bg-red-50 border-red-300' :
              result.risk_level === 'Medium Risk' ? 'bg-yellow-50 border-yellow-300' :
              'bg-green-50 border-green-300'
            }`}>
              <p className="font-semibold text-gray-800 text-lg">
                {result.recommendations.immediate_action}
              </p>
            </div>

            <RecommendationSection
              title="Lifestyle Modifications"
              items={result.recommendations.lifestyle}
            />
            <RecommendationSection
              title="Dietary Recommendations"
              items={result.recommendations.diet}
            />
            <RecommendationSection
              title="Exercise Guidelines"
              items={result.recommendations.exercise}
            />
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-4 mt-8">
            <button
              onClick={onDownload}
              className="flex-1 min-w-[200px] flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-lg"
            >
              <Download className="w-5 h-5" />
              Download PDF Report
            </button>
            <button
              onClick={onDashboard}
              className={`px-6 py-3 rounded-lg transition ${
                theme === 'dark'
                  ? 'bg-gray-700 text-white hover:bg-gray-600'
                  : 'bg-gray-600 text-white hover:bg-gray-700'
              }`}
            >
              Go to Dashboard
            </button>
            <button
              onClick={onBack}
              className={`px-6 py-3 rounded-lg transition ${
                theme === 'dark'
                  ? 'bg-gray-700 text-white hover:bg-gray-600'
                  : 'bg-gray-600 text-white hover:bg-gray-700'
              }`}
            >
              New Assessment
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultDisplay;

