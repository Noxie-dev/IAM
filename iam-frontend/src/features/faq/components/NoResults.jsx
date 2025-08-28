import React from 'react';
import { Search } from 'lucide-react';

/**
 * NoResults - Component displayed when no FAQs match the filters
 */
const NoResults = ({ onReset }) => {
  return (
    <section className="text-center py-16">
      <div className="w-24 h-24 bg-gradient-to-br from-gray-600 to-gray-700 rounded-full flex items-center justify-center mx-auto mb-6">
        <Search className="w-10 h-10 text-gray-400" />
      </div>
      <h3 className="text-2xl font-semibold text-white mb-4">No questions found</h3>
      <p className="text-gray-400 mb-8 max-w-md mx-auto">Try adjusting your search or browse a different category.</p>
      <button 
        onClick={onReset} 
        className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-6 py-3 rounded-xl font-medium transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/25"
        aria-label="Reset all filters and show all FAQ articles"
      >
        Reset Filters
      </button>
    </section>
  );
};

export default NoResults;

