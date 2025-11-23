
from update_manager import UpdateManager
import time

class MockUpdateManager(UpdateManager):
    def check_for_updates(self):
        time.sleep(1) # Simulate network delay
        return {
            "version": "9.9.9",
            "url": "https://github.com/example/repo",
            "body": "This is a mock update for testing purposes.\n\n- Feature 1\n- Fix 2",
            "assets": [],
            "exe_asset": {"name": "mock.zip", "browser_download_url": "http://example.com/mock.zip", "size": 1234567},
            "can_auto_update": True
        }, None

    def download_update(self, asset, progress_callback=None):
        # Simulate download
        total = 100 * 1024 * 1024 # 100 MB
        downloaded = 0
        chunk = 1024 * 1024
        
        for _ in range(100):
            time.sleep(0.05)
            downloaded += chunk
            if progress_callback:
                progress_callback(downloaded, total)
        
        return "mock_path.zip"
