import os
import subprocess
import sys

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from .gui import GUI
from .stack import STAC

class SectionViewer(ttk.Frame):
    def __init__(self, arg):
        eDir = os.path.dirname(os.path.abspath(__file__))
        eDir = eDir.replace("\\", "/") + "/"
        
        self.eDir = eDir
        
        root = tk.Tk()
        root.withdraw()
        root.iconbitmap(eDir + "img/SectionViewer.ico")
        label = ttk.Label(root, text="Open OIB, TIFF, or SECV file")
        label.pack(padx=50, pady=30)
        root.title('SectionViewer')
        super().__init__(root)
        self.root = root
        
        if len(arg) == 0:
            arg = sys.argv[1:]
        self.wins = []
        
        self.root.deiconify()
        if len(arg) == 0:
            self.open_new(self.root)
        else:
            self.open_new(self.root, file_name=arg[0])
    
    def open_new(self, master, file_name=None):
        
        if file_name == None:
            fTyp = [("SectionViewer projects", "*.secv"), 
                    ("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]), 
                    ("SV multi-stack files", "*.stac"),
                    ("All files", "*")]
            if not os.path.isfile(self.eDir + "init_dir.txt"):
                with open(self.eDir + "init_dir.txt", "w") as f:
                    f.write(os.path.expanduser("~/Desktop"))
            with open(self.eDir + "init_dir.txt", "r") as f:
                iDir = f.read()
            if not os.path.isdir(iDir):
                iDir = os.path.expanduser("~/Desktop")
            file_name = filedialog.askopenfilename(parent=master, filetypes=fTyp, 
                                                   initialdir=iDir, title="Open")
        
        if len(file_name) > 0:
            file_name = file_name.replace("\\", "/")
                
            master = tk.Toplevel(self.root)
            master.withdraw()
            master.iconbitmap(self.eDir + "img/SectionViewer.ico")
            self.wins += [master]
            if file_name[-5:] == ".stac":
                gui = STAC(self, master, file_name)
            else:
                gui = GUI(self, master, file_name)
            
            if gui.Hub.load_success:
                with open(self.eDir + "init_dir.txt", "w") as f:
                    f.write(os.path.dirname(file_name))
                self.root.withdraw()
            else:
                master.destroy()
                close = True
                for w in self.wins:
                    close = close and not bool(w.winfo_exists())
                if close:
                    self.root.destroy()
        else:
            close = True
            for w in self.wins:
                close = close and not bool(w.winfo_exists())
            if close:
                self.root.destroy()
        
def _test():
    app = SectionViewer([])
    app.mainloop()

def main(*arg):
    eDir = os.path.dirname(os.path.abspath(__file__))
    eDir = eDir.replace("\\", "/") + "/"
    with open(eDir + "epath.txt", "r") as f:
        epath = f.read()
    if not os.path.isfile(epath):
        print("preparing installer...")
        subprocess.run("python " + eDir + "setup_msi.py bdist_msi",
                       stdout=subprocess.PIPE, shell=True)
        with open(eDir + "epath.txt", "r") as f:
            epath = f.read()
        if os.path.isfile(epath):
            print("successfully installed")
        else:
            print("canceled")
            return
    if len(arg) > 0:
        subprocess.run(epath + " {0}".format(arg[0]), shell=True)
    else:
        subprocess.run(epath, shell=True)
    
def launch(file_name=None):
    eDir = os.path.dirname(os.path.abspath(__file__))
    eDir = eDir.replace("\\", "/") + "/"
    with open(eDir + "epath.txt", "r") as f:
        epath = f.read()
    if not os.path.isfile(epath):
        print("preparing installer...")
        subprocess.run("python " + eDir + "setup_msi.py bdist_msi",
                       stdout=subprocess.PIPE, shell=True)
        with open(eDir + "epath.txt", "r") as f:
            epath = f.read()
        if os.path.isfile(epath):
            print("successfully installed")
        else:
            print("canceled")
            return
    if file_name == None:
        fTyp = [("SectionViewer projects", "*.secv"), 
                ("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]), 
                ("SV multi-stack files", "*.stac"),
                ("All files", "*")]
        if not os.path.isfile(eDir + "init_dir.txt"):
            with open(eDir + "init_dir.txt", "w") as f:
                f.write(os.path.expanduser("~/Desktop"))
        with open(eDir + "init_dir.txt", "r") as f:
            iDir = f.read()
        if not os.path.isdir(iDir):
            iDir = os.path.expanduser("~/Desktop")
        root = tk.Tk()
        root.title('SectionViewer')
        label = ttk.Label(root, text="Open OIB, TIFF, or SECV file")
        label.pack(padx=50, pady=30)
        root.iconbitmap(eDir + "img/SectionViewer.ico")
        file_name = filedialog.askopenfilename(parent=root, filetypes=fTyp, 
                                               initialdir=iDir, title="Open")
        root.destroy()
    if len(file_name) == 0:
        return
    subprocess.Popen(epath + " {0}".format(file_name), shell=True)
    return file_name

