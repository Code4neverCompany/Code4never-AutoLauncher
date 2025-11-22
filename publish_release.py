import os
import glob
import subprocess
import json
import sys

VERSION_FILE = "version_info.json"

def load_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    return "0.0.0"

def publish_release():
    version = load_version()
    print(f"Publishing Release v{version}...")
    
    # Find artifacts
    release_dir = "release"
    files = glob.glob(f"{release_dir}/*v{version}*")
    
    if not files:
        print(f"No artifacts found for version {version} in {release_dir}/")
        return
    
    print(f"Found artifacts: {files}")
    
    tag = f"v{version}"
    title = f"v{version} Release"
    
    cmd = [
        "gh", "release", "create", tag,
    ] + files + [
        "--title", title,
        "--generate-notes"
    ]
    
    print("Running gh release create...")
    try:
        subprocess.run(cmd, check=True)
        print("✅ Release published successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to publish release: {e}")

if __name__ == "__main__":
    publish_release()
