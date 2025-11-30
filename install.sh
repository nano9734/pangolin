#!/bin/bash -e

# your new venv so python is using it
echo "creating a new virtual environment..."
python3 -m venv .venv
echo "activating your new virtual environment so Python is using it..."
source .venv/bin/activate

echo "installing required packages..."
pip install -r requirements.txt

echo "***************************************"
echo "	Thanks for installing Pangolin"
echo "	Your virtual environment is ready and all required packages are successfully installed."
echo "	To activate the environment later, run: \"source venv/bin/activate\""
