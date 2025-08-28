import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { X, CreditCard, Check } from 'lucide-react';

const PaymentModal = ({ isOpen, onClose, onPaymentSuccess }) => {
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchPlans();
    }
  }, [isOpen]);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/subscription-plans');
      const data = await response.json();
      
      if (data.success) {
        setPlans(data.plans);
        setSelectedPlan(data.plans[0]); // Select first plan by default
      }
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!selectedPlan) return;

    setProcessing(true);
    
    try {
      // Create payment intent
      const response = await fetch('/api/create-payment-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: selectedPlan.price,
          currency: selectedPlan.currency,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // In a real implementation, you would use Stripe Elements here
        // For this demo, we'll simulate a successful payment
        setTimeout(async () => {
          try {
            const confirmResponse = await fetch('/api/confirm-payment', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                payment_intent_id: data.payment_intent_id,
              }),
            });

            const confirmData = await confirmResponse.json();
            
            if (confirmData.success) {
              alert('Payment successful! Premium features unlocked.');
              onPaymentSuccess();
              onClose();
            } else {
              alert('Payment failed: ' + confirmData.error);
            }
          } catch (error) {
            console.error('Error confirming payment:', error);
            alert('Error processing payment');
          } finally {
            setProcessing(false);
          }
        }, 2000); // Simulate processing time
      } else {
        alert('Error creating payment: ' + data.error);
        setProcessing(false);
      }
    } catch (error) {
      console.error('Error processing payment:', error);
      alert('Error processing payment');
      setProcessing(false);
    }
  };

  const formatPrice = (price) => {
    return `R${(price / 100).toFixed(2)}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-card rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Upgrade to Premium</h2>
          <Button variant="outline" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading plans...</div>
        ) : (
          <div className="space-y-6">
            <p className="text-muted-foreground">
              Choose a plan to unlock premium features and unlimited transcription.
            </p>

            <div className="grid gap-4">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedPlan?.id === plan.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => setSelectedPlan(plan)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-semibold">{plan.name}</h3>
                      <p className="text-2xl font-bold text-primary">
                        R{(plan.price / 100).toFixed(2)}
                        <span className="text-sm font-normal text-muted-foreground">/month</span>
                      </p>
                    </div>
                    {selectedPlan?.id === plan.id && (
                      <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                        <Check className="w-4 h-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                  
                  <ul className="space-y-2">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <Check className="w-4 h-4 text-green-500" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div className="border-t pt-6">
              <div className="bg-muted p-4 rounded-lg mb-4">
                <p className="text-sm text-muted-foreground mb-2">
                  <strong>Demo Payment:</strong> This is a demonstration. In a real application, 
                  you would enter your payment details using Stripe Elements.
                </p>
                <p className="text-sm text-muted-foreground">
                  Click "Subscribe Now" to simulate a successful payment.
                </p>
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={handlePayment}
                  disabled={!selectedPlan || processing}
                  className="flex-1 flex items-center gap-2"
                  size="lg"
                >
                  <CreditCard className="w-4 h-4" />
                  {processing ? 'Processing...' : `Subscribe to ${selectedPlan?.name || 'Plan'}`}
                </Button>
                
                <Button
                  variant="outline"
                  onClick={onClose}
                  disabled={processing}
                  size="lg"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentModal;

