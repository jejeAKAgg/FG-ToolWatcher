# LINUX Python env
VENV = __TWlinux__

# Commands
.PHONY: setup run clean build

# Default
all: run

# Setting up environments and installing requirements.
setup:
    python3 -m venv $(VENV)
    $(VENV)/bin/pip install -r requirements.txt
    @echo "System ready!"

# Run the APP.
run:
    $(VENV)/bin/python Launcher.py

# Clean cache/builds [Use it as "last thing to do"].
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -rf build/ dist/ *.spec
    @echo "Cleaning successful."

# Build .exe executable.
build:
    $(VENV)/bin/pyinstaller --onefile Launcher.py