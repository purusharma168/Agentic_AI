import os
import streamlit as st
import subprocess
import sys


def validate_environment():
    """Check if required packages are installed"""
    required_packages = [
        "streamlit", "openai", "langgraph", "requests",
        "beautifulsoup4", "pandas", "numpy", "python-dateutil"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("Packages installed successfully.")


def check_api_keys():
    """Check if API keys are set in environment variables"""
    required_keys = ["NVIDIA_API_KEY", "SERPER_API_KEY"]
    missing_keys = []

    for key in required_keys:
        if not os.environ.get(key):
            missing_keys.append(key)

    if missing_keys:
        print(f"Warning: Missing API keys: {', '.join(missing_keys)}")
        print("You'll need to enter these keys in the application sidebar.")
    else:
        print("All required API keys found in environment variables.")


def main():
    """Main entry point for the application"""
    print("Starting Indian Travel Assistant Application...")
    print("Validating environment...")
    validate_environment()
    print("Checking API keys...")
    check_api_keys()
    print("Launching Streamlit application...")
    subprocess.run(["streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()
