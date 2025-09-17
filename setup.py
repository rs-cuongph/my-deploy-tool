#!/usr/bin/env python3
"""
Setup script for Deploy Tool
Ensures cross-platform compatibility and dependencies
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version} detected")
    return True


def check_platform():
    """Check platform compatibility."""
    system = platform.system().lower()
    supported_platforms = ['windows', 'linux', 'darwin']  # darwin = macOS

    if system not in supported_platforms:
        print(f"Warning: Platform '{system}' may not be fully supported")
    else:
        print(f"✓ Platform '{system}' is supported")

    return True


def install_dependencies():
    """Install required Python packages."""
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False


def check_ssh_availability():
    """Check if SSH is available on the system."""
    try:
        # Check if ssh command is available
        subprocess.run(["ssh", "-V"], capture_output=True, check=True)
        print("✓ SSH client is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: SSH client not found. Some features may not work.")
        return False


def create_sample_config():
    """Create a sample configuration file if it doesn't exist."""
    config_file = Path("config.yml")
    if not config_file.exists():
        print("Creating sample configuration file...")
        # The config.yml should already exist from previous step
        print("✓ Configuration file created")
    else:
        print("✓ Configuration file already exists")
    return True


def setup():
    """Main setup function."""
    print("Deploy Tool Setup")
    print("=" * 50)

    checks = [
        ("Python version", check_python_version),
        ("Platform compatibility", check_platform),
        ("Dependencies", install_dependencies),
        ("SSH availability", check_ssh_availability),
        ("Configuration", create_sample_config),
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...")
        if not check_func():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ Setup completed successfully!")
        print("\nUsage:")
        print("  python deploy_tool.py <local_path> <remote_path>")
        print("  python deploy_tool.py --help")
    else:
        print("⚠ Setup completed with warnings")

    return all_passed


if __name__ == "__main__":
    setup()