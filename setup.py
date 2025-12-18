# setup.py
# !/usr/bin/env python3
"""
Setup script for Messenger App
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_command(command, description=None):
    """Run a shell command with description"""
    if description:
        print(f"\n📦 {description}...")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description or 'Command'} failed")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8 or higher is required. Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version} detected")
    return True


def create_virtualenv():
    """Create virtual environment"""
    venv_path = BASE_DIR / 'venv'
    if venv_path.exists():
        print(f"✅ Virtual environment already exists at {venv_path}")
        return True

    print("🧪 Creating virtual environment...")
    success = run_command(
        f'python -m venv "{venv_path}"',
        "Creating virtual environment"
    )

    if success:
        print(f"\n📝 Virtual environment created at: {venv_path}")
        print("🔧 To activate it:")
        print("   - Windows: venv\\Scripts\\activate")
        print("   - Mac/Linux: source venv/bin/activate")
    return success


def install_requirements():
    """Install Python requirements"""
    requirements_file = BASE_DIR / 'requirements.txt'
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    print("📦 Installing requirements...")

    # Determine pip command based on OS
    if sys.platform == 'win32':
        pip_cmd = BASE_DIR / 'venv' / 'Scripts' / 'pip'
    else:
        pip_cmd = BASE_DIR / 'venv' / 'bin' / 'pip'

    success = run_command(
        f'"{pip_cmd}" install -r requirements.txt',
        "Installing Python packages"
    )

    if success:
        print("✅ All packages installed successfully")
    return success


def setup_database():
    """Setup database"""
    print("🗄️ Setting up database...")

    # Create .env file if it doesn't exist
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        print("📄 Creating .env file from template...")
        env_template = BASE_DIR / '.env.example'
        if env_template.exists():
            import shutil
            shutil.copy(env_template, env_file)
            print("✅ Created .env file. Please edit it with your actual credentials.")
        else:
            print("❌ .env.example not found")
            return False

    # Create media directories
    media_dirs = ['media', 'media/profile_pics', 'media/message_files', 'media/group_photos']
    for dir_name in media_dirs:
        dir_path = BASE_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_name}")

    # Create logs directory
    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Determine python command
    if sys.platform == 'win32':
        python_cmd = BASE_DIR / 'venv' / 'Scripts' / 'python'
    else:
        python_cmd = BASE_DIR / 'venv' / 'bin' / 'python'

    # Run migrations
    success = run_command(
        f'"{python_cmd}" manage.py makemigrations',
        "Creating migrations"
    )

    if success:
        success = run_command(
            f'"{python_cmd}" manage.py migrate',
            "Applying migrations"
        )

    if success:
        print("✅ Database setup complete")
    return success


def create_superuser():
    """Create superuser"""
    print("👑 Creating superuser...")

    username = input("Enter superuser username [admin]: ") or "admin"
    email = input("Enter superuser email [admin@example.com]: ") or "admin@example.com"

    if sys.platform == 'win32':
        python_cmd = BASE_DIR / 'venv' / 'Scripts' / 'python'
    else:
        python_cmd = BASE_DIR / 'venv' / 'bin' / 'python'

    # Run createsuperuser command
    command = f'"{python_cmd}" manage.py createsuperuser --username {username} --email {email}'

    success = run_command(
        command,
        "Creating superuser"
    )

    if success:
        print(f"✅ Superuser created:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   You'll be prompted to set a password")
    return success


def main():
    """Main setup function"""
    print("🚀 Messenger App Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        return

    # Create virtual environment
    if not create_virtualenv():
        return

    # Install requirements
    if not install_requirements():
        return

    # Setup database
    if not setup_database():
        return

    # Ask about superuser
    create_super = input("\n❓ Do you want to create a superuser? (y/n): ").lower()
    if create_super in ['y', 'yes']:
        create_superuser()

    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your actual credentials")
    print("2. Activate the virtual environment:")
    print("   - Windows: venv\\Scripts\\activate")
    print("   - Mac/Linux: source venv/bin/activate")
    print("3. Run the development server:")
    print("   python manage.py runserver")
    print("4. Visit http://localhost:8000")
    print("\n🔧 For production deployment:")
    print("   - Set DEBUG=False in .env")
    print("   - Configure ALLOWED_HOSTS")
    print("   - Set up HTTPS")
    print("   - Use a production database (PostgreSQL)")


if __name__ == '__main__':
    main()