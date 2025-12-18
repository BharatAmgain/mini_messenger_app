# emergency_cleanup.py
import os
import subprocess
import sys


def remove_secrets_from_files():
    """Remove hardcoded secrets from all files"""
    print("Removing hardcoded secrets...")

    files_to_clean = [
        'messenger/settings.py',
        '.env.example',
        '.env',
    ]

    for filepath in files_to_clean:
        if os.path.exists(filepath):
            print(f"Cleaning: {filepath}")

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace hardcoded Twilio SID
            content = content.replace('ACb1f4d1fb64cf30a79a7ccfb504584f4b', 'TWILIO_ACCOUNT_SID_PLACEHOLDER')
            content = content.replace('your_actual_auth_token_here', 'TWILIO_AUTH_TOKEN_PLACEHOLDER')
            content = content.replace('VA87fd0e149dd0297b83d48740df293f3e', 'TWILIO_VERIFY_SERVICE_SID_PLACEHOLDER')

            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  ✅ Cleaned")


def cleanup_git():
    """Remove .env from git and clean cache"""
    print("\nCleaning git...")

    commands = [
        ['git', 'rm', '--cached', '.env'],
        ['git', 'rm', '--cached', '.env.example'],
        ['git', 'add', '.gitignore'],
        ['git', 'add', 'messenger/settings.py'],
        ['git', 'commit', '-m', 'EMERGENCY: Remove all secrets from repository'],
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {' '.join(cmd)}")
            else:
                print(f"⚠️  {' '.join(cmd)}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")


def create_safe_files():
    """Create safe template files"""
    print("\nCreating safe template files...")

    # Create clean .env.example
    env_example = """# .env.example - SAFE TEMPLATE
# Copy to .env and fill with your actual values

# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Twilio (get these from Twilio console)
TWILIO_ACCOUNT_SID=your_account_sid_from_twilio
TWILIO_AUTH_TOKEN=your_auth_token_from_twilio
TWILIO_PHONE_NUMBER=+15005550006
TWILIO_VERIFY_SERVICE_SID=your_verify_service_sid

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
"""

    with open('.env.example', 'w') as f:
        f.write(env_example)
    print("✅ Created clean .env.example")

    # Check settings.py
    if os.path.exists('messenger/settings.py'):
        with open('messenger/settings.py', 'r') as f:
            content = f.read()

        # Verify no hardcoded secrets
        if 'ACb1f4d1fb64cf30a79a7ccfb504584f4b' in content:
            print("❌ WARNING: settings.py still has hardcoded Twilio SID!")
        else:
            print("✅ settings.py is clean")


def main():
    print("=" * 60)
    print("EMERGENCY SECURITY CLEANUP")
    print("=" * 60)

    remove_secrets_from_files()
    create_safe_files()
    cleanup_git()

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Delete your current .env file (it has exposed secrets)")
    print("2. Generate NEW Twilio credentials (old ones are compromised)")
    print("3. Create new .env file with fresh credentials")
    print("4. Run: git push origin main --force")
    print("=" * 60)

    # Ask for confirmation
    response = input("\n⚠️  This will force push. Continue? (yes/no): ")
    if response.lower() == 'yes':
        subprocess.run(['git', 'push', 'origin', 'main', '--force'])
        print("✅ Force push completed!")
    else:
        print("❌ Operation cancelled")


if __name__ == "__main__":
    main()