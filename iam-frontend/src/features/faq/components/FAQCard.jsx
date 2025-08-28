import React from 'react';
import { ThumbsUp, ArrowRight } from 'lucide-react';

/**
 * FAQCard - Displays a single FAQ item.
 * It's memoized for performance, only re-rendering when its own props change.
 */
const FAQCard = React.memo(({ faq, onCardClick, onTagClick }) => {
  const totalVotes = faq.helpful.yes + faq.helpful.no;
  const helpfulPercentage = totalVotes > 0 ? Math.round((faq.helpful.yes / totalVotes) * 100) : 0;

  return (
    <div
      className="group bg-gradient-to-br from-white/5 to-white/0 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-white/10 hover:border-gray-600 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-1 transform flex flex-col"
      onClick={() => onCardClick(faq)}
    >
      <div className="flex-grow">
        <h3 className="text-lg font-semibold text-white group-hover:text-blue-100 transition-colors cursor-pointer mb-3">
          {faq.question}
        </h3>
        <p className="text-gray-400 text-sm mb-4 group-hover:text-gray-300 transition-colors">
          {`${faq.answer.substring(0, 120)}...`}
        </p>
      </div>
      <div className="flex flex-wrap gap-2 mt-auto">
        {faq.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            onClick={(e) => { e.stopPropagation(); onTagClick(tag); }}
            className="px-2.5 py-1 text-xs rounded-full bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-blue-300 border border-blue-500/20 cursor-pointer hover:bg-blue-600/30 transition-colors"
          >
            {tag}
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between text-xs text-gray-500 pt-4 mt-4 border-t border-gray-700/50">
        <div className="flex items-center space-x-1">
          <ThumbsUp className="w-3 h-3" />
          <span>{helpfulPercentage}% helpful</span>
        </div>
        <div className="flex items-center space-x-1 text-blue-400">
          <span>View details</span>
          <ArrowRight className="w-3 h-3 transform group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </div>
  );
});

FAQCard.displayName = 'FAQCard';

export default FAQCard;

