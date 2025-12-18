import os
import django
from django.template import loader, Context
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

def check_template():
    print(">>> Checking base.html Syntax...")
    try:
        # Load the template
        t = loader.get_template('base.html')
        print("SUCCESS: Template loaded successfully.")
    except Exception as e:
        print(f"FAILED: Template syntax error: {e}")
        return

    print(">>> Checking dashboard/index.html Syntax (since it extends base)...")
    try:
        t = loader.get_template('dashboard/index.html')
        print("SUCCESS: Dashboard Template loaded successfully.")
    except Exception as e:
        print(f"FAILED: Dashboard syntax error: {e}")

if __name__ == '__main__':
    check_template()
