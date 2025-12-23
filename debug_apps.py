import sys
import os

# Add the project to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connect_io.settings')

try:
    import django

    django.setup()
    print("✅ Django setup successful")

    from django.apps import apps

    print("\n📋 Installed apps:")
    for app in apps.get_app_configs():
        print(f"  - {app.name}")

    # Check for chat app specifically
    try:
        chat_app = apps.get_app_config('chat')
        print(f"\n✅ Chat app found: {chat_app}")
    except LookupError:
        print("\n❌ Chat app not found!")

except Exception as e:
    print(f"\n❌ Error during Django setup: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback

    traceback.print_exc()