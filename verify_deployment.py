#!/usr/bin/env python3
"""
Deployment verification script for the Pachinko Revenue Calculator.

Verifies that all deployment configuration files are properly set up
and the application is ready for Streamlit Cloud deployment.
"""

import os
import sys
import json
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False


def check_requirements_txt():
    """Check requirements.txt file."""
    print("\n📦 Checking requirements.txt...")

    if not check_file_exists("requirements.txt", "Requirements file"):
        return False

    with open("requirements.txt", "r") as f:
        requirements = f.read()

    required_packages = [
        "streamlit",
        "plotly",
        "pandas",
        "psycopg2-binary",
        "cryptography",
        "psutil"
    ]

    missing_packages = []
    for package in required_packages:
        if package not in requirements:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        return False
    else:
        print("✅ All required packages found")
        return True


def check_streamlit_config():
    """Check Streamlit configuration files."""
    print("\n⚙️ Checking Streamlit configuration...")

    config_files = [
        (".streamlit/config.toml", "Streamlit config"),
        (".streamlit/secrets.toml.example", "Secrets example"),
        ("packages.txt", "System packages")
    ]

    all_exist = True
    for file_path, description in config_files:
        if not check_file_exists(file_path, description):
            all_exist = False

    return all_exist


def check_source_files():
    """Check source code files."""
    print("\n📁 Checking source files...")

    source_files = [
        ("app.py", "Main application"),
        ("src/config.py", "Configuration manager"),
        ("src/deployment.py", "Deployment manager"),
        ("src/database.py", "Database manager"),
        ("src/ui_manager.py", "UI manager"),
        ("src/stats.py", "Statistics calculator"),
        ("src/authentication.py", "Authentication manager"),
        ("src/models.py", "Data models")
    ]

    all_exist = True
    for file_path, description in source_files:
        if not check_file_exists(file_path, description):
            all_exist = False

    return all_exist


def check_deployment_files():
    """Check deployment-specific files."""
    print("\n🚀 Checking deployment files...")

    deployment_files = [
        ("DEPLOYMENT.md", "Deployment guide"),
        (".streamlit/config.toml", "Streamlit configuration"),
        ("packages.txt", "System packages list")
    ]

    all_exist = True
    for file_path, description in deployment_files:
        if not check_file_exists(file_path, description):
            all_exist = False

    return all_exist


def check_environment_variables():
    """Check environment variable configuration."""
    print("\n🔐 Checking environment variables...")

    # Check if secrets example exists and has required variables
    secrets_example = ".streamlit/secrets.toml.example"
    if not os.path.exists(secrets_example):
        print("❌ Secrets example file not found")
        return False

    with open(secrets_example, "r") as f:
        secrets_content = f.read()

    required_vars = [
        "ENVIRONMENT",
        "DATABASE_URL",
        "SECRET_KEY",
        "ENCRYPTION_KEY"
    ]

    missing_vars = []
    for var in required_vars:
        if var not in secrets_content:
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables in example: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables documented")
        return True


def check_free_tier_configuration():
    """Check free tier limit configuration."""
    print("\n💰 Checking free tier configuration...")

    try:
        # Check if config.py has free tier limits
        with open("src/config.py", "r") as f:
            config_content = f.read()

        if "free_tier_limits" in config_content:
            print("✅ Free tier limits configured")
            return True
        else:
            print("❌ Free tier limits not found in configuration")
            return False

    except Exception as e:
        print(f"❌ Error checking free tier configuration: {e}")
        return False


def main():
    """Main verification function."""
    print("🎰 勝てるクン - Deployment Verification")
    print("=" * 50)

    checks = [
        ("Requirements", check_requirements_txt),
        ("Streamlit Config", check_streamlit_config),
        ("Source Files", check_source_files),
        ("Deployment Files", check_deployment_files),
        ("Environment Variables", check_environment_variables),
        ("Free Tier Config", check_free_tier_configuration)
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, check_function in checks:
        try:
            if check_function():
                passed_checks += 1
        except Exception as e:
            print(f"❌ Error in {check_name} check: {e}")

    print("\n" + "=" * 50)
    print(
        f"📊 Verification Results: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("🎉 All checks passed! Ready for Streamlit Cloud deployment.")
        print("\n📋 Next steps:")
        print("1. Push code to GitHub repository")
        print("2. Set up Supabase database")
        print("3. Configure Streamlit Cloud with environment variables")
        print("4. Deploy application")
        return True
    else:
        print("⚠️ Some checks failed. Please fix the issues before deployment.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
