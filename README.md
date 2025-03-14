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
   git clone https://github.com/yourusername/linchat.git
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

You can start LinChat in three ways:
- Type `linchat` in your terminal
- Search for "LinChat" in your applications menu
- Run `./linchat.py` from the project directory

### Asking Questions

1. Type your question in the text area
2. Press Enter to submit
3. The window will expand to show the response below your question

Use Shift+Enter to create a new line without submitting.

## Customization

You can customize the appearance of LinChat by modifying the CSS in the `apply_css` method in `linchat.py`.

## License

MIT