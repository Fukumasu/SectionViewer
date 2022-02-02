import os
import subprocess
import sys

import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from .gui import GUI
from .stack import STAC

class SectionViewer(ttk.Frame):
    def __init__(self, arg):
        mDir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(mDir)
        
        root = tk.Tk()
        root.withdraw()
        root.iconbitmap('img/SectionViewer.ico')
        icon = cv2.imread('img/resources.png')[-128:,:128]
        icon = ImageTk.PhotoImage(Image.fromarray(icon[:,:,::-1]))
        canvas = tk.Canvas(root, width=240, height=150)
        canvas.create_rectangle(0, 0, 2000, 2000, fill='#606060', width=0)
        canvas.create_image(56, 11, image=icon, anchor='nw')
        canvas.pack()
        root.geometry('+0+0')
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
            fTyp = [('SectionViewer projects', '*.secv'), 
                    ('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']), 
                    ('SV multi-stack files', '*.stac'),
                    ('All files', '*')]
            if not os.path.isfile('init_dir.txt'):
                with open('init_dir.txt', 'w') as f:
                    f.write(os.path.expanduser('~/Desktop'))
            with open('init_dir.txt', 'r') as f:
                idir = f.read()
            if not os.path.isdir(idir):
                idir = os.path.expanduser('~/Desktop')
            file_name = filedialog.askopenfilename(parent=master, filetypes=fTyp, 
                                                   initialdir=idir, title='Open')
        
        if len(file_name) > 0:
            file_name = file_name.replace('\\', '/')
                
            master = tk.Toplevel(self.root)
            master.withdraw()
            master.iconbitmap('img/SectionViewer.ico')
            self.wins += [master]
            if file_name[-5:] == '.stac':
                gui = STAC(self, master, file_name)
            else:
                gui = GUI(self, master, file_name)
            
            if hasattr(gui, 'Hub'):
                with open('init_dir.txt', 'w') as f:
                    f.write(os.path.dirname(file_name))
        else:
            close = True
            for w in self.wins:
                close = close and not bool(w.winfo_exists())
            if close:
                self.root.destroy()

    
def launch(file_name=None):
    mDir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(mDir)
    
    with open('exe_path.txt', 'r') as f:
        epath = f.read()
    if '--reinstall' in sys.argv[1:] or not os.path.isfile(epath):
        print('preparing installer...')
        subprocess.run('python ' + 'setup_msi.py bdist_msi',
                       stdout=subprocess.PIPE, shell=True)
        with open('exe_path.txt', 'r') as f:
            epath0 = f.read()
        if os.path.isfile(epath0):
            print('successfully installed')
        else:
            with open('exe_path.txt', 'w') as f:
                f.write(epath)
            print('canceled')
            return
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    if not os.path.isfile(str(file_name)):
        fTyp = [('SectionViewer projects', '*.secv'), 
                ('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']), 
                ('SV multi-stack files', '*.stac'),
                ('All files', '*')]
        if not os.path.isfile('init_dir.txt'):
            with open('init_dir.txt', 'w') as f:
                f.write(os.path.expanduser('~/Desktop'))
        with open('init_dir.txt', 'r') as f:
            iDir = f.read()
        if not os.path.isdir(iDir):
            iDir = os.path.expanduser('~/Desktop')
        root = tk.Tk()
        root.iconbitmap('img/SectionViewer.ico')
        icon = cv2.imread('img/resources.png')[-128:,:128]
        icon = ImageTk.PhotoImage(Image.fromarray(icon[:,:,::-1]))
        canvas = tk.Canvas(root, width=240, height=150)
        canvas.create_rectangle(0, 0, 2000, 2000, fill='#606060', width=0)
        canvas.create_image(56, 11, image=icon, anchor='nw')
        canvas.pack()
        root.title('SectionViewer')
        root.geometry('+0+0')
        file_name = filedialog.askopenfilename(parent=root, filetypes=fTyp, 
                                               initialdir=iDir, title='Open')
        root.destroy()
    if len(file_name) == 0:
        return
    subprocess.Popen(epath + ' {0}'.format(file_name), shell=True)
    return file_name


def main(*args):
    app = SectionViewer(args)
    app.mainloop()
    

