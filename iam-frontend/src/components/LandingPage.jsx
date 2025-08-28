import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';
// Assuming Button and Crown are correctly set up in your project
// If not, you might need to replace them with standard button/icon elements
// For example: import { Crown } from 'lucide-react';
// For example: const Button = ({ children, ...props }) => <button {...props}>{children}</button>;

// A placeholder for the Button component if you don't have one from a UI library
const Button = ({ children, className, onClick, disabled }) => (
  <button className={className} onClick={onClick} disabled={disabled}>
    {children}
  </button>
);

// A placeholder for the Crown icon if lucide-react is not installed
const Crown = ({ className }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14" />
  </svg>
);


const LandingPage = ({ onLogin, onSignup }) => {
  const navigate = useNavigate();
  const [motionEnabled, setMotionEnabled] = useState(true);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);


  // Modal states
  const [showContactModal, setShowContactModal] = useState(false);
  const [showComingSoonModal, setShowComingSoonModal] = useState(null);

  // Contact form states
  const [contactStep, setContactStep] = useState(1);
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [contactErrors, setContactErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Check for user preference on reduced motion
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      setMotionEnabled(false);
    }
  }, []);

  // Mouse move handler for interactive effects
  const handleMouseMove = (e) => {
    if (!motionEnabled) return;
    
    setMousePosition({ x: e.clientX, y: e.clientY });
    setIsHovering(true);
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
  };

  const toggleMotion = () => {
    setMotionEnabled(!motionEnabled);
  };

  // Contact form validation
  const validateContactStep = (step) => {
    const errors = {};

    switch (step) {
      case 1:
        if (!contactForm.name.trim()) {
          errors.name = 'Name is required';
        } else if (contactForm.name.trim().length < 2) {
          errors.name = 'Name must be at least 2 characters';
        }
        break;
      case 2: {
        const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        if (!contactForm.email.trim()) {
          errors.email = 'Email is required';
        } else if (!emailRegex.test(contactForm.email.trim())) {
          errors.email = 'Please enter a valid email address';
        }
        break;
      }
      case 3:
        if (!contactForm.message.trim()) {
          errors.message = 'Message is required';
        } else if (contactForm.message.trim().length < 10) {
          errors.message = 'Message must be at least 10 characters';
        } else if (contactForm.message.trim().length > 500) {
          errors.message = 'Message must be less than 500 characters';
        }
        break;
      default:
        break;
    }

    setContactErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Contact form handlers
  const handleContactNext = () => {
    if (validateContactStep(contactStep)) {
      setContactStep(contactStep + 1);
    }
  };

  const handleContactBack = () => {
    setContactStep(contactStep - 1);
    setContactErrors({});
  };

  const handleContactSubmit = async () => {
    if (!validateContactStep(1) || !validateContactStep(2) || !validateContactStep(3)) {
        // Final validation before submitting
        return;
    }
    setIsSubmitting(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Reset form and close modal
    setContactForm({ name: '', email: '', message: '' });
    setContactStep(1);
    setContactErrors({});
    setIsSubmitting(false);
    setShowContactModal(false);

    // Show success message (you could implement a toast notification here)
    // Using console.log instead of alert for better practice in React apps
    console.log('Success: Thank you for your message! We\'ll get back to you soon.');
  };

  return (
    <div>
      {/* Header */}
      <header className="landing-header">
        <div className="header-content">
          <div className="logo">
            <img src="/IAM_logo_header.png" alt="IAM Logo" className="logo-icon" />
            <span>IAM SaaS Platform</span>
          </div>
          <nav className="nav-actions">
            <button onClick={onLogin} className="nav-link">
              Log in
            </button>
            <Button onClick={onSignup} className="btn-signup">
              Sign up
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section 
        className={`hero-section ${!motionEnabled ? 'motion-disabled' : ''}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {/* Animated Lines Background */}
        {motionEnabled && (
          <div className="animated-lines">
            {/* Horizontal lines */}
            {Array.from({ length: 10 }, (_, i) => (
              <div key={`h-${i}`} className={`line line-h line-h${i + 1}`} />
            ))}
            
            {/* Vertical lines */}
            {Array.from({ length: 10 }, (_, i) => (
              <div key={`v-${i}`} className={`line line-v line-v${i + 1}`} />
            ))}
            
            {/* Diagonal lines */}
            <div className="line line-d line-d1" />
            <div className="line line-d line-d2" />
          </div>
        )}

        {/* Glow Effect */}
        {motionEnabled && (
          <div 
            className="glow-effect"
            style={{
              left: mousePosition.x,
              top: mousePosition.y,
              opacity: isHovering ? 1 : 0
            }}
          />
        )}

        {/* Hero Content */}
        <div className="hero-content">
          <div className="hero-main">
            <img src="/IAM_logo_hero.svg" alt="IAM Hero Logo" className="hero-logo" />
            <div className="hero-text">
              <h1>
                Transform Your Meetings into<br />
                <span className="highlight">Actionable Insights</span>
              </h1>
            </div>
          </div>
          <p className="subtitle">
            Professional AI-powered transcription for South African businesses. Record, transcribe, and organize your meetings with 95%+ accuracy, speaker identification, and intelligent summaries.
          </p>

          {/* Key Features */}
          <div className="features-grid">
            <div className="feature-item">
              <div className="feature-icon">🎯</div>
              <span>95%+ Accuracy</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">👥</div>
              <span>Speaker ID</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">⚡</div>
              <span>Real-time Processing</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔒</div>
              <span>POPIA Compliant</span>
            </div>
          </div>

          <div className="cta-buttons">
            <Button onClick={onSignup} className="btn btn-primary">
              Start Free Trial
              <span className="btn-subtitle">No credit card required</span>
            </Button>
            <Button onClick={onLogin} className="btn btn-secondary">
              Sign in →
            </Button>
          </div>

          {/* Social Proof */}
          <div className="social-proof">
            <p className="social-proof-text">
              Trusted by 100+ South African businesses
            </p>
            <div className="stats">
              <div className="stat">
                <span className="stat-number">99.9%</span>
                <span className="stat-label">Uptime</span>
              </div>
              <div className="stat">
                <span className="stat-number">10k+</span>
                <span className="stat-label">Hours Transcribed</span>
              </div>
              <div className="stat">
                <span className="stat-number">&lt;2s</span>
                <span className="stat-label">Response Time</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="pricing-section">
        <div className="pricing-container">
          <div className="pricing-header">
            <h2>Choose Your Plan</h2>
            <p className="pricing-subtitle">
              Flexible pricing for teams of all sizes. Start free and scale as you grow.
            </p>
          </div>

          <div className="pricing-grid">
            {/* Free Tier */}
            <div className="pricing-card">
              <div className="pricing-card-header">
                <h3 className="pricing-tier-name">Free</h3>
                <div className="pricing-price">
                  <span className="price-currency">R</span>
                  <span className="price-amount">0</span>
                  <span className="price-period">/month</span>
                </div>
                <p className="pricing-description">Perfect for trying out our service</p>
              </div>
              <div className="pricing-features">
                <ul>
                  <li>✓ Basic meeting recording & transcription</li>
                  <li>✓ Limited to 2 transcriptions per month</li>
                  <li>✗ No enhanced audio processing</li>
                  <li>✗ No team collaboration features</li>
                </ul>
              </div>
              <div className="pricing-card-footer">
                <Button onClick={onSignup} className="pricing-btn pricing-btn-free">
                  Get Started Free
                </Button>
              </div>
            </div>

            {/* Per-Sit Tier */}
            <div className="pricing-card pricing-card-popular">
              <div className="popular-badge">Most Popular</div>
              <div className="pricing-card-header">
                <h3 className="pricing-tier-name">Per-Sit</h3>
                <div className="pricing-price">
                  <span className="price-currency">R</span>
                  <span className="price-amount">450</span>
                  <span className="price-period">/month</span>
                </div>
                <p className="pricing-description">Ideal for individual professionals</p>
              </div>
              <div className="pricing-features">
                <ul>
                  <li>✓ All Free Tier features</li>
                  <li>✓ Enhanced audio processing (noise reduction, speaker isolation)</li>
                  <li>✓ Unlimited transcriptions</li>
                  <li>✓ Calendar integration with auto-start recording</li>
                  <li>✓ Countdown reminders</li>
                  <li>✓ Single-user access</li>
                </ul>
              </div>
              <div className="pricing-card-footer">
                <Button onClick={onSignup} className="pricing-btn pricing-btn-popular">
                  Start Free Trial
                </Button>
              </div>
            </div>

            {/* Teams Tier */}
            <div className="pricing-card">
              <div className="pricing-card-header">
                <h3 className="pricing-tier-name">Teams</h3>
                <div className="pricing-price">
                  <span className="price-currency">R</span>
                  <span className="price-amount">750</span>
                  <span className="price-period">/month</span>
                </div>
                <p className="pricing-description">Perfect for growing teams</p>
              </div>
              <div className="pricing-features">
                <ul>
                  <li>✓ All Per-Sit Tier features</li>
                  <li>✓ Multi-user collaboration</li>
                  <li>✓ Team management dashboard</li>
                  <li>✓ Shared storage and usage metrics</li>
                  <li>✓ Priority support</li>
                  <li>✓ Custom branding options</li>
                </ul>
              </div>
              <div className="pricing-card-footer">
                <Button onClick={onSignup} className="pricing-btn pricing-btn-teams">
                  Start Free Trial
                </Button>
              </div>
            </div>

            {/* Enterprise Tier */}
            <div className="pricing-card">
              <div className="pricing-card-header">
                <h3 className="pricing-tier-name">Enterprise</h3>
                <div className="pricing-price">
                  <span className="price-amount-custom">Custom</span>
                  <span className="price-period">Contact Sales</span>
                </div>
                <p className="pricing-description">For large organizations with specific needs</p>
              </div>
              <div className="pricing-features">
                <ul>
                  <li>✓ All Teams Tier features</li>
                  <li>✓ Dedicated account manager</li>
                  <li>✓ SLA-backed uptime guarantees</li>
                  <li>✓ White-labeling options</li>
                  <li>✓ Advanced analytics and reporting</li>
                  <li>✓ Custom integrations</li>
                </ul>
              </div>
              <div className="pricing-card-footer">
                {/* CORRECTED: This button now opens the contact modal */}
                <Button onClick={() => setShowContactModal(true)} className="pricing-btn pricing-btn-enterprise">
                  Contact Sales
                </Button>
              </div>
            </div>
          </div>

          <div className="pricing-footer">
            <p className="pricing-note">
              All plans include POPIA compliance, 256-bit encryption, and 99.9% uptime SLA.
              <br />
              <strong>30-day money-back guarantee</strong> on all paid plans.
            </p>
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <footer className="footer-section">
        <div className="footer-animated-bg">
          {motionEnabled && (
            <div className="footer-lines">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="footer-line"
                  style={{
                    left: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 10}s`,
                    animationDuration: `${15 + Math.random() * 10}s`
                  }}
                />
              ))}
            </div>
          )}
        </div>
        <div className="footer-container">
                        <div className="footer-content">
                <div className="footer-brand">
                  <div className="footer-logo">
                    <img 
                      src="/IAM_logo_footer.png" 
                      alt="IAM Logo" 
                      className="footer-logo-icon" 
                      onClick={() => window.location.href = '/'}
                      title="Go to Home"
                    />
                    <span>IAM - In A Meeting</span>
                  </div>
                  <p className="footer-tagline">
                    Professional AI-powered transcription for South African businesses
                  </p>
                </div>
            <div className="footer-contact">
              <h4 className="footer-section-title">Contact Us</h4>
              <div className="contact-info">
                <a href="tel:0823982486" className="contact-link">
                  📞 082 398 2486
                </a>
                <a href="mailto:info@iam.co.za" className="contact-link">
                  ✉️ info@iam.co.za
                </a>
              </div>
            </div>
            <div className="footer-nav">
              <h4 className="footer-section-title">Quick Links</h4>
              <nav className="footer-links">
                <button onClick={() => navigate('/faq')} className="footer-link">
                  FAQ
                </button>
                <button onClick={() => setShowComingSoonModal('blog')} className="footer-link">
                  IAM Blog
                </button>
                <button onClick={() => setShowComingSoonModal('how-it-works')} className="footer-link">
                  How Does IAM Work
                </button>
                <button onClick={() => setShowContactModal(true)} className="footer-link">
                  Contact Us
                </button>
              </nav>
            </div>
          </div>
          <div className="footer-bottom">
            <p className="footer-copyright">
              © 2025 IAM - In A Meeting. All rights reserved. | POPIA Compliant
            </p>
          </div>
        </div>
      </footer>

      {/* Contact Form Page */}
      {showContactModal && (
        <div className="contact-page-container">
          {/* Landing Page Header */}
          <header className="landing-header">
            <div className="header-content">
              <div className="logo">
                <img src="/IAM_logo_header.png" alt="IAM Logo" className="logo-icon" />
                <span>IAM SaaS Platform</span>
              </div>
              <nav className="nav-actions">
                <button onClick={onLogin} className="nav-link">
                  Log in
                </button>
                <Button onClick={onSignup} className="btn-signup">
                  Sign up
                </Button>
              </nav>
            </div>
          </header>

          <div className="contact-page-content">
            <div
              className="contact-modal"
              onClick={(e) => e.stopPropagation()}
              onMouseMove={(e) => {
                if (motionEnabled) {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const x = ((e.clientX - rect.left) / rect.width) * 100;
                  const y = ((e.clientY - rect.top) / rect.height) * 100;
                  setMousePosition({ x, y });
                }
              }}
              onMouseEnter={() => setIsHovering(true)}
              onMouseLeave={() => setIsHovering(false)}
            >
              {motionEnabled && (
                <div className="contact-modal-lines">
                  {[...Array(15)].map((_, i) => (
                    <div
                      key={i}
                      className="contact-modal-line"
                      style={{
                        left: `${Math.random() * 100}%`,
                        animationDelay: `${Math.random() * 10}s`,
                        animationDuration: `${15 + Math.random() * 10}s`
                      }}
                    />
                  ))}
                </div>
              )}
              {motionEnabled && isHovering && (
                <div
                  className="contact-modal-glow"
                  style={{
                    left: `${mousePosition.x}%`,
                    top: `${mousePosition.y}%`,
                  }}
                />
              )}
              <div className="contact-title-section">
                <div className="contact-header-row">
                  <div>
                    <h2 className="contact-page-title">Get in Touch</h2>
                    <p className="contact-page-subtitle">We'd love to hear from you. Send us a message and we'll respond as soon as possible.</p>
                  </div>
                  <button 
                    onClick={() => setShowContactModal(false)}
                    className="contact-close-btn"
                    aria-label="Close contact form"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className="contact-progress">
                {[1, 2, 3, 4].map((step) => (
                  <div
                    key={step}
                    className={`progress-step ${contactStep >= step ? 'active' : ''}`}
                  >
                    {step}
                  </div>
                ))}
              </div>
              <div className="contact-modal-content">
                {contactStep === 1 && (
                  <div className="contact-step">
                    <h3>What's your name?</h3>
                    <input
                      type="text"
                      placeholder="Enter your full name"
                      value={contactForm.name}
                      onChange={(e) => setContactForm({...contactForm, name: e.target.value})}
                      className={`contact-input ${contactErrors.name ? 'error' : ''}`}
                      autoFocus
                    />
                    {contactErrors.name && <span className="error-message">{contactErrors.name}</span>}
                    <div className="contact-buttons">
                      <Button onClick={handleContactNext} className="btn btn-primary">
                        Next →
                      </Button>
                    </div>
                  </div>
                )}
                {contactStep === 2 && (
                  <div className="contact-step">
                    <h3>What's your email address?</h3>
                    <input
                      type="email"
                      placeholder="Enter your email address"
                      value={contactForm.email}
                      onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                      className={`contact-input ${contactErrors.email ? 'error' : ''}`}
                      autoFocus
                    />
                    {contactErrors.email && <span className="error-message">{contactErrors.email}</span>}
                    <div className="contact-buttons">
                      <Button onClick={handleContactBack} className="btn btn-secondary">
                        ← Back
                      </Button>
                      <Button onClick={handleContactNext} className="btn btn-primary">
                        Next →
                      </Button>
                    </div>
                  </div>
                )}
                {contactStep === 3 && (
                  <div className="contact-step">
                    <h3>What would you like to tell us?</h3>
                    <textarea
                      placeholder="Enter your message (10-500 characters)"
                      value={contactForm.message}
                      onChange={(e) => setContactForm({...contactForm, message: e.target.value})}
                      className={`contact-textarea ${contactErrors.message ? 'error' : ''}`}
                      rows="4"
                      autoFocus
                    />
                    <div className="character-count">
                      {contactForm.message.length}/500
                    </div>
                    {contactErrors.message && <span className="error-message">{contactErrors.message}</span>}
                    <div className="contact-buttons">
                      <Button onClick={handleContactBack} className="btn btn-secondary">
                        ← Back
                      </Button>
                      <Button onClick={handleContactNext} className="btn btn-primary">
                        Next →
                      </Button>
                    </div>
                  </div>
                )}
                {contactStep === 4 && (
                  <div className="contact-step">
                    <h3>Review Your Information</h3>
                    <div className="contact-review">
                      <div className="review-item">
                        <strong>Name:</strong> {contactForm.name}
                      </div>
                      <div className="review-item">
                        <strong>Email:</strong> {contactForm.email}
                      </div>
                      <div className="review-item">
                        <strong>Message:</strong> {contactForm.message}
                      </div>
                    </div>
                    <div className="contact-buttons">
                      <Button onClick={handleContactBack} className="btn btn-secondary">
                        ← Back
                      </Button>
                      <Button
                        onClick={handleContactSubmit}
                        className="btn btn-primary"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? 'Sending...' : 'Send Message'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Coming Soon Modal */}
      {showComingSoonModal && (
        <div className="modal-overlay" onClick={() => setShowComingSoonModal(null)}>
          <div className="coming-soon-modal" onClick={(e) => e.stopPropagation()}>
            <div className="coming-soon-header">
              <h2>Coming Soon</h2>
              <button className="modal-close" onClick={() => setShowComingSoonModal(null)}>×</button>
            </div>
            <div className="coming-soon-content">
              <div className="coming-soon-icon">🚀</div>
              <h3>
                {showComingSoonModal === 'faq' && 'FAQ Page'}
                {showComingSoonModal === 'blog' && 'IAM Blog'}
                {showComingSoonModal === 'how-it-works' && 'How Does IAM Work'}
              </h3>
              <p>
                We're working hard to bring you this feature. Expected launch: Q2 2025
              </p>
              <div className="coming-soon-buttons">
                <Button onClick={() => setShowComingSoonModal(null)} className="btn btn-primary">
                  Got it
                </Button>
                <Button onClick={() => {
                  setShowComingSoonModal(null);
                  setShowContactModal(true);
                }} className="btn btn-secondary">
                  Contact Us for Updates
                </Button>
              </div>
            </div>
          </div>

          {/* Landing Page Footer */}
          <footer className="footer-section">
            <div className="footer-animated-bg">
              {motionEnabled && (
                <div className="footer-lines">
                  {[...Array(20)].map((_, i) => (
                    <div
                      key={i}
                      className="footer-line"
                      style={{
                        left: `${Math.random() * 100}%`,
                        animationDelay: `${Math.random() * 10}s`,
                        animationDuration: `${15 + Math.random() * 10}s`
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
            <div className="footer-container">
              <div className="footer-content">
                <div className="footer-brand">
                  <div className="footer-logo">
                    <img 
                      src="/IAM_logo_footer.png" 
                      alt="IAM Logo" 
                      className="footer-logo-icon" 
                      onClick={() => window.location.href = '/'}
                      title="Go to Home"
                    />
                    <span>IAM - In A Meeting</span>
                  </div>
                  <p className="footer-tagline">
                    Professional AI-powered transcription for South African businesses
                  </p>
                </div>
                <div className="footer-contact">
                  <h4 className="footer-section-title">Contact Us</h4>
                  <div className="contact-info">
                    <a href="tel:0823982486" className="contact-link">
                      📞 082 398 2486
                    </a>
                    <a href="mailto:info@iam.co.za" className="contact-link">
                      ✉️ info@iam.co.za
                    </a>
                  </div>
                </div>
                <div className="footer-nav">
                  <h4 className="footer-section-title">Quick Links</h4>
                  <nav className="footer-links">
                    <button onClick={() => {
                      setShowContactModal(false);
                      navigate('/faq');
                    }} className="footer-link">
                      FAQ
                    </button>
                    <button onClick={() => {
                      setShowContactModal(false);
                      setShowComingSoonModal('blog');
                    }} className="footer-link">
                      IAM Blog
                    </button>
                    <button onClick={() => {
                      setShowContactModal(false);
                      setShowComingSoonModal('how-it-works');
                    }} className="footer-link">
                      How Does IAM Work
                    </button>
                    <button onClick={() => setShowContactModal(false)} className="footer-link">
                      ← Back to Home
                    </button>
                  </nav>
                </div>
              </div>
              <div className="footer-bottom">
                <p className="footer-copyright">
                  © 2025 IAM - In A Meeting. All rights reserved. | POPIA Compliant
                </p>
              </div>
            </div>
          </footer>
        </div>
      )}

      {/* Accessibility Toggle */}
      <button className="motion-toggle" onClick={toggleMotion}>
        🎬 {motionEnabled ? 'Disable' : 'Enable'} Animations
      </button>
    </div>
  );
};

export default LandingPage;
