from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import os
import requests
import json
from datetime import datetime

roi_bp = Blueprint('roi', __name__)

@roi_bp.route('/roi-calculator', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*')
def roi_calculator():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Extract form data with safe conversion
        def safe_float_conversion(value, default=0):
            """Safely convert value to float, handling empty strings and None"""
            if value is None or value == '' or value == 'undefined':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        monthly_revenue = safe_float_conversion(data.get('monthly_revenue'), 0)
        average_order_value = safe_float_conversion(data.get('average_order_value'), 0)
        monthly_orders = safe_float_conversion(data.get('monthly_orders'), 0)
        business_category = data.get('business_category', '')
        current_conversion_rate = safe_float_conversion(data.get('current_conversion_rate'), 0)
        cart_abandonment_rate = safe_float_conversion(data.get('cart_abandonment_rate'), 0)
        monthly_ad_spend = safe_float_conversion(data.get('monthly_ad_spend'), 0)
        
        hours_week_manual_tasks = data.get('hours_week_manual_tasks', '')
        business_stage = data.get('business_stage', '')
        biggest_challenges = data.get('biggest_challenges', [])
        
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        email = data.get('email', '')
        company = data.get('company', '')
        phone = data.get('phone', '')
        website = data.get('website', '')
        
        # Calculate ROI projections
        roi_data = calculate_roi_projections(
            monthly_revenue, average_order_value, monthly_orders,
            business_category, current_conversion_rate, cart_abandonment_rate
        )
        
        # Debug logging
        print(f"🔍 DEBUG: Processing ROI calculator for {email}")
        print(f"🔍 DEBUG: SendGrid API key configured: {'Yes' if os.environ.get('SENDGRID_API_KEY') else 'No'}")
        
        # Send ROI report email to user
        email_success = send_roi_report_email(email, first_name, roi_data, data)
        print(f"🔍 DEBUG: ROI email success: {email_success}")
        
        # Send lead notification to Chime
        lead_success = send_lead_notification_email(data, roi_data)
        print(f"🔍 DEBUG: Lead notification success: {lead_success}")
        
        # Submit to HubSpot (if configured)
        hubspot_success = submit_to_hubspot(data, roi_data)
        print(f"🔍 DEBUG: HubSpot success: {hubspot_success}")
        
        return jsonify({
            'success': True,
            'message': 'ROI report sent successfully',
            'roi_data': roi_data,
            'debug_info': {
                'email_sent': email_success,
                'lead_notification_sent': lead_success,
                'hubspot_submitted': hubspot_success,
                'sendgrid_configured': bool(os.environ.get('SENDGRID_API_KEY'))
            }
        })
        
    except Exception as e:
        print(f"Error processing ROI calculator: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@roi_bp.route('/test-email', methods=['POST'])
@cross_origin(origins='*')
def test_email():
    """Test endpoint for debugging email functionality"""
    try:
        data = request.get_json()
        email = data.get('email', 'ericuva@gmail.com')
        
        print(f"🔍 TEST: Starting email test to {email}")
        
        # Test SendGrid configuration
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '')
        print(f"🔍 TEST: SendGrid API key configured: {'Yes' if sendgrid_api_key else 'No'}")
        
        if sendgrid_api_key:
            print(f"🔍 TEST: API key starts with: {sendgrid_api_key[:10]}...")
        
        # Test email sending
        test_subject = "🧪 Email Function Test"
        test_html = "<h1>Email Test</h1><p>This is a test email to verify the email sending functionality is working.</p>"
        
        success = send_email_via_sendgrid(email, test_subject, test_html)
        
        return jsonify({
            'success': success,
            'message': f'Test email {"sent" if success else "failed"}',
            'debug_info': {
                'sendgrid_configured': bool(sendgrid_api_key),
                'target_email': email,
                'api_key_preview': sendgrid_api_key[:10] + '...' if sendgrid_api_key else 'Not configured'
            }
        })
        
    except Exception as e:
        print(f"❌ Error in test email: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_roi_projections(monthly_revenue, average_order_value, monthly_orders, 
                            business_category, current_conversion_rate, cart_abandonment_rate):
    """Calculate ROI projections based on business data"""
    
    # Industry multipliers based on business category
    industry_multipliers = {
        'fashion-apparel': 1.8,
        'electronics-tech': 2.1,
        'health-wellness': 1.9,
        'beauty-cosmetics': 2.0,
        'home-garden': 1.7,
        'food-beverage': 1.6,
        'pet-products': 1.8,
        'jewelry-accessories': 2.2,
        'sports-fitness': 1.9,
        'other': 1.8
    }
    
    multiplier = industry_multipliers.get(business_category, 1.8)
    
    # Calculate improvements
    conversion_improvement = min(current_conversion_rate * 0.4, 2.0)  # 40% improvement, max 2%
    cart_recovery = cart_abandonment_rate * 0.15  # Recover 15% of abandoned carts
    
    # Calculate new metrics
    new_conversion_rate = current_conversion_rate + conversion_improvement
    recovered_orders = monthly_orders * (cart_recovery / 100)
    new_monthly_orders = monthly_orders + recovered_orders
    
    # Calculate revenue projections
    current_monthly_revenue = monthly_revenue
    projected_monthly_revenue = new_monthly_orders * average_order_value
    monthly_increase = projected_monthly_revenue - current_monthly_revenue
    annual_increase = monthly_increase * 12
    
    # ROI calculations
    chime_investment = 2997  # Monthly Chime cost
    monthly_roi = (monthly_increase - chime_investment) / chime_investment * 100
    annual_roi = annual_increase / (chime_investment * 12) * 100
    
    return {
        'current_monthly_revenue': current_monthly_revenue,
        'projected_monthly_revenue': projected_monthly_revenue,
        'monthly_increase': monthly_increase,
        'annual_increase': annual_increase,
        'current_conversion_rate': current_conversion_rate,
        'projected_conversion_rate': new_conversion_rate,
        'recovered_orders': recovered_orders,
        'monthly_roi': monthly_roi,
        'annual_roi': annual_roi,
        'payback_period': max(1, chime_investment / monthly_increase) if monthly_increase > 0 else 12
    }

def send_email_via_sendgrid(to_email, subject, html_content, from_email="hello@chimehq.co"):
    """Send email using SendGrid API"""
    try:
        # Get SendGrid API key from environment
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '')
        
        print(f"🔍 Debug: Attempting to send email to {to_email}")
        print(f"🔍 Debug: SendGrid API key configured: {'Yes' if sendgrid_api_key else 'No'}")
        
        if not sendgrid_api_key:
            print("❌ SendGrid API key not configured")
            return False
        
        # Prepare SendGrid API request
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": from_email, "name": "Chime Team"},
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        print(f"🔍 Debug: Sending email with subject: {subject}")
        
        # Send the email
        response = requests.post(url, headers=headers, json=data)
        
        print(f"🔍 Debug: SendGrid response status: {response.status_code}")
        
        if response.status_code == 202:
            print(f"✅ Email successfully sent to {to_email} via SendGrid")
            return True
        else:
            print(f"❌ SendGrid API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email via SendGrid: {str(e)}")
        return False

