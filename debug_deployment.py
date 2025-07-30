#!/usr/bin/env python3
"""
Streamlit Cloud deployment debug script.
Use this to identify specific package installation issues.
"""

import sys
import subprocess
import importlib


def check_package_installation():
    """Check if all required packages can be imported."""

    required_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'),
        ('plotly', 'plotly'),
        ('psycopg2', 'psycopg2'),
        ('bcrypt', 'bcrypt'),
        ('cryptography', 'cryptography'),
        ('dateutil', 'python-dateutil'),
        ('streamlit_authenticator', 'streamlit-authenticator')
    ]

    print("🔍 Checking package imports...")
    print("=" * 50)

    failed_imports = []

    for module_name, package_name in required_packages:
        try:
            importlib.import_module(module_name)
            print(f"✅ {package_name}: OK")
        except ImportError as e:
            print(f"❌ {package_name}: FAILED - {e}")
            failed_imports.append(package_name)

    print("=" * 50)

    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
        return False
    else:
        print("✅ All packages imported successfully!")
        return True


def check_system_info():
    """Display system information for debugging."""
    print("\n🖥️ System Information:")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")

    try:
        import platform
        print(f"Architecture: {platform.architecture()}")
        print(f"Machine: {platform.machine()}")
    except:
        pass


def test_database_packages():
    """Test database-related packages specifically."""
    print("\n🗄️ Database Package Tests:")
    print("=" * 50)

    # Test psycopg2
    try:
        import psycopg2
        print(f"✅ psycopg2 version: {psycopg2.__version__}")
    except ImportError as e:
        print(f"❌ psycopg2 import failed: {e}")

    # Test cryptography
    try:
        import cryptography
        print(f"✅ cryptography version: {cryptography.__version__}")
    except ImportError as e:
        print(f"❌ cryptography import failed: {e}")


def main():
    """Main debug function."""
    print("🎰 Pachinko App - Deployment Debug")
    print("=" * 50)

    check_system_info()

    if check_package_installation():
        print("\n🎉 All basic packages are working!")
        test_database_packages()
    else:
        print("\n⚠️ Some packages failed to import.")
        print("Check the Streamlit Cloud logs for more details.")


if __name__ == "__main__":
    main()
