#!/bin/bash

# Python env name
VENV_NAME=".venv"

echo "Creating '$VENV_NAME'..."
python3 -m venv $VENV_NAME

echo "Activating..."
source $VENV_NAME/bin/activate

echo "Updating pip..."
pip install --upgrade pip

echo "Installing required backend dependencies..."
pip install beautifulsoup4 cloudscraper pandas pydantic requests SQLAlchemy
pip install -r .requirements/requirements.txt

echo "'$VENV_NAME" operational.