import os
import sys
import time
import json5
import shutil
import requests
import threading
import webbrowser # :( yet another import bloating my software
import subprocess
from PIL import Image
from io import BytesIO
import customtkinter as ctk
from tkinter import messagebox
from luaparser import ast, astnodes

MODS_PATH = os.path.join(os.getenv('APPDATA'), "Balatro", "Mods")
SMODS_PATH = os.path.join(os.getenv('APPDATA'), "Balatro", "Versions")
CACHE_PATH = os.path.join(os.getenv('APPDATA'), "Bitters")

if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)

global busy
busy = False

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
    return os.path.join(base_path, "ASSETS", relative_path)

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
        shutil.rmtree(mod_folder)  # delete folder and contents
    except PermissionError: 
        show_admin_warning("you need to make me administrator to delete stuff")
    row.destroy()

# load all mods
def load_mods(frame, ctkBut, ctkButtons):
    global busy
    if busy: show_admin_warning("Jeez give it a bloody second"); return
    busy = True

    for widget in frame.winfo_children():
        widget.destroy()

    if ctkBut: # fix my fuck up
        for btn in ctkButtons:
            # Im lazy so you get a for loop
            ctkButtons[btn].configure(fg_color="#12121A", hover_color="#222235")
        ctkBut.configure(fg_color="#6366F1", hover_color="#6366F1")

    # check for mod path, if no, then make it
    if not os.path.exists(MODS_PATH):
        os.makedirs(MODS_PATH)

    Currentsmods = None
    mods = []                               #   ↰
    seen_mods = set()                       #   ↑
                                            #   ↑
    # go through each mod and add them to the table
    # note that this also includes finding current smods
    if len(os.listdir(MODS_PATH)) == 0:
        ctk.CTkLabel(frame, text = "You dont have any mods..", font=("Comic Sans MS", 32), pady=8).pack()
        ctk.CTkLabel(frame, text = "try going to #modding in the balatro server", font=("Comic Sans MS", 24), pady=8).pack()

        discordicon = resource_path("Placeholder.png")
        invitelink = "https://discord.gg/balatro"
        link = "https://discord.gg/1116389027176787968/1209506514763522108"
        link = link.replace("https://", "discord://")
        ctk.CTkButton(frame,
                      image=ctk.CTkImage(Image.open(discordicon), size=(24, 24)),      
                      text = "Balatro Discord Server", font=("Comic Sans MS", 16),      
                      command=lambda: (webbrowser.open_new(invitelink), webbrowser.open_new(link))
                      ).pack(pady=8)

        busy = False

        return
    else:
        for folder in os.listdir(MODS_PATH):
            folder_path = os.path.join(MODS_PATH, folder)
            if not os.path.isdir(folder_path):
                continue

            data = None

            # version = None
            for file in os.listdir(folder_path):
                if not file.endswith(".json"):
                    continue
                json_path = os.path.join(folder_path, file)

                smods = False

                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        temp_data = json5.load(f)
                    if temp_data.get("id") and temp_data.get("id") not in seen_mods:
                        data = temp_data
                        break
                    else:
                        if temp_data.get("name") == "Steamodded":
                            data = temp_data # waaawawawa
                            smods = True
                            break
                except:
                    continue
            if smods: # Smods related
                version_path = None
                version = None
                for fname in os.listdir(folder_path):
                    if fname == "version.lua":
                        version_path = os.path.join(folder_path, fname)
                        break

                if version_path: 

                    with open(version_path, "r", encoding="utf-8") as f: # yet again still smods related
                        lua_src = f.read()

                    tree = ast.parse(lua_src)

                    for node in ast.walk(tree):
                        if isinstance(node, astnodes.Return) and isinstance(node.values[0], astnodes.String): # should always be 0, since it doesnt ever have more than 1 return, istg if john smods changes it
                            version = node.values[0].s
                            break
            

            if not data:
                continue
            
            if not smods:
                seen_mods.add(data["id"])
                ignore_file = os.path.join(folder_path, ".lovelyignore")
                is_on = not os.path.exists(ignore_file)
                mods.append({
                    "folder_path": folder_path,
                    "data": data,
                    "is_on": is_on
                })
            else:
                Currentsmods = {
                    "folder_name": folder,
                    "folder_path": folder_path,
                    "version": version,
                }

    # self explanatory
    mods.sort(key=lambda m: (not m["is_on"], (m["data"].get("display_name") or m["data"].get("name")).lower()))
    



