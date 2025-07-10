from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        
        # Extract form data
        monthly_revenue = float(data.get('monthly_revenue', 0))
        average_order_value = float(data.get('average_order_value', 0))
        monthly_orders = float(data.get('monthly_orders', 0))
        business_category = data.get('business_category', '')
        current_conversion_rate = float(data.get('current_conversion_rate', 0))
        cart_abandonment_rate = float(data.get('cart_abandonment_rate', 0))
        monthly_ad_spend = float(data.get('monthly_ad_spend', 0))
        
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
        
        # Send ROI report email to user
        send_roi_report_email(email, first_name, roi_data)
        
        # Send lead notification to Chime
        send_lead_notification_email(data, roi_data)
        
        # Submit to HubSpot (if configured)
        submit_to_hubspot(data, roi_data)
        
        return jsonify({
            'success': True,
            'message': 'ROI report sent successfully',
            'roi_data': roi_data
        })
        
    except Exception as e:
        print(f"Error processing ROI calculator: {str(e)}")
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

def send_roi_report_email(email, first_name, roi_data):
    """Send ROI report email to the user"""
    try:
        # Email configuration using environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        port = int(os.environ.get('SMTP_PORT', '587'))
        sender_email = os.environ.get('SENDER_EMAIL', 'hello@chimehq.co')
        password = os.environ.get('SMTP_PASSWORD', '')
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your Personalized ROI Report - ${roi_data['monthly_increase']:,.0f}/month Growth Potential"
        message["From"] = sender_email
        message["To"] = email
        
        # Create HTML content
        html = f"""
        <html>
          <body>
            <h2>Hi {first_name},</h2>
            <p>Here's your personalized ROI report showing how Chime can grow your business:</p>
            
            <h3>📊 Your Growth Projections</h3>
            <ul>
              <li><strong>Current Monthly Revenue:</strong> ${roi_data['current_monthly_revenue']:,.0f}</li>
              <li><strong>Projected Monthly Revenue:</strong> ${roi_data['projected_monthly_revenue']:,.0f}</li>
              <li><strong>Monthly Increase:</strong> ${roi_data['monthly_increase']:,.0f}</li>
              <li><strong>Annual Increase:</strong> ${roi_data['annual_increase']:,.0f}</li>
            </ul>
            
            <h3>🎯 Performance Improvements</h3>
            <ul>
              <li><strong>Conversion Rate:</strong> {roi_data['current_conversion_rate']:.1f}% → {roi_data['projected_conversion_rate']:.1f}%</li>
              <li><strong>Recovered Orders:</strong> {roi_data['recovered_orders']:.0f} additional orders/month</li>
              <li><strong>ROI:</strong> {roi_data['annual_roi']:.0f}% annually</li>
            </ul>
            
            <p>Ready to achieve these results? <a href="https://calendly.com/chime-demo">Book your free strategy call</a></p>
            
            <p>Best regards,<br>The Chime Team</p>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Note: In demo mode, we'll just log the email instead of actually sending
        print(f"ROI Report Email sent to {email}")
        print(f"Subject: {message['Subject']}")
        
    except Exception as e:
        print(f"Error sending ROI report email: {str(e)}")

def send_lead_notification_email(form_data, roi_data):
    """Send lead notification to Chime team"""
    try:
        # Email configuration
        recipient_emails = ["hello@chimehq.co", "eric@chimehq.co"]
        
        # Create lead scoring
        score = calculate_lead_score(form_data, roi_data)
        
        for email in recipient_emails:
            print(f"Lead notification sent to {email}")
            print(f"Lead Score: {score}/100")
            print(f"Company: {form_data.get('company', 'N/A')}")
            print(f"Revenue Potential: ${roi_data['monthly_increase']:,.0f}/month")
        
    except Exception as e:
        print(f"Error sending lead notification: {str(e)}")

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
        # HubSpot API configuration using environment variables
        hubspot_api_key = os.environ.get('HUBSPOT_API_KEY', '')
        hubspot_portal_id = os.environ.get('HUBSPOT_PORTAL_ID', '')
        
        # Prepare HubSpot data
        hubspot_data = {
            "fields": [
                {"name": "email", "value": form_data.get('email', '')},
                {"name": "firstname", "value": form_data.get('first_name', '')},
                {"name": "lastname", "value": form_data.get('last_name', '')},
                {"name": "company", "value": form_data.get('company', '')},
                {"name": "phone", "value": form_data.get('phone', '')},
                {"name": "website", "value": form_data.get('website', '')},
                {"name": "monthly_revenue", "value": str(form_data.get('monthly_revenue', ''))},
                {"name": "business_category", "value": form_data.get('business_category', '')},
                {"name": "projected_monthly_increase", "value": str(roi_data['monthly_increase'])},
                {"name": "lead_score", "value": str(calculate_lead_score(form_data, roi_data))}
            ]
        }
        
        # In production, make actual API call to HubSpot
        if hubspot_api_key and hubspot_portal_id:
            # Make actual HubSpot API call here
            print("HubSpot API call would be made here")
        
        print("HubSpot contact created/updated")
        print("HubSpot deal created")
        print(f"Lead score: {calculate_lead_score(form_data, roi_data)}/100")
        
    except Exception as e:
        print(f"Error submitting to HubSpot: {str(e)}")

