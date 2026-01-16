#!/bin/bash

# Define the virtual environment directory
VENV_DIR="venv"

# Check if the virtual environment already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists."
else
    # Create the virtual environment
    python3 -m venv $VENV_DIR
    echo "Virtual environment created."
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Dependencies installed."
else
    echo "No requirements.txt file found."
fi

# Set up PATH to include the virtual environment's bin directory
export PATH="$(pwd)/$VENV_DIR/bin:$PATH"

echo "Setup complete. Virtual environment is ready and activated."

