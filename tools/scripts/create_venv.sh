#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Check if uv is installed in the venv, if not install it
if [ ! -f ".venv/bin/uv" ]; then
    echo "uv not found in virtual environment. Installing uv..."
    .venv/bin/pip install uv
else
    echo "uv is already installed in virtual environment."
fi

echo ""
echo "Setup complete!"
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
