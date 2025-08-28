from flask import Blueprint, request, jsonify
import stripe
import os

payment_bp = Blueprint('payment', __name__)

# Set Stripe API key (in production, use environment variable)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # Replace with actual test key

@payment_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        data = request.get_json()
        amount = data.get('amount', 999)  # Default $9.99 for premium features
        currency = data.get('currency', 'usd')
        
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents
            currency=currency,
            metadata={
                'integration_check': 'accept_a_payment',
                'user_id': data.get('user_id', 'anonymous')
            }
        )
        
        return jsonify({
            'success': True,
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        })
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@payment_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({
                'success': False,
                'error': 'Payment intent ID is required'
            }), 400
        
        # Retrieve the payment intent to check its status
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            # Payment was successful, update user's subscription/credits
            # In a real app, you would update the user's account here
            
            return jsonify({
                'success': True,
                'message': 'Payment successful! Premium features unlocked.',
                'payment_status': intent.status
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Payment not completed',
                'payment_status': intent.status
            })
            
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@payment_bp.route('/subscription-plans', methods=['GET'])
def get_subscription_plans():
    """Return available subscription plans"""
    plans = [
        {
            'id': 'basic',
            'name': 'Basic Plan',
            'price': 18000,  # 180 ZAR in cents
            'currency': 'zar',
            'features': [
                '10 hours of transcription per month',
                'Basic audio recording',
                'Local storage',
                'Email support'
            ]
        },
        {
            'id': 'premium',
            'name': 'Premium Plan',
            'price': 36000,  # 360 ZAR in cents
            'currency': 'zar',
            'features': [
                'Unlimited transcription',
                'Advanced audio recording',
                'Cloud backup',
                'Priority support',
                'Advanced AI features'
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'plans': plans
    })

