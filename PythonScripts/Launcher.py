import tkinter as tk
from tkinter import ttk
from ConfigHandler import ConfigHandler
from PokemonHunter import ShinyCatcher

# Configuration schema: (section, option, widget, widget_type, transform_func)
WIDGET_CONFIG_SCHEMA = [
        {
            'section': 'Movement',
            'option': 'ntiles',
            'widget': 'entry_tiles',
            'widget_type': 'entry',
            'transform': lambda x: x  # No transformation needed
        },
        {
            'section': 'OCR',
            'option': 'wanted_pokemon',
            'widget': 'multiselect_pokemon',
            'widget_type': 'multiselect',
            'transform': lambda x: "(" + ", ".join(x) + ")"  # Wrap in parentheses and quotes
        },
        {
            'section': 'AutoCatch',
            'option': 'sync_enabled',
            'widget': 'sync_var',
            'widget_type': 'boolean',
            'transform': lambda x: str(x)
        },
        {
            'section': 'AutoCatch',
            'option': 'fs_enabled',
            'widget': 'fs_var',
            'widget_type': 'boolean',
            'transform': lambda x: str(x)
        },
        {
            'section': 'Other',
            'option': 'play_shiny_sound',
            'widget': 'shiny_sound_bool',
            'widget_type': 'boolean',
            'transform': lambda x: str(x)
        },
        {
            'section': 'Other',
            'option': 'play_wanted_sound',
            'widget': 'shiny_wanted_bool',
            'widget_type': 'boolean',
            'transform': lambda x: str(x)
        },
        {
            'section': 'AutoCatch',
            'option': 'fs_pokemon_position',
            'widget': 'fs_pokemon_entry',
            'widget_type': 'entry',
            'transform': lambda x: x
        },
        {
            'section': 'AutoCatch',
            'option': 'fs_move_position',
            'widget': 'fs_move_entry',
            'widget_type': 'entry',
            'transform': lambda x: x
        },
        {
            'section': 'AutoCatch',
            'option': 'ball_to_use',
            'widget': 'ball_entry',
            'widget_type': 'entry',
            'transform': lambda x: x
        }
    ]


class AutoCatcherLauncher:
    def __init__(self, config_path="CONFIG.ini"):
        self.config_path = config_path
        self.config_handler = ConfigHandler(config_path)
        self.root = tk.Tk()
        self.widgets = {}  # Store all widget references
        self.pokemon_list = load_pokemon_names(self.config_handler.get("Files", "names_file"))

        self._setup_gui()

    def _setup_gui(self):
        self.root.title("AutoCatcher Configuration")
        self.root.geometry("600x500")
        self.root.resizable(True, True)  # Disable resizing
        self.root.configure(padx=15, pady=15)  # Internal padding

        self._create_widgets()

    def _create_widgets(self):
        """Create widgets based on schema"""
        row_counter = 0

        # Group by sections for better organization
        sections = {}
        for item in WIDGET_CONFIG_SCHEMA:
            section = item['section']
            if section not in sections:
                sections[section] = []
            sections[section].append(item)

        # Create UI by sections
        for section, items in sections.items():
            # Section header
            ttk.Label(self.root, text=f"{section} Settings",
                      font=("Arial", 12, "bold")).grid(
                row=row_counter, column=0, columnspan=2,
                sticky="w", pady=(15, 5))
            row_counter += 1

            for item in items:
                self._create_widget_item(item, row_counter)
                row_counter += 1

        # Start button
        self.start_button = ttk.Button(self.root, text="Start Bot",
                                       command=self._start_bot)
        self.start_button.grid(row=row_counter, column=0, columnspan=2, pady=20)

        # Configure column weights for proper resizing
        self.root.grid_columnconfigure(1, weight=1)

    def _create_widget_item(self, item, row):
        """Create individual widget based on schema item"""
        section, option, widget_name = item['section'], item['option'], item['widget']

        # Get default value from config
        default_value = self.config_handler.get(section, option)

        # Create label
        label_text = option.replace('_', ' ').title()
        ttk.Label(self.root, text=label_text + ":").grid(
            row=row, column=0, sticky="w", padx=5)

        # Create widget based on type
        if item['widget_type'] == 'entry':
            widget = ttk.Entry(self.root)
            widget.insert(0, str(default_value))
            widget.grid(row=row, column=1, padx=5, pady=2,sticky="w")
            self.widgets[widget_name] = widget

        elif item['widget_type'] == 'boolean':
            # Convert string to boolean for checkbox
            bool_value = default_value
            var = tk.BooleanVar(value=bool_value)
            widget = ttk.Checkbutton(self.root, variable=var)
            widget.grid(row=row, column=1, sticky="w", padx=5)
            self.widgets[widget_name] = var

        elif item['widget_type'] == 'multiselect':
            # Create frame for the tag entry
            frame = ttk.Frame(self.root)
            frame.grid(row=row, column=1, padx=5, pady=2, sticky="ew")

            # Create the tag entry widget
            widget = TagEntry(frame, self.pokemon_list, default_value)
            widget.pack(fill=tk.BOTH, expand=True)
            self.widgets[widget_name] = widget

            widget.after(100, widget.update_layout)


    def _get_widget_value(self, widget_name, widget_type):
        """Get value from widget based on its type"""
        widget = self.widgets[widget_name]

        if widget_type == 'entry':
            return widget.get()
        elif widget_type == 'boolean':
            return widget.get()
        elif widget_type == 'multiselect':
            return widget.get_selected()

    def _start_bot(self):
        """Update config from UI and start bot"""
        # Update config using schema
        for item in WIDGET_CONFIG_SCHEMA:
            section = item['section']
            option = item['option']
            widget_value = self._get_widget_value(item['widget'], item['widget_type'])

            # Apply transformation if needed
            transformed_value = item['transform'](widget_value)

            # Ensure section exists
            if section not in self.config_handler.configParser:
                self.config_handler.configParser[section] = {}

            # Update config value
            self.config_handler.configParser[section][option] = transformed_value

        # Save config
        #TODO: Implement Bulk save in ConfigHandler() instead of full rewrite
        self.config_handler._save_config()

        # Close and start bot
        self.root.destroy()
        self._run_bot()


    def _run_bot(self):
        sc = ShinyCatcher(self.config_path)
        sc.main()

    def run(self):
        self.root.mainloop()


