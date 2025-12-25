#!/bin/bash -e

echo "creating a new virtual environment..."
python3 -m venv venv

echo "activating your new virtual environment so python is using it..."
source venv/bin/activate

echo "installing required packages..."
pip install -r requirements.txt

echo "****************************************************************************"
echo "  Thanks for installing Pangolin"
echo "  Your virtual environment is ready and all required packages are installed."
echo "  To activate the environment later, run: \"source venv/bin/activate\""
