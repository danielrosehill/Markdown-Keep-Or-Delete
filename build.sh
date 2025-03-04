#!/bin/bash

echo "=== Markdown Keep or Delete - Build Script ==="
echo "This script will build the application using PyInstaller."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Check if PyQt5 is installed
python -c "import PyQt5" &> /dev/null
if [ $? -ne 0 ]; then
    echo "PyQt5 not found. Installing..."
    pip install PyQt5
fi

# Check if markdown is installed
python -c "import markdown" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Python-Markdown not found. Installing..."
    pip install markdown
fi

echo "Building application..."

# Clean previous build if it exists
if [ -d "dist" ]; then
    echo "Cleaning previous build..."
    rm -rf dist
fi

# Run PyInstaller
pyinstaller main.spec

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Executable can be found at: $(pwd)/dist/main"
    
    # Make the executable executable
    chmod +x dist/main
    
    echo ""
    echo "To run the application, use:"
    echo "./dist/main"
    
    # Ask if user wants to run the application
    read -p "Do you want to run the application now? (y/n): " run_now
    if [ "$run_now" = "y" ] || [ "$run_now" = "Y" ]; then
        ./dist/main
    fi
else
    echo "Build failed. Please check the error messages above."
fi