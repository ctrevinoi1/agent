#!/usr/bin/env python
"""
System Check Script

Checks if the OSINT system can run properly by verifying:
1. Required packages are installed
2. Environment variables are set
3. LLM API can be accessed
4. Directories are properly set up
"""

import os
import sys
import platform
import importlib
import pkg_resources
import dotenv

def check_python_version():
    """Check if Python version is compatible."""
    print("\n=== Python Version Check ===")
    required_version = (3, 10)
    current_version = sys.version_info
    
    print(f"Current Python version: {platform.python_version()}")
    print(f"Required Python version: >= {required_version[0]}.{required_version[1]}")
    
    if current_version >= required_version:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python version is not compatible")
        return False

def check_required_packages():
    """Check if all required packages are installed."""
    print("\n=== Package Check ===")
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-dotenv",
        "openai",
        "pyside6",
        "websockets",
        "requests",
        "aiohttp",
        "sqlalchemy",
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Also check package versions
    try:
        import camel_ai
        print(f"✅ camel-ai is installed (version: {pkg_resources.get_distribution('camel-ai').version})")
    except (ImportError, pkg_resources.DistributionNotFound):
        print("❌ camel-ai is not installed")
        missing_packages.append("camel-ai")
    
    # Additional package-specific checks could be added here
    
    return len(missing_packages) == 0

def check_environment_variables():
    """Check if required environment variables are set."""
    print("\n=== Environment Variables Check ===")
    dotenv.load_dotenv()
    
    required_vars = [
        "OPENAI_API_KEY",
        "BING_API_KEY",
        "GOOGLE_GEOCODE_API_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "OPENAI_API_KEY":
                # Mask API key for security
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
                print(f"✅ {var} is set: {masked_value}")
            else:
                print(f"✅ {var} is set")
        else:
            missing_vars.append(var)
            print(f"❌ {var} is not set")
    
    if missing_vars:
        print("\nNeed to set the following environment variables:")
        print("Create a .env file in the project root with:")
        for var in missing_vars:
            print(f"{var}=your_{var.lower()}_here")
        return False
    
    return True

def check_directories():
    """Check if required directories exist."""
    print("\n=== Directory Check ===")
    required_dirs = [
        "app/data",
        "app/data/media",
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"✅ {directory} exists")
        else:
            missing_dirs.append(directory)
            print(f"❌ {directory} does not exist")
    
    if missing_dirs:
        print("\nCreating missing directories...")
        for directory in missing_dirs:
            os.makedirs(directory, exist_ok=True)
            print(f"Created {directory}")
    
    return True

def check_openai_api():
    """Check if OpenAI API can be accessed."""
    print("\n=== OpenAI API Check ===")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY is not set, skipping API check")
        return False
    
    try:
        import openai
        openai.api_key = api_key
        
        # Make a simple API call
        print("Testing API access...")
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Say hello",
            max_tokens=5
        )
        
        if response and hasattr(response, "choices") and len(response.choices) > 0:
            print(f"✅ Successfully connected to OpenAI API")
            return True
        else:
            print("❌ Failed to get a valid response from OpenAI API")
            return False
    
    except Exception as e:
        print(f"❌ Error accessing OpenAI API: {str(e)}")
        return False

def main():
    """Run all checks."""
    print("=== OSINT System Check ===")
    print("Checking if the system can run properly...\n")
    
    # Run all checks
    python_ok = check_python_version()
    packages_ok = check_required_packages()
    env_vars_ok = check_environment_variables()
    directories_ok = check_directories()
    api_ok = check_openai_api()
    
    # Summarize results
    print("\n=== Check Summary ===")
    checks = [
        ("Python Version", python_ok),
        ("Required Packages", packages_ok),
        ("Environment Variables", env_vars_ok),
        ("Directories", directories_ok),
        ("OpenAI API Access", api_ok)
    ]
    
    all_ok = True
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        if not result:
            all_ok = False
        print(f"{check_name}: {status}")
    
    # Final verdict
    print("\n=== Final Result ===")
    if all_ok:
        print("✅ System check PASSED. The OSINT system should run properly.")
        print("Run 'python main.py' to start the system")
        return 0
    else:
        print("❌ System check FAILED. Please fix the issues above before running the system.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 