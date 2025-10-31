import os
import sys
import json
import subprocess
import random
import getpass
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

MODS_PATH = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Balatro', "Mods")

def show_admin_warning(Text):
    popup = ctk.CTkToplevel()
    popup.title("Warning")
    popup.geometry("350x180")
    popup.grab_set()  # lock focus to popup
    popup.resizable(False, False)
    popup.attributes("-topmost", True)

    # center it on screen
    popup.update_idletasks()
    w = popup.winfo_width()
    h = popup.winfo_height()
    x = (popup.winfo_screenwidth() // 2) - (w // 2)
    y = (popup.winfo_screenheight() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")

    frame = ctk.CTkFrame(popup, fg_color="transparent", corner_radius=10)
    frame.pack(expand=True, fill="both", padx=20, pady=20)

    label = ctk.CTkLabel(frame, text=Text, font=("Comic Sans MS", 18), wraplength=280, justify="center")
    label.pack(pady=(15, 10))

    btn = ctk.CTkButton(frame, text="alright then", font=("Comic Sans MS", 14, "bold"), command=popup.destroy, width=100)
    btn.pack(pady=(5, 10))

    popup.mainloop()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "ASSets", relative_path)

# open steam version of balatro
def start_game():
    try:
        subprocess.run("start steam://run/2379780", shell=True)
    except Exception as e:
        messagebox.showerror("Error", f"Couldn't launch Balatro:/n{e}")

# toggle mod state
def toggle_mod(mod_folder, button):
    ignore_file = os.path.join(mod_folder, ".lovelyignore")
    if os.path.exists(ignore_file):
        os.remove(ignore_file)
        button.configure(text="On", fg_color="#4CAF81")
    else:
        open(ignore_file, "w").close()
        button.configure(text="Off", fg_color="#E53552")

    # update the row's enabled state
    try:
        parent = button.master
        parent.enabled = (button.cget("text") == "On")
    except Exception:
        pass

def deleteMod(mod_folder, row):
    try:
        os.remove(mod_folder)
    except PermissionError: 
        show_admin_warning("you need to make me administrator to delete stuff")
    row.destroy()

# load all mods
def load_mods(frame):
    for widget in frame.winfo_children():
        widget.destroy()

    if not os.path.exists(MODS_PATH):
        os.makedirs(MODS_PATH)

    mods = []
    seen_mods = set()

    for folder in os.listdir(MODS_PATH):
        folder_path = os.path.join(MODS_PATH, folder)
        if not os.path.isdir(folder_path):
            continue

        data = None

        for file in os.listdir(folder_path):
            if not file.endswith(".json"):
                continue
            json_path = os.path.join(folder_path, file)
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    temp_data = json.load(f)
                if temp_data.get("id") and temp_data.get("id") not in seen_mods:
                    data = temp_data
                    break
            except:
                continue

        if not data:
            continue

        seen_mods.add(data["id"])
        ignore_file = os.path.join(folder_path, ".lovelyignore")
        is_on = not os.path.exists(ignore_file)
        mods.append({
            "folder_path": folder_path,
            "data": data,
            "is_on": is_on
        })

    mods.sort(key=lambda m: (not m["is_on"], (m["data"].get("display_name") or m["data"].get("name")).lower()))

    index = 1
    for mod in mods:
        folder_path = mod["folder_path"]
        data = mod["data"]
        is_on = mod["is_on"]

        if index == 3:
            index = 1

        name = data.get("display_name") or data.get("name")
        author = ", ".join(data.get("author", [])) if data.get("author") else ""
        color = "#1E1E1E" if index == 1 else "#2A2A2A"
        hover_color = "#3B3B3B"
        row = ctk.CTkFrame(frame, fg_color=color)
        row.pack(fill="x", padx=10, pady=10)

        # store folder path & initial state
        row.folder_path = folder_path
        row.enabled = is_on

        # --- Icon ---
        image_path = resource_path("Placeholder.png")
        assets_path = os.path.join(folder_path, "assets", "1x")
        if os.path.exists(assets_path):
            for file in os.listdir(assets_path):
                if not file.lower().endswith(".png"):
                    continue
                if "icon" in file.lower():
                    image_path = os.path.join(assets_path, file)
                    break

        image = ctk.CTkImage(dark_image=Image.open(image_path), size=(40, 40))
        image_label = ctk.CTkLabel(row, image=image, text="")
        image_label.pack(side="left", padx=10)

        # title
        name_label = ctk.CTkLabel(row, text=name, text_color="#fff", font=("Comic Sans MS", 16))
        name_label.pack(side="left", padx=10)

        # author
        if author:
            author_label = ctk.CTkLabel(row, text=f"by {author}", text_color="#aaa", font=("Comic Sans MS", 12, "normal", "italic"))
            author_label.pack(side="left", padx=10)

        # toggle button
        btn_text = "On" if is_on else "Off"
        btn_color = "#4CAF81" if is_on else "#E53552"
        row.toggle_btn = ctk.CTkButton(row, text=btn_text, width=60, fg_color=btn_color, font=("Comic Sans MS", 14))
        row.toggle_btn.configure(command=lambda f=folder_path, b=row.toggle_btn: toggle_mod(f, b))
        row.toggle_btn.pack(side="right", padx=10)

        # Delete Button
        delIcon = resource_path("bin.png")  # finally I can check my mods folder
        delImg = ctk.CTkImage(dark_image=Image.open(delIcon))
        del_btn = ctk.CTkButton(row, image=delImg, text="", command=None, width=24, fg_color="#8F1939", hover_color="#771127") # add command=lambda: If variables to be added
        del_btn.configure(command=lambda r=row, f=folder_path: deleteMod(f, r)) # btw i have to use configure for naming i think
        del_btn.pack(side="right", padx=5)

        # hover effect
        for object in {row, image_label, name_label, row.toggle_btn, del_btn}:
            object.bind("<Enter>", lambda e, r=row, c=hover_color: r.configure(fg_color=c))
            object.bind("<Leave>", lambda e, r=row, c=color: r.configure(fg_color=c))


        index += 1

# App button Funcs
Mods = [
    "Angled Bitterness",
    "Milky's Bullshit",
    "Busted Buffoons",
    "Balala",
    "Terraria",
    "Aikoyori's shenanigans",
    "Tangents",
    "Lucky Rabbit",
    "Hot potato",
    "Cold Beans",
    "Garbshit",
    "Jambatro",
    "Vall-karri",
    "Maniatro",
    "Balatropit! actually probably dont.",
    "Ultrakill"
]

Music = [
    "Ween",
    "Primus",
    "MiLKY-P",
    "Slipknot",
    "Arcanaut",
    "femtanyl",
    "Nick Drake",
    "Mr. Bungle",
    "Radio head",
    "Jamiroquai",
    "Sound Garden",
    "Eliott Smith",
    "Stevie Wonder",
    "Geordie Greep",
    "System Of A Down",
    "Tyler the Creator",
    "Queens of the Stone Age",
]

Titles = [
    ":3",
    "Play " + random.choice(Mods),
    "Go listen to " + random.choice(Music)
]

def EnableMods():
    for mod in mod_list.winfo_children():
        if not mod.enabled:
            toggle_mod(mod.folder_path, mod.toggle_btn)

def DisableMods():
    for mod in mod_list.winfo_children():
        if mod.enabled:
            toggle_mod(mod.folder_path, mod.toggle_btn)

def OpenFolder():
    subprocess.Popen('explorer ' + MODS_PATH)

msgs = [
    "say gex",
    "go play " + random.choice(Mods),
    "go listen to " + random.choice(Music),
    "Die",
    ":3",
    "WARNING! popup may explode",
    "please dont make more popups",
    "wawa"
]

def popup(e):
    if e.num == 3:
        show_admin_warning(random.choice(msgs))
# --- APP SETUP ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


app = ctk.CTk()
app.title("Bitter's bmm | " + random.choice(Titles))
app.geometry("1200x800")

# top frame
top_frame = ctk.CTkFrame(app, fg_color="#111")
top_frame.pack(fill="x")

title = ctk.CTkButton(top_frame, text="Bitter's mod manager", fg_color="transparent", font=("Comic Sans MS", 20, "bold"), command=lambda: load_mods(mod_list))
title.pack(side="left", padx=15, pady=10)
title.bind("<Button>", popup)

start_btn = ctk.CTkButton(top_frame, text="Start Game", command=start_game, font=("Comic Sans MS", 16))
start_btn.pack(side="right", padx=15, pady=10)

# toggle buttons
btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent") # so like its placed right
btn_frame.place(relx=0.5, rely=0.5, anchor="center")

disablebtn = ctk.CTkButton(btn_frame, text="Disable Mods", command=DisableMods, font=("Comic Sans MS", 16), fg_color="#E53552", hover_color="#9E1B31")
disablebtn.grid(row=0, column=0, padx=10)

enablebtn = ctk.CTkButton(btn_frame, text="Enable Mods", command=EnableMods, font=("Comic Sans MS", 16), fg_color="#4CAF81", hover_color="#1F8A58")
enablebtn.grid(row=0, column=1, padx=10)

# Mod Folder Button
folderIcon = resource_path("Folder.png")  # finally I can check my mods folder
folderImg = ctk.CTkImage(dark_image=Image.open(folderIcon))
folder_btn = ctk.CTkButton(top_frame, image=folderImg, text="", command=OpenFolder, width=24, fg_color="#A3931F", hover_color="#82740B") # add command=lambda: If variables to be added
folder_btn.pack(side="left", padx=3, pady=10)

# mod list frame
mod_frame_outer = ctk.CTkFrame(app, fg_color="#151515")
mod_frame_outer.pack(fill="both", expand=True, padx=3, pady=10)

mod_list = ctk.CTkScrollableFrame(mod_frame_outer)
mod_list.pack(fill="both", expand=True, padx=10, pady=10)

load_mods(mod_list)

app.mainloop()

# pyinstaller --onefile --noconsole --icon=icon.ico --add-data "ASSETS;ASSETS" main.py when exporting