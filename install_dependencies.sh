#!/bin/bash

# ----------------------------------------
# Install dependencies for Face Recognition project
# For Ubuntu 20.04 / 22.04 / etc.
# ----------------------------------------

echo "Updating package lists..."
sudo apt update
echo "Installing cmake"
sudo apt install cmake

echo "Installing basic build tools..."
sudo apt install -y build-essential cmake unzip pkg-config

echo "Installing Python 3.10, venv and dev packages..."
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev

echo "Creating Python 3.10 virtual environment..."
python3.10 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip inside venv..."
pip install --upgrade pip

echo "Installing Python libraries inside venv..."
pip uninstall numpy
pip install numpy==1.24
pip install dlib
pip install face_recognition
pip install opencv-python
pip install flask requests

echo "All dependencies installed successfully!"
echo "Virtual environment created at ./venv"
echo ""
echo "To activate it later, use:"
echo "source venv/bin/activate"
