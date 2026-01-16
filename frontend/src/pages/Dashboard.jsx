import React, { useState, useEffect } from 'react';
import { FileText, Activity, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from '../context/ThemeContext';
import api from '../config/api';
import Navbar from '../components/Navbar';
import StatCard from '../components/StatCard';
import AssessmentCard from '../components/AssessmentCard';

const Dashboard = ({ onNavigate }) => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const { theme } = useTheme();

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      const res = await api.get('/predictions');
      setPredictions(res.data);
    } catch (err) {
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (reportId) => {
    try {
      const res = await api.get(`/generate-report/${reportId}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `heart_report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading report:', err);
    }
  };

  const stats = {
    total: predictions.length,
    highRisk: predictions.filter(p => p.risk_level === 'High Risk').length,
    mediumRisk: predictions.filter(p => p.risk_level === 'Medium Risk').length,
    lowRisk: predictions.filter(p => p.risk_level === 'Low Risk').length
  };

  const chartData = [
    { name: 'High Risk', value: stats.highRisk, color: '#ef4444' },
    { name: 'Medium Risk', value: stats.mediumRisk, color: '#f59e0b' },
    { name: 'Low Risk', value: stats.lowRisk, color: '#10b981' }
  ];

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <Navbar onNavigate={onNavigate} />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
            Welcome to Your Dashboard
          </h2>
          <p className={`mt-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Track your heart health assessments and insights
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Assessments"
            value={stats.total}
            icon={<FileText />}
            color="blue"
          />
          <StatCard
            title="High Risk"
            value={stats.highRisk}
            icon={<AlertCircle />}
            color="red"
          />
          <StatCard
            title="Medium Risk"
            value={stats.mediumRisk}
            icon={<TrendingUp />}
            color="yellow"
          />
          <StatCard
            title="Low Risk"
            value={stats.lowRisk}
            icon={<CheckCircle />}
            color="green"
          />
        </div>

        {/* Chart & New Assessment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Risk Distribution Chart */}
          <div className={`p-6 rounded-xl shadow-lg ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
            <h2 className={`text-xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
              Risk Distribution
            </h2>
            {stats.total > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className={`text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  No assessments yet. Start your first assessment!
                </p>
              </div>
            )}
          </div>

          {/* New Assessment CTA */}
          <div className={`p-6 rounded-xl shadow-lg bg-gradient-to-br ${
            theme === 'dark' 
              ? 'from-blue-900 to-indigo-900' 
              : 'from-blue-50 to-indigo-50'
          } flex flex-col items-center justify-center`}>
            <Activity className={`w-20 h-20 mb-4 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-500'}`} />
            <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
              Ready for Assessment?
            </h2>
            <p className={`text-center mb-6 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
              Complete a new heart disease risk assessment
            </p>
            <button
              onClick={() => onNavigate('predict')}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold shadow-lg"
            >
              Start New Assessment
            </button>
          </div>
        </div>

        {/* Recent Assessments */}
        <div className={`p-6 rounded-xl shadow-lg ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
          <h2 className={`text-xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
            Recent Assessments
          </h2>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className={`mt-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Loading assessments...
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {predictions.slice(0, 5).map((pred) => (
                <AssessmentCard
                  key={pred._id}
                  prediction={pred}
                  onDownload={() => downloadReport(pred._id)}
                />
              ))}
              {predictions.length === 0 && (
                <p className={`text-center py-8 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  No assessments found. Start your first assessment!
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;