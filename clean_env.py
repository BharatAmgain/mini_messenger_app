import re


def clean_env_file():
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        # Remove inline comments (everything after # that's not inside quotes)
        if '=' in line and '#' in line:
            parts = line.split('#', 1)
            # Check if # is inside quotes
            if parts[0].count('"') % 2 == 0 and parts[0].count("'") % 2 == 0:
                line = parts[0].strip() + '\n'
        cleaned_lines.append(line)

    with open('.env.clean', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

    print("✅ Created clean .env.clean file")
    print("Copy it over your .env file:")
    print("cp .env.clean .env")


if __name__ == "__main__":
    clean_env_file()