# Seperator | find mods to smods




    # buttons to change smods version, if someone shows me them having 7 smods buttons, I'll consider making it a dropdown
    if not os.path.exists(SMODS_PATH):
        os.makedirs(SMODS_PATH)

    # I have to copy paste, since smods json is different from other mods
    
    versions = []
    seen_versions = set()

    smodsRow = ctk.CTkFrame(frame, fg_color="#0A0A0F")
    smodsRow.pack(fill="x")

    for folder in os.listdir(SMODS_PATH):
        folder_path = os.path.join(SMODS_PATH, folder)
        if not os.path.isdir(folder_path):
            continue
        

        version_path = os.path.join(folder_path, "version.lua")

        if os.path.exists(version_path):
            try:
                version = None
                with open(version_path, "r", encoding="utf-8") as f:
                    lua_src = f.read()

                tree = ast.parse(lua_src)

                for node in ast.walk(tree):
                    if isinstance(node, astnodes.Return) and isinstance(node.values[0], astnodes.String): # should always be 0, since it doesnt ever have more than 1 return, istg if john smods changes it
                        version = node.values[0].s
                        break
            
                if version and version not in seen_versions:
                    seen_versions.add(version)
                    versions.append({
                        "folder_path": folder_path,
                        "folder_name": folder,
                        "version": version,
                    })
            except:
                pass

    def changeSmods(smod): # smod = [folder_path: string, version: string, folder_name: string]
        smod_path = smod["folder_path"]
        smod_name = smod["folder_name"]

        # Remove old smods | maybe later ill check to see if its in the versions folder 🤷‍♂️ (the shrug guy does the 67 haha guys im so funny)
        shutil.rmtree(Currentsmods["folder_path"], True)

        # Add the new smod_path (DONT FUCKING DELETE IT THIS TIME)
        shutil.copytree(smod_path, os.path.join(MODS_PATH, smod_name))

        # Relllooooadd
        load_mods(frame, None, None)

    found = False
    def addsmod(smod):
        smod_path = smod["folder_path"]
        smod_ver = smod["version"]

        selected = False 

        color = "#12121A"
        # Check if current smods == this one
        if smod_ver == Currentsmods["version"]:
            color = "#181822"
            selected = True 
            found = smod_path


        # remove the text other than the actual version | when 1.0.1 or smth comes out ill change it to that
        smod_ver = smod_ver[smod_ver.find("-")+1:len(smod_ver)]
        smod_ver = smod_ver[0:smod_ver.find("-")] # mitosis

        # make button
        btn = ctk.CTkButton(smodsRow, fg_color=color, hover_color = "#222235", font=("Comic Sans MS", 24), text=smod_ver, command=lambda s=smod: changeSmods(s))
        btn.pack(expand=True,side="left",pady=8)

    for smod in versions:
        addsmod(smod)
    if not found and not os.path.exists(os.path.join(SMODS_PATH, Currentsmods["folder_name"])):
        # clone smods version, and paste it to SMODS_PATH
        shutil.copytree(Currentsmods["folder_path"], os.path.join(SMODS_PATH, Currentsmods["folder_name"]))
    if len(smodsRow.winfo_children()) == 0:
        ctk.CTkLabel(smodsRow, text = "Couldn't find any instances of smods, try reloading.", font=("Comic Sans MS", 24), pady=8).pack()




# Seperator | smods to mods button creation




    # Create the buttons for mods
    index = 1
    for mod in mods:
        folder_path = mod["folder_path"]
        data = mod["data"]
        is_on = mod["is_on"]

        if index == 3:
            index = 1

        name = data.get("display_name") or data.get("name")
        author = ", ".join(data.get("author", [])) if data.get("author") else ""
        color = "#12121A" if index == 1 else "#181822"
        hover_color = "#222235"
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
        name_label = ctk.CTkLabel(row, text=name, font=("Comic Sans MS", 16))
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
        
    # add funny nothing button
    nothn_btn = ctk.CTkButton(frame, text="Button that does nothing", font=("Comic Sans MS", 24, "normal", "italic"))
    nothn_btn.pack(padx=5)
    busy = False

