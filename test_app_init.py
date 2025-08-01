#!/usr/bin/env python3
"""
Test application initialization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_app_init():
    with open('app_init_test.txt', 'w', encoding='utf-8') as f:
        f.write("🧪 Application Initialization Test\n")
        f.write("=" * 50 + "\n\n")

        try:
            # Test imports
            f.write("1. Testing imports...\n")
            from src.pachinko_app import PachinkoApp
            f.write("✅ PachinkoApp import successful\n\n")

            # Test app creation
            f.write("2. Testing app creation...\n")
            try:
                app = PachinkoApp()
                f.write("✅ PachinkoApp created\n")

                # Test component initialization
                f.write("3. Testing component initialization...\n")
                app._initialize_components()
                f.write("✅ Components initialized\n")

                # Test readiness
                f.write("4. Testing app readiness...\n")
                if app.is_ready():
                    f.write("✅ App is ready\n")
                else:
                    f.write("❌ App is not ready\n")

                # Test individual components
                f.write("5. Testing individual components...\n")
                if app.db_manager:
                    f.write("✅ Database manager available\n")
                else:
                    f.write("❌ Database manager missing\n")

                if app.auth_manager:
                    f.write("✅ Auth manager available\n")
                else:
                    f.write("❌ Auth manager missing\n")

                if app.ui_manager:
                    f.write("✅ UI manager available\n")
                else:
                    f.write("❌ UI manager missing\n")

            except Exception as app_error:
                f.write(f"❌ App creation/initialization failed: {app_error}\n")
                import traceback
                f.write(traceback.format_exc())
                f.write("\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
            f.write("\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("App initialization test completed\n")


if __name__ == "__main__":
    test_app_init()
    print("App initialization test completed. Check app_init_test.txt for results.")
