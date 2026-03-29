import customtkinter as ctk
import json
import os
import shutil
import zipfile
import subprocess
import sys
import tempfile
import webbrowser  # Added for the GitHub link
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LangMaster(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lang Master 0.2") # Updated version
        self.geometry("1000x700")

        if hasattr(sys, '_MEIPASS'):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(self.base_path, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.after(200, lambda: self.iconbitmap(icon_path))
            except: pass

        self.original_data = {}
        self.modified_data = {}
        self.filtered_keys = []
        self.loaded_count = 0
        self.batch_size = 50
        self.has_unsaved_changes = False

        self.load_initial_data()
        self.setup_ui()
        self.apply_filter_and_search()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_initial_data(self):
        filename = os.path.join(self.base_path, "en_us.json")
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.original_data = json.load(f)
            except Exception as e:
                messagebox.showerror("JSON Error", f"Failed to read en_us.json:\n{e}")
        else:
            self.original_data = {"item.minecraft.info": "No en_us.json found. Import one!"}

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="LANG MASTER", font=("Segoe UI", 18, "bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="Import JSON", command=self.import_json).pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="Export as Pack", fg_color="#2b8a3e", command=self.export_as_resource_pack).pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="Reset All", fg_color="#a61e1e", hover_color="#7a1515", command=self.confirm_reset).pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="Open RP Folder", fg_color="#444", command=self.open_mc_folder).pack(pady=5, padx=10)

        ctk.CTkLabel(self.sidebar, text="View Filter:").pack(pady=(20,0))
        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(self.sidebar, values=["All", "Renamed Only", "Original Only"], 
                          variable=self.filter_var, command=lambda x: self.apply_filter_and_search()).pack(pady=10)
        
        ctk.CTkLabel(self.sidebar, text="By Vaporwave", font=("Segoe UI", 12, "italic"), text_color="gray").pack(pady=5)
        
        # GITHUB LINK
        github_link = ctk.CTkLabel(self.sidebar, text="GitHub Repository", font=("Segoe UI", 11, "underline"), text_color="#1f6aa5", cursor="hand2")
        github_link.pack(pady=5)
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Vaporwave-13/Lang-Master"))

        # VERSION NUMBER AND STATS AT BOTTOM
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.bottom_sidebar.pack(side="bottom", pady=20, fill="x")

        self.stats_lbl = ctk.CTkLabel(self.bottom_sidebar, text="Modified: 0", font=("Arial", 12, "bold"))
        self.stats_lbl.pack()

        self.version_lbl = ctk.CTkLabel(self.bottom_sidebar, text="v0.2", font=("Segoe UI", 10), text_color="#555555")
        self.version_lbl.pack()

        # Main View
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.search_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Search items...", height=40)
        self.search_entry.pack(fill="x", pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filter_and_search())

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Minecraft Library")
        self.scroll_frame.pack(fill="both", expand=True)
        self.load_more_btn = ctk.CTkButton(self.scroll_frame, text="Load More...", command=self.load_next_batch)
        self.scroll_frame._parent_canvas.bind("<MouseWheel>", self.on_mousewheel, add="+")

    def add_row(self, key, original, current):
        is_renamed = key in self.modified_data
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=2, padx=5)
        
        key_font = ("Consolas", 10, "bold") if is_renamed else ("Consolas", 10)
        key_color = "white" if is_renamed else "gray"
        
        key_label = ctk.CTkLabel(row, text=key, font=key_font, width=250, anchor="w", text_color=key_color)
        key_label.pack(side="left", padx=10)
        
        entry = ctk.CTkEntry(row, width=350, font=("Segoe UI", 12))
        entry.insert(0, current)
        entry.pack(side="left", padx=10, pady=5)

        def on_change(event=None):
            val = entry.get()
            if val != original:
                self.modified_data[key] = val
                key_label.configure(font=("Consolas", 10, "bold"), text_color="white")
                self.has_unsaved_changes = True
            else:
                self.modified_data.pop(key, None)
                key_label.configure(font=("Consolas", 10), text_color="gray")
                self.has_unsaved_changes = True
                
            self.stats_lbl.configure(text=f"Modified: {len(self.modified_data)}")

        entry.bind("<FocusOut>", on_change)
        entry.bind("<Return>", on_change)

    def on_closing(self):
        if not self.modified_data or not self.has_unsaved_changes:
            self.destroy()
            return
        res = messagebox.askyesnocancel("Unsaved Changes", "Save changes as a pack before quitting?")
        if res is True: 
            if self.export_as_resource_pack(): self.destroy()
        elif res is False: self.destroy()

    def export_as_resource_pack(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip Archive", "*.zip")])
        if not save_path: return
        img_path = filedialog.askopenfilename(title="Select Pack Icon", filetypes=[("Images", "*.png *.jpg *.jpeg")])

        with tempfile.TemporaryDirectory() as temp_dir:
            lang_path = os.path.join(temp_dir, "assets", "minecraft", "lang")
            os.makedirs(lang_path, exist_ok=True)
            final_data = self.original_data.copy()
            final_data.update(self.modified_data)
            with open(os.path.join(lang_path, "en_us.json"), 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=4)
            mcmeta = {"pack": {"pack_format": 34, "description": "by Vaporwave"}}
            with open(os.path.join(temp_dir, "pack.mcmeta"), 'w', encoding='utf-8') as f:
                json.dump(mcmeta, f, indent=4)
            if img_path and os.path.exists(img_path):
                shutil.copy(img_path, os.path.join(temp_dir, "pack.png"))
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))
        
        self.has_unsaved_changes = False
        messagebox.showinfo("Success", "Texture Pack Created!")
        return True

    def apply_filter_and_search(self):
        query = self.search_entry.get().lower()
        mode = self.filter_var.get()
        self.filtered_keys = [k for k, v in self.original_data.items() if 
                              (not query or query in k.lower() or query in str(self.modified_data.get(k, v)).lower()) and
                              (mode == "All" or (mode == "Renamed Only" and k in self.modified_data) or (mode == "Original Only" and k not in self.modified_data))]
        self.load_more_btn.pack_forget()
        for child in self.scroll_frame.winfo_children():
            if child != self.load_more_btn: child.destroy()
        self.loaded_count = 0
        self.load_next_batch()

    def load_next_batch(self):
        self.load_more_btn.pack_forget()
        end = min(self.loaded_count + self.batch_size, len(self.filtered_keys))
        for key in self.filtered_keys[self.loaded_count:end]:
            self.add_row(key, self.original_data[key], self.modified_data.get(key, self.original_data[key]))
        self.loaded_count = end
        if self.loaded_count < len(self.filtered_keys): self.load_more_btn.pack(pady=20)

    def on_mousewheel(self, event):
        if self.scroll_frame._scrollbar.get() > 0.9:
            if self.loaded_count < len(self.filtered_keys): self.load_next_batch()

    def open_mc_folder(self):
        path = os.path.expandvars(r'%APPDATA%\.minecraft\resourcepacks')
        if os.path.exists(path): subprocess.Popen(f'explorer "{path}"')

    def confirm_reset(self):
        if self.modified_data and messagebox.askyesno("Confirm", "Discard all renames?"):
            self.modified_data = {}
            self.has_unsaved_changes = True
            self.apply_filter_and_search()

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f: self.original_data = json.load(f)
                self.modified_data = {}; self.has_unsaved_changes = False; self.apply_filter_and_search()
            except Exception as e: messagebox.showerror("Error", f"Failed to load JSON:\n{e}")

if __name__ == "__main__":
    app = LangMaster()
    app.mainloop()