# the info funcs
def load_download(frame, ctkBut, ctkButtons):
    global busy
    if busy: show_admin_warning("Jeez give it a bloody second"); return
    busy = True
    for w in frame.winfo_children():
        w.destroy()

    if ctkBut: # fix my fuck up
        for btn in ctkButtons:
            # Im lazy so you get a for loop
            ctkButtons[btn].configure(fg_color="#12121A", hover_color="#222235")
        ctkBut.configure(fg_color="#6366F1", hover_color="#6366F1")

    warnlabel = ctk.CTkLabel(frame, text="uhhh this might take a sec...")
    warnlabel.pack()
    
    def worker():

        mods = []

        CHUNK = 20
        idx = 0

        def show_chunk(start, loadbut):
            if loadbut: loadbut.destroy()

            nonlocal idx
            chunk = mods[start:start+CHUNK]
            for i, m in enumerate(chunk):
                color = "#1E1E1E" if idx % 2 == 0 else "#2A2A2A"
                row = ctk.CTkFrame(frame, fg_color=color, width=260, height=200)
                row.grid(padx=10, pady=5)
                
                # later change this to a url (m["thumb"])
                image = Image.open(resource_path("Placeholder.png"))
                if m["thumb"]:
                    try:
                        image = Image.open(BytesIO(requests.get(m["thumb"]).content))
                    except:
                        pass

                img = ctk.CTkImage(dark_image=image, size=(250 ,141.625)) # 16:9
                
                ctk.CTkLabel(row, image=img, text="").pack(side="top", padx=10, pady=5)
                ctk.CTkLabel(row, text=m["meta"].get("title") or m["name"], text_color="#fff", font=("Comic Sans MS", 16)).pack(side="left", padx=10, pady=5)

                def dl(mod=m):
                    pass

                ctk.CTkButton(row, text="Download", width=80, fg_color="#4C78E5", command=dl).pack(side="right", padx=10, pady=5)
                idx += 1

            # load more
            if start + CHUNK < len(mods):
                btn = ctk.CTkButton(frame, text="Load More") # sometimes just wont create ig
                btn.grid(pady=10)
                btn.configure(False,command=lambda b=btn: show_chunk(start+CHUNK, b))

        frame.after(0, lambda: show_chunk(0, None))
        
        base = "https://raw.githubusercontent.com/skyline69/balatro-mod-index/main/mods"
        repo = "https://api.github.com/repos/skyline69/balatro-mod-index/contents/mods"
        folders = requests.get(repo).json()
        folders = sorted(folders, key=lambda item: item["name"][str.find(item["name"], "@"):len(item["name"])]) # omg my 1 month problem was that I was that **I** sorted it wrong...

        threads = []
        def loadmod_cool(f):

            modinfo = {"name": f["name"], "meta": {}, "desc": "", "thumb": None, "dl": None}

            try:
                meta = requests.get(f"{base}/{f['name']}/meta.json").json()

                modinfo["meta"] = meta
                modinfo["name"] = meta["title"]
                # meta Meta:  {'title': '123abc', 'requires-steamodded': False, 'requires-talisman': False, 'categories': ['Quality of Life', 'Miscellaneous'], 'author': '123abc',
                #  'repo': 'https://github.com/123/abc', 'downloadURL': 'https://github.com/123/abc/archive/refs/tags/V1.0.0.zip', 'version': '1.0.0'}
                modinfo["dl"] = meta.get("download_url")
            except: return

            try:
                modinfo["desc"] = requests.get(f"{base}/{f['name']}/description.md").text
            except:
                modinfo["desc"] = "Unabled To load description"
                pass

            try:
                thumb_url = f"{base}/{f['name']}/thumbnail.jpg"
                if requests.head(thumb_url).status_code == 200:
                    modinfo["thumb"] = thumb_url
            except: pass

            mods.append(modinfo)

        chunkshown = False
        for i in range(len(folders)):
            f = folders[i]
            if f["type"] != "dir": continue
            threads = [t for t in threads if t.is_alive()]  # fuck dead threads

            while len(threads) >= 5:
                time.sleep(0.1)
                threads = [t for t in threads if t.is_alive()]      

            curthread = threading.Thread(target=lambda: loadmod_cool(f))            
            threads.append(curthread)
            curthread.start() 
                            # vv Because of this being called outside of the threads (since i dont want it running several times), 
            if len(mods) >= 25 and not chunkshown:
                warnlabel.destroy()
                chunkshown = True
                show_chunk(0, None)
                global busy
                busy = False

    t = threading.Thread(target=worker)
    t.start() # to not lag my uio
    
# info buttons
def createInfobuttons(frame, modframe): # frame = sidemenu, modframe = the frame for mods
    # the set menu buttons
    button_configs = [ # thanks to the guy from discord
        {"pady": 7.5, "func": load_mods, "title": "Installed"},
        {"pady": 0, "func": load_download, "title": "Browse"},
        {"pady": 7.5, "func": load_download, "title": "Modpacks"},
    ]
    buttons = {}
    for config in button_configs:
        ctkbut = ctk.CTkButton(frame, text=config["title"], font=("Comic Sans MS", 24), fg_color="#12121A", hover_color="#222235")
        ctkbut.configure(command=lambda c = config["func"], b = ctkbut: c(modframe, b, buttons))
        if button_configs[0] == config:
            ctkbut.configure(fg_color="#6366F1", hover_color="#6366F1")
        ctkbut.pack(fill="x", padx=15, pady=config["pady"], ipady = 3)
        buttons[len(buttons)] = ctkbut
        print(ctkbut, buttons)

