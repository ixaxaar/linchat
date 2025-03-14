#!/bin/bash

set -e

echo "Installing LinChat dependencies..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "Please don't run as root. The script will use sudo when needed."
  exit 1
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
  echo "Python3 not found. Installing..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip
fi

# Install GTK dependencies
echo "Installing GTK dependencies..."
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user requests markdown

# Create config directory and default config
echo "Creating default configuration..."
mkdir -p ~/.config/linchat/
cat > ~/.config/linchat/config.ini << EOL
[API]
endpoint = https://api.openai.com/v1/chat/completions
api_key = 
model = gpt-3.5-turbo
EOL

# Create desktop entry
echo "Creating desktop entry..."
mkdir -p ~/.local/share/applications/
cat > ~/.local/share/applications/linchat.desktop << EOL
[Desktop Entry]
Name=LinChat
Comment=Minimal LLM Chat for Linux
Exec=$(pwd)/linchat.py
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
Keywords=llm;ai;assistant;openai;
EOL

# Make script executable
chmod +x linchat.py

# Create symbolic link in bin directory
echo "Creating symbolic link in ~/bin..."
mkdir -p ~/bin
ln -sf "$(pwd)/linchat.py" ~/bin/linchat

echo "LinChat installation complete!"
echo "You can now run it by typing 'linchat' in a terminal or searching for LinChat in your applications menu."
echo ""
echo "IMPORTANT: You need to set your API key in ~/.config/linchat/config.ini"
echo "You can also configure the endpoint and model in the same file."