import React, { useState, useEffect, useCallback } from 'react';
import { X, Check, Copy, ThumbsUp, ThumbsDown, ArrowRight } from 'lucide-react';
import { categories } from '../data.js';

/**
 * FAQModal - A detailed view for a selected FAQ.
 * Enhanced with accessibility features and keyboard navigation.
 */
const FAQModal = ({ faq, relatedFAQs, onClose, onTagClick, onRelatedClick }) => {
  const [copied, setCopied] = useState(false);
  const [vote, setVote] = useState(null);

  // Effect to reset state when the modal opens for a new FAQ
  useEffect(() => {
    setCopied(false);
    setVote(null);
  }, [faq]);

  // Enhanced accessibility: Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  // Focus trapping for accessibility
  useEffect(() => {
    const modal = document.querySelector('[role="dialog"]');
    if (!modal) return;

    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    modal.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      modal.removeEventListener('keydown', handleTabKey);
    };
  }, [faq]);

  const handleCopy = useCallback(() => {
    const url = `${window.location.href.split('#')[0]}#faq-${faq.id}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [faq.id]);

  if (!faq) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
    >
      <div 
        className="bg-gradient-to-br from-slate-800 to-slate-900 border border-gray-700 rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl shadow-blue-500/10"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <h2 
                id="modal-title"
                className="text-3xl font-bold text-white leading-tight mb-4"
              >
                {faq.question}
              </h2>
              <div className="flex items-center space-x-3">
                <div className="px-4 py-1 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-full border border-blue-500/20">
                  <span className="text-sm text-blue-300 capitalize">
                    {categories.find(cat => cat.id === faq.category)?.name || 'General'}
                  </span>
                </div>
                <button 
                  onClick={handleCopy} 
                  className="flex items-center space-x-2 text-sm text-gray-400 hover:text-white transition-colors"
                  aria-label={copied ? 'Link copied to clipboard' : 'Copy link to this FAQ'}
                >
                  {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
                  <span>{copied ? 'Link Copied!' : 'Copy Link'}</span>
                </button>
              </div>
            </div>
            <button
              onClick={onClose}
              className="ml-4 w-10 h-10 bg-gray-700 hover:bg-gray-600 rounded-full flex items-center justify-center transition-colors text-gray-400 hover:text-white flex-shrink-0"
              aria-label="Close modal"
            >
              <X size={20} />
            </button>
          </div>
          
          <div 
            id="modal-description"
            className="prose prose-lg prose-invert max-w-none text-gray-300 leading-relaxed mb-8"
          >
            {faq.answer}
          </div>
          
          <div className="border-t border-gray-700 pt-6">
            <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Related Tags</h4>
            <div className="flex flex-wrap gap-3 mb-8">
              {faq.tags.map((tag) => (
                <button
                  key={tag}
                  className="px-4 py-2 text-sm rounded-full bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-blue-300 border border-blue-500/20 hover:bg-blue-600/30 transition-colors cursor-pointer"
                  onClick={() => onTagClick(tag)}
                  aria-label={`Search for ${tag}`}
                >
                  {tag}
                </button>
              ))}
            </div>

            {relatedFAQs && relatedFAQs.length > 0 && (
              <>
                <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Related Questions</h4>
                <div className="space-y-3 mb-8">
                  {relatedFAQs.map(relatedFaq => (
                    <button 
                      key={relatedFaq.id} 
                      onClick={() => onRelatedClick(relatedFaq)}
                      className="text-blue-400 hover:text-blue-300 transition-colors cursor-pointer flex items-center space-x-2 w-full text-left"
                      aria-label={`View related question: ${relatedFaq.question}`}
                    >
                      <ArrowRight size={14} />
                      <span>{relatedFaq.question}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
            
            <div className="flex flex-col sm:flex-row gap-4 bg-white/5 p-6 rounded-xl border border-gray-700/50">
              <p className="flex-1 text-gray-300 my-auto">Was this article helpful?</p>
              <div className="flex items-center space-x-3">
                <button 
                  onClick={() => setVote('yes')}
                  className={`px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center space-x-2 ${vote === 'yes' ? 'bg-emerald-500 text-white' : 'border border-gray-600 hover:border-gray-500 hover:bg-white/5 text-gray-300 hover:text-white'}`}
                  aria-label="Mark this article as helpful"
                >
                  <ThumbsUp className="w-4 h-4" />
                  <span>Yes</span>
                </button>
                <button 
                  onClick={() => setVote('no')}
                  className={`px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center space-x-2 ${vote === 'no' ? 'bg-red-500 text-white' : 'border border-gray-600 hover:border-gray-500 hover:bg-white/5 text-gray-300 hover:text-white'}`}
                  aria-label="Mark this article as not helpful"
                >
                  <ThumbsDown className="w-4 h-4" />
                  <span>No</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FAQModal;



