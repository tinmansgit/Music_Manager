# Music Manager v2.0 20250414.07:45
import os, json, subprocess, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from mutagen import File
import music_manager_logger
from music_manager_logger import log_error, log_debug

DB_FILENAME = "/home/coder/bin/Python/Music_Manager/music_db.json"
EXTS = ('.mp3', '.ogg', '.oga', '.flac')
PLAYME_SCRIPT = "/home/coder/bin/Python/PlayMe/playme.py"

def load_db():
    log_debug("Attempting to load database.")
    if not os.path.exists(DB_FILENAME):
        log_debug(f"{DB_FILENAME} does not exist. Creating new db.")
        save_db({})
    try:
        with open(DB_FILENAME, 'r', encoding='utf-8') as f:
            db = json.load(f)
            log_debug(f"Database loaded successfully with {len(db)} record(s).")
            return db
    except Exception as e:
        log_error(f"Error loading db: {e}")
        return {}

def save_db(db):
    log_debug("Attempting to save database.")
    try:
        with open(DB_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
        log_debug("Database saved successfully.")
    except Exception as e:
        log_error(f"Error saving db: {e}")

def extract_meta(fp):
    log_debug(f"Extracting metadata from file: {fp}")
    meta = {"title": "", "artist": "", "album": "", "tracknumber": ""}
    try:
        audio = File(fp, easy=True)
        if audio and audio.tags:
            log_debug(f"Found tags in file: {fp}")
            for k in meta:
                meta[k] = audio.tags.get(k, [""])[0]
                log_debug(f"Extracted {k}: {meta[k]}")
        else:
            log_debug(f"No tags found in file: {fp}")
    except Exception as e:
        log_error(f"Error extracting meta {fp}: {e}")
    return meta

def add_file(db, fp):
    log_debug(f"Adding file: {fp}")
    if not fp.lower().endswith(EXTS):
        log_error(f"Unsupported file extension for: {fp}")
        return db
    try:
        s = os.stat(fp)
        log_debug(f"Obtained file stats for: {fp}")
    except Exception as e:
        log_error(f"Error accessing {fp}: {e}")
        return db
    meta = extract_meta(fp)
    rec = {
        "artist": meta["artist"],
        "title": meta["title"],
        "album": meta["album"],
        "tracknumber": meta["tracknumber"],
        "file_size": s.st_size,
        "file_name": os.path.basename(fp),
        "full_path": os.path.abspath(fp)
    }
    db[rec["full_path"]] = rec
    log_debug(f"Added file record: {rec}")
    return db

def import_dir(db, d):
    log_debug(f"Importing directory: {d}")
    for r, _, fs in os.walk(d):
        log_debug(f"Operating in directory: {r} with {len(fs)} file(s)")
        for f in fs:
            fp = os.path.join(r, f)
            if fp.lower().endswith(EXTS):
                log_debug(f"Found supported file: {fp}")
                add_file(db, fp)
            else:
                log_debug(f"Ignoring unsupported file: {fp}")
    return db

def create_form(frame, fields, init=None):
    log_debug("Creating form.")
    entries = {}
    for idx, (label, key) in enumerate(fields):
        ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="w", pady=2)
        ent = ttk.Entry(frame, width=50)
        ent.grid(row=idx, column=1, sticky="w", pady=2)
        entries[key] = ent
        if key == "full_path":
            ttk.Button(frame, text="Browse", command=lambda e=ent: browse_file(e, entries)).grid(row=idx, column=2, padx=5)
        if init and key in init:
            log_debug(f"Initializing field '{key}' with value '{init[key]}'")
            ent.insert(0, str(init[key]))
    log_debug("Form created.")
    return entries

def browse_file(path_entry, entries):
    log_debug("Browsing file...")
    fp = filedialog.askopenfilename(title="Select", filetypes=[("Audio", "*.mp3 *.ogg *.oga *.flac")])
    if fp:
        log_debug(f"File selected: {fp}")
        path_entry.delete(0, tk.END)
        path_entry.insert(0, fp)
        entries["file_name"].delete(0, tk.END)
        entries["file_name"].insert(0, os.path.basename(fp))
        try:
            size = os.stat(fp).st_size
            entries["file_size"].delete(0, tk.END)
            entries["file_size"].insert(0, size)
            log_debug(f"File size for '{fp}' is {size} bytes")
        except Exception as e:
            log_error(f"Error for {fp}: {e}")

