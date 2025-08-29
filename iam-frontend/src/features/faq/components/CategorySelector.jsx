import React from 'react';
import { categories, faqData } from '../data.js';

/**
 * CategorySelector - Category filter buttons
 */
const CategorySelector = ({ selectedCategory, onCategoryClick }) => {
  return (
    <section className="flex flex-wrap justify-center gap-3 mb-12">
      {categories.map((category) => {
        const count = category.id === 'all' ? faqData.length : faqData.filter(f => f.category === category.id).length;
        return (
          <button
            key={category.id}
            onClick={() => onCategoryClick(category.id)}
            className={`group flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-300 hover:scale-105 ${selectedCategory === category.id ? `bg-gradient-to-r ${category.color} text-white shadow-lg` : 'bg-white/5 text-gray-300 hover:bg-white/10 hover:text-white border border-gray-700 hover:border-gray-600'}`}
            aria-label={`Filter by ${category.name} category, ${count} articles`}
            aria-pressed={selectedCategory === category.id}
          >
            <category.icon size={18} />
            <span>{category.name}</span>
            <span className={`px-2 py-0.5 rounded-full text-xs ${selectedCategory === category.id ? 'bg-white/20' : 'bg-gray-700/50'}`}>{count}</span>
          </button>
        );
      })}
    </section>
  );
};

export default CategorySelector;



