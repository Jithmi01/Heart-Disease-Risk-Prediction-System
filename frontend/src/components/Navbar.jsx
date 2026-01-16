import React, { useState } from 'react';
import { Heart, LogOut, User, Menu, X } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';

const Navbar = ({ onNavigate }) => {
  const { theme } = useTheme();
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  return (
    <header className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-lg sticky top-0 z-50`}>
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div 
            className="flex items-center gap-3 cursor-pointer" 
            onClick={() => onNavigate('dashboard')}
          >
            <Heart className="w-8 h-8 text-red-500" />
            <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
              Heart Care
            </h1>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-4">
            <ThemeToggle />
            
            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                  theme === 'dark' 
                    ? 'bg-gray-700 hover:bg-gray-600 text-white' 
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                }`}
              >
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                  {user?.name?.charAt(0).toUpperCase()}
                </div>
                <span className="font-medium">{user?.name}</span>
              </button>

              {showDropdown && (
                <div className={`absolute right-0 mt-2 w-48 rounded-lg shadow-xl ${
                  theme === 'dark' ? 'bg-gray-700' : 'bg-white'
                } overflow-hidden`}>
                  <button
                    onClick={() => {
                      onNavigate('profile');
                      setShowDropdown(false);
                    }}
                    className={`w-full px-4 py-3 text-left flex items-center gap-2 ${
                      theme === 'dark' 
                        ? 'hover:bg-gray-600 text-white' 
                        : 'hover:bg-gray-100 text-gray-800'
                    }`}
                  >
                    <User className="w-4 h-4" />
                    My Profile
                  </button>
                  <button
                    onClick={() => {
                      logout();
                      setShowDropdown(false);
                    }}
                    className="w-full px-4 py-3 text-left flex items-center gap-2 text-red-500 hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="md:hidden p-2"
          >
            {showMobileMenu ? (
              <X className={theme === 'dark' ? 'text-white' : 'text-gray-800'} />
            ) : (
              <Menu className={theme === 'dark' ? 'text-white' : 'text-gray-800'} />
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {showMobileMenu && (
          <div className="md:hidden mt-4 pb-4 space-y-2">
            <button
              onClick={() => {
                onNavigate('profile');
                setShowMobileMenu(false);
              }}
              className={`w-full px-4 py-2 rounded-lg text-left flex items-center gap-2 ${
                theme === 'dark' 
                  ? 'bg-gray-700 text-white' 
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <User className="w-4 h-4" />
              My Profile
            </button>
            <button
              onClick={() => {
                logout();
                setShowMobileMenu(false);
              }}
              className="w-full px-4 py-2 rounded-lg text-left flex items-center gap-2 bg-red-500 text-white"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Navbar;