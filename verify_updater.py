
import os
import requests
from update_manager import UpdateManager

def verify_update_check():
    print("--- Verifying Update Manager API Connection ---")
    um = UpdateManager()
    
    # Check for updates
    print(f"Current version (as seen by UM): {um.get_current_version()}")
    print(f"Target Repo: {um.GITHUB_REPO if hasattr(um, 'GITHUB_REPO') else 'Code4neverCompany/Code4never-AutoLauncher'}")
    
    # We expect this to not return 403 now
    update_info, error_msg = um.check_for_updates()
    
    if error_msg:
        print(f"❌ Update check failed: {error_msg}")
    else:
        print("✅ Update check successful!")
        if update_info:
            print(f"🚀 Update available: v{update_info['version']}")
        else:
            print("✨ Application is up to date.")

if __name__ == "__main__":
    verify_update_check()
