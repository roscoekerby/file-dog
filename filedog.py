import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import json
from pathlib import Path

# File extensions to include
VALID_EXTENSIONS = {'.py', '.html', '.js', '.css', '.dart', '.txt', '.md', '.yaml', '.json', '.xml', '.sql'}


class FileDog:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🐕 FileDog - Advanced File Selector")
        self.root.geometry("900x700")

        # Data structures
        self.selected_files = set()
        self.selected_folders = set()
        self.excluded_files = set()
        self.excluded_folders = set()
        self.base_directory = None
        self.show_hidden = tk.BooleanVar(value=False)
        self.include_all_extensions = tk.BooleanVar(value=False)

        # Colors for selection states
        self.colors = {
            'fully_selected': '#90EE90',  # Light green
            'partially_selected': '#FFA500',  # Orange
            'excluded': '#FFB6C1',  # Light red
            'normal': '#FFFFFF'  # White
        }

        self.setup_ui()
        self.tree_items = {}  # Maps tree item IDs to file/folder paths

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🐕 FileDog", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Directory selection
        ttk.Button(control_frame, text="📁 Select Base Directory",
                   command=self.select_base_directory).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)

        # Options
        options_frame = ttk.LabelFrame(control_frame, text="Options", padding="5")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Checkbutton(options_frame, text="Show hidden files/folders",
                        variable=self.show_hidden, command=self.refresh_tree).grid(row=0, column=0, sticky=tk.W)

        ttk.Checkbutton(options_frame, text="Include all file types",
                        variable=self.include_all_extensions, command=self.refresh_tree).grid(row=1, column=0,
                                                                                              sticky=tk.W)

        # Selection buttons
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(buttons_frame, text="✅ Select All",
                   command=self.select_all).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=1)
        ttk.Button(buttons_frame, text="❌ Clear All",
                   command=self.clear_all).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=1)
        ttk.Button(buttons_frame, text="🔄 Refresh",
                   command=self.refresh_tree).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=1)

        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Button(action_frame, text="💾 Save Selection",
                   command=self.save_selection).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=1)
        ttk.Button(action_frame, text="📂 Load Selection",
                   command=self.load_selection).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=1)

        ttk.Button(action_frame, text="🔧 Combine Files",
                   command=self.combine_files).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        # Legend
        legend_frame = ttk.LabelFrame(control_frame, text="Legend", padding="5")
        legend_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)

        legend_items = [
            ("🟢 Fully Selected", self.colors['fully_selected']),
            ("🟠 Partially Selected", self.colors['partially_selected']),
            ("🔴 Excluded", self.colors['excluded'])
        ]

        for i, (text, color) in enumerate(legend_items):
            label = ttk.Label(legend_frame, text=text)
            label.grid(row=i, column=0, sticky=tk.W)

        # File tree
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, selectmode='extended')
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # Tree columns
        self.tree["columns"] = ("size", "type", "status")
        self.tree.column("#0", width=400, minwidth=200)
        self.tree.column("size", width=80, minwidth=50)
        self.tree.column("type", width=80, minwidth=50)
        self.tree.column("status", width=100, minwidth=80)

        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.heading("size", text="Size", anchor=tk.W)
        self.tree.heading("type", text="Type", anchor=tk.W)
        self.tree.heading("status", text="Status", anchor=tk.W)

        # Bind events
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right click
        self.tree.bind("<Double-1>", self.toggle_selection)  # Double click
        self.tree.bind("<space>", self.toggle_selection)  # Space bar

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_var = tk.StringVar(value="Select a base directory to start")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        self.selection_count_var = tk.StringVar(value="")
        self.selection_count_label = ttk.Label(status_frame, textvariable=self.selection_count_var)
        self.selection_count_label.grid(row=0, column=1, sticky=tk.E)
        status_frame.columnconfigure(0, weight=1)

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="✅ Select", command=lambda: self.toggle_selection(force_select=True))
        self.context_menu.add_command(label="❌ Exclude", command=lambda: self.toggle_selection(force_exclude=True))
        self.context_menu.add_command(label="🔄 Toggle", command=self.toggle_selection)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📁 Select All in Folder", command=self.select_all_in_folder)
        self.context_menu.add_command(label="🚫 Exclude All in Folder", command=self.exclude_all_in_folder)

    def select_base_directory(self):
        directory = filedialog.askdirectory(title="Select Base Directory")
        if directory:
            self.base_directory = directory
            self.status_var.set(f"Base directory: {directory}")
            self.refresh_tree()

    def is_hidden(self, path):
        """Check if a file or folder is hidden"""
        name = os.path.basename(path)
        return name.startswith('.')

    def should_include_file(self, file_path):
        """Check if a file should be included based on extension"""
        if self.include_all_extensions.get():
            return True
        _, ext = os.path.splitext(file_path)
        return ext.lower() in VALID_EXTENSIONS

    def get_file_size(self, file_path):
        """Get formatted file size"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size}B"
            elif size < 1024 * 1024:
                return f"{size // 1024}KB"
            else:
                return f"{size // (1024 * 1024)}MB"
        except:
            return "N/A"

    def populate_tree(self, parent="", path=""):
        """Populate the tree view with files and folders"""
        if not path:
            path = self.base_directory

        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return

        folders = []
        files = []

        for item in items:
            item_path = os.path.join(path, item)

            # Skip hidden files/folders if not showing them
            if not self.show_hidden.get() and self.is_hidden(item_path):
                continue

            if os.path.isdir(item_path):
                folders.append((item, item_path))
            elif self.should_include_file(item_path):
                files.append((item, item_path))

        # Add folders first
        for item, item_path in folders:
            status = self.get_item_status(item_path, is_folder=True)
            folder_id = self.tree.insert(parent, "end", text=f"📁 {item}",
                                         values=("", "Folder", status),
                                         tags=(status,))
            self.tree_items[folder_id] = item_path
            self.update_item_color(folder_id, status)

            # Recursively populate subfolder
            self.populate_tree(folder_id, item_path)

        # Add files
        for item, item_path in files:
            status = self.get_item_status(item_path, is_folder=False)
            size = self.get_file_size(item_path)
            ext = os.path.splitext(item)[1] or "No ext"

            file_id = self.tree.insert(parent, "end", text=f"📄 {item}",
                                       values=(size, ext, status),
                                       tags=(status,))
            self.tree_items[file_id] = item_path
            self.update_item_color(file_id, status)

    def get_item_status(self, path, is_folder=False):
        """Get the status of an item (selected, excluded, etc.)"""
        if is_folder:
            if path in self.excluded_folders:
                return "Excluded"
            elif path in self.selected_folders:
                return "Selected"
            else:
                # Check if partially selected
                selected_count = 0
                total_count = 0
                for root, dirs, files in os.walk(path):
                    # Filter hidden items
                    if not self.show_hidden.get():
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]

                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.should_include_file(file_path):
                            total_count += 1
                            if file_path in self.selected_files:
                                selected_count += 1

                if total_count == 0:
                    return "Empty"
                elif selected_count == 0:
                    return "None"
                elif selected_count == total_count:
                    return "All Selected"
                else:
                    return f"Partial ({selected_count}/{total_count})"
        else:
            if path in self.excluded_files:
                return "Excluded"
            elif path in self.selected_files:
                return "Selected"
            else:
                return "None"

    def update_item_color(self, item_id, status):
        """Update the color of a tree item based on its status"""
        if "Selected" in status or status == "Selected":
            color = self.colors['fully_selected']
        elif "Partial" in status:
            color = self.colors['partially_selected']
        elif status == "Excluded":
            color = self.colors['excluded']
        else:
            color = self.colors['normal']

        # Note: tkinter Treeview doesn't support individual item background colors
        # This would require custom styling or a different approach
        # For now, we use the status column to show the state

    def refresh_tree(self):
        """Refresh the tree view"""
        if not self.base_directory:
            return

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_items.clear()

        # Repopulate
        self.populate_tree()
        self.update_selection_count()

    def toggle_selection(self, event=None, force_select=False, force_exclude=False):
        """Toggle selection state of selected items"""
        selection = self.tree.selection()
        if not selection:
            return

        for item_id in selection:
            path = self.tree_items.get(item_id)
            if not path:
                continue

            is_folder = os.path.isdir(path)

            if force_select:
                self.select_item(path, is_folder)
            elif force_exclude:
                self.exclude_item(path, is_folder)
            else:
                # Toggle based on current state
                if is_folder:
                    if path in self.selected_folders:
                        self.exclude_item(path, is_folder)
                    elif path in self.excluded_folders:
                        self.clear_item_selection(path, is_folder)
                    else:
                        self.select_item(path, is_folder)
                else:
                    if path in self.selected_files:
                        self.exclude_item(path, is_folder)
                    elif path in self.excluded_files:
                        self.clear_item_selection(path, is_folder)
                    else:
                        self.select_item(path, is_folder)

        self.refresh_tree()

    def select_item(self, path, is_folder):
        """Select an item or folder"""
        if is_folder:
            self.selected_folders.add(path)
            self.excluded_folders.discard(path)
            # Also select all files in the folder
            for root, dirs, files in os.walk(path):
                if not self.show_hidden.get():
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]

                for file in files:
                    file_path = os.path.join(root, file)
                    if self.should_include_file(file_path):
                        self.selected_files.add(file_path)
                        self.excluded_files.discard(file_path)
        else:
            self.selected_files.add(path)
            self.excluded_files.discard(path)

    def exclude_item(self, path, is_folder):
        """Exclude an item or folder"""
        if is_folder:
            self.excluded_folders.add(path)
            self.selected_folders.discard(path)
            # Also exclude all files in the folder
            for root, dirs, files in os.walk(path):
                if not self.show_hidden.get():
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]

                for file in files:
                    file_path = os.path.join(root, file)
                    if self.should_include_file(file_path):
                        self.excluded_files.add(file_path)
                        self.selected_files.discard(file_path)
        else:
            self.excluded_files.add(path)
            self.selected_files.discard(path)

    def clear_item_selection(self, path, is_folder):
        """Clear selection state of an item"""
        if is_folder:
            self.selected_folders.discard(path)
            self.excluded_folders.discard(path)
            # Clear selection for all files in folder
            for root, dirs, files in os.walk(path):
                if not self.show_hidden.get():
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]

                for file in files:
                    file_path = os.path.join(root, file)
                    if self.should_include_file(file_path):
                        self.selected_files.discard(file_path)
                        self.excluded_files.discard(file_path)
        else:
            self.selected_files.discard(path)
            self.excluded_files.discard(path)

    def select_all(self):
        """Select all items in the tree"""
        if not self.base_directory:
            return

        for root, dirs, files in os.walk(self.base_directory):
            if not self.show_hidden.get():
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files = [f for f in files if not f.startswith('.')]

            # Select folders
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                self.selected_folders.add(dir_path)
                self.excluded_folders.discard(dir_path)

            # Select files
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_include_file(file_path):
                    self.selected_files.add(file_path)
                    self.excluded_files.discard(file_path)

        self.refresh_tree()

    def clear_all(self):
        """Clear all selections"""
        self.selected_files.clear()
        self.selected_folders.clear()
        self.excluded_files.clear()
        self.excluded_folders.clear()
        self.refresh_tree()

    def select_all_in_folder(self):
        """Select all items in the selected folder"""
        selection = self.tree.selection()
        for item_id in selection:
            path = self.tree_items.get(item_id)
            if path and os.path.isdir(path):
                self.select_item(path, is_folder=True)
        self.refresh_tree()

    def exclude_all_in_folder(self):
        """Exclude all items in the selected folder"""
        selection = self.tree.selection()
        for item_id in selection:
            path = self.tree_items.get(item_id)
            if path and os.path.isdir(path):
                self.exclude_item(path, is_folder=True)
        self.refresh_tree()

    def show_context_menu(self, event):
        """Show context menu on right click"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def get_selected_files_list(self):
        """Get list of all selected files (excluding excluded ones)"""
        all_selected = set()

        # Add explicitly selected files
        all_selected.update(self.selected_files)

        # Add files from selected folders
        for folder in self.selected_folders:
            if folder not in self.excluded_folders:
                for root, dirs, files in os.walk(folder):
                    if not self.show_hidden.get():
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]

                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.should_include_file(file_path):
                            all_selected.add(file_path)

        # Remove excluded files
        all_selected -= self.excluded_files

        return sorted(list(all_selected))

    def update_selection_count(self):
        """Update the selection count display"""
        selected_files = self.get_selected_files_list()
        count = len(selected_files)
        self.selection_count_var.set(f"Selected: {count} files")

    def save_selection(self):
        """Save current selection to a file"""
        if not self.base_directory:
            messagebox.showwarning("Warning", "No base directory selected!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Selection",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            selection_data = {
                'base_directory': self.base_directory,
                'selected_files': list(self.selected_files),
                'selected_folders': list(self.selected_folders),
                'excluded_files': list(self.excluded_files),
                'excluded_folders': list(self.excluded_folders),
                'show_hidden': self.show_hidden.get(),
                'include_all_extensions': self.include_all_extensions.get(),
                'timestamp': datetime.now().isoformat()
            }

            try:
                with open(file_path, 'w') as f:
                    json.dump(selection_data, f, indent=2)
                messagebox.showinfo("Success", f"Selection saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save selection: {e}")

    def load_selection(self):
        """Load selection from a file"""
        file_path = filedialog.askopenfilename(
            title="Load Selection",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    selection_data = json.load(f)

                self.base_directory = selection_data['base_directory']
                self.selected_files = set(selection_data.get('selected_files', []))
                self.selected_folders = set(selection_data.get('selected_folders', []))
                self.excluded_files = set(selection_data.get('excluded_files', []))
                self.excluded_folders = set(selection_data.get('excluded_folders', []))
                self.show_hidden.set(selection_data.get('show_hidden', False))
                self.include_all_extensions.set(selection_data.get('include_all_extensions', False))

                self.status_var.set(f"Base directory: {self.base_directory}")
                self.refresh_tree()

                messagebox.showinfo("Success", "Selection loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load selection: {e}")

    def combine_files(self):
        """Combine selected files into a single output file"""
        selected_files = self.get_selected_files_list()

        if not selected_files:
            messagebox.showwarning("Warning", "No files selected!")
            return

        # Ask for output file location
        output_path = filedialog.asksaveasfilename(
            title="Save Combined File As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"filedog_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not output_path:
            return

        self.write_combined_file(selected_files, output_path)

        result = messagebox.askyesno("Success",
                                     f"Combined {len(selected_files)} files!\n\nOpen the file?")
        if result:
            try:
                os.startfile(output_path)
            except:
                messagebox.showinfo("Info", f"File saved at: {output_path}")

    def write_combined_file(self, file_list, output_path):
        """Write the combined file with all selected files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(f"# 🐕 FileDog Combined Files\n")
            out_file.write(f"# Generated on: {timestamp}\n")
            out_file.write(f"# Base directory: {self.base_directory}\n")
            out_file.write(f"# Total files: {len(file_list)}\n")
            out_file.write(f"# Hidden files shown: {self.show_hidden.get()}\n")
            out_file.write(f"# All extensions included: {self.include_all_extensions.get()}\n\n")

            # Write file list
            out_file.write("# Selected Files:\n")
            for file_path in file_list:
                try:
                    rel_path = os.path.relpath(file_path, self.base_directory)
                except ValueError:
                    rel_path = file_path
                out_file.write(f"# - {rel_path}\n")
            out_file.write("\n")

            # Write file contents
            for file_path in file_list:
                try:
                    rel_path = os.path.relpath(file_path, self.base_directory)
                except ValueError:
                    rel_path = file_path

                out_file.write(f"\n\n{'=' * 80}\n# FILE: {rel_path}\n")
                out_file.write(f"# Full path: {file_path}\n")
                out_file.write(f"{'=' * 80}\n")

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        out_file.write(content)
                        if not content.endswith('\n'):
                            out_file.write('\n')
                except Exception as e:
                    out_file.write(f"\n# Failed to read {file_path}: {e}\n")

    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Update selection count periodically
        def update_count():
            self.update_selection_count()
            self.root.after(1000, update_count)

        self.root.after(100, update_count)
        self.root.mainloop()

    def on_closing(self):
        """Handle application closing"""
        self.root.destroy()


def main():
    print("🐕 Starting FileDog...")

    # Check if directory was passed as command line argument
    if len(sys.argv) > 1:
        initial_dir = sys.argv[1]
        if os.path.isdir(initial_dir):
            app = FileDog()
            app.base_directory = initial_dir
            app.status_var.set(f"Base directory: {initial_dir}")
            app.refresh_tree()
            app.run()
        else:
            messagebox.showerror("Error", f"'{initial_dir}' is not a valid directory.")
    else:
        app = FileDog()
        app.run()


if __name__ == "__main__":
    main()