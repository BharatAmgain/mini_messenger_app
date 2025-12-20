# messenger/views.py - COMPLETE VERSION
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.middleware.csrf import get_token


def csrf_failure(request, reason=""):
    """Custom CSRF failure view - FIXED VERSION"""
    # Get CSRF token for the response
    csrf_token = get_token(request)

    # For AJAX requests, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'CSRF verification failed',
            'detail': 'CSRF token missing or incorrect',
            'reason': reason,
            'csrf_token': csrf_token
        }, status=403)

    context = {
        'title': 'Security Verification Failed',
        'message': 'The request could not be processed because a security token was invalid or missing.',
        'detail': 'This is usually caused by:',
        'reasons': [
            'Your session expired (logged out)',
            'You submitted a form without proper security tokens',
            'You tried to access the page from a different browser/tab',
            'The page was open for too long without activity'
        ],
        'reason': reason,
        'csrf_token': csrf_token,
        'user': request.user,
    }
    return render(request, 'errors/csrf_failure.html', context, status=403)


def health_check(request):
    """Simple health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'ok',
        'service': 'Connect.io Messenger',
        'timestamp': 'server_time_placeholder'
    })


@require_GET
def data_deletion_view(request):
    """Facebook-required data deletion instructions page"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Deletion Instructions - Connect.io</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 40px auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #2563eb;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 15px;
            font-size: 2.2em;
        }
        h2 { 
            color: #4b5563;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        h3 {
            color: #374151;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 1.2em;
        }
        .step {
            background: #f8fafc;
            padding: 20px;
            border-left: 4px solid #3b82f6;
            margin: 20px 0;
            border-radius: 8px;
        }
        .warning {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            margin: 10px 5px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
        }
        .button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        ul, ol { 
            padding-left: 25px;
            margin: 15px 0;
        }
        li { 
            margin: 10px 0;
            padding-left: 5px;
        }
        p { margin: 15px 0; }
        .text-center { text-align: center; }
        .mt-40 { margin-top: 40px; }
        .contact-info {
            background: #ecfdf5;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .contact-info p { margin: 8px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Data Deletion Instructions</h1>

        <div class="warning">
            <strong>⚠️ Important:</strong> This page explains how to delete your account and all associated data from Connect.io. Deletion is permanent and cannot be undone.
        </div>

        <h2>🚀 How to Delete Your Account</h2>

        <div class="step">
            <h3>Option 1: Delete from within the App (Recommended)</h3>
            <p>If you have the Connect.io app installed:</p>
            <ol>
                <li>Open the Connect.io app and log in to your account</li>
                <li>Go to <strong>Profile</strong> → <strong>Settings</strong> → <strong>Account Settings</strong></li>
                <li>Click on <strong>"Delete My Account"</strong> button</li>
                <li>Read the warning message carefully</li>
                <li>Enter your password to confirm</li>
                <li>Click <strong>"Permanently Delete Account"</strong></li>
                <li>You will receive a confirmation email within 24 hours</li>
            </ol>
        </div>

        <div class="step">
            <h3>Option 2: Request via Email</h3>
            <p>If you can't access the app or have uninstalled it:</p>
            <ol>
                <li>Send an email to: <strong>support@connect.io</strong></li>
                <li>Use the subject line: <strong>"Account Deletion Request"</strong></li>
                <li>Include the following information:
                    <ul>
                        <li>Your registered email address</li>
                        <li>Your username (if different from email)</li>
                        <li>Your phone number (if registered)</li>
                        <li>Reason for deletion (optional)</li>
                    </ul>
                </li>
                <li>We will verify your identity and send a confirmation email</li>
                <li>We'll confirm deletion within 48 hours</li>
            </ol>
        </div>

        <h2>🗑️ What Gets Deleted?</h2>
        <p>When you delete your account, the following data will be permanently removed:</p>
        <ul>
            <li>✅ Your profile information (name, email, phone number, profile picture)</li>
            <li>✅ All chat messages and conversations (both sent and received)</li>
            <li>✅ Uploaded photos, videos, and media files</li>
            <li>✅ Friends list, connections, and contact information</li>
            <li>✅ Account settings, preferences, and notification settings</li>
            <li>✅ Activity history, login logs, and usage data</li>
            <li>✅ Group memberships and channel subscriptions</li>
        </ul>

        <div class="warning">
            <h3>❗ Important Information</h3>
            <p><strong>Permanent deletion:</strong> Once your account is deleted, it cannot be recovered. All your data will be permanently removed from our servers.</p>
            <p><strong>Processing time:</strong> Complete data removal from all our systems and backups may take up to 30 days.</p>
            <p><strong>Legal retention:</strong> We may retain certain data as required by law (e.g., for fraud prevention, security investigations, or legal compliance). This data will be kept only as long as legally required.</p>
            <p><strong>Messages to others:</strong> Messages you've sent to other users will remain in their accounts unless they also delete them.</p>
        </div>

        <div class="contact-info">
            <h2>📞 Need Help or Have Questions?</h2>
            <p>Contact our support team for assistance:</p>
            <p><strong>📧 Email:</strong> support@connect.io</p>
            <p><strong>⏰ Response time:</strong> 24-48 hours during business days</p>
            <p><strong>📍 Address:</strong> Kavresthali, Kathmandu, Nepal</p>
        </div>

        <div class="text-center mt-40">
            <a href="/" class="button">🏠 Back to Home</a>
            <a href="/privacy-policy/" class="button">📄 Privacy Policy</a>
            <a href="/terms/" class="button">📜 Terms of Service</a>
        </div>

        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 0.9em;">
            <p>© 2025 Connect.io. All rights reserved.</p>
            <p>Last updated: December 2025</p>
        </div>
    </div>
</body>
</html>"""
    return HttpResponse(html_content)


@require_GET
def privacy_policy_view(request):
    """Privacy Policy page"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - Connect.io</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6; 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 40px auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #dc2626;
            text-align: center;
            border-bottom: 3px solid #dc2626;
            padding-bottom: 15px;
            font-size: 2.2em;
            margin-bottom: 30px;
        }
        h2 { 
            color: #4b5563;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 10px;
        }
        .update { 
            background: #fef3c7;
            border: 2px solid #f59e0b;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .section {
            margin: 25px 0;
        }
        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }
        li {
            margin: 10px 0;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            margin: 10px 5px;
            transition: all 0.3s;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .text-center { text-align: center; }
        .mt-40 { margin-top: 40px; }
        .contact-info {
            background: #ecfdf5;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Privacy Policy</h1>

        <div class="update">
            <strong>📅 Last Updated:</strong> December 2025
        </div>

        <div class="section">
            <h2>1. Introduction</h2>
            <p>Welcome to Connect.io. We respect your privacy and are committed to protecting your personal data. This privacy policy explains how we collect, use, and protect your information when you use our messaging service.</p>
        </div>

        <div class="section">
            <h2>2. Information We Collect</h2>
            <h3>2.1 Information You Provide:</h3>
            <ul>
                <li>Account information (name, email, phone number)</li>
                <li>Profile information (photo, bio, location)</li>
                <li>Messages and media you send and receive</li>
                <li>Contacts and friend lists</li>
                <li>Payment information (if applicable)</li>
            </ul>

            <h3>2.2 Automatically Collected Information:</h3>
            <ul>
                <li>Device information (type, OS, browser)</li>
                <li>IP address and location data</li>
                <li>Usage data and interaction logs</li>
                <li>Cookies and similar technologies</li>
            </ul>
        </div>

        <div class="section">
            <h2>3. How We Use Your Information</h2>
            <p>We use your information to:</p>
            <ul>
                <li>Provide and improve our messaging services</li>
                <li>Facilitate communication between users</li>
                <li>Ensure security and prevent fraud</li>
                <li>Send important service updates</li>
                <li>Personalize your experience</li>
                <li>Comply with legal obligations</li>
            </ul>
        </div>

        <div class="section">
            <h2>4. Data Security</h2>
            <p>We implement industry-standard security measures:</p>
            <ul>
                <li>End-to-end encryption for messages</li>
                <li>Secure data transmission (TLS/SSL)</li>
                <li>Regular security audits</li>
                <li>Access controls and authentication</li>
                <li>Data encryption at rest</li>
            </ul>
        </div>

        <div class="section">
            <h2>5. Data Sharing</h2>
            <p>We do NOT sell your personal data. We may share information:</p>
            <ul>
                <li>With your consent</li>
                <li>To comply with legal requirements</li>
                <li>With service providers (under strict confidentiality)</li>
                <li>To protect rights and safety</li>
                <li>During business transfers (merger/acquisition)</li>
            </ul>
        </div>

        <div class="contact-info">
            <h2>6. Contact Information</h2>
            <p>If you have questions about this Privacy Policy:</p>
            <p><strong>📧 Email:</strong> privacy@connect.io</p>
            <p><strong>📞 Phone:</strong> +977-XXXXXXXXXX</p>
            <p><strong>📍 Address:</strong> Kavresthali, Kathmandu, Nepal</p>
        </div>

        <div class="section">
            <h2>7. Your Rights</h2>
            <p>You have the right to:</p>
            <ul>
                <li>Access your personal data</li>
                <li>Correct inaccurate data</li>
                <li>Delete your data (right to be forgotten)</li>
                <li>Restrict processing</li>
                <li>Data portability</li>
                <li>Object to processing</li>
                <li>Withdraw consent</li>
            </ul>
        </div>

        <div class="text-center mt-40">
            <a href="/" class="button">🏠 Back to Home</a>
            <a href="/data-deletion/" class="button">🗑️ Data Deletion</a>
            <a href="/terms/" class="button">📜 Terms of Service</a>
        </div>

        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 0.9em;">
            <p>© 2025 Connect.io. All rights reserved.</p>
            <p>This policy may be updated periodically. Please check back for changes.</p>
        </div>
    </div>
</body>
</html>"""
    return HttpResponse(html_content)


@require_GET
def terms_view(request):
    """Terms of Service page"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - Connect.io</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6; 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 40px auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #0891b2;
            text-align: center;
            border-bottom: 3px solid #0891b2;
            padding-bottom: 15px;
            font-size: 2.2em;
            margin-bottom: 30px;
        }
        h2 { 
            color: #4b5563;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 10px;
        }
        .acceptance {
            background: #dbeafe;
            border: 2px solid #3b82f6;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .section {
            margin: 25px 0;
        }
        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }
        li {
            margin: 10px 0;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            margin: 10px 5px;
            transition: all 0.3s;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .text-center { text-align: center; }
        .mt-40 { margin-top: 40px; }
        .prohibited {
            background: #fee2e2;
            border: 2px solid #ef4444;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📜 Terms of Service</h1>

        <div class="acceptance">
            <p><strong>By using Connect.io, you agree to these Terms of Service. If you disagree, please do not use our service.</strong></p>
        </div>

        <div class="section">
            <h2>1. Acceptance of Terms</h2>
            <p>These Terms of Service ("Terms") govern your use of Connect.io messaging service. By creating an account or using our services, you agree to be bound by these Terms.</p>
        </div>

        <div class="section">
            <h2>2. Eligibility</h2>
            <p>You must be at least 13 years old to use our service. If you are under 18, you confirm that you have parental consent. You are responsible for ensuring your use of Connect.io complies with all applicable laws.</p>
        </div>

        <div class="section">
            <h2>3. Account Responsibility</h2>
            <ul>
                <li>You are responsible for maintaining account security</li>
                <li>You must not share your account credentials</li>
                <li>You are responsible for all activity under your account</li>
                <li>You must provide accurate information during registration</li>
                <li>You must notify us immediately of any security breach</li>
            </ul>
        </div>

        <div class="section">
            <h2>4. Acceptable Use</h2>
            <p>You agree to use Connect.io for lawful purposes only. You must not:</p>

            <div class="prohibited">
                <ul>
                    <li>Harass, threaten, or bully other users</li>
                    <li>Share illegal, harmful, or offensive content</li>
                    <li>Impersonate others or provide false information</li>
                    <li>Attempt to hack or compromise our systems</li>
                    <li>Send spam or unsolicited messages</li>
                    <li>Violate intellectual property rights</li>
                    <li>Collect user data without consent</li>
                    <li>Use automated systems to access our services</li>
                    <li>Distribute viruses or malicious code</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>5. Intellectual Property</h2>
            <p>Connect.io owns all rights, title, and interest in the service. You retain ownership of your content, but grant us a license to display and distribute it as part of our service.</p>
        </div>

        <div class="section">
            <h2>6. Termination</h2>
            <p>We may suspend or terminate your account if you violate these Terms. You may delete your account at any time through the app settings or by contacting support.</p>
        </div>

        <div class="section">
            <h2>7. Limitation of Liability</h2>
            <p>Connect.io is provided "as is" without warranties. We are not liable for:</p>
            <ul>
                <li>Service interruptions or downtime</li>
                <li>Data loss or corruption</li>
                <li>Unauthorized access to your account</li>
                <li>Conduct of other users</li>
                <li>Indirect or consequential damages</li>
            </ul>
        </div>

        <div class="section">
            <h2>8. Changes to Terms</h2>
            <p>We may update these Terms periodically. We will notify you of significant changes. Continued use after changes constitutes acceptance.</p>
        </div>

        <div class="section">
            <h2>9. Governing Law</h2>
            <p>These Terms are governed by the laws of Nepal. Any disputes shall be resolved in the courts of Kathmandu, Nepal.</p>
        </div>

        <div class="section">
            <h2>10. Contact Us</h2>
            <p>For questions about these Terms:</p>
            <p><strong>📧 Email:</strong> legal@connect.io</p>
            <p><strong>📍 Address:</strong> Kavresthali, Kathmandu, Nepal</p>
        </div>

        <div class="text-center mt-40">
            <a href="/" class="button">🏠 Back to Home</a>
            <a href="/privacy-policy/" class="button">🔒 Privacy Policy</a>
            <a href="/data-deletion/" class="button">🗑️ Data Deletion</a>
        </div>

        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 0.9em;">
            <p>© 2025 Connect.io. All rights reserved.</p>
            <p>Last Updated: December 2025</p>
        </div>
    </div>
</body>
</html>"""
    return HttpResponse(html_content)


def home_view(request):
    """Home page view"""
    return render(request, 'home.html', {})