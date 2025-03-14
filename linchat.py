#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import threading
import json
import os
import configparser
import requests  # type: ignore
from markdown import markdown  # type: ignore
import textwrap
import re


class LinChat(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        # Set up window properties
        self.set_decorated(False)  # No window decoration
        self.set_keep_above(True)  # Stay on top
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(600, 40)  # Very small initially
        self.set_border_width(0)

        # Make window movable
        self.connect("button-press-event", self.on_window_click)

        # Close on Escape key
        self.connect("key-press-event", self.on_key_press)

        # Create main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)

        # Text input area
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_buffer = self.text_view.get_buffer()
        # Set margins using the newer API
        self.text_view.set_margin_start(0)
        self.text_view.set_margin_end(0)
        self.text_view.set_margin_top(0)
        self.text_view.set_margin_bottom(0)

        # Connect to "changed" signal to resize the window
        self.text_buffer.connect("changed", self.on_input_changed)

        self.input_scrolled_window = Gtk.ScrolledWindow()
        self.input_scrolled_window.set_hexpand(True)
        self.input_scrolled_window.set_vexpand(False)
        self.input_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.input_scrolled_window.add(self.text_view)
        self.main_box.pack_start(self.input_scrolled_window, False, False, 0)

        # Response TextView for output (initially hidden)
        self.response_view = Gtk.TextView()
        self.response_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.response_view.set_editable(False)
        self.response_view.set_cursor_visible(False)
        self.response_buffer = self.response_view.get_buffer()

        # Add text tags for formatting
        self.response_buffer.create_tag("default", foreground="#ffffff")
        self.response_buffer.create_tag(
            "code", foreground="#ffffff", background="#2d2d2d", family="monospace", left_margin=20, right_margin=20
        )
        self.response_buffer.create_tag("h1", foreground="#ffffff", weight=Pango.Weight.BOLD, scale=1.5)
        self.response_buffer.create_tag("h2", foreground="#ffffff", weight=Pango.Weight.BOLD, scale=1.3)
        self.response_buffer.create_tag("h3", foreground="#ffffff", weight=Pango.Weight.BOLD, scale=1.1)
        self.response_buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.response_buffer.create_tag("italic", style=Pango.Style.ITALIC)

        # Create TextView container
        self.response_scrolled = Gtk.ScrolledWindow()
        self.response_scrolled.set_hexpand(True)
        self.response_scrolled.set_vexpand(True)
        self.response_scrolled.add(self.response_view)
        self.response_scrolled.set_no_show_all(True)  # Initially hidden
        self.main_box.pack_start(self.response_scrolled, True, True, 0)

        # Load configuration
        self.config = self.load_config()

        # Apply CSS for styling
        self.apply_css()

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.expanduser("~/.config/linchat/config.ini")

        # Default configuration
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            config["API"] = {
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "api_key": "",
                "model": "gpt-3.5-turbo",
            }
            with open(config_path, "w") as configfile:
                config.write(configfile)
        else:
            config.read(config_path)

        return config

    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css = """
        window {
            background-color: #1e1e1e;
            border: none;
            box-shadow: none;
        }
        textview {
            padding: 8px;
            border: none;
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Ubuntu Mono', monospace;
            font-size: 12pt;
        }
        textview text {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .response-view text {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        textview:selected {
            background-color: #3584e4;
            color: #ffffff;
        }
        scrolledwindow {
            border: none;
            background-color: #1e1e1e;
        }
        """
        css_provider.load_from_data(css.encode())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_window_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            self.begin_move_drag(event.button, event.x_root, event.y_root, event.time)
            return True
        return False

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        elif event.keyval == Gdk.KEY_Return and not (event.state & Gdk.ModifierType.SHIFT_MASK):
            # Enter pressed without Shift
            start_iter = self.text_buffer.get_start_iter()
            end_iter = self.text_buffer.get_end_iter()
            text = self.text_buffer.get_text(start_iter, end_iter, True)

            if text.strip():
                self.send_query(text)
                return True
        return False

    def send_query(self, query):
        try:
            # Clear the buffer
            self.response_buffer.delete(self.response_buffer.get_start_iter(), self.response_buffer.get_end_iter())

            # Add loading text with tag
            self.response_buffer.insert_with_tags_by_name(self.response_buffer.get_end_iter(), "⏳ Thinking...", "h2")

            # Show response area and resize window
            self.response_scrolled.set_visible(True)
            self.response_view.set_visible(True)
            self.response_scrolled.show_all()
            self.resize(600, 400)

            # Force UI update
            while Gtk.events_pending():
                Gtk.main_iteration()

            print("TextView should be showing loading message...")

            # Make the API call in a separate thread
            thread = threading.Thread(target=self.call_api, args=(query,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            print(f"Error in send_query: {str(e)}")
            import traceback

            traceback.print_exc()

    def call_api(self, query):
        try:
            # Print full config for debugging
            print("Current config:", dict(self.config._sections))

            api_key = self.config["API"]["api_key"].strip()
            endpoint = self.config["API"]["endpoint"].strip()
            model = self.config["API"]["model"].strip()

            if not api_key:
                error_msg = (
                    "⚠️ Error: API key not configured.\n\nPlease set your API key in ~/.config/linchat/config.ini"
                )
                print(error_msg)
                GLib.idle_add(self.update_response, error_msg)
                return

            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

            # Build payload conditionally
            payload = {"model": model, "messages": [{"role": "user", "content": query}]}

            # Add temperature only for models that support it
            if model not in ["o1", "claude-3"]:
                payload["temperature"] = 1.0

            # Print debug info
            print(f"Sending request to: {endpoint}")
            print(f"Model: {model}")
            print(f"API Key configured: {'Yes' if api_key else 'No'}")

            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                response_json = response.json()
                print(f"Response received: {str(response_json)[:100]}...")
                message_content = response_json["choices"][0]["message"]["content"]

                # Update UI in main thread
                GLib.idle_add(self.update_response, message_content)
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                print(f"API Error: {error_msg}")
                GLib.idle_add(self.update_response, error_msg)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"Exception: {error_msg}")
            import traceback

            traceback.print_exc()
            GLib.idle_add(self.update_response, error_msg)

    def on_input_changed(self, buffer):
        # Count lines
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        line_count = text.count("\n") + 1

        # Calculate height based on number of lines (up to 10 lines)
        line_height = 20  # Approximate height of a line
        input_height = min(line_height * 10, max(line_height, line_height * line_count))

        # Resize input area if needed
        if not self.response_scrolled.get_visible():
            # Only resize window if response is not visible
            self.resize(600, input_height + 40)  # Add padding

        return False

    def update_response(self, text):
        # Debug output
        print(f"Updating response text (length: {len(text)})")
        print(f"First 50 chars: {text[:50]}")

        try:
            # Clear the buffer
            self.response_buffer.delete(self.response_buffer.get_start_iter(), self.response_buffer.get_end_iter())

            # Insert text with basic formatting
            self.response_buffer.insert_with_tags_by_name(self.response_buffer.get_end_iter(), text, "default")

            # Make sure response view is visible and update display
            self.response_scrolled.set_visible(True)
            self.response_view.set_visible(True)
            self.response_scrolled.show_all()

            # Resize window to show response
            height = min(800, max(400, len(text) // 3 + 100))
            self.resize(600, height)

            # Process any pending events to ensure UI updates
            while Gtk.events_pending():
                Gtk.main_iteration()

            print("Response text should be visible now")

        except Exception as e:
            print(f"Error updating response: {str(e)}")
            import traceback

            traceback.print_exc()

        return False  # Important for GLib.idle_add


def main():
    app = LinChat()
    app.connect("destroy", Gtk.main_quit)
    # First show all, then hide the response area
    app.show_all()
    app.response_scrolled.set_visible(False)
    # Set small initial size
    app.resize(600, 40)
    Gtk.main()


if __name__ == "__main__":
    main()
