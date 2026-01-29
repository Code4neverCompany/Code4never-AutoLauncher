"""
Release Candidate Script for AutoLauncher
==========================================
A single command that builds the .exe, installs it to a temporary
directory, and runs a headless smoke test.

Usage:
    python scripts/release_candidate.py [--skip-build] [--keep-temp]

Options:
    --skip-build   Skip PyInstaller build (use existing dist/Autolauncher)
    --keep-temp    Don't delete temp install directory after test

© 2026 4never Company. All rights reserved.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime

# Project root (one level up from scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist" / "Autolauncher"
SMOKE_TEST = PROJECT_ROOT / "tests" / "smoke_test.py"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{msg}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_step(num, msg):
    print(f"{Colors.CYAN}[Step {num}]{Colors.ENDC} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.ENDC}")


def step_1_build_exe(skip_build: bool) -> bool:
    """Build the executable with PyInstaller."""
    print_step(1, "Building Executable with PyInstaller")
    
    if skip_build:
        print_warning("Skipping build (--skip-build flag)")
        if not DIST_DIR.exists():
            print_error(f"No existing build found at {DIST_DIR}")
            return False
        print_success(f"Using existing build at {DIST_DIR}")
        return True
    
    spec_file = PROJECT_ROOT / "autolauncher.spec"
    if not spec_file.exists():
        print_error(f"Spec file not found: {spec_file}")
        return False
    
    print_info(f"Running: python -m PyInstaller --noconfirm --clean {spec_file}")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec_file)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print_error("PyInstaller build failed!")
            print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
            return False
        
        print_success("PyInstaller build completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print_error("Build timed out after 5 minutes")
        return False
    except Exception as e:
        print_error(f"Build failed: {e}")
        return False


def step_2_install_to_temp() -> Path:
    """Copy the built exe to a temporary directory."""
    print_step(2, "Installing to Temporary Directory")
    
    if not DIST_DIR.exists():
        print_error(f"Dist directory not found: {DIST_DIR}")
        return None
    
    # Create temp directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_base = Path(tempfile.gettempdir()) / "c4n-autolauncher-rc"
    temp_dir = temp_base / f"install_{timestamp}"
    
    print_info(f"Installing to: {temp_dir}")
    
    try:
        # Clean up old temp installs
        if temp_base.exists():
            for old_dir in temp_base.iterdir():
                if old_dir.is_dir() and old_dir.name.startswith("install_"):
                    try:
                        shutil.rmtree(old_dir)
                    except:
                        pass  # Ignore cleanup failures
        
        # Copy dist to temp
        shutil.copytree(DIST_DIR, temp_dir)
        
        exe_path = temp_dir / "Autolauncher.exe"
        if exe_path.exists():
            print_success(f"Installed to {temp_dir}")
            print_info(f"Exe size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return temp_dir
        else:
            print_error("Autolauncher.exe not found in installed directory")
            return None
            
    except Exception as e:
        print_error(f"Installation failed: {e}")
        return None


def step_3_run_smoke_test(install_dir: Path) -> bool:
    """Run the smoke test against the installed exe."""
    print_step(3, "Running Headless Smoke Test")
    
    exe_path = install_dir / "Autolauncher.exe"
    if not exe_path.exists():
        print_error(f"Exe not found: {exe_path}")
        return False
    
    # Option A: Run the existing smoke test (tests source code imports)
    print_info("Running source-level smoke test...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(SMOKE_TEST)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Print output
        print(result.stdout)
        
        if result.returncode != 0:
            print_error("Source smoke test failed!")
            if result.stderr:
                print(result.stderr)
            return False
        
        print_success("Source smoke test passed")
        
    except Exception as e:
        print_error(f"Source smoke test failed: {e}")
        return False
    
    # Option B: Quick launch test - verify exe starts without crash
    print_info("Running exe launch test (5 second window)...")
    
    try:
        # Set environment to signal headless/test mode
        env = os.environ.copy()
        env["AUTOLAUNCHER_SMOKE_TEST"] = "1"
        
        # Start the exe and wait briefly
        proc = subprocess.Popen(
            [str(exe_path)],
            cwd=str(install_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait 5 seconds for initial startup
        try:
            proc.wait(timeout=5)
            # If it exits within 5 seconds, that's likely a crash
            if proc.returncode != 0:
                print_error(f"Exe crashed immediately with code {proc.returncode}")
                stderr = proc.stderr.read().decode('utf-8', errors='replace')
                if stderr:
                    print(stderr[:1000])
                return False
            else:
                # Exited cleanly (might be due to smoke test mode)
                print_success("Exe started and exited cleanly")
                
        except subprocess.TimeoutExpired:
            # Still running after 5 seconds = good sign
            print_success("Exe started and stayed running for 5 seconds")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except:
                proc.kill()
        
        return True
        
    except Exception as e:
        print_error(f"Exe launch test failed: {e}")
        return False


def step_4_cleanup(install_dir: Path, keep_temp: bool):
    """Clean up temporary installation."""
    print_step(4, "Cleanup")
    
    if keep_temp:
        print_warning(f"Keeping temp directory: {install_dir}")
        return
    
    try:
        shutil.rmtree(install_dir)
        print_success("Temporary installation removed")
    except Exception as e:
        print_warning(f"Could not clean up temp directory: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="AutoLauncher Release Candidate Script"
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip PyInstaller build, use existing dist/"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary installation directory"
    )
    args = parser.parse_args()
    
    print_header("🚀 AutoLauncher Release Candidate")
    print(f"Project: {PROJECT_ROOT}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Build
    if not step_1_build_exe(args.skip_build):
        print_error("Release candidate FAILED at Step 1 (Build)")
        sys.exit(1)
    
    # Step 2: Install to temp
    install_dir = step_2_install_to_temp()
    if not install_dir:
        print_error("Release candidate FAILED at Step 2 (Install)")
        sys.exit(1)
    
    # Step 3: Smoke test
    test_passed = step_3_run_smoke_test(install_dir)
    
    # Step 4: Cleanup
    step_4_cleanup(install_dir, args.keep_temp)
    
    # Final result
    print_header("📋 Release Candidate Result")
    
    if test_passed:
        print_success("All checks PASSED! ✨")
        print_success("This build is ready for release.")
        print()
        print(f"📦 Dist: {DIST_DIR}")
        sys.exit(0)
    else:
        print_error("Release candidate FAILED!")
        print_error("Do NOT release this build.")
        sys.exit(1)


if __name__ == "__main__":
    main()