def send_email_via_sendgrid_improved(to_email, subject, html_content, first_name):
    """Send email via SendGrid with improved deliverability settings"""
    try:
        print(f"🔍 Debug: Sending improved email to {to_email}")
        
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '')
        if not sendgrid_api_key:
            print("❌ SendGrid API key not configured")
            return False
        
        # Create plain text version for better deliverability
        plain_text = f"""
Hi {first_name},

Congratulations on taking the first step toward transforming your store's performance. Based on your current metrics, we've identified specific opportunities that could significantly increase your monthly revenue within 60 days.

Your Custom Revenue Growth Analysis Results
Conservative projections based on 500+ successful implementations.

We've prepared a detailed analysis showing your growth potential, including projected revenue increases and time savings on manual tasks.

Your Next Steps:
1. Schedule a 30-minute strategy call with our founder
2. Receive your custom implementation plan  
3. Start seeing results in 30 days

Schedule your strategy call: https://calendly.com/chimehq/strategy-call

Best regards,
The Chime Team

Chime | Revenue Growth Solutions
hello@chimehq.co
https://chimehq.co

To unsubscribe, reply with "unsubscribe"
        """
        
        # Improved email data structure
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": to_email, "name": first_name}],
                    "subject": subject
                }
            ],
            "from": {
                "email": "hello@chimehq.co",
                "name": "Chime Team"
            },
            "reply_to": {
                "email": "hello@chimehq.co",
                "name": "Chime Team"
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": plain_text
                },
                {
                    "type": "text/html", 
                    "value": html_content
                }
            ],
            "categories": ["roi-report", "business-analysis"],
            "custom_args": {
                "campaign": "roi_calculator",
                "source": "website"
            },
            "tracking_settings": {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True},
                "subscription_tracking": {"enable": True}
            },
            "mail_settings": {
                "bypass_list_management": {"enable": False},
                "footer": {"enable": False},
                "sandbox_mode": {"enable": False}
            }
        }
        
        headers = {
            "Authorization": f"Bearer {sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=email_data
        )
        
        print(f"🔍 Debug: SendGrid response status: {response.status_code}")
        
        if response.status_code == 202:
            print(f"✅ Email sent successfully via improved SendGrid")
            return True
        else:
            print(f"❌ SendGrid API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in improved SendGrid function: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return False

def send_roi_report_email(email, first_name, roi_data, form_data=None):
    """
    Send ROI report email using the new mobile-optimized template
    """
    try:
        print(f"🔍 DEBUG: Starting ROI email send to {email}")
        
        # Calculate additional metrics for the email with proper type conversion
        try:
            monthly_revenue = float(form_data.get('monthly_revenue', 0)) if form_data and form_data.get('monthly_revenue') else 0
            monthly_orders = float(form_data.get('monthly_orders', 0)) if form_data and form_data.get('monthly_orders') else 0
            average_order_value = float(form_data.get('average_order_value', 0)) if form_data and form_data.get('average_order_value') else 0
            cart_abandonment_rate = float(form_data.get('cart_abandonment_rate', 70)) if form_data and form_data.get('cart_abandonment_rate') else 70
            current_conversion_rate = float(form_data.get('current_conversion_rate', 2.5)) if form_data and form_data.get('current_conversion_rate') else 2.5
        except (ValueError, TypeError) as e:
            print(f"❌ ERROR: Type conversion failed: {e}")
            # Use safe defaults
            monthly_revenue = 0
            monthly_orders = 0
            average_order_value = 0
            cart_abandonment_rate = 70
            current_conversion_rate = 2.5
            
        business_category = form_data.get('business_category', 'E-commerce') if form_data else 'E-commerce'
        company = form_data.get('company', 'Your Business') if form_data else 'Your Business'
        hours_week_manual_tasks = form_data.get('hours_week_manual_tasks', '11-20') if form_data else '11-20'
        
        # Calculate derived metrics
        monthly_increase = roi_data.get('monthly_increase', 0)
        annual_increase = roi_data.get('annual_increase', 0)
        recovered_orders = (cart_abandonment_rate / 100) * monthly_orders * 0.6  # 60% recovery rate
        daily_loss = monthly_increase / 30 if monthly_increase > 0 else 0
        weekly_loss = daily_loss * 7
        
        # Create the complete HTML email template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Revenue Growth Analysis - Chime</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; padding: 20px !important; }}
            .header {{ padding: 20px !important; }}
            .content {{ padding: 20px !important; }}
            .metrics-grid {{ padding: 20px !important; }}
            .metrics-card {{ margin: 10px 0 !important; }}
            .metrics-value {{ font-size: 14px !important; }}
            .metrics-label {{ font-size: 8px !important; }}
            .section-padding {{ padding: 20px !important; margin: 20px 0 !important; }}
            .cta-button {{ padding: 15px 25px !important; font-size: 16px !important; }}
            h1 {{ font-size: 24px !important; }}
            h2 {{ font-size: 18px !important; }}
            h3 {{ font-size: 16px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1a202c; background-color: #f7fafc;">
    <div class="container" style="max-width: 650px; margin: 0 auto; background-color: #ffffff;">
        
        <!-- Header -->
        <div class="header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 40px 20px; color: white;">
            <div style="text-align: center;">
                <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">Chime</h1>
                <p style="margin: 8px 0 0; color: rgba(255,255,255,0.9); font-size: 16px; font-weight: 500;">Revenue Growth Analysis</p>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="content" style="padding: 40px;">
            
            <!-- Opening Section -->
            <p style="margin: 0 0 20px; font-size: 18px; color: #1a202c; font-weight: 500;">Hi {first_name},</p>
            
            <p style="margin: 0 0 25px; font-size: 16px; line-height: 1.7; color: #2d3748;">
                Thank you for completing the Revenue Growth Calculator for <strong style="color: #667eea;">{company}</strong>. Based on your current monthly revenue of <strong style="color: #667eea;">${monthly_revenue:,}</strong> and {business_category} business model, I've identified some significant opportunities that could transform your growth trajectory.
            </p>
            
            <!-- Metrics Grid -->
            <div class="metrics-grid" style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border-radius: 12px; padding: 25px; margin: 30px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 20px; color: #1a202c; font-size: 18px; font-weight: 700; text-align: center;">Your Projected Performance Improvements</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 50%; padding: 8px;">
                            <div class="metrics-card" style="text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div class="metrics-value" style="font-size: 18px; font-weight: 700; color: #667eea; margin-bottom: 4px; line-height: 1.1;">${monthly_increase:,.0f}</div>
                                <div class="metrics-label" style="font-size: 9px; color: #4a5568; font-weight: 600; line-height: 1.2;">Monthly Revenue Increase</div>
                            </div>
                        </td>
                        <td style="width: 50%; padding: 8px;">
                            <div class="metrics-card" style="text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div class="metrics-value" style="font-size: 18px; font-weight: 700; color: #48bb78; margin-bottom: 4px; line-height: 1.1;">${annual_increase:,.0f}</div>
                                <div class="metrics-label" style="font-size: 9px; color: #4a5568; font-weight: 600; line-height: 1.2;">Annual Revenue Growth</div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 50%; padding: 8px;">
                            <div class="metrics-card" style="text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div class="metrics-value" style="font-size: 18px; font-weight: 700; color: #ed8936; margin-bottom: 4px; line-height: 1.1;">{recovered_orders:.0f}</div>
                                <div class="metrics-label" style="font-size: 9px; color: #4a5568; font-weight: 600; line-height: 1.2;">Recovered Orders/Month</div>
                            </div>
                        </td>
                        <td style="width: 50%; padding: 8px;">
                            <div class="metrics-card" style="text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div class="metrics-value" style="font-size: 18px; font-weight: 700; color: #9f7aea; margin-bottom: 4px; line-height: 1.1;">20+</div>
                                <div class="metrics-label" style="font-size: 9px; color: #4a5568; font-weight: 600; line-height: 1.2;">Hours Saved Weekly</div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <p style="margin: 25px 0; font-size: 16px; line-height: 1.7; color: #2d3748;">
                Your biggest opportunity right now is your <strong style="color: #e53e3e;">{cart_abandonment_rate:.0f}% cart abandonment rate</strong> and <strong style="color: #e53e3e;">{current_conversion_rate:.1f}% conversion rate</strong> – both areas where we typically see immediate improvements. In this email, I'll show you exactly how to capture that lost revenue and the specific dollar impact for your business.
            </p>
            
            <!-- Value Delivery Section -->
            <div class="section-padding" style="background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%); border-left: 4px solid #667eea; padding: 30px; margin: 35px 0; border-radius: 0 12px 12px 0;">
                <h2 style="margin: 0 0 25px; color: #1a202c; font-size: 22px; font-weight: 700;">Your Personalized Growth Analysis</h2>
                
                <div style="margin: 25px 0;">
                    <h3 style="margin: 0 0 15px; color: #667eea; font-size: 18px; font-weight: 600;">💰 Revenue Recovery Opportunity</h3>
                    <p style="margin: 0 0 15px; line-height: 1.7; color: #2d3748;">
                        With {monthly_orders:.0f} monthly orders and a {cart_abandonment_rate:.0f}% abandonment rate, you're losing approximately <strong style="color: #667eea;">{recovered_orders:.0f} potential orders every month</strong>. At your current AOV of ${average_order_value:.0f}, that's <strong style="color: #667eea;">${monthly_increase:,.0f} in recoverable revenue monthly</strong> – or <strong style="color: #667eea;">${annual_increase:,.0f} annually</strong>.
                    </p>
                    <p style="margin: 0 0 20px; line-height: 1.7; color: #2d3748;">
                        Industry benchmark for {business_category} businesses is 45-55% cart abandonment. Your current rate suggests immediate optimization opportunities that our AI typically improves within the first 30 days.
                    </p>
                </div>
                
                <div style="margin: 25px 0;">
                    <h3 style="margin: 0 0 15px; color: #48bb78; font-size: 18px; font-weight: 600;">⚡ Automation Impact</h3>
                    <p style="margin: 0 0 15px; line-height: 1.7; color: #2d3748;">
                        You're currently spending <strong style="color: #48bb78;">{hours_week_manual_tasks} hours per week</strong> on manual tasks. Our AI automation typically saves 20+ hours weekly, allowing you to focus on strategic growth instead of operational tasks. That's equivalent to hiring a full-time employee without the overhead costs.
                    </p>
                    <p style="margin: 0 0 20px; line-height: 1.7; color: #2d3748;">
                        Based on similar {business_category} businesses we've worked with, Chime delivers an average of <strong style="color: #48bb78;">188% revenue growth</strong> within the first 90 days through intelligent automation and conversion optimization.
                    </p>
                </div>
                
                <div style="margin: 25px 0;">
                    <h3 style="margin: 0 0 15px; color: #9f7aea; font-size: 18px; font-weight: 600;">🎯 Your Competitive Edge</h3>
                    <p style="margin: 0 0 15px; line-height: 1.7; color: #2d3748;">
                        While your competitors are still manually managing their operations, implementing our AI-powered system positions you to capture market share through superior customer experience and operational efficiency. The businesses that automate first typically see 25-40% market share gains in their category.
                    </p>
                </div>
            </div>
            
            <!-- Social Proof Section -->
            <div class="section-padding" style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); border-left: 4px solid #48bb78; padding: 30px; margin: 35px 0; border-radius: 0 12px 12px 0;">
                <h2 style="margin: 0 0 25px; color: #1a202c; font-size: 22px; font-weight: 700;">Success Stories from Similar Businesses</h2>
                
                <div style="margin: 25px 0; padding: 25px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 15px; color: #1a202c; font-size: 16px; font-weight: 600;">TechStyle Apparel - Fashion & Apparel</h4>
                    <p style="margin: 0 0 15px; font-style: italic; color: #2d3748; line-height: 1.6; border-left: 3px solid #48bb78; padding-left: 15px;">
                        "Chime's AI reduced our cart abandonment from 78% to 31% in just 3 weeks. Our monthly revenue jumped from $85K to $156K, and we're saving 28 hours per week on manual processes. The ROI was 340% in the first quarter."
                    </p>
                    <p style="margin: 0; font-weight: 600; color: #48bb78; font-size: 14px;">
                        — Jennifer Walsh, Founder
                    </p>
                </div>
                
                <div style="margin: 25px 0; padding: 25px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 15px; color: #1a202c; font-size: 16px; font-weight: 600;">GrowthTech Solutions - Electronics & Technology</h4>
                    <p style="margin: 0 0 15px; font-style: italic; color: #2d3748; line-height: 1.6; border-left: 3px solid #48bb78; padding-left: 15px;">
                        "The 48-hour setup was seamless, and we saw results immediately. Our conversion rate improved from 2.1% to 4.8%, generating an additional $94K monthly. Chime's automation handles what used to take our team 35 hours weekly."
                    </p>
                    <p style="margin: 0; font-weight: 600; color: #48bb78; font-size: 14px;">
                        — Alex Thompson, CEO
                    </p>
                </div>
            </div>
            
            <!-- Urgency & Scarcity Section -->
            <div class="section-padding" style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 1px solid #f59e0b; padding: 30px; margin: 35px 0; border-radius: 12px;">
                <h2 style="margin: 0 0 20px; color: #92400e; font-size: 22px; font-weight: 700;">⏰ The Cost of Waiting</h2>
                <p style="margin: 0 0 18px; color: #92400e; line-height: 1.7; font-size: 16px;">
                    Every day you delay optimization, you're losing approximately <strong style="color: #d97706;">${daily_loss:,.0f} in recoverable revenue</strong>. That's <strong style="color: #d97706;">${weekly_loss:,.0f} per week</strong> walking out the door due to cart abandonment and conversion inefficiencies.
                </p>
                <p style="margin: 0; color: #92400e; line-height: 1.7; font-size: 16px;">
                    Meanwhile, your automated competitors are capturing market share and customer loyalty. The businesses that implement AI-powered optimization first typically maintain a 6-12 month competitive advantage that becomes increasingly difficult for others to overcome.
                </p>
            </div>
            
            <!-- Call-to-Action Section -->
            <div class="section-padding" style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); padding: 35px; margin: 35px 0; border-radius: 12px; text-align: center; border: 2px solid #e2e8f0;">
                <h2 style="margin: 0 0 25px; color: #1a202c; font-size: 24px; font-weight: 700;">Ready to Capture Your ${monthly_increase:,.0f}/Month Opportunity?</h2>
                
                <p style="margin: 0 0 30px; color: #2d3748; font-size: 16px; line-height: 1.7;">
                    Let's discuss your specific growth strategy in a complimentary 30-minute consultation. I'll show you exactly how to implement our proven system for your business, with no obligation and complete transparency about costs and timeline.
                </p>
                
                <div style="margin: 30px 0;">
                    <a href="https://chimehq.co/#/contact" class="cta-button" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 18px 40px; border-radius: 8px; font-weight: 600; font-size: 18px; margin: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">Schedule Your Growth Strategy Call →</a>
                </div>
                
                <p style="margin: 25px 0 0; color: #718096; font-size: 14px; line-height: 1.6;">
                    Or reply to this email, and I'll personally reach out within 4 hours.<br>
                    <a href="https://chimehq.co/#/contact" style="color: #667eea; text-decoration: none; font-weight: 500;">Click here to view available consultation times</a>
                </p>
            </div>
            
            <!-- Guarantee Section -->
            <div style="background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%); border: 1px solid #3182ce; padding: 25px; margin: 30px 0; border-radius: 12px;">
                <h3 style="margin: 0 0 20px; color: #1e4a72; font-size: 20px; font-weight: 700;">🛡️ Our Growth Guarantee</h3>
                <ul style="margin: 0; padding-left: 25px; color: #1e4a72; line-height: 1.8; font-size: 15px;">
                    <li style="margin-bottom: 8px;"><strong>15-25% revenue growth</strong> guaranteed within 90 days</li>
                    <li style="margin-bottom: 8px;"><strong>48-hour setup</strong> with full data backup and rollback capabilities</li>
                    <li style="margin-bottom: 8px;"><strong>30-day results timeline</strong> or full refund</li>
                    <li style="margin-bottom: 8px;"><strong>SOC 2 certified</strong> enterprise-grade security</li>
                    <li><strong>90-day money-back guarantee</strong> if you're not completely satisfied</li>
                </ul>
            </div>
            
            <!-- Closing -->
            <div style="margin: 40px 0 25px; padding-top: 25px; border-top: 2px solid #e2e8f0;">
                <p style="margin: 0 0 15px; color: #2d3748; line-height: 1.7; font-size: 16px;">
                    Looking forward to helping you capture that ${monthly_increase:,.0f} monthly opportunity and transform your business operations.
                </p>
                <p style="margin: 0 0 10px; color: #2d3748; font-size: 16px;">Best regards,</p>
                <p style="margin: 0; font-weight: 600; color: #1a202c; font-size: 16px;">The Chime Team</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); padding: 25px 40px; border-top: 2px solid #e2e8f0; text-align: center;">
            <p style="margin: 0 0 15px; color: #4a5568; font-size: 14px; font-weight: 500;">
                Chime | AI-Powered Revenue Growth Solutions<br>
                <a href="mailto:hello@chimehq.co" style="color: #667eea; text-decoration: none; font-weight: 500;">hello@chimehq.co</a> | 
                <a href="https://chimehq.co" style="color: #667eea; text-decoration: none; font-weight: 500;">chimehq.co</a>
            </p>
            <p style="margin: 0; color: #718096; font-size: 12px; line-height: 1.5;">
                <a href="#" style="color: #718096; text-decoration: none;">Unsubscribe</a> | 
                <a href="https://chimehq.co/privacy" style="color: #718096; text-decoration: none;">Privacy Policy</a> |
                This email complies with CAN-SPAM regulations
            </p>
        </div>
    </div>
