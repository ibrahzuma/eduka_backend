import glob

def fix_routers():
    urls_files = glob.glob('**/urls.py', recursive=True)
    
    for file_path in urls_files:
        with open(file_path, 'r') as f:
            content = f.read()
            
        if 'DefaultRouter' in content:
            new_content = content.replace('DefaultRouter', 'SimpleRouter')
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Patched {file_path}")

if __name__ == "__main__":
    fix_routers()
