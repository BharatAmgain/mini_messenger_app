# fix_twilio_import.py - EMERGENCY FIX
import os
import sys
import subprocess
import shutil


def check_twilio():
    print("Checking Twilio installation...")

    # Try to import twilio
    try:
        import twilio
        print(f"✅ Twilio version: {twilio.__version__}")
        print(f"✅ Twilio path: {twilio.__file__}")
        return True
    except ImportError as e:
        print(f"❌ Twilio not installed: {e}")
        return False
    except Exception as e:
        print(f"❌ Twilio import error: {e}")
        return False


def fix_twilio_import():
    """Fix the broken import in twilio package"""
    print("\nFixing Twilio import issue...")

    # Find twilio package location
    try:
        import twilio
        twilio_path = twilio.__file__
        print(f"Twilio package at: {twilio_path}")

        # The issue is in: twilio/rest/__init__.py line 13
        rest_init_path = os.path.join(os.path.dirname(twilio_path), 'rest', '__init__.py')

        if os.path.exists(rest_init_path):
            print(f"Found: {rest_init_path}")

            # Read the file
            with open(rest_init_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for the problematic line
            if 'from test_twilio.base.client_base import ClientBase' in content:
                print("❌ Found broken import!")

                # Fix the import
                content = content.replace(
                    'from test_twilio.base.client_base import ClientBase',
                    'from twilio.base.client_base import ClientBase'
                )

                # Write back
                with open(rest_init_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print("✅ Fixed import in twilio/rest/__init__.py")
                return True
            else:
                print("✅ Import looks correct")
                return True
        else:
            print(f"❌ File not found: {rest_init_path}")
            return False

    except Exception as e:
        print(f"❌ Error fixing import: {e}")
        return False


def reinstall_twilio():
    """Reinstall twilio package"""
    print("\nReinstalling Twilio...")
    try:
        # Uninstall
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "twilio", "-y"],
                       capture_output=True, text=True)

        # Install specific version
        result = subprocess.run([sys.executable, "-m", "pip", "install", "twilio==8.10.0"],
                                capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Twilio reinstalled successfully")
            return True
        else:
            print(f"❌ Reinstall failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error reinstalling: {e}")
        return False


def main():
    print("=" * 60)
    print("TWILIO IMPORT FIXER")
    print("=" * 60)

    # Option 1: Try to fix import
    print("\n[OPTION 1] Fixing broken import...")
    if fix_twilio_import():
        print("✅ Import fixed!")
        if check_twilio():
            print("\n✅ Twilio should now work!")
            return

    # Option 2: Reinstall
    print("\n[OPTION 2] Reinstalling twilio...")
    if reinstall_twilio():
        if check_twilio():
            print("\n✅ Twilio reinstalled and working!")
            return

    # Option 3: Manual fix
    print("\n[OPTION 3] Manual instructions:")
    print("1. Open PowerShell as Administrator")
    print("2. Run: pip uninstall twilio -y")
    print("3. Run: pip install twilio==8.10.0")
    print("4. Test: python -c \"import twilio; print('OK')\"")


if __name__ == "__main__":
    main()