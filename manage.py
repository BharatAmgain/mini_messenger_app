#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Fix for cgi module issue in Django 5.x with Python 3.13+
try:
    # Try to import cgi normally
    import cgi
except ImportError:
    # Create a mock cgi module if it doesn't exist
    import types

    # Create mock cgi module
    cgi_module = types.ModuleType('cgi')


    # Create mock FieldStorage class
    class MockFieldStorage:
        def __init__(self, fp=None, headers=None, outerboundary=b'',
                     environ=None, keep_blank_values=0, strict_parsing=0):
            self.fp = fp
            self.headers = headers or {}
            self.list = []
            self.name = None
            self.filename = None
            self.value = None

        def getvalue(self, key=None):
            return self.value

        def getfirst(self, key, default=None):
            return self.value if key == self.name else default

        def getlist(self, key):
            return [self.value] if key == self.name else []


    # Add mock classes to module
    cgi_module.FieldStorage = MockFieldStorage
    cgi_module.parse = lambda *args, **kwargs: {}
    cgi_module.parse_multipart = lambda *args, **kwargs: {}
    cgi_module.parse_header = lambda line: (line.split(';', 1)[0], {})

    # Add to sys.modules
    sys.modules['cgi'] = cgi_module


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()