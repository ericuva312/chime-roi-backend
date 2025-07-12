#!/usr/bin/env python3

# Fixed payment email functions that use proper SendGrid templates instead of ROI calculator emails

def send_payment_confirmation_email(customer_email, customer_name, plan_name, amount, is_recurring=False):
    """Send payment confirmation email to customer using proper SendGrid template"""
    import os
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    from datetime import datetime
    
    try:
        # SendGrid configuration
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        
        # Use proper payment confirmation template
        subject = f"Payment Confirmation - {plan_name}"
        
        # Create the email using SendGrid template
        message = Mail(
            from_email=Email("hello@chimehq.co", "Chime Team"),
            to_emails=To(customer_email),
            subject=subject
        )
        
        # Use the correct payment confirmation template HTML from the attachment
        html_content = f"""<!DOCTYPE html>
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
</html>"""
        
        # Plain text version
        text_content = f"""Payment Confirmation - {plan_name}

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
The Chime Team"""
        
        message.content = [
            Content("text/plain", text_content),
            Content("text/html", html_content)
        ]
        
        # Send the email
        response = sg.send(message)
        
        if response.status_code in [200, 202]:
            print(f"✅ Payment confirmation email sent to {customer_email}")
            return True
        else:
            print(f"❌ Failed to send payment confirmation email: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending payment confirmation email: {str(e)}")
        return False


def send_payment_notification_email(customer_data, plan_name, amount, is_recurring=False):
    """Send payment notification email to admin using proper SendGrid template"""
    import os
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    from datetime import datetime
    
    try:
        # SendGrid configuration
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        
        # Use proper payment notification template
        subject = f"New Payment Received - {plan_name} - {customer_data.get('company', 'N/A')}"
        
        # Create the email using SendGrid template
        message = Mail(
            from_email=Email("hello@chimehq.co", "Chime Team"),
            to_emails=To("hello@chimehq.co"),
            subject=subject
        )
        
        # Use the correct admin payment notification template HTML from the attachment
        html_content = f"""<!DOCTYPE html>
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
</html>"""
        
        # Plain text version
        text_content = f"""New Payment Received - {plan_name} - {customer_data.get('company', 'N/A')}

Payment Details:

Customer Information:
- Name: {customer_data.get('name', 'N/A')}
- Email: {customer_data.get('email', 'N/A')}
- Company: {customer_data.get('company', 'N/A')}
- Phone: {customer_data.get('phone', 'N/A')}
- Shopify Store: {customer_data.get('shopify_url', 'N/A')}

Payment Summary:
- Plan: {plan_name}
- Amount: ${amount:,.2f}
- Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
- Recurring: {"Yes - Monthly billing set up" if is_recurring else "No - One-time payment only"}

Next Steps:
- Contact customer within 24 hours
- Begin implementation process
- Set up 48-hour implementation timeline
- Schedule follow-up for 30-day results check

Customer confirmation email has been sent automatically."""
        
        message.content = [
            Content("text/plain", text_content),
            Content("text/html", html_content)
        ]
        
        # Send the email
        response = sg.send(message)
        
        if response.status_code in [200, 202]:
            print(f"✅ Payment notification email sent to hello@chimehq.co")
            return True
        else:
            print(f"❌ Failed to send payment notification email: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending payment notification email: {str(e)}")
        return False


if __name__ == "__main__":
    print("Fixed payment email functions created successfully!")
    print("These functions use proper SendGrid templates instead of ROI calculator emails.")

