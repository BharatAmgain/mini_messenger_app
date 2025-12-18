# test_form.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
import django
django.setup()

from accounts.forms import PasswordResetRequestForm

test_cases = [
    "amgaibharat46@gmail.com",  # Your email
    "9800000000",  # Simple Nepal number
    "+9779800000000",  # International format
    "09800000000",  # With leading zero
    "invalid-email",  # Should fail
    "123",  # Should fail
]

print("Testing Password Reset Form Validation:")
print("=" * 50)

for test_input in test_cases:
    form = PasswordResetRequestForm(data={'email_or_phone': test_input})
    print(f"\nInput: {test_input}")
    if form.is_valid():
        cleaned = form.cleaned_data['email_or_phone']
        print(f"✓ Valid → Type: {cleaned['type']}, Value: {cleaned['value']}")
    else:
        print(f"✗ Invalid → Errors: {form.errors}")