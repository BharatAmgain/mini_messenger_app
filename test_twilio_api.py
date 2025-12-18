# test_twilio_api.py - NEW TEST FILE
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()

    print("=" * 60)
    print("TWILIO API TEST")
    print("=" * 60)

    from django.conf import settings

    # Check Twilio settings
    print("Twilio Configuration:")
    print(f"ACCOUNT_SID: {settings.TWILIO_ACCOUNT_SID[:10]}...") if settings.TWILIO_ACCOUNT_SID else print(
        "ACCOUNT_SID: NOT SET")
    print(f"AUTH_TOKEN: {'SET' if settings.TWILIO_AUTH_TOKEN else 'NOT SET'}")
    print(f"VERIFY_SERVICE_SID: {settings.TWILIO_VERIFY_SERVICE_SID}")

    # Test Twilio client
    try:
        from twilio.rest import Client as TwilioClient

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized successfully")
    except Exception as e:
        print(f"❌ Twilio client error: {e}")

    # Test account info
    try:
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ Twilio account: {account.friendly_name}")
    except Exception as e:
        print(f"❌ Cannot fetch account: {e}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()