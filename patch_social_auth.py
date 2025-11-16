import os
import sys


def patch_social_auth():
    """Patch social-auth-app-django for Django 5.2 compatibility"""
    site_packages = None
    for path in sys.path:
        if 'site-packages' in path:
            site_packages = path
            break

    if not site_packages:
        print("Could not find site-packages directory")
        return

    models_file = os.path.join(site_packages, 'social_django', 'models.py')

    if os.path.exists(models_file):
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace condition with check
        if 'condition=~models.Q(uid="")' in content:
            content = content.replace('condition=~models.Q(uid="")', 'check=~models.Q(uid="")')

            with open(models_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Successfully patched social_django models.py")
        else:
            print("No need to patch - condition already replaced with check")
    else:
        print(f"Could not find {models_file}")


if __name__ == "__main__":
    patch_social_auth()