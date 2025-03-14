# LinChat

A minimal, borderless GTK application for quickly interacting with LLMs on Linux.

## Features

- Ultra-minimal UI with no window decorations or borders
- Starts as a small input box that expands to show responses
- Input box grows with multi-line input
- Configurable to work with any LLM API compatible with OpenAI's interface
- Clean text display with basic formatting for responses
- Easy to move around your desktop (click and drag)
- Press Escape to close, Enter to submit query, Shift+Enter for new line

## Requirements

- Python 3
- GTK 3
- OpenAI API key or compatible alternative API

## Installation

### Quick Install (from source)

#### Using Make (recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/ixaxaar/linchat.git
   cd linchat
   ```

2. Install dependencies:
   ```bash
   make deps
   ```

3. Install the application:
   ```bash
   sudo make install
   ```

#### Using the setup script

Alternatively, you can use the setup script for a user-local installation:

```bash
./setup.sh
```

The setup script will:
- Install required dependencies
- Create a default configuration
- Create a desktop entry
- Make the application executable
- Create a symbolic link in `~/bin`

### Package Installation

#### Arch Linux (AUR)

```bash
yay -S linchat
```

Or manually:
```bash
git clone https://aur.archlinux.org/linchat.git
cd linchat
makepkg -si
```

#### Ubuntu/Debian (PPA)

```bash
sudo add-apt-repository ppa:yourname/linchat
sudo apt update
sudo apt install linchat
```

See the [packaging documentation](pkg/README.md) for more details on building packages for different distributions.

## Development

### Makefile Commands

LinChat includes a Makefile with several useful commands:

- `make deps` - Install all dependencies
- `make run` - Run the application
- `make lint` - Run linting checks
- `make install` - Install the application system-wide
- `make uninstall` - Uninstall the application
- `make clean` - Clean build artifacts
- `make package` - Build packages for all platforms
- `make package-arch` - Build just the Arch Linux package
- `make package-deb` - Build just the Debian/Ubuntu package
- `make update-version VERSION=x.y.z` - Update version numbers in package files

### Requirements

Python dependencies are listed in `requirements.txt` and can be installed with:

```bash
pip install -r requirements.txt
```

## Configuration

Edit the configuration file at `~/.config/linchat/config.ini`:

```ini
[API]
endpoint = https://api.openai.com/v1/chat/completions
api_key = your_api_key_here
model = gpt-3.5-turbo
```

You can change the endpoint to use alternative API providers that are compatible with OpenAI's API format, such as local LLM servers, Anthropic Claude, etc.

## Usage

You can start LinChat in several ways:
- Type `linchat` in your terminal
- Search for "LinChat" in your applications menu
- Run `./linchat.py` from the project directory
- Set up a custom keyboard shortcut (see below)

### Asking Questions

1. Type your question in the text area
2. Press Enter to submit
3. The window will expand to show the response below your question

Use Shift+Enter to create a new line without submitting.

### Keyboard Shortcuts

- **Enter**: Submit your query
- **Shift+Enter**: Insert a new line in your query
- **Escape**: Close the application
- **Ctrl+C**: Copy selected text (or all text if nothing is selected)

### Command Line Options

LinChat supports various command-line options:

```
linchat [-h] [-v] [-q QUERY] [-p POSITION] [--width WIDTH] [--height HEIGHT]
```

- `-h, --help`: Show help message
- `-v, --version`: Show version and exit
- `-q, --query "TEXT"`: Submit this query immediately on startup
- `-p, --position POSITION`: Set window position (center, mouse)
- `--width WIDTH`: Set initial window width (default: 600)
- `--height HEIGHT`: Set initial window height (default: 40)

### Setting Up Global Keyboard Shortcuts

#### GNOME

1. Open Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts
2. Click "+" to add a new shortcut
3. Name: "LinChat"
4. Command: `linchat -p mouse`
5. Click "Set Shortcut" and press the key combination you want (e.g., `Alt+Space`)

#### KDE Plasma

1. Open System Settings → Shortcuts → Custom Shortcuts
2. Click "Edit" → "New" → "Global Shortcut" → "Command/URL"
3. Name the shortcut "LinChat"
4. Enter the command: `linchat -p mouse`
5. Click on "Trigger" and set your keyboard shortcut
6. Click "Apply"

#### i3, Sway, or other tiling window managers

Add to your config file (~/.config/i3/config or similar):

```
bindsym $mod+space exec linchat -p mouse
```

## Customization

You can customize the appearance of LinChat by modifying the CSS in the `apply_css` method in `linchat.py`.

## License

MIT