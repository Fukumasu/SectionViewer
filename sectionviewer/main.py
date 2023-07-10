import os
import platform
import subprocess
import sys

import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from .gui import GUI
from .stack import STAC

pf = platform.system()

class SectionViewer(ttk.Frame):
    def __init__(self, arg):
        self.fdir = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/') + '/'
        
        root = tk.Tk()
        root.withdraw()
        if pf == 'Windows':
            root.iconbitmap(self.fdir + 'img/icon.ico')
        icon = cv2.imread(self.fdir + 'img/resources.png')[-128:,:128]
        icon = ImageTk.PhotoImage(Image.fromarray(icon[:,:,::-1]))
        canvas = tk.Canvas(root, width=240, height=150)
        canvas.create_rectangle(0, 0, 2000, 2000, fill='#606060', width=0)
        canvas.create_image(56, 11, image=icon, anchor='nw')
        canvas.pack()
        root.geometry('+0+0')
        root.title('SectionViewer')
        super().__init__(root)
        self.root = root
        self.screenwidth = root.winfo_screenwidth()
        self.screenheight = root.winfo_screenheight()

        if pf == 'Windows':
            path = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
            path = path.split('/')
            if 'envs' in path:
                ei = [i for i in range(len(path)-1) if path[i] == 'envs'][0]
                envname = path[ei+1]
            else:
                ei = [i for i in range(len(path)) if path[i] == 'lib'][0]
                envname = 'base'
            activate = '/'.join(path[:ei]) + '/Scripts/activate.bat'
            execute = 'pythonw ' + '/'.join(path) + '/launch.py %1'
            commands = '@echo off\ncall {0}\ncall activate {1}\nstart {2}'.format(activate, envname, execute)
            with open('SectionViewer_entry.cmd', 'w') as f:
                f.write(commands)
        
        if len(arg) == 0:
            arg = sys.argv[1:]
        
        if len(arg) == 0:
            file_path = None
        else:
            file_path = arg[0]
        
        if file_path == None:
            self.root.deiconify()
            filetypes = [('SectionViewer files', '*.secv'), 
                         ('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']), 
                         ('SV multi-stack files', '*.stac'),
                         ('All files', '*')]
            if not os.path.isfile(self.fdir + 'init_dir.txt'):
                with open(self.fdir + 'init_dir.txt', 'w') as f:
                    f.write(os.path.expanduser('~/Desktop'))
            with open(self.fdir + 'init_dir.txt', 'r') as f:
                initialdir = f.read()
            if not os.path.isdir(initialdir):
                initialdir = os.path.expanduser('~/Desktop')
            file_path = filedialog.askopenfilename(parent=self.root, filetypes=filetypes, 
                                                   initialdir=initialdir, title='Open')
        
        if len(file_path) > 0:
            file_path = file_path.replace('\\', '/')
                
            master = tk.Toplevel(self.root)
            w, h = self.screenwidth, self.screenheight
            master.geometry('{0}x{1}+0+0'.format(w, h))
            if pf == 'Windows':
                master.iconbitmap(self.fdir + 'img/icon.ico')
                master.state('zoomed')
            
            pop = True if 'pop' in arg else False
            
            if file_path[-5:] == '.stac':
                gui = STAC(self, master, file_path, pop=pop)
            else:
                gui = GUI(self, master, file_path)
            
            if hasattr(gui, 'Hub') and not pop:
                with open(self.fdir + 'init_dir.txt', 'w') as f:
                    f.write(os.path.dirname(file_path))
        else:
            self.root.destroy()
                
    
    def open_new(self, master, file_path=None):
        
        if file_path == None:
            filetypes = [('SectionViewer files', '*.secv'), 
                         ('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']), 
                         ('SV multi-stack files', '*.stac'),
                         ('All files', '*')]
            if not os.path.isfile(self.fdir + 'init_dir.txt'):
                with open(self.fdir + 'init_dir.txt', 'w') as f:
                    f.write(os.path.expanduser('~/Desktop'))
            with open(self.fdir + 'init_dir.txt', 'r') as f:
                initialdir = f.read()
            if not os.path.isdir(initialdir):
                initialdir = os.path.expanduser('~/Desktop')
            file_path = filedialog.askopenfilename(parent=master, filetypes=filetypes, 
                                                   initialdir=initialdir, title='Open')
        
        if len(file_path) > 0:
            file_path = file_path.replace('\\', '/')
            subprocess.Popen('sectionviewer ' + file_path, shell=True)

    
def launch(file_path=None):
    if len(sys.argv) > 1 and file_path == None:
        if os.path.isfile(sys.argv[1]):
            file_path = sys.argv[1]
        else:
            file_path = ''
    if file_path == None:
        file_path = ''
    subprocess.Popen('sectionviewer ' + file_path, shell=True)
    return


def console_command():
    main()


def main(*args):
    app = SectionViewer(args)
    app.mainloop()