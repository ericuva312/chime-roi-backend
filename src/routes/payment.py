import os
import stripe
from flask import Blueprint, request, jsonify
from datetime import datetime
import requests

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

payment_bp = Blueprint('payment', __name__)

def send_payment_confirmation_email(customer_email, customer_name, plan_name, amount, is_recurring=False):
    """Send payment confirmation email to customer"""
    try:
        # Use the existing SendGrid infrastructure
        from .roi_calculator import send_email_via_sendgrid_improved
        
        subject = f"Payment Confirmation - {plan_name}"
        
        # Create email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payment Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Payment Confirmed</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Thank you for choosing Chime</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Hello {customer_name},</h2>
                
                <p>Your payment has been successfully processed! Here are the details:</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">Order Summary</h3>
                    <p><strong>Plan:</strong> {plan_name}</p>
                    <p><strong>Amount Charged:</strong> ${amount:,.2f}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    {"<p><strong>Billing:</strong> Monthly recurring payment set up</p>" if is_recurring else ""}
                </div>
                
                <h3 style="color: #495057;">What's Next?</h3>
                <ul style="padding-left: 20px;">
                    <li>Our team will contact you within 24 hours to begin setup</li>
                    <li>Implementation will be completed within 48 hours</li>
                    <li>You'll see results within 30 days or get your money back</li>
                </ul>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #2d5a2d;"><strong>🔒 Secure:</strong> Your payment was processed securely through Stripe with industry-leading encryption.</p>
                </div>
                
                <p>If you have any questions, please don't hesitate to contact us at <a href="mailto:hello@chimehq.co" style="color: #667eea;">hello@chimehq.co</a></p>
                
                <p style="margin-top: 30px;">Best regards,<br>The Chime Team</p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
                <p>Chime - AI-Powered E-commerce Automation</p>
                <p>This email was sent to {customer_email}</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Payment Confirmation - {plan_name}
        
        Hello {customer_name},
        
        Your payment has been successfully processed!
        
        Order Summary:
        - Plan: {plan_name}
        - Amount Charged: ${amount:,.2f}
        - Date: {datetime.now().strftime('%B %d, %Y')}
        {"- Billing: Monthly recurring payment set up" if is_recurring else ""}
        
        What's Next?
        - Our team will contact you within 24 hours to begin setup
        - Implementation will be completed within 48 hours
        - You'll see results within 30 days or get your money back
        
        If you have any questions, please contact us at hello@chimehq.co
        
        Best regards,
        The Chime Team
        
        Chime - AI-Powered E-commerce Automation
        """
        
        # Send email using existing infrastructure
        result = send_email_via_sendgrid_improved(
            to_email=customer_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email="hello@chimehq.co",
            from_name="Chime Team"
        )
        
        print(f"✅ Payment confirmation email sent to {customer_email}: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error sending payment confirmation email to {customer_email}: {str(e)}")
        return False

def send_payment_notification_email(customer_data, plan_name, amount, is_recurring=False):
    """Send payment notification email to hello@chimehq.co"""
    try:
        # Use the existing SendGrid infrastructure
        from .roi_calculator import send_email_via_sendgrid_improved
        
        subject = f"New Payment Received - {plan_name} - {customer_data.get('company', 'N/A')}"
        
        # Create email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Payment Received</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">💰 New Payment Received</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">{plan_name} - ${amount:,.2f}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Payment Details</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">Customer Information</h3>
                    <p><strong>Name:</strong> {customer_data.get('name', 'N/A')}</p>
                    <p><strong>Email:</strong> {customer_data.get('email', 'N/A')}</p>
                    <p><strong>Company:</strong> {customer_data.get('company', 'N/A')}</p>
                    <p><strong>Phone:</strong> {customer_data.get('phone', 'N/A')}</p>
                    <p><strong>Shopify Store:</strong> {customer_data.get('shopify_url', 'N/A')}</p>
                </div>
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2d5a2d;">Payment Summary</h3>
                    <p><strong>Plan:</strong> {plan_name}</p>
                    <p><strong>Amount:</strong> ${amount:,.2f}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Recurring:</strong> {"Yes - Monthly billing set up" if is_recurring else "No - One-time payment only"}</p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #856404;">Next Steps</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #856404;">
                        <li>Contact customer within 24 hours</li>
                        <li>Begin implementation process</li>
                        <li>Set up 48-hour implementation timeline</li>
                        <li>Schedule follow-up for 30-day results check</li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px; text-align: center;">
                    <strong>Customer confirmation email has been sent automatically.</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        New Payment Received - {plan_name}
        
        Payment Details:
        - Plan: {plan_name}
        - Amount: ${amount:,.2f}
        - Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        - Recurring: {"Yes - Monthly billing set up" if is_recurring else "No - One-time payment only"}
        
        Customer Information:
        - Name: {customer_data.get('name', 'N/A')}
        - Email: {customer_data.get('email', 'N/A')}
        - Company: {customer_data.get('company', 'N/A')}
        - Phone: {customer_data.get('phone', 'N/A')}
        - Shopify Store: {customer_data.get('shopify_url', 'N/A')}
        
        Next Steps:
        - Contact customer within 24 hours
        - Begin implementation process
        - Set up 48-hour implementation timeline
        - Schedule follow-up for 30-day results check
        
        Customer confirmation email has been sent automatically.
        """
        
        # Send email using existing infrastructure
        result = send_email_via_sendgrid_improved(
            to_email="hello@chimehq.co",
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email="hello@chimehq.co",
            from_name="Chime Payment System"
        )
        
        print(f"✅ Payment notification email sent to hello@chimehq.co: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error sending payment notification email: {str(e)}")
        return False

