import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Footer - Reusable footer component for FAQ and Contact pages
 */
const Footer = () => {
  const navigate = useNavigate();

  return (
    <footer className="bg-slate-900/90 backdrop-blur-md border-t border-white/10 mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                IAM
              </div>
              <span className="text-xl font-semibold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Intelligent Audio Manager
              </span>
            </div>
            <p className="text-gray-400 max-w-xs">
              Professional AI-powered transcription for South African businesses
            </p>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-white">Quick Links</h4>
            <nav className="flex flex-col space-y-2">
              <button 
                onClick={() => navigate('/')}
                className="text-gray-400 hover:text-white transition-colors text-left"
              >
                Home
              </button>
              <button 
                onClick={() => navigate('/faq')}
                className="text-gray-400 hover:text-white transition-colors text-left"
              >
                FAQ
              </button>
              <button 
                onClick={() => navigate('/')}
                className="text-gray-400 hover:text-white transition-colors text-left"
              >
                Features
              </button>
              <button 
                onClick={() => navigate('/')}
                className="text-gray-400 hover:text-white transition-colors text-left"
              >
                Pricing
              </button>
            </nav>
          </div>

          {/* Contact Information */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-white">Contact Us</h4>
            <div className="space-y-2">
              <a 
                href="tel:0823982486" 
                className="text-gray-400 hover:text-white transition-colors flex items-center space-x-2"
              >
                <span>📞</span>
                <span>082 398 2486</span>
              </a>
              <a 
                href="mailto:info@iam.co.za" 
                className="text-gray-400 hover:text-white transition-colors flex items-center space-x-2"
              >
                <span>✉️</span>
                <span>info@iam.co.za</span>
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-white/10 mt-8 pt-8 text-center">
          <p className="text-gray-500 text-sm">
            © 2025 IAM - In A Meeting. All rights reserved. | POPIA Compliant
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
