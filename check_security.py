#!/usr/bin/env python
# check_security.py - Verify your environment is secure

import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and is secure"""
    env_path = Path('.env')

    if not env_path.exists():
        print("❌ .env file not found!")
        return False

    try:
        # Try multiple encodings to read the file
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1']
        content = None

        for encoding in encodings:
            try:
                with open('.env', 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ .env file read successfully with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            print("❌ Could not read .env file with any encoding!")
            return False

        # Check for obvious placeholder tokens
        warnings = []

        if 'your-' in content.lower():
            warnings.append("Found placeholder values (contains 'your-')")

        if 'example.com' in content:
            warnings.append("Found example.com email")

        if 'django-insecure-' in content:
            warnings.append("Using default Django secret key")

        # Check Twilio token
        if 'TWILIO_AUTH_TOKEN' in content:
            token_line = [line for line in content.split('\n') if 'TWILIO_AUTH_TOKEN' in line][0]
            if 'your_' in token_line or 'placeholder' in token_line.lower():
                warnings.append("Twilio Auth Token appears to be a placeholder")

        if warnings:
            print("⚠️  Security warnings in .env file:")
            for warning in warnings:
                print(f"   - {warning}")
            return False

        print("✅ .env file looks secure")
        return True

    except Exception as e:
        print(f"❌ Error reading .env file: {str(e)}")
        print("   Try saving .env file with UTF-8 encoding in VS Code")
        return False


def check_gitignore():
    """Check if .env is in .gitignore"""
    gitignore_path = Path('.gitignore')

    if not gitignore_path.exists():
        print("❌ .gitignore file not found!")
        return False

    try:
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()

        if '.env' in content:
            print("✅ .env is in .gitignore")
            return True
        else:
            print("❌ .env is NOT in .gitignore!")
            return False
    except Exception as e:
        print(f"❌ Error reading .gitignore: {str(e)}")
        return False


def check_sensitive_files():
    """Check for sensitive files that should be deleted"""
    sensitive_files = [
        'test_twilio_api.py',
        'fix_twilio_import.py',
        'fix_is_verified.py',
        'twilio_config.py',
        '.env.backup',
        '.env.old',
        'secrets.py',
        'config_secret.py',
    ]

    found = []
    for file in sensitive_files:
        if Path(file).exists():
            found.append(file)

    if found:
        print("❌ Found sensitive files that should be deleted:")
        for file in found:
            print(f"   - {file}")
        return False

    print("✅ No sensitive files found")
    return True


def check_encoding_issues():
    """Check if files have encoding problems"""
    files_to_check = ['.env', 'check_security.py', 'manage.py', 'requirements.txt']

    print("🔍 Checking file encodings...")
    issues = []

    for file in files_to_check:
        file_path = Path(file)
        if file_path.exists():
            try:
                # Try UTF-8 first
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read()
            except UnicodeDecodeError:
                try:
                    # Try Latin-1
                    with open(file_path, 'r', encoding='latin-1') as f:
                        f.read()
                    issues.append(f"{file}: Latin-1 encoding (should be UTF-8)")
                except:
                    issues.append(f"{file}: Unknown encoding issue")

    if issues:
        print("⚠️  Encoding issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nTo fix encoding in VS Code:")
        print("   1. Open the file")
        print("   2. Click on encoding in bottom right")
        print("   3. Select 'Save with Encoding'")
        print("   4. Choose 'UTF-8'")
        return False

    print("✅ All files have proper encoding")
    return True


def main():
    print("🔒 Security Check")
    print("=" * 50)

    checks = [
        ("File encodings", check_encoding_issues()),
        ("Environment file", check_env_file()),
        (".gitignore", check_gitignore()),
        ("Sensitive files", check_sensitive_files()),
    ]

    print("\n" + "=" * 50)
    passed = all(result for _, result in checks)

    if passed:
        print("✅ All security checks passed!")
    else:
        print("❌ Security issues found!")
        print("\nRecommended actions:")
        print("1. Delete test_twilio_api.py and other sensitive files")
        print("2. Ensure .env contains real credentials, not placeholders")
        print("3. Add .env to .gitignore if not already")
        print("4. Rotate any exposed API keys immediately")
        print("5. Fix file encoding issues in VS Code")
        sys.exit(1)


if __name__ == "__main__":
    main()