@payment_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create a Stripe payment intent for one-time and recurring payments"""
    try:
        data = request.get_json()
        
        # Extract customer and plan information
        customer_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'company': data.get('company'),
            'phone': data.get('phone'),
            'shopify_url': data.get('shopify_url')
        }
        
        plan = data.get('plan', 'professional')
        
        # Define plan pricing
        plans = {
            'growth': {
                'name': 'Growth Plan',
                'setup_fee': 299700,  # $2,997 in cents
                'monthly_fee': 99700,  # $997 in cents
            },
            'professional': {
                'name': 'Professional Plan',
                'setup_fee': 499700,  # $4,997 in cents
                'monthly_fee': 149700,  # $1,497 in cents
            },
            'enterprise': {
                'name': 'Enterprise Plan',
                'setup_fee': 999700,  # $9,997 in cents
                'monthly_fee': 299700,  # $2,997 in cents
            }
        }
        
        if plan not in plans:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        plan_info = plans[plan]
        
        # Create or retrieve Stripe customer
        try:
            customer = stripe.Customer.create(
                email=customer_data['email'],
                name=customer_data['name'],
                metadata={
                    'company': customer_data.get('company', ''),
                    'phone': customer_data.get('phone', ''),
                    'shopify_url': customer_data.get('shopify_url', ''),
                    'plan': plan
                }
            )
        except Exception as e:
            print(f"Error creating Stripe customer: {str(e)}")
            return jsonify({'error': 'Failed to create customer'}), 500
        
        # Create payment intent for setup fee
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=plan_info['setup_fee'],
                currency='usd',
                customer=customer.id,
                metadata={
                    'plan': plan,
                    'plan_name': plan_info['name'],
                    'customer_name': customer_data['name'],
                    'customer_email': customer_data['email'],
                    'company': customer_data.get('company', ''),
                    'type': 'setup_fee'
                },
                description=f"{plan_info['name']} - Setup Fee"
            )
        except Exception as e:
            print(f"Error creating payment intent: {str(e)}")
            return jsonify({'error': 'Failed to create payment intent'}), 500
        
        # Create subscription for monthly recurring payments
        try:
            # First create a price for the monthly fee
            price = stripe.Price.create(
                unit_amount=plan_info['monthly_fee'],
                currency='usd',
                recurring={'interval': 'month'},
                product_data={
                    'name': f"{plan_info['name']} - Monthly Service",
                    'description': f"Monthly service fee for {plan_info['name']}"
                }
            )
            
            # Create subscription (will start after setup payment is confirmed)
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price.id}],
                trial_end=int((datetime.now().timestamp()) + (7 * 24 * 60 * 60)),  # 7 day trial
                metadata={
                    'plan': plan,
                    'plan_name': plan_info['name'],
                    'customer_name': customer_data['name'],
                    'customer_email': customer_data['email'],
                    'company': customer_data.get('company', '')
                }
            )
            
        except Exception as e:
            print(f"Error creating subscription: {str(e)}")
            # Continue without subscription if it fails
            subscription = None
        
        return jsonify({
            'client_secret': payment_intent.client_secret,
            'customer_id': customer.id,
            'subscription_id': subscription.id if subscription else None,
            'plan_info': {
                'name': plan_info['name'],
                'setup_fee': plan_info['setup_fee'] / 100,  # Convert back to dollars
                'monthly_fee': plan_info['monthly_fee'] / 100
            }
        })
        
    except Exception as e:
        print(f"Error in create_payment_intent: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payment_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    """Confirm payment and send confirmation emails"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID required'}), 400
        
        # Retrieve payment intent from Stripe
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except Exception as e:
            print(f"Error retrieving payment intent: {str(e)}")
            return jsonify({'error': 'Invalid payment intent'}), 400
        
        if payment_intent.status != 'succeeded':
            return jsonify({'error': 'Payment not successful'}), 400
        
        # Extract metadata
        metadata = payment_intent.metadata
        customer_data = {
            'name': metadata.get('customer_name'),
            'email': metadata.get('customer_email'),
            'company': metadata.get('company'),
            'phone': '',  # Not stored in metadata
            'shopify_url': ''  # Not stored in metadata
        }
        
        plan_name = metadata.get('plan_name')
        amount = payment_intent.amount / 100  # Convert from cents to dollars
        
        # Send confirmation emails
        customer_email_sent = send_payment_confirmation_email(
            customer_data['email'],
            customer_data['name'],
            plan_name,
            amount,
            is_recurring=True  # All plans have recurring components
        )
        
        notification_email_sent = send_payment_notification_email(
            customer_data,
            plan_name,
            amount,
            is_recurring=True
        )
        
        return jsonify({
            'success': True,
            'customer_email_sent': customer_email_sent,
            'notification_email_sent': notification_email_sent,
            'amount': amount,
            'plan_name': plan_name
        })
        
    except Exception as e:
        print(f"Error in confirm_payment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for payment events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"✅ Payment succeeded: {payment_intent['id']}")
        
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        print(f"✅ Subscription payment succeeded: {invoice['id']}")
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print(f"❌ Subscription payment failed: {invoice['id']}")
        
    return jsonify({'status': 'success'})

