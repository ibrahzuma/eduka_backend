
import re

file_path = r'c:\Users\admin\Downloads\eDuka Backend\eduka_backend\templates\base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern: {{ \n whitespace user.assigned... }}
# We want to replace it with {{ user.assigned... }}
pattern = r"({{)\s*\n\s*(user\.assigned_role\.name\|default:user\.get_role_display\|title }}\{% endif %\})"

# Check if pattern exists
match = re.search(pattern, content)
if match:
    print("Found broken pattern. Fixing...")
    # Replace with single line, keeping the {{ and the rest
    # \1 is {{
    # \2 is user.assigned...
    new_content = re.sub(pattern, r"\1 \2", content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed base.html")
else:
    print("Pattern not found. File might be already fixed or different structure.")
    # Debug: print snippet around line 578
    lines = content.splitlines()
    if len(lines) > 580:
        print("\nSnippet around line 578:")
        for i in range(575, 582):
            print(f"{i}: {lines[i]}")
