import React from 'react';
import { Heart, Shield, Activity, TrendingUp, ArrowRight } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import ThemeToggle from '../components/ThemeToggle';
import homeImg from '../img/homeimg.png';

const HomePage = ({ onNavigate }) => {
  const { theme } = useTheme();

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-blue-100'}`}>
      {/* Header */}
      <header className={`${theme === 'dark' ? 'bg-gray-800/50' : 'bg-white/80'} backdrop-blur-md sticky top-0 z-50`}>
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Heart className="w-8 h-8 text-red-500" />
            <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
              Heart Care AI
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <button
              onClick={() => onNavigate('login')}
              className={`px-6 py-2 rounded-lg font-semibold transition text-white  ${
                theme === 'dark'
                ? 'bg-green-700 text-white hover:bg-green-500'
                : 'bg-green-600 text-gray-700 hover:bg-green-500'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => onNavigate('register')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Sign Up
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className={`text-5xl font-bold mb-6 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              AI-Powered Heart Disease Risk Assessment
            </h2>
            <p className={`text-xl mb-8 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
              Get instant, accurate predictions using advanced machine learning. 
              Take control of your heart health today with personalized recommendations.
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => onNavigate('register')}
                className="px-8 py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition flex items-center gap-2 text-lg"
              >
                Get Started
                <ArrowRight className="w-5 h-5" />
              </button>
              <button
                onClick={() => onNavigate('login')}
                className={`px-8 py-4 rounded-lg font-semibold transition text-lg text-white ${
                  theme === 'dark'
                    ? 'bg-green-700 text-white hover:bg-green-500'
                    : 'bg-green-600 text-gray-700 hover:bg-green-500'
                  }`}
              >
                Sign In
              </button>
            </div>
          </div>
          <div className="relative">
            <div className="w-full h-96 rounded-2xl overflow-hidden shadow-2xl">
              <img 
                src={homeImg} 
                alt="Heart Care AI" 
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className={`py-20 ${theme === 'dark' ? 'bg-gray-800/50' : 'bg-white'}`}>
        <div className="max-w-7xl mx-auto px-4">
          <h3 className={`text-4xl font-bold text-center mb-12 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Why Choose Heart Care AI?
          </h3>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Shield className="w-12 h-12" />}
              title="Accurate Predictions"
              description="Our advanced ML model provides highly accurate risk assessments based on clinical data."
              color="blue"
            />
            <FeatureCard
              icon={<Activity className="w-12 h-12" />}
              title="Personalized Insights"
              description="Get tailored health recommendations based on your unique risk profile."
              color="red"
            />
            <FeatureCard
              icon={<TrendingUp className="w-12 h-12" />}
              title="Track Progress"
              description="Monitor your heart health over time with detailed reports and analytics."
              color="green"
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 py-20">
        <div className={`rounded-2xl p-12 text-center ${
          theme === 'dark'
            ? 'bg-gradient-to-r from-blue-900 to-indigo-900'
            : 'bg-gradient-to-r from-blue-600 to-indigo-600'
        }`}>
          <h3 className="text-4xl font-bold text-white mb-4">
            Ready to Take Control of Your Heart Health?
          </h3>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of users who trust Heart Care AI for their health assessments.
          </p>
          <button
            onClick={() => onNavigate('register')}
            className="px-10 py-4 bg-white text-blue-600 rounded-lg font-bold hover:bg-gray-100 transition text-lg"
          >
            Start Your Free Assessment
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-100'} py-8`}>
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
            © 2026 Heart Care AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

const FeatureCard = ({ icon, title, description, color }) => {
  const { theme } = useTheme();
  const colors = {
    blue: 'text-blue-500',
    red: 'text-red-500',
    green: 'text-green-500'
  };

  return (
    <div className={`p-8 rounded-xl ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'} hover:shadow-xl transition`}>
      <div className={`${colors[color]} mb-4`}>
        {icon}
      </div>
      <h4 className={`text-xl font-bold mb-3 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
        {title}
      </h4>
      <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
        {description}
      </p>
    </div>
  );
};

export default HomePage;