class BaseDialog(tk.Toplevel):
    def __init__(self, master, title, fields, init=None):
        log_debug(f"Initializing BaseDialog titled '{title}'")
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result = None
        frame = ttk.Frame(self)
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.entries = create_form(frame, fields, init)
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=10)
        ttk.Button(self.btn_frame, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(self.btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)
        log_debug("BaseDialog initialized.")

    def on_ok(self):
        log_debug("OK clicked on BaseDialog; processing entries.")
        self.result = {k: e.get().strip() for k, e in self.entries.items()}
        if self.result.get("full_path", "").lower().endswith(EXTS):
            meta = extract_meta(self.result["full_path"])
            for f in ("artist", "title", "album", "tracknumber"):
                if not self.result[f]:
                    self.result[f] = meta[f]
                    log_debug(f"Updated field '{f}' with metadata: {meta[f]}")
            if not self.result["file_name"]:
                self.result["file_name"] = os.path.basename(self.result["full_path"])
                log_debug(f"Set file_name to {self.result['file_name']}")
            if not self.result["file_size"]:
                try:
                    self.result["file_size"] = os.stat(self.result["full_path"]).st_size
                    log_debug(f"Set file_size to {self.result['file_size']}")
                except Exception as e:
                    log_error(f"Error getting file size for {self.result['full_path']}: {e}")
                    self.result["file_size"] = ""
        log_debug(f"Dialog result: {self.result}")
        self.destroy()

class EntryDialog(BaseDialog):
    def __init__(self, master, title, init=None):
        log_debug(f"Initializing EntryDialog titled '{title}'")
        fields = [("Artist", "artist"), ("Title", "title"), ("Album", "album"), ("Tracknumber", "tracknumber"),
                  ("Size", "file_size"), ("Name", "file_name"), ("Path", "full_path")]
        super().__init__(master, title, fields, init)

class ExtendedEntryDialog(tk.Toplevel):
    def __init__(self, master, keys_list, current_index, db):
        log_debug("Initializing ExtendedEntryDialog")
        super().__init__(master)
        self.master = master
        self.keys_list = keys_list
        self.current_index = current_index
        self.db = db
        self.title("Edit Extended")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result = None
        self.fields = [("Artist", "artist"), ("Title", "title"), ("Album", "album"), ("Tracknumber", "tracknumber"),
                       ("Size", "file_size"), ("Name", "file_name"), ("Path", "full_path")]
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.entries = create_form(self.form_frame, self.fields, self.current_record())
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(pady=10)
        ttk.Button(self.nav_frame, text="Previous", command=self.go_previous).pack(side="left", padx=5)
        ttk.Button(self.nav_frame, text="Save", command=self.save_current).pack(side="left", padx=5)
        ttk.Button(self.nav_frame, text="Next", command=self.go_next).pack(side="left", padx=5)
        ttk.Button(self.nav_frame, text="Close", command=self.on_close).pack(side="left", padx=5)
        log_debug("ExtendedEntryDialog initialized.")

    def current_record(self):
        key = self.keys_list[self.current_index]
        log_debug(f"Fetching current record for key: {key}")
        return self.db.get(key, {})

    def update_form(self):
        rec = self.current_record()
        log_debug(f"Updating form with record: {rec}")
        for key, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(rec.get(key, "")))

    def save_current(self):
        log_debug("Saving current record in ExtendedEntryDialog.")
        rec = {k: e.get().strip() for k, e in self.entries.items()}
        if rec.get("full_path", "").lower().endswith(EXTS):
            meta = extract_meta(rec["full_path"])
            for f in ("artist", "title", "album", "tracknumber"):
                if not rec[f]:
                    rec[f] = meta[f]
                    log_debug(f"Auto-filled field '{f}' with meta: {meta[f]}")
            if not rec["file_name"]:
                rec["file_name"] = os.path.basename(rec["full_path"])
                log_debug(f"Set file_name: {rec['file_name']}")
            if not rec["file_size"]:
                try:
                    rec["file_size"] = os.stat(rec["full_path"]).st_size
                    log_debug(f"Set file_size: {rec['file_size']}")
                except Exception as e:
                    log_error(f"Error getting file size {rec['full_path']}: {e}")
                    rec["file_size"] = ""
        current_key = self.keys_list[self.current_index]
        new_key = rec.get("full_path")
        if new_key and new_key != current_key:
            self.db.pop(current_key, None)
            self.db[new_key] = rec
            self.keys_list[self.current_index] = new_key
            log_debug(f"Updated record key: replaced {current_key} with {new_key}")
        else:
            self.db[current_key] = rec
            log_debug(f"Saved record for key: {current_key}")
        messagebox.showinfo("Save", "Saved.")

    def go_previous(self):
        log_debug("Navigating to previous record.")
        if self.current_index == 0:
            messagebox.showinfo("Navigation", "1st record.")
            log_debug("Already at first record; cannot go previous.")
            return
        self.save_current()
        self.current_index -= 1
        self.update_form()
        log_debug(f"Moved to record index: {self.current_index}")

    def go_next(self):
        log_debug("Navigating to next record.")
        if self.current_index == len(self.keys_list) - 1:
            messagebox.showinfo("Navigation", "Last record.")
            log_debug("Already at last record; cannot go next.")
            return
        self.save_current()
        self.current_index += 1
        self.update_form()
        log_debug(f"Moved to record index: {self.current_index}")

    def on_close(self):
        log_debug("Closing ExtendedEntryDialog; saving current record.")
        self.save_current()
        self.destroy()

