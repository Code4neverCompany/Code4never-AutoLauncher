"""
Publish Alpha Release Script
Packages the source code and creates a GitHub Pre-release (Alpha).
"""

import os
import shutil
import zipfile
import subprocess
import json

VERSION_FILE = "version_info.json"

def load_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    return "0.0.0"

def zip_project(version):
    output_filename = f"Autolauncher_v{version}_Source.zip"
    
    # Files/Dirs to exclude
    excludes = {
        'venv', '.git', '.vscode', '__pycache__', 
        'logs', 'dist', 'build', '.idea',
        output_filename, 'publish_alpha.py', 'package_source.py', 'prepare_release.py'
    }
    
    print(f"Packaging {output_filename}...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in excludes]
            
            for file in files:
                if file in excludes or file.endswith('.pyc'):
                    continue
                    
                file_path = os.path.join(root, file)
                # Archive name should not have leading ./
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                
    return output_filename

def create_github_release(version, zip_file):
    tag = f"v{version}"
    title = f"v{version} Alpha"
    
    print(f"Creating GitHub Pre-release {tag}...")
    
    # Construct command
    cmd = [
        "gh", "release", "create", tag, zip_file,
        "--prerelease",  # IMPORTANT: Mark as pre-release/alpha
        "--title", title,
        "--generate-notes" # Auto-generate notes from commits
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Release created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create release: {e}")

def main():
    print("--- Publish Alpha Release ---")
    
    # 1. Get Version
    version = load_version()
    print(f"Detected Version: {version}")
    
    confirm = input(f"Ready to publish v{version} as Alpha Pre-release? (y/n): ").lower()
    if confirm != 'y':
        print("Aborted.")
        return

    # 2. Package
    zip_file = zip_project(version)
    
    # 3. Publish
    create_github_release(version, zip_file)

if __name__ == "__main__":
    main()
