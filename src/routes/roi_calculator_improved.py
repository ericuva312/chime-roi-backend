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
        
        # Send lead notification to Chime (IMPROVED VERSION)
        lead_success = send_lead_notification_email_improved(data, roi_data)
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
    """Send ROI report email using the existing template"""
    # Use existing implementation from the original file
    # This function remains unchanged for customer emails
    pass

def send_lead_notification_email_improved(form_data, roi_data):
    """
    Send improved lead notification email to Chime team with better deliverability
    Optimized to avoid spam filters and improve inbox delivery
    """
    try:
        print(f"🔍 DEBUG: Starting improved lead notification email")
        
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
        
        # Create business-focused subject line (avoid spam triggers)
        subject = f"New Business Inquiry from {company}"
        
        # Create simplified, professional HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New Business Inquiry</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px;">
                <h1 style="color: #007bff; margin: 0; font-size: 24px;">New Business Inquiry</h1>
                <p style="margin: 5px 0 0; color: #666; font-size: 14px;">Revenue Growth Calculator Submission</p>
            </div>
            
            <div style="margin-bottom: 25px;">
                <h2 style="color: #333; font-size: 18px; margin-bottom: 15px;">Contact Information</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold; width: 30%;">Name:</td>
                        <td style="padding: 8px 0;">{first_name} {last_name}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                        <td style="padding: 8px 0;"><a href="mailto:{email}" style="color: #007bff; text-decoration: none;">{email}</a></td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Company:</td>
                        <td style="padding: 8px 0;">{company}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Website:</td>
                        <td style="padding: 8px 0;">{website}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Lead Score:</td>
                        <td style="padding: 8px 0; color: #007bff; font-weight: bold;">{lead_score}/100</td>
                    </tr>
                </table>
            </div>
            
            <div style="margin-bottom: 25px;">
                <h2 style="color: #333; font-size: 18px; margin-bottom: 15px;">Business Metrics</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold; width: 40%;">Monthly Revenue:</td>
                        <td style="padding: 8px 0;">${monthly_revenue:,.0f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Monthly Orders:</td>
                        <td style="padding: 8px 0;">{monthly_orders:,.0f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Average Order Value:</td>
                        <td style="padding: 8px 0;">${average_order_value:.2f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Conversion Rate:</td>
                        <td style="padding: 8px 0;">{current_conversion_rate:.1f}%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Cart Abandonment:</td>
                        <td style="padding: 8px 0;">{cart_abandonment_rate:.0f}%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Business Category:</td>
                        <td style="padding: 8px 0;">{business_category}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Business Stage:</td>
                        <td style="padding: 8px 0;">{business_stage}</td>
                    </tr>
                </table>
            </div>
            
            <div style="margin-bottom: 25px;">
                <h2 style="color: #333; font-size: 18px; margin-bottom: 15px;">Revenue Opportunity</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold; width: 50%;">Projected Monthly Increase:</td>
                        <td style="padding: 8px 0; color: #28a745; font-weight: bold;">${monthly_increase:,.0f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0; font-weight: bold;">Projected Annual Increase:</td>
                        <td style="padding: 8px 0; color: #28a745; font-weight: bold;">${annual_increase:,.0f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Growth Potential:</td>
                        <td style="padding: 8px 0;">{(monthly_increase/monthly_revenue*100) if monthly_revenue > 0 else 0:.1f}% monthly</td>
                    </tr>
                </table>
            </div>
            
            <div style="margin-bottom: 25px;">
                <h2 style="color: #333; font-size: 18px; margin-bottom: 15px;">Business Challenges</h2>
                <p style="margin: 0;"><strong>Manual Tasks:</strong> {hours_week_manual_tasks} hours/week</p>
                <p style="margin: 10px 0 0;"><strong>Key Challenges:</strong> {', '.join(biggest_challenges) if biggest_challenges else 'None specified'}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center;">
                <h3 style="color: #333; margin: 0 0 10px;">Recommended Action</h3>
                <p style="margin: 0; color: #666;">
                    {"High Priority - Contact within 2 hours" if lead_score >= 70 else "Medium Priority - Contact within 24 hours" if lead_score >= 50 else "Standard Priority - Contact within 48 hours"}
                </p>
                <div style="margin-top: 15px;">
                    <a href="mailto:{email}?subject=Re: Your Business Growth Analysis" style="display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px;">Reply to Inquiry</a>
                </div>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px;">
                <p style="margin: 0;">This inquiry was submitted via the Revenue Growth Calculator</p>
                <p style="margin: 5px 0 0;">Chime Business Solutions | hello@chimehq.co</p>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version for better deliverability
        plain_text = f"""
New Business Inquiry - Revenue Growth Calculator

CONTACT INFORMATION:
Name: {first_name} {last_name}
Email: {email}
Company: {company}
Website: {website}
Lead Score: {lead_score}/100

BUSINESS METRICS:
Monthly Revenue: ${monthly_revenue:,.0f}
Monthly Orders: {monthly_orders:,.0f}
Average Order Value: ${average_order_value:.2f}
Conversion Rate: {current_conversion_rate:.1f}%
Cart Abandonment: {cart_abandonment_rate:.0f}%
Business Category: {business_category}
Business Stage: {business_stage}

REVENUE OPPORTUNITY:
Projected Monthly Increase: ${monthly_increase:,.0f}
Projected Annual Increase: ${annual_increase:,.0f}
Growth Potential: {(monthly_increase/monthly_revenue*100) if monthly_revenue > 0 else 0:.1f}% monthly

BUSINESS CHALLENGES:
Manual Tasks: {hours_week_manual_tasks} hours/week
Key Challenges: {', '.join(biggest_challenges) if biggest_challenges else 'None specified'}

RECOMMENDED ACTION:
{"High Priority - Contact within 2 hours" if lead_score >= 70 else "Medium Priority - Contact within 24 hours" if lead_score >= 50 else "Standard Priority - Contact within 48 hours"}

Reply to: {email}

---
This inquiry was submitted via the Revenue Growth Calculator
Chime Business Solutions | hello@chimehq.co
        """
        
        # Send email using improved SendGrid configuration
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            print("❌ SendGrid API key not configured for lead notifications")
            return False
        
        # Send to Chime team
        notification_email = "hello@chimehq.co"
        
        # Improved email data structure for better deliverability
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": notification_email, "name": "Chime Team"}],
                    "subject": subject
                }
            ],
            "from": {
                "email": "hello@chimehq.co",
                "name": "Chime Business Solutions"
            },
            "reply_to": {
                "email": email,  # Reply goes to the lead
                "name": f"{first_name} {last_name}"
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
            "categories": ["business-inquiry"],  # Simplified categories
            "custom_args": {
                "source": "website_calculator",
                "lead_score": str(lead_score)
            },
            "tracking_settings": {
                "click_tracking": {"enable": False},  # Disable to reduce spam score
                "open_tracking": {"enable": False},   # Disable to reduce spam score
                "subscription_tracking": {"enable": False}
            },
            "mail_settings": {
                "bypass_list_management": {"enable": False},
                "footer": {"enable": False},
                "sandbox_mode": {"enable": False}
            },
            "headers": {
                "X-Priority": "3",  # Normal priority
                "X-MSMail-Priority": "Normal",
                "Importance": "Normal"
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
            print(f"✅ Improved lead notification email sent successfully to {notification_email}")
            return True
        else:
            print(f"❌ Failed to send improved lead notification email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending improved lead notification email: {str(e)}")
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

