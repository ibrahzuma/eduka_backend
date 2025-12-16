
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.test import Client

def verify_ui_logic():
    client = Client()
    print("Starting UI Logic Verification...")
    
    # 1. Login Page Logo
    print("\n[1] Checking Login Page Logo...")
    response = client.get('/accounts/login/')
    content = response.content.decode()
    if 'src="/static/img/logoeduka.png"' in content:
        print("Login Page: Logo Image Found.")
    else:
        print("Login Page: Logo Image NOT Found.")

    # 2. Registration Page Script
    print("\n[2] Checking Register Page Dynamic Script...")
    response = client.get('/accounts/register/')
    content = response.content.decode()
    
    expected_snippets = [
        "const districtsData = {",
        "'Dar es Salaam': ['Ilala',",
        "regionSelect.addEventListener('change', function() {"
    ]
    
    # 3. Check for New Regions and Data
    print("\n[3] Checking for Expanded Regional Data...")
    
    extra_snippets = [
        "'Katavi': ['Mpanda MC',",
        "'Simiyu': ['Bariadi TC',",
        "<option value=\"Songwe\">Songwe</option>"
    ]
    
    all_extra_found = True
    for snippet in extra_snippets:
        if snippet in content:
            print(f"Data Check: Found snippet '{snippet[:20]}...'")
        else:
            print(f"Data Check: MISSING snippet '{snippet[:20]}...'")
            all_extra_found = False

    if all_extra_found:
        print("Expanded Data Verification: SUCCESS.")
    else:
        print("Expanded Data Verification: INCOMPLETE.")

if __name__ == '__main__':
    verify_ui_logic()
