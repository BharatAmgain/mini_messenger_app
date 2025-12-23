import os
import re

def check_templates():
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "{% url 'accounts:" in content:
                        print(f"\nFound in: {filepath}")
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if "{% url 'accounts:" in line:
                                print(f"  Line {i}: {line.strip()}")

if __name__ == "__main__":
    check_templates()