#!/bin/bash

# create a new venv
echo "[INFO] Creating a new virtual environment..."
python3 -m venv .venv

# activate your new venv so Python is using it
echo "[INFO] Activating your new virtual environment so Python is using it..."
source .venv/bin/activate

# pip install to requirements.txt
echo "[INFO] Installing required packages..."
pip install -r requirements.txt

echo "[INFO] All tasks completed successfully!"
echo "[INFO] Your virtual environment is ready and all required packages are installed."
echo "[INFO] To activate the environment later, run:"
echo "source venv/bin/activate"
