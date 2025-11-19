import subprocess
import sys

def install(package):
    """Install a package using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required libraries
required_libraries = [
    "matplotlib",
    "numpy",
    "pandas",
    "requests",
    "scipy"
]

def check_and_install_libraries():
    """Check if libraries are installed and install them if missing."""
    print("Checking for required libraries...")
    for lib in required_libraries:
        try:
            __import__(lib)
            print(f" - {lib} is already installed.")
        except ImportError:
            print(f" - {lib} not found. Installing...")
            try:
                install(lib)
                print(f"   Successfully installed {lib}.")
            except Exception as e:
                print(f"   Failed to install {lib}. Error: {e}")

if __name__ == "__main__":
    check_and_install_libraries()
    print("\nLibrary check complete.")