# Load Pokémon names from file
def load_pokemon_names(names_file="Resources/pokemon_names.txt"):
    """Load all Pokémon names from the names file"""
    pokemon_list = []
    try:
        with open(names_file, 'r', encoding='utf-8') as f:
            pokemon_list = [name.strip().title() for name in f.readlines() if name.strip()]
    except FileNotFoundError:
        print(f"Warning: Pokémon names file not found at {names_file}")

    return sorted(pokemon_list)



class TagEntry(ttk.Frame):
    """Custom widget for multi-select with tags"""

    def __init__(self, parent, all_options, selected_options=(), *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.all_options = all_options
        self.selected_options = [opt for opt in list(selected_options) if opt and str(opt).strip()]

        self.grid_columnconfigure(0, weight=1)

        # Create a frame for tags that will wrap content
        self.tags_frame = ttk.Frame(self)
        self.tags_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        # Entry with dropdown
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self.entry_frame.grid_columnconfigure(0, weight=1)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self.entry_frame, textvariable=self.entry_var)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Bind events
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<Return>", self.on_return)
        self.entry.bind("<Tab>", self.on_tab)

        # Dropdown listbox
        self.listbox_frame = ttk.Frame(self)
        self.listbox = tk.Listbox(self.listbox_frame, height=6, selectmode=tk.SINGLE)
        self.listbox_scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.listbox_scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        #self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<Double-Button-1>", self.on_listbox_double_click)

        # Initially hide the listbox
        self.listbox_visible = False

        # Update display
        self.update_tags()
        self.filter_options("")

    def update_tags(self):
        """Update the display of tags with wrapping layout"""
        # Clear existing tags
        for widget in self.tags_frame.winfo_children():
            widget.destroy()

        # Only create tags if we have selected options
        if not self.selected_options:
            # Add a placeholder label when no tags are selected
            placeholder = ttk.Label(self.tags_frame, text="No Pokémon selected", foreground="gray")
            placeholder.grid(row=0, column=0, padx=2, pady=2, sticky="w")
            return

        # Create new tags with wrapping layout
        row = 0
        col = 0
        max_width = self.winfo_width() - 20  # Account for padding

        for option in self.selected_options:
            tag_frame = ttk.Frame(self.tags_frame)

            label = ttk.Label(tag_frame, text=option)
            label.pack(side=tk.LEFT, padx=(5, 0))

            remove_btn = ttk.Button(
                tag_frame,
                text="×",
                width=2,
                command=lambda opt=option: self.remove_option(opt)
            )
            remove_btn.pack(side=tk.RIGHT, padx=(2, 0))

            # Place the tag in the grid
            tag_frame.grid(row=row, column=col, padx=2, pady=2, sticky="w")

            # Update column and row for next tag
            tag_frame.update_idletasks()
            if col > 0 and self._get_row_width(row) + tag_frame.winfo_width() > max_width:
                # Move to next row if current row would be too wide
                row += 1
                col = 0
                tag_frame.grid(row=row, column=col, padx=2, pady=2, sticky="w")

            col += 1

    def update_layout(self):
        """Force update of tag layout after widget is fully created"""
        self.update_idletasks()  # Force UI update
        self.update_tags()  # Recalculate tag positions

    def _get_row_width(self, row):
        """Calculate the total width of all widgets in a row"""
        total_width = 0
        for widget in self.tags_frame.grid_slaves(row=row):
            if isinstance(widget, ttk.Frame):
                total_width += widget.winfo_width() + 4  # Add padding
        return total_width

    def filter_options(self, text):
        """Filter remaining wanted pokemon options based on text input"""
        text = text.lower()

        # Create a filtered list using list comprehension
        filtered = [
            opt for opt in self.all_options
            if opt.lower().startswith(text) and opt not in self.selected_options
        ]

        # Clear the current listbox contents and show new listbox contents
        self.listbox.delete(0, tk.END)
        for option in filtered[:20]:  # Limit to 20 options
            self.listbox.insert(tk.END, option)

        # Show/hide listbox based on whether we have options
        if filtered and text:
            if not self.listbox_visible:
                self.listbox_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
                self.listbox_visible = True
        else:
            if self.listbox_visible:
                self.listbox_frame.grid_forget()
                self.listbox_visible = False

    def add_option(self, option):
        """Add an option to selected options"""
        if option and option not in self.selected_options:
            self.selected_options.append(option)
            self.update_tags()
            self.entry_var.set("")
            self.filter_options("")

    def remove_option(self, option):
        """Remove an option from selected options"""
        if option in self.selected_options:
            self.selected_options.remove(option)
            self.update_tags()
            self.filter_options(self.entry_var.get())

    def on_key_release(self, event):
        """Handle key release in entry"""
        if event.keysym in ("Up", "Down"):
            # Navigate listbox with arrow keys
            if self.listbox_visible:
                current = self.listbox.curselection()
                if event.keysym == "Down":
                    new_index = (current[0] + 1) % self.listbox.size() if current else 0
                else:  # Up
                    new_index = (current[0] - 1) % self.listbox.size() if current else self.listbox.size() - 1
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(new_index)
                self.listbox.see(new_index)
        else:
            # Filter options based on text
            self.filter_options(self.entry_var.get())

    def on_return(self, event):
        """Handle return key press"""
        if self.listbox_visible and self.listbox.curselection():
            # Add selected item from listbox
            selected = self.listbox.get(self.listbox.curselection())
            self.add_option(selected)
        elif self.entry_var.get():
            # Try to find a matching option
            text = self.entry_var.get().title()
            matches = [opt for opt in self.all_options if opt.lower().startswith(text.lower())]
            if matches and matches[0] not in self.selected_options:
                self.add_option(matches[0])

        return "break"  # Prevent default behavior

    def on_tab(self, event):
        """Handle tab key press - autocomplete"""
        if self.entry_var.get():
            text = self.entry_var.get().title()
            matches = [opt for opt in self.all_options if opt.lower().startswith(text.lower())]
            if matches and matches[0] not in self.selected_options:
                self.entry_var.set(matches[0])
                self.entry.icursor(tk.END)

        return "break"  # Prevent default behavior

    def on_listbox_double_click(self, event):
        """Handle listbox double click"""
        if self.listbox.curselection():
            selected = self.listbox.get(self.listbox.curselection())
            self.add_option(selected)

    def get_selected(self):
        """Get selected options as a tuple"""
        return tuple(self.selected_options)

    def set_selected(self, options):
        """Set selected options"""
        self.selected_options = list(options)
        self.update_tags()
        self.filter_options(self.entry_var.get())


if __name__ == "__main__":
    launcher = AutoCatcherLauncher()
    launcher.run()