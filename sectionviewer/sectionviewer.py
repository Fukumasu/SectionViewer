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
from .param import svp, icon_path

class SectionViewer(ttk.Frame):
    def __init__(self, arg):
        root = tk.Tk()
        root.withdraw()
        root.iconbitmap(icon_path)
        icon = cv2.imread(svp('img/resources.png'))[-128:,:128]
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
            self.open_new(self.root, file_path=arg[0])
    
    def open_new(self, master, file_path=None):
        
        if file_path == None:
            filetypes = [('SectionViewer files', '*.secv'), 
                         ('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']), 
                         ('SV multi-stack files', '*.stac'),
                         ('All files', '*')]
            if not os.path.isfile(svp('init_dir.txt')):
                with open(svp('init_dir.txt'), 'w') as f:
                    f.write(os.path.expanduser('~/Desktop'))
            with open(svp('init_dir.txt'), 'r') as f:
                initialdir = f.read()
            if not os.path.isdir(initialdir):
                initialdir = os.path.expanduser('~/Desktop')
            file_path = filedialog.askopenfilename(parent=master, filetypes=filetypes, 
                                                   initialdir=initialdir, title='Open')
        
        if len(file_path) > 0:
            file_path = file_path.replace('\\', '/')
                
            master = tk.Toplevel(self.root)
            master.withdraw()
            master.iconbitmap(icon_path)
            self.wins += [master]
            if file_path[-5:] == '.stac':
                gui = STAC(self, master, file_path)
            else:
                gui = GUI(self, master, file_path)
            
            if hasattr(gui, 'Hub'):
                with open(svp('init_dir.txt'), 'w') as f:
                    f.write(os.path.dirname(file_path))
        else:
            close = True
            for w in self.wins:
                close = close and not bool(w.winfo_exists())
            if close:
                self.root.destroy()

    
pf = platform.system()
    
def launch(file_path=None):
    
    if pf == 'Windows':
        with open(svp('exe_path.txt'), 'r') as f:
            exe_path = f.read()
        if '--reinstall' in sys.argv[1:] or not os.path.isfile(exe_path):
            print('preparing installer...')
            subprocess.run('python ' + svp('setup_msi.py') + ' bdist_msi',
                           stdout=subprocess.PIPE, shell=True)
            with open(svp('exe_path.txt'), 'r') as f:
                exe_path0 = f.read()
            if os.path.isfile(exe_path0):
                print('successfully installed')
                exe_path = exe_path0
                if sys.argv[1:2] == ['--reinstall']:
                    sys.argv = sys.argv[:1] + sys.argv[2:]
            else:
                with open(svp('exe_path.txt'), 'w') as f:
                    f.write(exe_path)
                print('canceled')
                return
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    if file_path == None:
        root = tk.Tk()
        root.iconbitmap(icon_path)
        icon = cv2.imread(svp('img/resources.png'))[-128:,:128]
        icon = ImageTk.PhotoImage(Image.fromarray(icon[:,:,::-1]))
        canvas = tk.Canvas(root, width=240, height=150)
        canvas.create_rectangle(0, 0, 2000, 2000, fill='#606060', width=0)
        canvas.create_image(56, 11, image=icon, anchor='nw')
        canvas.pack()
        root.title('SectionViewer')
        root.geometry('+0+0')
        
        filetypes = [('SectionViewer files', '*.secv'), 
                     ('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']), 
                     ('SV multi-stack files', '*.stac'),
                     ('All files', '*')]
        if not os.path.isfile('init_dir.txt'):
            with open(svp('init_dir.txt'), 'w') as f:
                f.write(os.path.expanduser('~/Desktop'))
        with open(svp('init_dir.txt'), 'r') as f:
            initialdir = f.read()
        if not os.path.isdir(initialdir):
            initialdir = os.path.expanduser('~/Desktop')
            
        file_path = filedialog.askopenfilename(parent=root, filetypes=filetypes, 
                                               initialdir=initialdir, title='Open')
        root.destroy()
    if len(file_path) == 0:
        return
    if pf == 'Windows':
        subprocess.Popen(exe_path + ' {0}'.format(file_path), shell=True)
    else:
        subprocess.Popen('sectionviewer ' + file_path, shell=True)
    return file_path


if pf == 'Windows':
    def console_command():
        launch()
else:
    def console_command():
        main()


def main(*args):
    app = SectionViewer(args)
    app.mainloop()
    

