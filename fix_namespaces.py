import os
import re


def fix_template(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all accounts: namespace URLs
    replacements = [
        (r"{% url 'accounts:profile' %}", "/accounts/profile/"),
        (r"{% url 'accounts:settings' %}", "/accounts/settings/"),
        (r"{% url 'accounts:logout' %}", "/accounts/logout/"),
        (r"{% url 'accounts:login' %}", "/accounts/login/"),
        (r"{% url 'accounts:register' %}", "/accounts/register/"),
        (r"{% url 'accounts:password_reset_request' %}", "/accounts/password-reset/"),
        (r"{% url 'accounts:password_reset' %}", "/accounts/password-reset/"),
        (r"{% url 'accounts:password_reset_confirm' %}", "/accounts/password-reset-confirm/"),
        (r"{% url 'accounts:password_reset_done' %}", "/accounts/password-reset-done/"),
        (r"{% url 'accounts:password_reset_complete' %}", "/accounts/password-reset-complete/"),
    ]

    original_content = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def fix_all_templates():
    fixed_files = []
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if fix_template(filepath):
                    fixed_files.append(filepath)

    if fixed_files:
        print(f"Fixed {len(fixed_files)} files:")
        for f in fixed_files:
            print(f"  - {f}")
    else:
        print("No files needed fixing.")


if __name__ == "__main__":
    fix_all_templates()