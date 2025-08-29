/**
 * Example usage of the refactored FAQ feature
 * 
 * This file demonstrates how to integrate the FAQ feature
 * into your application and customize its behavior.
 */

import React from 'react';
import FAQPage from './index.jsx';

// Basic usage
export function BasicFAQExample() {
  return (
    <div className="min-h-screen">
      <FAQPage />
    </div>
  );
}

// Example of using individual components for custom layouts
import FAQHeader from './components/FAQHeader.jsx';
import CategorySelector from './components/CategorySelector.jsx';
import FAQCard from './components/FAQCard.jsx';
import { faqData } from './data.js';

export function CustomFAQLayout() {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('all');
  const [isSearchFocused, setIsSearchFocused] = React.useState(false);

  return (
    <div className="custom-faq-layout">
      {/* Custom header layout */}
      <div className="bg-gray-900 py-16">
        <div className="max-w-4xl mx-auto px-6">
          <FAQHeader
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            onSearchClear={() => setSearchTerm('')}
            isSearchFocused={isSearchFocused}
            onSearchFocus={() => setIsSearchFocused(true)}
            onSearchBlur={() => setIsSearchFocused(false)}
            totalArticles={faqData.length}
          />
        </div>
      </div>

      {/* Category selector in sidebar */}
      <div className="flex">
        <aside className="w-64 bg-gray-800 p-6">
          <CategorySelector
            selectedCategory={selectedCategory}
            onCategoryClick={setSelectedCategory}
          />
        </aside>
        
        <main className="flex-1 p-6">
          {/* Custom FAQ grid */}
          <div className="grid gap-4">
            {faqData
              .filter(faq => selectedCategory === 'all' || faq.category === selectedCategory)
              .map(faq => (
                <FAQCard
                  key={faq.id}
                  faq={faq}
                  onCardClick={() => console.log('FAQ clicked:', faq)}
                  onTagClick={(tag) => setSearchTerm(tag)}
                />
              ))}
          </div>
        </main>
      </div>
    </div>
  );
}

// Example of extending with custom data
import { categories } from './data.js';

const customFAQData = [
  {
    id: 100,
    category: 'custom',
    question: 'How do I use the refactored FAQ components?',
    answer: 'The refactored FAQ feature provides modular components that can be used individually or together. Import the components you need and compose them in your application.',
    tags: ['components', 'architecture', 'usage'],
    helpful: { yes: 0, no: 0 },
    relatedIds: []
  }
];

const customCategories = [
  ...categories,
  { 
    id: 'custom', 
    name: 'Custom', 
    icon: 'Star', 
    color: 'from-yellow-500 to-yellow-600' 
  }
];

export function ExtendedFAQExample() {
  // You can extend the data by combining with custom data
  const combinedData = [...faqData, ...customFAQData];
  
  return (
    <div>
      {/* Use the extended data in your components */}
      <p>Extended FAQ with {combinedData.length} articles</p>
      {/* Render your custom FAQ implementation */}
    </div>
  );
}



