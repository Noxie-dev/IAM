import React from 'react';
import { MessageCircle, ArrowRight } from 'lucide-react';

/**
 * ContactCard - Call-to-action section for contacting support
 */
const ContactCard = () => {
  return (
    <section className="mt-20">
      <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 backdrop-blur-sm border border-blue-500/20 rounded-3xl p-12 max-w-4xl mx-auto text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
          <MessageCircle className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">Still have questions?</h2>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-8">Our support team is available 24/7 to help you get the most out of IAM.</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button 
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-8 py-4 rounded-xl font-medium transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/25 flex items-center justify-center space-x-2"
            aria-label="Contact our support team"
          >
            <span>Contact Support</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </section>
  );
};

export default ContactCard;



