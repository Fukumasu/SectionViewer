import sys

from PIL import Image, ImageTk
import tkinter as tk

from .tools import base_dir, ask_file_path, resources, pf
from .gui.gui import Base_GUI
from .gui.secv import SECV_GUI
from .gui.stac import STAC_GUI


class SectionViewer(Base_GUI):
    def __init__(self, file_path = None):
        master = tk.Tk()
        self.master = master
        super().__init__(self)
        master.withdraw()
        if pf == 'Windows':
            master.iconbitmap(base_dir + 'img/icon.ico')
        
        icon = resources[-128:,:128]
        icon = ImageTk.PhotoImage(Image.fromarray(icon[:,:,::-1]))
        canvas = tk.Canvas(master, width=240, height=150)
        canvas.create_rectangle(0, 0, 2000, 2000, fill = '#606060', width = 0)
        canvas.create_image(56, 11, image=icon, anchor = 'nw')
        canvas.pack()
        master.geometry('+0+0')
        master.title('SectionViewer')
        master.screenwidth = master.winfo_screenwidth()
        master.screenheight = master.winfo_screenheight()
        
        if file_path is None:
            if len(sys.argv) > 1:
                file_path = ' '.join(sys.argv[1:])
            else:
                file_path = ask_file_path(master)
            
        if len(file_path) > 0:
            file_path = file_path.replace('\\', '/')
            
            if file_path[-5:] == '.stac':
                STAC_GUI(master, file_path)
            else:
                SECV_GUI(master, file_path)
        else:
            master.destroy()

def main():
    app = SectionViewer()
    app.mainloop()
    
if __name__ == '__main__':
    main()
