# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 21:09:58 2020

@author: kazuu
"""
import os
import subprocess
from subprocess import PIPE
import sys
import zipfile

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
        super().__init__(root)
        self.root = root
        
        if len(arg) == 0:
            arg = sys.argv[1:]
        self.wins = []
        
        self.create_widgets(self.root)
        self.root.bind("<Control-o>", lambda event: self.open_new(self.root))
        self.root.title("SectionViewer")
        if len(arg) == 0:
            self.root.deiconify()
        else:
            self.open_new(self.root, file_name=arg[0])
        
    def create_widgets(self, master):
        self.menu_bar = tk.Menu(master)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=lambda: self.open_new(self.root), accelerator="Ctrl+O")
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        master.config(menu=self.menu_bar)
        
        label = ttk.Label(master, text="Press Ctrl+O to open a file.")
        label.pack(padx=50, pady=30)
    
    
    def open_new(self, master, file_name=None):
        
        if file_name == None:
            fTyp = [("SectionViewer projects", "*.secv"), 
                    ("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]), 
                    ("SV multi-stack files", "*.stac")]
            if not os.path.isfile(self.eDir + ".init_dir.txt"):
                with open(self.eDir + ".init_dir.txt", "w") as f:
                    f.write(os.path.expanduser("~/Desktop"))
            with open(self.eDir + ".init_dir.txt", "r") as f:
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
                with open(self.eDir + ".init_dir.txt", "w") as f:
                    f.write(os.path.dirname(file_name))
                self.root.withdraw()
            else:
                master.destroy()
                close = True
                for w in self.wins:
                    close = close and not bool(w.winfo_exists())
                if close:
                    self.root.deiconify()
        

def main(*arg):
    eDir = os.path.dirname(os.path.abspath(__file__))
    eDir = eDir.replace("\\", "/") + "/"
    assoc = subprocess.run("assoc .secv", shell=True, stdout=PIPE, text=True)
    if assoc!='.secv=SectionViewerFile\n':
        subprocess.run('powershell start-process ' + eDir + 'assocsecv.bat -verb runas', shell=True)
    if not os.path.isfile(eDir + "img/xyz.png"):
        with zipfile.ZipFile(eDir + "img/resources.zip") as zp:
            zp.extractall(path=eDir+"img/")
    app = SectionViewer(arg)
    app.mainloop()
    
def launch(file_name=None):
    eDir = os.path.dirname(os.path.abspath(__file__))
    eDir = eDir.replace("\\", "/") + "/"
    if file_name == None:
        fTyp = [("SectionViewer projects", "*.secv"), 
                ("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]), 
                ("SV multi-stack files", "*.stac")]
        if not os.path.isfile(eDir + ".init_dir.txt"):
            with open(eDir + ".init_dir.txt", "w") as f:
                f.write(os.path.expanduser("~/Desktop"))
        with open(eDir + ".init_dir.txt", "r") as f:
            iDir = f.read()
        if not os.path.isdir(iDir):
            iDir = os.path.expanduser("~/Desktop")
        root = tk.Tk()
        root.withdraw()
        root.iconbitmap(eDir + "img/SectionViewer.ico")
        file_name = filedialog.askopenfilename(parent=root, filetypes=fTyp, 
                                               initialdir=iDir, title="Open")
        root.destroy()
    if len(file_name) == 0:
        return
    subprocess.Popen("sectionviewer {0}".format(file_name), shell=True)
    return file_name
    
if __name__ == "__main__":
    launch()
