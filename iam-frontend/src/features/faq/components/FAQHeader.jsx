import React from 'react';
import { Search, X, Sparkles } from 'lucide-react';

/**
 * FAQHeader - Header section with title, description, and search bar
 */
const FAQHeader = ({ 
  searchTerm, 
  onSearchChange, 
  onSearchClear, 
  isSearchFocused, 
  onSearchFocus, 
  onSearchBlur,
  totalArticles 
}) => {
  return (
    <section className="text-center mb-16">
      <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-full px-6 py-2 mb-8 backdrop-blur-sm border border-blue-500/20">
        <Sparkles className="w-4 h-4 text-blue-400" />
        <span className="text-sm text-blue-300">Knowledge Base • {totalArticles} Articles</span>
      </div>
      <h1 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">
        How can we help?
      </h1>
      <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-12">
        Find answers to common questions about our AI-powered transcription platform.
      </p>
      <div className="max-w-2xl mx-auto relative">
        <div className={`relative transition-all duration-300 ${isSearchFocused ? 'scale-105' : ''}`}>
          <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-colors ${isSearchFocused ? 'text-blue-400' : 'text-gray-500'}`} size={20} />
          <input
            type="text"
            placeholder="Search for answers... (e.g., 'POPIA', 'API', 'export')"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            onFocus={onSearchFocus}
            onBlur={onSearchBlur}
            className={`w-full pl-12 pr-12 py-4 bg-white/5 backdrop-blur-sm border rounded-xl text-white placeholder-gray-400 focus:outline-none transition-all duration-300 ${isSearchFocused ? 'border-blue-500 bg-white/10 shadow-lg shadow-blue-500/20' : 'border-gray-600 hover:border-gray-500'}`}
            aria-label="Search FAQ articles"
          />
          {searchTerm && (
            <button 
              onClick={onSearchClear} 
              className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
              aria-label="Clear search"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>
    </section>
  );
};

export default FAQHeader;

