import os
import shutil


def reset_migrations():
    apps = ['accounts', 'chat']

    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            # Keep __init__.py and delete other migration files
            for file in os.listdir(migrations_dir):
                if file != '__init__.py' and file.endswith('.py'):
                    os.remove(os.path.join(migrations_dir, file))
                    print(f"Deleted: {os.path.join(migrations_dir, file)}")

            # Delete pycache directories
            pycache = os.path.join(migrations_dir, '__pycache__')
            if os.path.exists(pycache):
                shutil.rmtree(pycache)
                print(f"Deleted: {pycache}")

    print("\n✅ Migration files reset. Now run:")
    print("python manage.py makemigrations")
    print("python manage.py migrate")