class MultiEditDialog(BaseDialog):
    def __init__(self, master):
        log_debug("Initializing MultiEditDialog")
        fields = [("Artist", "artist"), ("Title", "title"), ("Album", "album"), ("Tracknumber", "tracknumber")]
        super().__init__(master, "Multi-Edit", fields)

    def on_ok(self):
        log_debug("OK clicked on MultiEditDialog; processing entries.")
        self.result = {k: e.get().strip() for k, e in self.entries.items() if e.get().strip()}
        log_debug(f"MultiEditDialog result: {self.result}")
        self.destroy()

class MusicDBApp(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            icon = tk.PhotoImage(file="/home/coder/bin/Python/Music_Manager/music_manager_icon.png")
            self.iconphoto(False, icon)
        except Exception as e:
            log_error(f"Failed to load icon: {e}")
        log_debug("Initializing MusicDBApp")
        self.title("Music Manager")
        self.geometry("1000x600")
        self.db = load_db()
        log_debug(f"Database loaded with {len(self.db)} records")
        self.sort_info = {"column": None, "reverse": False}
        self.search_text = tk.StringVar()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        log_debug("Creating widgets")
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background="black", foreground="white", fieldbackground="black", font=("TkDefaultFont", 11))
        s.configure("Treeview.Heading", background="grey20", foreground="white")
        
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        for (txt, cmd) in [("Import Directory", self.handle_import_directory),
                           ("Add File", self.handle_add_file),
                           ("Add Manually", self.handle_add_entry),
                           ("Edit", self.handle_edit_entry),
                           ("Delete", self.handle_delete_entry),
                           ("PlayMe", self.handle_open_playme),
                           ("Refresh", self.refresh_list),
                           ("Save to File", self.handle_save_to_file),
                           ("Close", self.on_close)]:
            log_debug(f"Adding toolbar button: {txt}")
            ttk.Button(toolbar, text=txt, command=cmd).pack(side="left", padx=2)

        s_frame = ttk.Frame(self)
        s_frame.pack(fill="x", padx=5, pady=(0,5))
        ttk.Label(s_frame, text="Search:").pack(side="left")
        se = ttk.Entry(s_frame, textvariable=self.search_text, width=40)
        se.pack(side="left", padx=2)
        se.bind("<Return>", lambda e: self.search_records())
        for txt, cmd in [("Search", self.search_records), ("Clear Search", self.clear_search)]:
            log_debug(f"Adding search toolbar button: {txt}")
            ttk.Button(s_frame, text=txt, command=cmd).pack(side="left", padx=2)
        
        cont = ttk.Frame(self)
        cont.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(cont, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        cols = ("artist", "title", "album", "tracknumber", "file_size", "file_name", "full_path")
        self.tree = ttk.Treeview(cont, columns=cols, show="headings", selectmode="extended", yscrollcommand=scrollbar.set)
        for col in cols:
            self.tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100, anchor="w")
            log_debug(f"Configured tree column: {col}")
        self.tree.tag_configure("odd", background="black")
        self.tree.tag_configure("even", background="grey20")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        self.total_label = ttk.Label(self, text="Total Files: 0")
        self.total_label.pack(side="bottom", pady=5)
        log_debug("Widgets created, refreshing list")
        self.refresh_list()

    def refresh_list(self, recs=None):
        log_debug("Refreshing list")
        for i in self.tree.get_children():
            self.tree.delete(i)
        recs = recs or list(self.db.values())
        if self.sort_info["column"]:
            log_debug(f"Sorting list by column: {self.sort_info['column']} with reverse={self.sort_info['reverse']}")
            try:
                recs.sort(key=lambda r: int(r.get("file_size") or 0) if self.sort_info["column"] == "file_size"
                          else r.get(self.sort_info["column"], "").lower(), reverse=self.sort_info["reverse"])
            except Exception as e:
                log_error(f"Sort error: {e}")
        else:
            recs.sort(key=lambda r: r.get("artist", "").lower())
        for idx, r in enumerate(recs):
            tag = "even" if idx % 2 == 0 else "odd"
            try:
                size_bytes = int(r.get("file_size") or 0)
                size_mb = f"{size_bytes/(1024*1024):.2f} MB"
            except Exception:
                size_mb = ""
            self.tree.insert("", tk.END, iid=r["full_path"],
                             values=(r["artist"], r["title"], r["album"], r["tracknumber"], size_mb, r["file_name"], r["full_path"]),
                             tags=(tag,))
            log_debug(f"Inserted record: {r['full_path']} with tag: {tag}")
        self.total_label.config(text=f"Total Files: {len(self.db)}")
        log_debug(f"Total files displayed: {len(self.db)}")

    def sort_by_column(self, col):
        log_debug(f"Sorting by column: {col}")
        if self.sort_info["column"] == col:
            self.sort_info["reverse"] = not self.sort_info["reverse"]
            log_debug(f"Toggled sort order for '{col}'. Reverse now: {self.sort_info['reverse']}")
        else:
            self.sort_info = {"column": col, "reverse": False}
            log_debug(f"Switched sort column to: {col}")
        self.refresh_list()

    def search_records(self):
        term = self.search_text.get().strip().lower()
        log_debug(f"Searching records for term: '{term}'")
        if not term:
            log_debug("Empty search term; displaying all records")
            self.refresh_list()
            return
        filtered = [r for r in self.db.values() if any(term in str(r.get(k, "")).lower() for k in r)]
        log_debug(f"Found {len(filtered)} records matching '{term}'")
        self.refresh_list(filtered)

    def clear_search(self):
        log_debug("Clearing search criteria")
        self.search_text.set("")
        self.refresh_list()

    def handle_import_directory(self):
        log_debug("Triggered handle_import_directory")
        d = filedialog.askdirectory(title="Select Directory")
        if d:
            log_debug(f"Directory selected for import: {d}")
            self.db = import_dir(self.db, d)
            log_debug(f"Database updated after import; now {len(self.db)} records")
            save_db(self.db)
            self.refresh_list()
            messagebox.showinfo("Import", "Completed")
        else:
            log_debug("No directory selected for import")

    def handle_add_file(self):
        log_debug("Triggered handle_add_file")
        fp = filedialog.askopenfilename(title="Select", filetypes=[("Audio", "*.mp3 *.ogg *.oga *.flac")])
        if fp:
            log_debug(f"File selected for addition: {fp}")
            add_file(self.db, fp)
            save_db(self.db)
            self.refresh_list()
            messagebox.showinfo("Add", f"File '{os.path.basename(fp)}' added")
        else:
            log_debug("No file selected in handle_add_file")

    def handle_add_entry(self):
        log_debug("Triggered handle_add_entry")
        d = EntryDialog(self, "Add New")
        self.wait_window(d)
        if d.result and d.result.get("full_path"):
            log_debug(f"New entry added with full_path: {d.result['full_path']}")
            self.db[d.result["full_path"]] = d.result
            save_db(self.db)
            self.refresh_list()
            messagebox.showinfo("Add", "Added")
        else:
            log_debug("Add entry failed: 'full_path' missing or dialog cancelled")
            messagebox.showerror("Error", "Full Path")

    def handle_edit_entry(self):
        log_debug("Triggered handle_edit_entry")
        sel = self.tree.selection()
        if not sel:
            log_debug("Edit aborted: No selection")
            messagebox.showwarning("Edit", "None selected")
            return
        if len(sel) == 1:
            keys_order = self.tree.get_children()
            current_key = sel[0]
            try:
                current_index = list(keys_order).index(current_key)
            except ValueError:
                log_debug("Edit error: Selected key not found in tree")
                messagebox.showerror("Edit", "Not found")
                return
            log_debug(f"Editing one entry: {current_key} at index {current_index}")
            d = ExtendedEntryDialog(self, list(keys_order), current_index, self.db)
            self.wait_window(d)
            save_db(self.db)
            self.refresh_list()
            messagebox.showinfo("Edit", "Updated")
        else:
            log_debug(f"Editing multiple entries: {sel}")
            d = MultiEditDialog(self)
            self.wait_window(d)
            if d.result:
                for key in sel:
                    if key in self.db:
                        self.db[key].update(d.result)
                        log_debug(f"Updated record: {key} with {d.result}")
                    else:
                        log_error(f"Edit error: {key} not found")
                        messagebox.showerror("Error", f"{key} not found")
                save_db(self.db)
                self.refresh_list()
                messagebox.showinfo("Edit", "Updated")
            else:
                log_debug("MultiEditDialog cancelled or returned no result")

    def handle_delete_entry(self):
        log_debug("Triggered handle_delete_entry")
        sel = self.tree.selection()
        if not sel:
            log_debug("Delete aborted: No selection")
            messagebox.showwarning("Delete", "None selected")
            return
        if messagebox.askyesno("Delete", "Sure?"):
            for key in sel:
                if key in self.db:
                    log_debug(f"Deleting record: {key}")
                    self.db.pop(key, None)
                else:
                    log_error(f"Delete error: {key} not found")
            save_db(self.db)
            self.refresh_list()
            messagebox.showinfo("Delete", "Deleted")
        else:
            log_debug("Delete cancelled by user")

    def handle_open_playme(self):
        log_debug("Triggered handle_open_playme")
        sel = self.tree.selection()
        if not sel:
            log_debug("PlayMe aborted: No selection")
            messagebox.showwarning("PlayMe", "None selected")
            return
        fps = [self.db[k]["full_path"] for k in sel if k in self.db]
        if not fps:
            log_debug("PlayMe error: No valid file paths found for selection")
            messagebox.showerror("PlayMe", "Not found")
            return
        try:
            log_debug(f"Launching PLAYME_SCRIPT with files: {fps}")
            subprocess.Popen(["python3", PLAYME_SCRIPT] + fps)
            messagebox.showinfo("PlayMe", "Launched")
        except Exception as e:
            log_error(f"Error launching PLAYME_SCRIPT: {e}")
            messagebox.showerror("PlayMe", f"Error: {e}")

    def handle_save_to_file(self):
        log_debug("Triggered handle_save_to_file")
        updated = 0
        for rec in self.db.values():
            fp = rec.get("full_path")
            if not fp or not os.path.isfile(fp):
                log_error(f"File not found: {fp}")
                continue
            try:
                audio = File(fp, easy=True)
                if audio is None:
                    log_error(f"Mutagen could not open file: {fp}")
                    continue
                for tag in ("artist", "title", "album", "tracknumber"):
                    value = rec.get(tag, "")
                    if value:
                        audio[tag] = value
                        log_debug(f"Set {tag}='{value}' for file: {fp}")
                audio.save()
                updated += 1
            except Exception as e:
                log_error(f"Error writing metadata to {fp}: {e}")
        save_db(self.db)
        self.refresh_list()
        messagebox.showinfo("Save to File", f"Metadata written to {updated} file(s).")
        log_debug("Completed metadata save to files.")

    def on_close(self):
        log_debug("Application close requested")
        if messagebox.askyesno("Exit", "Sure?"):
            log_debug("Closing application")
            self.destroy()
        else:
            log_debug("Close cancelled by user")

if __name__ == "__main__":
    MusicDBApp().mainloop()