</body>
</html>"""

        # Create plain text version for better deliverability
        plain_text = f"""Hi {first_name},

Thank you for completing the Revenue Growth Calculator for {company}. Based on your current monthly revenue of ${monthly_revenue:,} and {business_category} business model, I've identified some significant opportunities that could transform your growth trajectory.

YOUR PROJECTED PERFORMANCE IMPROVEMENTS:
- Monthly Revenue Increase: ${monthly_increase:,.0f}
- Annual Revenue Growth: ${annual_increase:,.0f}
- Recovered Orders/Month: {recovered_orders:.0f}
- Hours Saved Weekly: 20+

Your biggest opportunity right now is your {cart_abandonment_rate:.0f}% cart abandonment rate and {current_conversion_rate:.1f}% conversion rate – both areas where we typically see immediate improvements.

REVENUE RECOVERY OPPORTUNITY:
With {monthly_orders:.0f} monthly orders and a {cart_abandonment_rate:.0f}% abandonment rate, you're losing approximately {recovered_orders:.0f} potential orders every month. At your current AOV of ${average_order_value:.0f}, that's ${monthly_increase:,.0f} in recoverable revenue monthly – or ${annual_increase:,.0f} annually.

THE COST OF WAITING:
Every day you delay optimization, you're losing approximately ${daily_loss:,.0f} in recoverable revenue. That's ${weekly_loss:,.0f} per week walking out the door due to cart abandonment and conversion inefficiencies.

