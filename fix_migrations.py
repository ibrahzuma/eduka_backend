import os
import glob
import subprocess

def fix_migrations():
    # Find all urls.py files
    urls_files = glob.glob('**/urls.py', recursive=True)
    
    modified_files = {}

    print("Disabling routers in urls.py files...")
    for file_path in urls_files:
        with open(file_path, 'r') as f:
            content = f.read()
            
        new_lines = []
        original_content = content
        modified = False
        
        for line in content.splitlines():
            # Comment out lines that assign router.urls or include it
            if ('router.urls' in line) and (not line.strip().startswith('#')):
                new_lines.append(f"# {line}")
                if 'urlpatterns =' in line:
                     new_lines.append("urlpatterns = []")
                modified = True
            else:
                new_lines.append(line)
        
        if modified:
            modified_files[file_path] = original_content
            with open(file_path, 'w') as f:
                f.write('\n'.join(new_lines))
            print(f"Modified {file_path}")

    try:
        print("\nRunning makemigrations...")
        result = subprocess.run(['python', 'manage.py', 'makemigrations'], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        
        if result.returncode == 0:
            print("\nRunning migrate...")
            result = subprocess.run(['python', 'manage.py', 'migrate'], capture_output=True, text=True)
            print(result.stdout)
            print(result.stderr)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        print("\nRestoring files...")
        for file_path, original in modified_files.items():
            with open(file_path, 'w') as f:
                f.write(original)
            print(f"Restored {file_path}")

if __name__ == "__main__":
    fix_migrations()
