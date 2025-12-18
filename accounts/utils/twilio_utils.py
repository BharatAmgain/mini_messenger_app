# accounts/utils/twilio_utils.py
import requests
import base64
from django.conf import settings


def send_twilio_verification(phone_number):
    """Send verification code via Twilio"""
    if not all([settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_VERIFY_SERVICE_SID]):
        return None, "Twilio not configured"

    service_sid = settings.TWILIO_VERIFY_SERVICE_SID
    url = f"https://verify.twilio.com/v2/Services/{service_sid}/Verifications"

    # Basic auth
    auth_string = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
    auth_bytes = auth_string.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')

    headers = {
        'Authorization': f'Basic {base64_auth}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'To': phone_number,
        'Channel': 'sms',  # or 'call', 'whatsapp', 'email'
    }

    try:
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 201:
            result = response.json()
            return result.get('sid'), "Verification sent"
        else:
            return None, f"Failed to send: {response.status_code}"

    except Exception as e:
        return None, f"Error: {str(e)}"


def verify_twilio_code(phone_number, code):
    """Verify code with Twilio"""
    if not all([settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_VERIFY_SERVICE_SID]):
        return False, "Twilio not configured"

    service_sid = settings.TWILIO_VERIFY_SERVICE_SID
    url = f"https://verify.twilio.com/v2/Services/{service_sid}/VerificationCheck"

    # Basic auth
    auth_string = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
    auth_bytes = auth_string.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')

    headers = {
        'Authorization': f'Basic {base64_auth}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'To': phone_number,
        'Code': code,
    }

    try:
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 201:
            result = response.json()
            if result.get('status') == 'approved' and result.get('valid') == True:
                return True, "Verification successful"
            else:
                return False, "Invalid verification code"
        else:
            return False, f"Verification failed: {response.status_code}"

    except Exception as e:
        return False, f"Error: {str(e)}"