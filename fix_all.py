import os
import re


def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count original occurrences
    original_count = content.count("{% url 'accounts:")

    # Replace accounts: namespace URLs with direct URLs
    replacements = [
        ("{% url 'accounts:notifications' %}", "/accounts/notifications/"),
        ("{% url 'accounts:settings_main' %}", "/accounts/settings/"),
        ("{% url 'accounts:login' %}", "/accounts/login/"),
        ("{% url 'accounts:profile' %}", "/accounts/profile/"),
        ("{% url 'accounts:settings' %}", "/accounts/settings/"),
        ("{% url 'accounts:logout' %}", "/accounts/logout/"),
        ("{% url 'accounts:register' %}", "/accounts/register/"),
        ("{% url 'accounts:password_reset_request' %}", "/accounts/password-reset/"),
        ("{% url 'accounts:password_reset' %}", "/accounts/password-reset/"),
        ("{% url 'accounts:password_reset_confirm' %}", "/accounts/password-reset-confirm/"),
        ("{% url 'accounts:password_reset_done' %}", "/accounts/password-reset-done/"),
        ("{% url 'accounts:password_reset_complete' %}", "/accounts/password-reset-complete/"),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    new_count = content.count("{% url 'accounts:")

    if new_count < original_count:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fixed {filepath}: {original_count} → {new_count} namespace references")
        return True
    elif original_count > 0:
        print(f"✗ Failed to fix {filepath}: still has {original_count} namespace references")
        return False
    else:
        return False


def fix_all():
    files_to_fix = [
        "templates/chat/chat_home.html",
        "templates/otp/status.html",
        "templates/otp/verify_login.html"
    ]

    # Also check for other files that might have issues
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if filepath not in files_to_fix:
                    files_to_fix.append(filepath)

    fixed_count = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_file(filepath):
                fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

    # Verify all fixes
    print("\nVerifying fixes...")
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    count = content.count("{% url 'accounts:")
                    if count > 0:
                        print(f"⚠  Warning: {filepath} still has {count} namespace reference(s)")


if __name__ == "__main__":
    fix_all()