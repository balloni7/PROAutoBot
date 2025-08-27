import pyautogui
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import os
# Try to use screeninfo if available
from screeninfo import get_monitors

class ScreenSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Selector")
        self.root.geometry("800x600")

        # Get screen information
        self.screens = self.get_screen_info()

        # Create UI
        self.create_widgets()

        # Start with the first screen
        self.selected_screen = list(self.screens.keys())[0]
        self.update_preview()

    def get_screen_info(self):
        """Get information about all connected screens"""
        screens = {}
        try:

            monitors = get_monitors()
            for i, monitor in enumerate(monitors):
                screens[f"Screen {i + 1}"] = {
                    "left": monitor.x,
                    "top": monitor.y,
                    "width": monitor.width,
                    "height": monitor.height
                }
        except ImportError:
            # Fallback to primary screen if screeninfo not available
            screens = {
                "Primary Screen": {
                    "left": 0,
                    "top": 0,
                    "width": pyautogui.size().width,
                    "height": pyautogui.size().height
                }
            }
        return screens

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Screen selection
        ttk.Label(main_frame, text="Select Screen:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.screen_var = tk.StringVar()
        screen_dropdown = ttk.Combobox(main_frame, textvariable=self.screen_var,
                                       values=list(self.screens.keys()))
        screen_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        screen_dropdown.bind('<<ComboboxSelected>>', self.on_screen_select)

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="5")
        preview_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Preview image
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Capture Screenshot",
                   command=self.capture_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh Preview",
                   command=self.update_preview).pack(side=tk.LEFT, padx=5)

        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, pady=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def on_screen_select(self, event):
        self.selected_screen = self.screen_var.get()
        self.update_preview()

    def update_preview(self):
        """Update the preview of the selected screen"""
        screen = self.screens[self.selected_screen]

        # Capture the screen region in a thread to prevent UI freezing
        def capture():
            self.status_var.set("Capturing preview...")
            screenshot = pyautogui.screenshot(region=(
                screen["left"], screen["top"],
                screen["width"], screen["height"]
            ))

            # Resize for preview
            preview_width = 400
            preview_height = int(screen["height"] * (preview_width / screen["width"]))
            screenshot = screenshot.resize((preview_width, preview_height), Image.Resampling.LANCZOS)

            # Update the preview
            photo = ImageTk.PhotoImage(screenshot)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Keep a reference

            self.status_var.set("Preview updated")

        # Run in a thread to prevent UI freezing
        threading.Thread(target=capture, daemon=True).start()

    def capture_screenshot(self):
        """Capture the full screenshot of the selected screen"""
        screen = self.screens[self.selected_screen]

        def capture():
            self.status_var.set("Capturing screenshot...")

            # Capture the screen
            screenshot = pyautogui.screenshot(region=(
                screen["left"], screen["top"],
                screen["width"], screen["height"]
            ))

            # Save the screenshot
            filename = f"screenshot_{self.selected_screen.replace(' ', '_')}.png"
            screenshot.save(filename)

            self.status_var.set(f"Screenshot saved as {filename}")

            # Open the image if possible
            try:
                screenshot.show()
            except:
                pass  # Some systems might not be able to show the image

        # Run in a thread to prevent UI freezing
        threading.Thread(target=capture, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenSelector(root)
    root.mainloop()