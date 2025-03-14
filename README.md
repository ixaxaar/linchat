# LinChat

A minimal, borderless GTK application for quickly interacting with LLMs on Linux.

## Features

- Ultra-minimal UI with no window decorations or borders
- Configurable to work with any LLM API compatible with OpenAI's interface
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

### API Configuration

```ini
[API]
# The API endpoint to use
endpoint = https://api.openai.com/v1/chat/completions
# Your API key
api_key = your_api_key_here
# The model to use for completion
model = gpt-3.5-turbo
```

You can change the endpoint to use alternative API providers that are compatible with OpenAI's API format, such as local LLM servers, Anthropic Claude, etc.

### UI Customization

You can customize the colors and appearance of LinChat by editing these sections:

```ini
[Colors]
# Main background color
background = #1e1e1e
# Text color
text = #ffffff
# Text selection highlight color
text_selection = #3584e4
# Button color
button = #3584e4
# Button hover state color
button_hover = #4a90e2
# Button active (pressed) state color
button_active = #2c6cb9
# Button text color
button_text = #ffffff

[UI]
# Font family for the application
font_family = Ubuntu Mono, monospace
# Font size in points
font_size = 12
# Border radius for UI elements (buttons) in pixels
border_radius = 4
# Padding for buttons in pixels
padding = 6
```

### Complete Configuration Example

Here's a complete configuration example with all available options:

```ini
[API]
endpoint = https://api.openai.com/v1/chat/completions
api_key = sk-your-api-key-here
model = gpt-3.5-turbo

[Colors]
background = #1e1e1e
text = #ffffff
text_selection = #3584e4
button = #3584e4
button_hover = #4a90e2
button_active = #2c6cb9
button_text = #ffffff

[UI]
font_family = Ubuntu Mono, monospace
font_size = 12
border_radius = 4
padding = 6
```

### Theme Examples

#### Dark Theme (Default)
```ini
[Colors]
background = #1e1e1e
text = #ffffff
text_selection = #3584e4
button = #3584e4
button_hover = #4a90e2
button_active = #2c6cb9
button_text = #ffffff
```

#### Light Theme
```ini
[Colors]
background = #f5f5f5
text = #2a2a2a
text_selection = #add8e6
button = #007bff
button_hover = #0069d9
button_active = #0062cc
button_text = #ffffff
```

#### Nord Theme
```ini
[Colors]
background = #2e3440
text = #eceff4
text_selection = #5e81ac
button = #81a1c1
button_hover = #88c0d0
button_active = #5e81ac
button_text = #eceff4
```

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