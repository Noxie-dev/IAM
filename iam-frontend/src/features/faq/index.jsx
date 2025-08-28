import React, { useState, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './FAQ.css';

// Data imports
import { faqData } from './data.js';

// Hook imports
import { useDebounce } from './hooks/useDebounce.js';
import { useMousePosition } from './hooks/useMousePosition.js';

// Component imports
import AnimatedGradientBackground from './components/AnimatedGradientBackground.jsx';
import FAQHeader from './components/FAQHeader.jsx';
import CategorySelector from './components/CategorySelector.jsx';
import FAQCard from './components/FAQCard.jsx';
import NoResults from './components/NoResults.jsx';
import ContactCard from './components/ContactCard.jsx';
import FAQModal from './components/FAQModal.jsx';
import Footer from '../../components/layout/Footer.jsx';

/**
 * FAQPage - Main container component for the FAQ feature
 * Manages all state and logic, composes UI from child components
 */
const FAQPage = () => {
  const navigate = useNavigate();
  
  // State management
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedFAQ, setSelectedFAQ] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  
  // Refs
  const containerRef = useRef(null);
  
  // Custom hooks
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const mousePosition = useMousePosition(containerRef);

  // Memoized filtering logic to prevent re-calculation on every render
  const filteredFAQs = useMemo(() => {
    return faqData.filter(faq => {
      const lowercasedSearch = debouncedSearchTerm.toLowerCase();
      const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
      const matchesSearch = debouncedSearchTerm === '' || 
        faq.question.toLowerCase().includes(lowercasedSearch) ||
        faq.answer.toLowerCase().includes(lowercasedSearch) ||
        faq.tags.some(tag => tag.toLowerCase().includes(lowercasedSearch));
      return matchesCategory && matchesSearch;
    });
  }, [selectedCategory, debouncedSearchTerm]);

  // Calculate related FAQs for the modal
  const relatedFAQs = useMemo(() => {
    if (!selectedFAQ) return [];
    return selectedFAQ.relatedIds
      .map(id => faqData.find(f => f.id === id))
      .filter(Boolean);
  }, [selectedFAQ]);

  // Event handlers using useCallback for performance
  const handleCardClick = useCallback((faq) => setSelectedFAQ(faq), []);
  const closeModal = useCallback(() => setSelectedFAQ(null), []);
  const handleCategoryClick = useCallback((categoryId) => setSelectedCategory(categoryId), []);
  const handleTagClick = useCallback((tag) => {
    setSearchTerm(tag);
    closeModal();
  }, [closeModal]);
  const handleRelatedClick = useCallback((faq) => setSelectedFAQ(faq), []);
  const handleSearchChange = useCallback((value) => setSearchTerm(value), []);
  const handleSearchClear = useCallback(() => setSearchTerm(''), []);
  const handleSearchFocus = useCallback(() => setIsSearchFocused(true), []);
  const handleSearchBlur = useCallback(() => setIsSearchFocused(false), []);
  const handleReset = useCallback(() => {
    setSearchTerm('');
    setSelectedCategory('all');
  }, []);

  return (
    <div ref={containerRef} className="faq-container min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white relative overflow-hidden font-sans" style={{ colorScheme: 'dark' }}>
      <AnimatedGradientBackground mousePosition={mousePosition} />

      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-white/10">
        <nav className="flex items-center justify-between px-8 py-4 max-w-7xl mx-auto">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center space-x-4 hover:opacity-80 transition-opacity"
              aria-label="Go to home page"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold">IAM</div>
              <span className="text-xl font-semibold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent hidden sm:inline">Intelligent Audio Manager</span>
            </button>
          </div>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => navigate('/')}
              className="text-gray-300 hover:text-white transition-colors"
            >
              ← Back to Home
            </button>
            <button className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-5 py-2.5 rounded-lg font-medium transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/25">
              Get Started Free
            </button>
          </div>
        </nav>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        <FAQHeader
          searchTerm={searchTerm}
          onSearchChange={handleSearchChange}
          onSearchClear={handleSearchClear}
          isSearchFocused={isSearchFocused}
          onSearchFocus={handleSearchFocus}
          onSearchBlur={handleSearchBlur}
          totalArticles={faqData.length}
        />

        <CategorySelector
          selectedCategory={selectedCategory}
          onCategoryClick={handleCategoryClick}
        />

        {filteredFAQs.length > 0 ? (
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredFAQs.map((faq) => (
              <FAQCard 
                key={faq.id} 
                faq={faq} 
                onCardClick={handleCardClick} 
                onTagClick={handleTagClick} 
              />
            ))}
          </section>
        ) : (
          <NoResults onReset={handleReset} />
        )}

        <ContactCard />
      </main>

      <Footer />

      {selectedFAQ && (
        <FAQModal 
          faq={selectedFAQ} 
          relatedFAQs={relatedFAQs}
          onClose={closeModal} 
          onTagClick={handleTagClick} 
          onRelatedClick={handleRelatedClick} 
        />
      )}
    </div>
  );
};

export default FAQPage;