# App button Funcs
def EnableMods():
    for mod in mod_list.winfo_children():
        try:
            if not mod.enabled:
                toggle_mod(mod.folder_path, mod.toggle_btn)
        except:
            pass

def DisableMods():
    for mod in mod_list.winfo_children():
        try:
            if mod.enabled:
                toggle_mod(mod.folder_path, mod.toggle_btn)
        except:
            pass

def OpenFolder():
    subprocess.Popen('explorer ' + MODS_PATH)
# --- APP SETUP ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(resource_path("theme.json"))


app = ctk.CTk()
app.title("Bitter's bmm")
app.geometry("1200x800")

# top frame
top_frame = ctk.CTkFrame(app, height=120)
top_frame.pack(fill="x")

# Container
Title = ctk.CTkFrame(top_frame, fg_color="transparent")
Title.pack(side="left", padx=16)
# Kitty
ctk.CTkLabel(Title, text="", image=ctk.CTkImage( Image.open( resource_path( "Kittty8Bit.png" ) ), size=(24, 24) ) ).pack(side="left", padx=3)
# Bitter (THSTEFJNDC ME!!!)
ctk.CTkLabel(Title, text="Bitter's", font=("Comic Sans MS", 24, "bold")).pack(side="left", padx=4)
# Superscript
ctk.CTkLabel(Title, text="Mod Manager", font=("Comic Sans MS", 16, "italic")).pack(padx=5)

# start
start_btn = ctk.CTkButton(top_frame, text="▶ Start Game", command=start_game, font=("Comic Sans MS", 16))
start_btn.pack(side="right", padx=15, pady=10, ipady=5)

# Center buttons
btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent") # so like its placed right
btn_frame.place(relx=0.5, rely=0.5, anchor="center")

# Refresh
RefreshIcon = resource_path("Folder.png")  # finally I can check my mods folder
Refresh_btn = ctk.CTkButton(btn_frame, image=ctk.CTkImage(Image.open(RefreshIcon), size=(20,20)), text="Refresh", command=lambda: load_mods(mod_list, None, None), font=("Comic Sans MS", 16), fg_color="#1B3B44", hover_color="#0C2228")
Refresh_btn.grid(row=0, column=0, padx=10, ipady = 5)

# Disable
disablebtn = ctk.CTkButton(btn_frame, text="Disable Mods", command=DisableMods, font=("Comic Sans MS", 16), fg_color="#E53552", hover_color="#9E1B31")
disablebtn.grid(row=0, column=1, padx=10, ipady = 5)

# Enable
enablebtn = ctk.CTkButton(btn_frame, text="Enable Mods", command=EnableMods, font=("Comic Sans MS", 16), fg_color="#4CAF81", hover_color="#1F8A58")
enablebtn.grid(row=0, column=2, padx=10, ipady = 5)

# Folder
folderIcon = resource_path("Folder.png")  # finally I can check my mods folder
folder_btn = ctk.CTkButton(btn_frame, image=ctk.CTkImage(Image.open(folderIcon), size=(20,20)), text="Downloaded", command=OpenFolder, font=("Comic Sans MS", 16), fg_color="#1B3B44", hover_color="#0C2228")
folder_btn.grid(row=0, column=3, padx=10, ipady = 5)

# mod list frame
frame_outer = ctk.CTkFrame(app, fg_color="#0A0A0F")
frame_outer.pack(fill="both", expand=True, padx=3, pady=10)

mod_list = ctk.CTkScrollableFrame(frame_outer, fg_color="#12121A")
mod_list.pack(side="right", fill="both", ipadx = 325, expand=True, padx=10, pady=10)

Infoframe = ctk.CTkFrame(frame_outer, fg_color="#12121A")
Infoframe.pack(side="left", fill="both", ipadx = 33, expand=True, padx=10, pady=10)
createInfobuttons(Infoframe, mod_list)


load_mods(mod_list, None, None)

app.grid_columnconfigure(0, weight=1)
app.mainloop()

# pyinstaller --onefile --noconsole --icon=icon.ico --add-data "ASSETS;ASSETS" main.py when exporting