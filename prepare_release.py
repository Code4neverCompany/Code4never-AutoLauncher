"""
Prepare Release Script
Helper script to update version and changelog before pushing to GitHub.
"""

import json
import datetime
import os

VERSION_FILE = "version_info.json"

def load_version_info():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    return {"version": "0.0.0", "changelog": []}

def save_version_info(data):
    with open(VERSION_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    print("--- Autolauncher Release Preparation ---")
    data = load_version_info()
    current_version = data.get("version", "0.0.0")
    print(f"Current Version: {current_version}")
    
    # 1. Bump Version
    print("\nSelect version bump type:")
    print("1. Patch (x.x.+1)")
    print("2. Minor (x.+1.0)")
    print("3. Major (+1.0.0)")
    print("4. Custom")
    print("5. No Change")
    
    choice = input("Choice (1-5): ").strip()
    
    major, minor, patch = map(int, current_version.split('.'))
    
    if choice == '1':
        patch += 1
    elif choice == '2':
        minor += 1
        patch = 0
    elif choice == '3':
        major += 1
        minor = 0
        patch = 0
    elif choice == '4':
        new_ver = input("Enter new version (x.y.z): ").strip()
        major, minor, patch = map(int, new_ver.split('.'))
    
    new_version = f"{major}.{minor}.{patch}"
    
    if choice != '5':
        print(f"\nNew Version: {new_version}")
        data['version'] = new_version
        data['build_date'] = datetime.date.today().isoformat()
    
    # 2. Add Changelog
    if choice != '5' or input("\nAdd changelog entry? (y/n): ").lower() == 'y':
        print("\nEnter changes (one per line, empty line to finish):")
        changes = []
        while True:
            line = input("- ").strip()
            if not line:
                break
            changes.append(line)
        
        if changes:
            new_entry = {
                "version": new_version,
                "date": datetime.date.today().isoformat(),
                "changes": changes
            }
            # Prepend to list
            data['changelog'].insert(0, new_entry)
            print("Changelog updated.")
            
    # Save
    save_version_info(data)
    print(f"\n{VERSION_FILE} updated successfully!")
    print("Don't forget to commit and push!")

if __name__ == "__main__":
    main()