READY TO CAPTURE YOUR ${monthly_increase:,.0f}/MONTH OPPORTUNITY?
Let's discuss your specific growth strategy in a complimentary 30-minute consultation. Schedule your call at: https://chimehq.co/#/contact

OUR GROWTH GUARANTEE:
- 15-25% revenue growth guaranteed within 90 days
- 48-hour setup with full data backup and rollback capabilities
- 30-day results timeline or full refund
- SOC 2 certified enterprise-grade security
- 90-day money-back guarantee if you're not completely satisfied

Looking forward to helping you capture that ${monthly_increase:,.0f} monthly opportunity and transform your business operations.

Best regards,
The Chime Team

Chime | AI-Powered Revenue Growth Solutions
hello@chimehq.co | chimehq.co
"""

        # Create subject line with personalization
        subject = f"{first_name}, your ${monthly_increase:,.0f}/month revenue opportunity analysis is ready"
        
        # Send email using improved SendGrid function
        success = send_email_via_sendgrid_improved(
            to_email=email,
            subject=subject,
            html_content=html_content,
            first_name=first_name
        )
        
        print(f"🔍 DEBUG: ROI email send result: {success}")
        return success
        
    except Exception as e:
        print(f"❌ ERROR in send_roi_report_email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    """Send ROI report email to user with improved deliverability"""
    try:
        print(f"🔍 Debug: Starting ROI report email for {email}")
        
        # Map business category to readable format
        category_mapping = {
            'electronics-tech': 'Electronics & Technology',
            'fashion-apparel': 'Fashion & Apparel', 
            'health-wellness': 'Health & Wellness',
            'home-garden': 'Home & Garden',
            'food-beverage': 'Food & Beverage',
            'beauty-cosmetics': 'Beauty & Cosmetics',
            'sports-fitness': 'Sports & Fitness',
            'automotive': 'Automotive',
            'other': 'E-commerce'
        }
        
        # Get business category from form_data if available
        business_category = 'E-commerce'  # default
        if form_data and 'business_category' in form_data:
            business_category = category_mapping.get(form_data['business_category'], 'E-commerce')
        
        # Calculate time savings based on manual tasks
        time_saved = 20  # default
        if form_data and 'hours_week_manual_tasks' in form_data:
            hours_range = form_data['hours_week_manual_tasks']
            if hours_range == '1-10':
                time_saved = 15
            elif hours_range == '11-20':
                time_saved = 25
            elif hours_range == '21-40':
                time_saved = 35
            elif hours_range == '40+':
                time_saved = 50
        
        # Format currency values
        monthly_increase = f"${roi_data['monthly_increase']:,.0f}"
        annual_growth = f"${roi_data['annual_increase']:,.0f}"
        
        # Create business-focused subject line for better deliverability
        subject = f"{first_name}, your {monthly_increase} revenue potential analysis is ready"
        
        # Create HTML email with improved deliverability
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Revenue Growth Analysis - Chime</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333333; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                
                <!-- Header -->
                <div style="background-color: #ffffff; padding: 30px 40px 20px; border-bottom: 1px solid #e9ecef;">
                    <div style="text-align: center;">
                        <h1 style="margin: 0; color: #2c3e50; font-size: 24px; font-weight: 600;">Chime</h1>
                        <p style="margin: 5px 0 0; color: #6c757d; font-size: 14px;">Revenue Growth Analysis</p>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 40px;">
                    <p style="margin: 0 0 20px; font-size: 16px; color: #2c3e50;">Hi {first_name},</p>
                    
                    <p style="margin: 0 0 25px; font-size: 16px; line-height: 1.6;">
                        Congratulations on taking the first step toward transforming your store's performance. Based on your current metrics, we've identified specific opportunities that could add <strong>{monthly_increase}</strong> to your monthly revenue within 60 days.
                    </p>
                    
                    <!-- Results Section -->
                    <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 25px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                        <h2 style="margin: 0 0 15px; color: #2c3e50; font-size: 20px; font-weight: 600;">Your Custom Revenue Growth Analysis Results</h2>
                        <p style="margin: 0 0 20px; color: #6c757d; font-size: 14px;">Conservative projections based on 500+ successful {business_category} implementations:</p>
                        
                        <div style="margin: 20px 0;">
                            <h3 style="margin: 0 0 15px; color: #007bff; font-size: 18px;">Your Growth Potential</h3>
                            
                            <div style="margin: 15px 0;">
                                <p style="margin: 0 0 5px; font-weight: 600; color: #2c3e50;">Projected Monthly Revenue Increase</p>
                                <p style="margin: 0; font-size: 24px; font-weight: 700; color: #28a745;">{monthly_increase}</p>
                            </div>
                            
                            <div style="margin: 15px 0;">
                                <p style="margin: 0 0 5px; font-weight: 600; color: #2c3e50;">Projected Annual Revenue Growth</p>
                                <p style="margin: 0; font-size: 20px; font-weight: 600; color: #007bff;">{annual_growth}</p>
                            </div>
                            
                            <div style="margin: 15px 0;">
                                <p style="margin: 0 0 5px; font-weight: 600; color: #2c3e50;">Time Saved on Manual Tasks</p>
                                <p style="margin: 0; font-size: 18px; font-weight: 600; color: #6f42c1;">{time_saved} hours/month</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Guarantee Section -->
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; margin: 25px 0; border-radius: 8px;">
                        <h3 style="margin: 0 0 10px; color: #856404; font-size: 18px;">Risk-Free Implementation Guarantee</h3>
                        <p style="margin: 0; color: #856404; font-size: 14px; line-height: 1.5;">
                            Unlike other AI tools that promise but don't deliver, our 48-hour setup includes full data backup and rollback capabilities. If you don't see measurable results in 30 days, we'll refund your investment completely.
                        </p>
                    </div>
                    
                    <!-- Testimonial -->
                    <div style="background-color: #e8f5e8; border-left: 4px solid #28a745; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                        <h3 style="margin: 0 0 15px; color: #155724; font-size: 16px;">What Other Leaders Are Saying</h3>
                        <p style="margin: 0 0 10px; font-style: italic; color: #155724; line-height: 1.5;">
                            "Our abandoned cart recovery went from 12% to 67% in just 3 weeks. Chime's AI services identified customer behavior patterns we never noticed. Implementation was seamless, and the team supported us through every step. ROI was 340% in the first quarter."
                        </p>
                        <p style="margin: 0; font-weight: 600; color: #155724; font-size: 14px;">
                            — Sarah Chen, Founder of PetStyle Co. (Generated $2.3M revenue in 2024)
                        </p>
                    </div>
                    
                    <!-- Next Steps -->
                    <div style="margin: 30px 0;">
                        <h3 style="margin: 0 0 20px; color: #2c3e50; font-size: 20px;">Your Next Steps</h3>
                        <p style="margin: 0 0 20px; color: #2c3e50;">Book a Strategy Call this week. During our 30-minute consultation, we'll:</p>
                        
                        <div style="margin: 20px 0;">
                            <div style="margin: 15px 0; padding: 15px 0; border-bottom: 1px solid #e9ecef;">
                                <p style="margin: 0; font-weight: 600; color: #007bff;">1. Schedule a 30-minute strategy call</p>
                                <p style="margin: 5px 0 0; color: #6c757d; font-size: 14px;">Meet with our founder to discuss your specific growth opportunities.</p>
                            </div>
                            
                            <div style="margin: 15px 0; padding: 15px 0; border-bottom: 1px solid #e9ecef;">
                                <p style="margin: 0; font-weight: 600; color: #007bff;">2. Receive your custom implementation plan</p>
                                <p style="margin: 5px 0 0; color: #6c757d; font-size: 14px;">We'll create a tailored 90-day roadmap for your business.</p>
                            </div>
                            
                            <div style="margin: 15px 0; padding: 15px 0;">
                                <p style="margin: 0; font-weight: 600; color: #007bff;">3. Start seeing results in 30 days</p>
                                <p style="margin: 5px 0 0; color: #6c757d; font-size: 14px;">Our 48-hour setup means you'll see growth quickly.</p>
                            </div>
                        </div>
                        
                        <!-- CTA Button -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://calendly.com/chimehq/strategy-call" style="display: inline-block; background-color: #007bff; color: #ffffff; text-decoration: none; padding: 15px 30px; border-radius: 8px; font-weight: 600; font-size: 16px;">Schedule Your Strategy Call →</a>
                        </div>
                    </div>
                    
                    <!-- Closing -->
                    <div style="margin: 40px 0 20px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                        <p style="margin: 0 0 10px; color: #2c3e50;">Best regards,</p>
                        <p style="margin: 0; font-weight: 600; color: #2c3e50;">The Chime Team</p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 20px 40px; border-top: 1px solid #e9ecef; text-align: center;">
                    <p style="margin: 0 0 10px; color: #6c757d; font-size: 12px;">
                        Chime | Revenue Growth Solutions<br>
                        <a href="mailto:hello@chimehq.co" style="color: #007bff; text-decoration: none;">hello@chimehq.co</a>
                    </p>
                    <p style="margin: 0; color: #6c757d; font-size: 11px;">
                        <a href="#" style="color: #6c757d; text-decoration: none;">Unsubscribe</a> | 
                        <a href="https://chimehq.co" style="color: #6c757d; text-decoration: none;">Visit our website</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        print(f"🔍 Debug: Calling send_email_via_sendgrid for ROI report")
        
        # Send via SendGrid with improved deliverability settings
        success = send_email_via_sendgrid_improved(email, subject, html, first_name)
        
        if success:
            print(f"✅ ROI Report Email successfully sent to {email}")
        else:
            print(f"❌ Failed to send ROI Report Email to {email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error sending ROI report email: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return False    # Create lead scoring
        score = calculate_lead_score(form_data, roi_data)
        
        subject = f"🚨 New ROI Calculator Lead - {form_data.get('company', 'Unknown Company')} (Score: {score}/100)"
        recipient_emails = ["hello@chimehq.co"]
        
        # Create HTML content
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
              <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🚨 New ROI Calculator Lead</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 18px;">Lead Score: {score}/100</p>
              </div>
              
              <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">👤 Contact Information</h3>
                <ul style="list-style: none; padding: 0;">
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Name:</strong> {form_data.get('first_name', '')} {form_data.get('last_name', '')}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Email:</strong> <a href="mailto:{form_data.get('email', '')}">{form_data.get('email', '')}</a></li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Company:</strong> {form_data.get('company', 'N/A')}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Phone:</strong> {form_data.get('phone', 'N/A')}</li>
                  <li style="padding: 8px 0;"><strong>Website:</strong> {form_data.get('website', 'N/A')}</li>
                </ul>
              </div>
              
              <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">💰 Business Metrics</h3>
                <ul style="list-style: none; padding: 0;">
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Monthly Revenue:</strong> ${float(form_data.get('monthly_revenue', 0)):,.0f}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Average Order Value:</strong> ${float(form_data.get('average_order_value', 0)):,.0f}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Monthly Orders:</strong> {float(form_data.get('monthly_orders', 0)):,.0f}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Business Category:</strong> {form_data.get('business_category', 'N/A')}</li>
                  <li style="padding: 8px 0;"><strong>Business Stage:</strong> {form_data.get('business_stage', 'N/A')}</li>
                </ul>
              </div>
              
              <div style="background: #e8f5e8; padding: 25px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #28a745;">
                <h3 style="color: #28a745; margin-top: 0;">🎯 ROI Projections</h3>
                <ul style="list-style: none; padding: 0;">
                  <li style="padding: 8px 0; border-bottom: 1px solid #d4edda;"><strong>Monthly Revenue Increase:</strong> +${roi_data['monthly_increase']:,.0f}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #d4edda;"><strong>Annual Revenue Increase:</strong> +${roi_data['annual_increase']:,.0f}</li>
                  <li style="padding: 8px 0; border-bottom: 1px solid #d4edda;"><strong>Annual ROI:</strong> {roi_data['annual_roi']:.0f}%</li>
                  <li style="padding: 8px 0;"><strong>Payback Period:</strong> {roi_data['payback_period']:.1f} months</li>
                </ul>
              </div>
              
              <div style="background: #fff3cd; padding: 25px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #ffc107;">
                <h3 style="color: #856404; margin-top: 0;">⚠️ Challenges & Goals</h3>
                <p><strong>Manual Tasks:</strong> {form_data.get('hours_week_manual_tasks', 'N/A')} hours/week</p>
                <p><strong>Biggest Challenges:</strong> {', '.join(form_data.get('biggest_challenges', []))}</p>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <p style="font-size: 18px; font-weight: bold; color: #667eea;">Follow up within 24 hours for best conversion!</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        print(f"🔍 Debug: Sending lead notification to {len(recipient_emails)} recipients")
        
        # Send to each recipient
        all_success = True
        for recipient in recipient_emails:
            success = send_email_via_sendgrid(recipient, subject, html)
            if success:
                print(f"✅ Lead notification email successfully sent to {recipient}")
            else:
                print(f"❌ Failed to send lead notification email to {recipient}")
                all_success = False
        
        return all_success
        
    except Exception as e:
        print(f"❌ Error sending lead notification: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return False

def calculate_lead_score(form_data, roi_data):
    """Calculate lead score based on form data and ROI projections"""
    score = 0
    
    # Revenue-based scoring
    monthly_revenue = float(form_data.get('monthly_revenue', 0))
    if monthly_revenue > 100000:
        score += 30
    elif monthly_revenue > 50000:
        score += 20
    elif monthly_revenue > 25000:
        score += 10
    
    # Business stage scoring
    business_stage = form_data.get('business_stage', '')
    if business_stage in ['growth', 'established', 'enterprise']:
        score += 20
    
    # ROI potential scoring
    if roi_data['monthly_increase'] > 10000:
        score += 30
    elif roi_data['monthly_increase'] > 5000:
        score += 20
    elif roi_data['monthly_increase'] > 2000:
        score += 10
    
    # Contact info completeness
    if form_data.get('phone'):
        score += 10
    if form_data.get('website'):
        score += 10
    
    return min(score, 100)

def submit_to_hubspot(form_data, roi_data):
    """Submit lead data to HubSpot"""
    try:
        print(f"🔍 Debug: Starting HubSpot submission")
        
        # HubSpot API configuration using environment variables
        hubspot_api_key = os.environ.get('HUBSPOT_API_KEY', '')
        hubspot_portal_id = os.environ.get('HUBSPOT_PORTAL_ID', '')
        
        print(f"🔍 Debug: HubSpot API key configured: {'Yes' if hubspot_api_key else 'No'}")
        print(f"🔍 Debug: HubSpot Portal ID configured: {'Yes' if hubspot_portal_id else 'No'}")
        
        if not hubspot_api_key or not hubspot_portal_id:
            print("⚠️  HubSpot credentials not configured")
            return False
        
        # Calculate lead score
        lead_score = calculate_lead_score(form_data, roi_data)
        
        print(f"🔍 Debug: Lead score calculated: {lead_score}")
        
        # Create/Update Contact in HubSpot
        contact_data = {
            "properties": {
                "email": form_data.get('email', ''),
                "firstname": form_data.get('first_name', ''),
                "lastname": form_data.get('last_name', ''),
                "company": form_data.get('company', ''),
                "phone": form_data.get('phone', ''),
                "website": form_data.get('website', ''),
                "lifecyclestage": "lead",
                # Store additional data in notes field (using standard notes property)
                "notes": f"ROI Calculator Submission - Monthly Revenue: ${form_data.get('monthly_revenue', '')}, Business Category: {form_data.get('business_category', '')}, Projected Monthly Increase: ${roi_data['monthly_increase']}, Lead Score: {lead_score}"
            }
        }
        
        print(f"🔍 Debug: Creating HubSpot contact for {form_data.get('email', '')}")
        
        # Create contact
        contact_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        contact_headers = {
            "Authorization": f"Bearer {hubspot_api_key}",
            "Content-Type": "application/json"
        }
        
        contact_response = requests.post(contact_url, headers=contact_headers, json=contact_data)
        
        print(f"🔍 Debug: HubSpot contact response status: {contact_response.status_code}")
        
        if contact_response.status_code == 201:
            contact_id = contact_response.json().get('id')
            print(f"✅ HubSpot contact created: {contact_id}")
        elif contact_response.status_code == 409:
            # Contact already exists, update it
            email = form_data.get('email', '')
            update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{email}?idProperty=email"
            update_response = requests.patch(update_url, headers=contact_headers, json=contact_data)
            print(f"🔍 Debug: HubSpot contact update response status: {update_response.status_code}")
            if update_response.status_code == 200:
                contact_id = update_response.json().get('id')
                print(f"✅ HubSpot contact updated: {contact_id}")
            else:
                print(f"❌ Failed to update HubSpot contact: {update_response.status_code} - {update_response.text}")
                return False
        else:
            print(f"❌ Failed to create HubSpot contact: {contact_response.status_code} - {contact_response.text}")
            return False
        
        print(f"🔍 Debug: Creating HubSpot deal")
        
        # Create Deal in HubSpot
        deal_data = {
            "properties": {
                "dealname": f"ROI Calculator Lead - {form_data.get('company', 'Unknown Company')}",
                "dealstage": "appointmentscheduled",
                "pipeline": "default",
                "amount": str(roi_data['annual_increase']),
                "closedate": "",
                "hubspot_owner_id": "",
                "deal_source": "ROI Calculator",
                "monthly_revenue": str(form_data.get('monthly_revenue', '')),
                "projected_increase": str(roi_data['monthly_increase']),
                "lead_score": str(lead_score)
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]
                }
            ]
        }
        
        deal_url = "https://api.hubapi.com/crm/v3/objects/deals"
        deal_response = requests.post(deal_url, headers=contact_headers, json=deal_data)
        
        print(f"🔍 Debug: HubSpot deal response status: {deal_response.status_code}")
        
        if deal_response.status_code == 201:
            deal_id = deal_response.json().get('id')
            print(f"✅ HubSpot deal created: {deal_id}")
        else:
            print(f"❌ Failed to create HubSpot deal: {deal_response.status_code} - {deal_response.text}")
        
        print(f"✅ HubSpot integration complete - Lead score: {lead_score}/100")
        return True
        
    except Exception as e:
        print(f"❌ Error submitting to HubSpot: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return False


def send_lead_notification_email(form_data, roi_data):
    """
    Send lead notification email to Chime team when a new ROI calculator submission is received
    """
    try:
        print(f"🔍 DEBUG: Starting lead notification email")
        
        # Extract form data with safe defaults
        first_name = form_data.get('first_name', 'Unknown')
        last_name = form_data.get('last_name', 'User')
        email = form_data.get('email', 'No email provided')
        company = form_data.get('company', 'Unknown Company')
        phone = form_data.get('phone', 'Not provided')
        website = form_data.get('website', 'Not provided')
        
        # Business metrics with safe conversion
        try:
            monthly_revenue = float(form_data.get('monthly_revenue', 0))
            monthly_orders = float(form_data.get('monthly_orders', 0))
            average_order_value = float(form_data.get('average_order_value', 0))
            cart_abandonment_rate = float(form_data.get('cart_abandonment_rate', 0))
            current_conversion_rate = float(form_data.get('current_conversion_rate', 0))
        except (ValueError, TypeError):
            monthly_revenue = 0
            monthly_orders = 0
            average_order_value = 0
            cart_abandonment_rate = 0
            current_conversion_rate = 0
        
        business_category = form_data.get('business_category', 'Not specified')
        business_stage = form_data.get('business_stage', 'Not specified')
        hours_week_manual_tasks = form_data.get('hours_week_manual_tasks', 'Not specified')
        biggest_challenges = form_data.get('biggest_challenges', [])
        
        # ROI projections
        monthly_increase = roi_data.get('monthly_increase', 0)
        annual_increase = roi_data.get('annual_increase', 0)
        
        # Calculate lead score
        lead_score = 0
        if monthly_revenue > 100000:
            lead_score += 30
        elif monthly_revenue > 50000:
            lead_score += 20
        elif monthly_revenue > 10000:
            lead_score += 10
            
        if cart_abandonment_rate > 60:
            lead_score += 20
        elif cart_abandonment_rate > 40:
            lead_score += 10
            
        if current_conversion_rate < 3:
            lead_score += 15
            
        if business_stage in ['Growth (2-5 years)', 'Established (5+ years)']:
            lead_score += 15
            
        if len(biggest_challenges) >= 3:
            lead_score += 10
        
        # Create notification email content with professional subject
        subject = f"ROI Calculator Submission - {company} (Lead Score: {lead_score}/100)"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New ROI Calculator Lead</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px;">ROI Calculator Submission</h1>
                <p style="margin: 10px 0 0; font-size: 18px; opacity: 0.9;">Lead Score: {lead_score}/100</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                <h2 style="color: #2c3e50; margin-top: 0;">Contact Information</h2>
                <p><strong>Name:</strong> {first_name} {last_name}</p>
                <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                <p><strong>Company:</strong> {company}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Website:</strong> {website}</p>
            </div>
            
            <div style="background: #e8f5e8; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                <h2 style="color: #27ae60; margin-top: 0;">Business Metrics</h2>
                <p><strong>Monthly Revenue:</strong> ${monthly_revenue:,.0f}</p>
                <p><strong>Monthly Orders:</strong> {monthly_orders:,.0f}</p>
                <p><strong>Average Order Value:</strong> ${average_order_value:.2f}</p>
                <p><strong>Conversion Rate:</strong> {current_conversion_rate:.1f}%</p>
                <p><strong>Cart Abandonment Rate:</strong> {cart_abandonment_rate:.0f}%</p>
                <p><strong>Business Category:</strong> {business_category}</p>
                <p><strong>Business Stage:</strong> {business_stage}</p>
                <p><strong>Manual Tasks Hours/Week:</strong> {hours_week_manual_tasks}</p>
            </div>
            
            <div style="background: #fff3cd; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                <h2 style="color: #856404; margin-top: 0;">Revenue Opportunity</h2>
                <p><strong>Projected Monthly Increase:</strong> ${monthly_increase:,.0f}</p>
                <p><strong>Projected Annual Increase:</strong> ${annual_increase:,.0f}</p>
                <p><strong>ROI Potential:</strong> {(monthly_increase/monthly_revenue*100) if monthly_revenue > 0 else 0:.1f}% monthly growth</p>
            </div>
            
            <div style="background: #f8d7da; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                <h2 style="color: #721c24; margin-top: 0;">Biggest Challenges</h2>
                <ul>
                    {"".join([f"<li>{challenge}</li>" for challenge in biggest_challenges])}
                </ul>
            </div>
            
            <div style="background: #d1ecf1; padding: 25px; border-radius: 10px; text-align: center;">
                <h2 style="color: #0c5460; margin-top: 0;">Next Steps</h2>
                <p>This lead has been automatically added to HubSpot CRM.</p>
                <p><strong>Recommended Action:</strong> {"High Priority - Contact within 2 hours" if lead_score >= 70 else "Medium Priority - Contact within 24 hours" if lead_score >= 50 else "Standard Priority - Contact within 48 hours"}</p>
                <a href="mailto:{email}?subject=Re: Your Revenue Growth Analysis for {company}" style="display: inline-block; background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px;">Reply to Lead</a>
            </div>
        </body>
        </html>
        """
        
        # Send email using SendGrid
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            print("❌ SendGrid API key not configured for lead notifications")
            return False
        
        # Send to Chime team
        notification_email = "hello@chimehq.co"  # Chime team email
        
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": notification_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": "hello@chimehq.co",
                "name": "Chime ROI Calculator"
            },
            "reply_to": {
                "email": "hello@chimehq.co",
                "name": "Chime Team"
            },
            "content": [
                {"type": "text/html", "value": html_content}
            ],
            "categories": ["lead-notification", "roi-calculator"],
            "custom_args": {
                "campaign": "lead_notifications",
                "source": "roi_calculator",
                "lead_score": str(lead_score)
            },
            "tracking_settings": {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True},
                "subscription_tracking": {"enable": False}
            },
            "mail_settings": {
                "bypass_list_management": {"enable": False},
                "footer": {"enable": False},
                "sandbox_mode": {"enable": False}
            }
        }
        
        headers = {
            "Authorization": f"Bearer {sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=email_data
        )
        
        if response.status_code == 202:
            print(f"✅ Lead notification email sent successfully to {notification_email}")
            return True
        else:
            print(f"❌ Failed to send lead notification email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending lead notification email: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return False

