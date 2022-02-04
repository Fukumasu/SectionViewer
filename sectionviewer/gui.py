import os
import platform
import shutil
import time
import traceback

import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox

from .hub import Hub

pf = platform.system()

class GUI(ttk.Frame):
    def __init__(self, SV, master, file_path):
        self.SV = SV
        self.file_path = file_path
        self.file_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        
        resources = cv2.imread('img/resources.png')
        c_image = resources[:35,:36]
        self.c_image = ImageTk.PhotoImage(Image.fromarray(c_image[:,:,::-1]))
        p_image = resources[:35,36:72]
        self.p_image = ImageTk.PhotoImage(Image.fromarray(p_image[:,:,::-1]))
        s_image = resources[:35,72:108]
        self.s_image = ImageTk.PhotoImage(Image.fromarray(s_image[:,:,::-1]))
        k_image = resources[35:204]
        self.k_image = ImageTk.PhotoImage(Image.fromarray(k_image[:,:,::-1]))
        self.xyz = resources[:22,108:174]
        e_image = resources[:14,174:188]
        self.e_image = ImageTk.PhotoImage(Image.fromarray(e_image[:,:,::-1]))
        hor_image = resources[:20,188:208]
        self.hor_image = ImageTk.PhotoImage(Image.fromarray(hor_image[:,:,::-1]))
        ver_image = resources[:20,208:228]
        self.ver_image = ImageTk.PhotoImage(Image.fromarray(ver_image[:,:,::-1]))
        
        self.thickness = tk.StringVar()
        self.a_on = tk.BooleanVar()
        self.b_on = tk.BooleanVar()
        self.p_on = tk.BooleanVar()
        self.g_on = tk.BooleanVar()
        self.white = tk.BooleanVar()
        self.depth = tk.IntVar()
        self.zoom = tk.StringVar()
        self.upperleft = (0,0)
        self.lock = False
        
        super().__init__(master)
        self.title = self.file_name
        self.master.title(self.title)
        
        # Palette
        self.palette = tk.Toplevel(self.master)
        self.palette.withdraw()
        if pf == 'Windows':
            self.palette.iconbitmap('img/icon.ico')
        self.palette.resizable(height=False, width=False)
        
        self.SV.root.withdraw()
        self.create_widgets()
        self.master.update()
        
        def close():
            if self.master.winfo_exists: 
                self.master.destroy()
            close = True
            for w in self.SV.wins:
                close = close and not bool(w.winfo_exists())
            if close:
                self.SV.root.destroy()
        try:
            self.Hub = Hub(self, file_path)
        except Exception as e:
            messagebox.showerror('Error', traceback.format_exception_only(type(e), e)[0],
                                 parent=self.master)
            close()
            return
        if not self.Hub.load_success:
            close()
            return
        
        def switch(event):
            if str(self.palette.focus_get())[-5:] != 'entry':
                key = event.keysym
                if key == 'c':
                    self.Hub.channels.settings()
                elif key == 'p':
                    self.Hub.points.settings()
                elif key == 's':
                    self.Hub.snapshots.settings()
                    
        self.palette.bind('<c>', switch)
        self.palette.bind('<p>', switch)
        self.palette.bind('<s>', switch)
        self.palette.bind('<Control-s>', lambda event: self.Hub.save(self.Hub.secv_name))
        self.palette.bind('<Control-w>', lambda event: self.Hub.save())
        self.palette.bind('<Control-z>', lambda event: self.Hub.undo())
        self.palette.bind('<Control-Shift-Z>', lambda event: self.Hub.redo())
        self.palette.bind('<Control-y>', lambda event: self.Hub.redo())
        self.palette.bind('<Return>', lambda event: [self.palette.grab_release(), 
                                                     self.palette.withdraw()])
        def hide():
            self.palette.grab_release()
            self.palette.withdraw()
        self.palette.protocol('WM_DELETE_WINDOW', hide)
        
        self.create_commands()
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        self.master.deiconify()
        
        self.shift = np.array([0.,0.])
        self.angle = 0.
        self.expand = 1.
        self.trim = np.array([0.,0.])
        
        self.click = None
        self.click_time = 0
        self.p_num = -1
        self.mode = 0
        
        if pf == 'Windows':
            self.flags = np.array([1,4,131072,256])
        elif pf == 'Linux':
            self.flags = np.array([1,4,8,256])
        
        self.first = True
        
        
    def create_widgets(self):
        # Guide
        self.guide_note = ttk.Notebook(self.master)
        self.guide_note.pack(padx=10, pady=10, side=tk.RIGHT)
        
        self.guide_frame = ttk.Frame(self.guide_note)
        self.guide_canvas = tk.Canvas(self.guide_frame, width=400, height=569)
        bary = tk.Scrollbar(self.guide_frame, orient=tk.VERTICAL)
        bary.pack(side=tk.RIGHT, fill=tk.Y)
        bary.config(command=self.guide_canvas.yview)
        self.guide_canvas.config(yscrollcommand=bary.set)
        self.guide_canvas.config(scrollregion=(0,0,400,569))
        self.guide_id = self.guide_canvas.create_image(0, 0, anchor='nw')
        self.guide_canvas.create_image(0, 400, anchor='nw', image=self.k_image)
        self.guide_canvas.pack()
        self.guide_note.add(self.guide_frame, text='Guide')
        
        self.side_frame = ttk.Frame(self.guide_note)
        self.side_canvas = tk.Canvas(self.side_frame, width=400, height=569)
        bary = tk.Scrollbar(self.side_frame, orient=tk.VERTICAL)
        bary.pack(side=tk.RIGHT, fill=tk.Y)
        bary.config(command=self.side_canvas.yview)
        self.side_canvas.config(yscrollcommand=bary.set)
        self.side_canvas.config(scrollregion=(0,0,400,569))
        fill = '#ffffff' if self.white.get() else '#000000'
        self.side_back = self.side_canvas.create_rectangle(0, 0, 400, 569, fill=fill, width=0)
        self.side_id = self.side_canvas.create_image(0, 0, anchor='nw')
        self.side_canvas.pack()
        self.guide_note.add(self.side_frame, text='Side view')
        
        name = self.guide_note.tab(self.guide_note.select(), 'text')
        if name == 'Guide':
            self.guide_mode = 'guide'
        else:
            self.guide_mode = 'sideview'
        
        # Main
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.top = ttk.Frame(self.main_frame)
        self.top.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)
        
        self.buttons = ttk.Frame(self.top)
        self.buttons.pack(side=tk.LEFT, padx=5, pady=5)
        self.c_button = ttk.Button(self.buttons, image=self.c_image)
        self.c_button.grid(column=0, row=0)
        self.p_button = ttk.Button(self.buttons, image=self.p_image)
        self.p_button.grid(column=1, row=0)
        self.s_button = ttk.Button(self.buttons, image=self.s_image)
        self.s_button.grid(column=2, row=0)
        
        self.display = ttk.LabelFrame(self.top, text='Display')
        self.display.pack(side=tk.RIGHT, ipady=3)
        
        ttk.Label(self.display, text='Zoom [%]').grid(column=0, row=0, padx=5, sticky=tk.W)
        self.e_button = ttk.Button(self.display, width=4, image=self.e_image)
        self.e_button.grid(column=1, row=0, sticky=tk.W)
        self.zm_values = [  10,  13,  16,  20,  25,  32,  40,  50,  63,  79,
                           100, 126, 158, 200, 251, 316, 398, 501, 631, 794,
                          1000,1259,1585,1995]
        self.combo_zm = ttk.Combobox(self.display, values=self.zm_values, width=12, textvariable=self.zoom)
        self.combo_zm.grid(column=0, row=1, columnspan=2, padx=5, sticky=tk.W)
        ttk.Label(self.display, text='Thickness [px]').grid(column=2, row=0, padx=5, sticky=tk.W)
        values = [1,2,3,4,5,7,10,15,20,25,30,40,50,70,100,150,200,250,300,400,500,700,1000]
        self.combo_th = ttk.Combobox(self.display, values=values, width=12, textvariable=self.thickness)
        self.combo_th.grid(column=2, row=1, padx=5, sticky=tk.W)
        self.chk_a = ttk.Checkbutton(self.display, variable=self.a_on, text='Axes (A)')
        self.chk_a.grid(column=3, row=0, padx=5, sticky=tk.W)
        self.chk_b = ttk.Checkbutton(self.display, variable=self.b_on, text='Scale bar (B)')
        self.chk_b.grid(column=3, row=1, padx=5, sticky=tk.W)
        self.chk_p = ttk.Checkbutton(self.display, variable=self.p_on, text='Points')
        self.chk_p.grid(column=4, row=0, padx=5, sticky=tk.W)
        self.chk_g = ttk.Checkbutton(self.display, variable=self.g_on, text='Guide (G)')
        self.chk_g.grid(column=4, row=1, padx=5, sticky=tk.W)
        self.rad_b = ttk.Radiobutton(self.display, text='Black', value=False, 
                                     variable=self.white)
        self.rad_b.grid(column=5, row=0, padx=5, sticky=tk.W)
        self.rad_w = ttk.Radiobutton(self.display, text='White', value=True, 
                                     variable=self.white)
        self.rad_w.grid(column=5, row=1, padx=5, sticky=tk.W)
        
        self.bottom = ttk.Frame(self.main_frame)
        self.bottom.pack(side=tk.BOTTOM, anchor=tk.S,  fill=tk.X, expand=True)
        
        self.bar_text = tk.StringVar()
        self.bar_text.set('Scale bar: None μm')
        self.bar_button = ttk.Button(self.bottom, textvariable=self.bar_text)
        self.bar_button.pack(side=tk.RIGHT, anchor=tk.N, padx=5, pady=5)
        
        self.coor_text = tk.StringVar()
        self.coor_text.set('[x,y,z] =\n    vals =')
        self.coor_info = ttk.Label(self.bottom, textvariable=self.coor_text, width=30)
        self.coor_info.pack(side=tk.LEFT, anchor=tk.N, padx=5, pady=5)
        
        self.scale_frame = ttk.Frame(self.bottom)
        self.scale_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.scale = tk.Scale(self.scale_frame, length=2000, variable=self.depth,
                              orient='horizontal', showvalue=False)
        self.scale.pack(side=tk.LEFT)
        
        self.sec_frame = ttk.Frame(self.main_frame)
        self.sec_frame.pack(padx=2, pady=3)
        self.sec_cf = ttk.Frame(self.sec_frame)
        self.sec_canvas = tk.Canvas(self.sec_cf, width=2000, height=2000)
        self.barx = tk.Scrollbar(self.sec_frame, orient=tk.HORIZONTAL)
        self.barx.pack(side=tk.BOTTOM, fill=tk.X)
        self.barx.config(command=self.sec_canvas.xview)
        self.bary = tk.Scrollbar(self.sec_frame, orient=tk.VERTICAL)
        self.bary.pack(side=tk.RIGHT, fill=tk.Y)
        self.bary.config(command=self.sec_canvas.yview)
        self.sec_canvas.config(xscrollcommand=self.barx.set)
        self.sec_canvas.config(yscrollcommand=self.bary.set)
        self.sec_canvas.config(scrollregion=(0,0,0,0))
        
        self.sec_canvas.pack(side=tk.LEFT, anchor=tk.NW)
        self.sec_cf.pack(side=tk.LEFT)
        
        if pf == 'Windows':
            self.master.state('zoomed')
        fill = '#ffffff' if self.white.get() else '#000000'
        self.sec_back = self.sec_canvas.create_rectangle(0, 0, 0, 0, fill=fill, width=0)
        self.sec_id = self.sec_canvas.create_image(0, 0, anchor='nw')
        if self.g_on.get():
            self.master.minsize(850, 400)
        else:
            self.master.minsize(400, 400)
            

    def create_commands(self):
        Hub = self.Hub
        
        self.menu_bar = tk.Menu(self.master)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label='Open',
                                   command=lambda: self.SV.open_new(self.master),
                                   accelerator='Ctrl+O')
        self.file_menu.add_command(label='Reload',
                                   command=lambda: Hub.reload(),
                                   accelerator='Ctrl+R')
        self.file_menu.add_command(label='Save', 
                                   command=lambda: Hub.save(Hub.secv_name), 
                                   accelerator='Ctrl+S')
        self.file_menu.add_command(label='Save As',
                                   command=lambda: Hub.save(), 
                                   accelerator='Ctrl+Shift+S')
        self.file_menu.add_command(label='Export', 
                                   command=Hub.export, 
                                   accelerator='Ctrl+E')
        
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label='Undo', 
                                   command=Hub.undo, 
                                   accelerator='Ctrl+Z')
        self.edit_menu.add_command(label='Redo', 
                                   command=Hub.redo, 
                                   accelerator='Ctrl+Y')
        
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label='Channels', 
                                       command=Hub.channels.settings,
                                       accelerator='C')
        self.settings_menu.add_command(label='Points', 
                                       command=Hub.points.settings,
                                       accelerator='P')
        self.settings_menu.add_command(label='Scale bar', 
                                       command=Hub.geometry.set_bar_length)
        self.settings_menu.add_command(label='Details', 
                                       command=Hub.geometry.details)
        
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tools_menu.add_command(label='Snapshots', command=Hub.snapshots.settings,
                                    accelerator='S')
        self.tools_menu.add_command(label='Stack', command=Hub.stack.settings)
        
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        self.menu_bar.add_cascade(label='Edit', menu=self.edit_menu)
        self.menu_bar.add_cascade(label='Settings', menu=self.settings_menu)
        self.menu_bar.add_cascade(label='Tools', menu=self.tools_menu)
        
        self.master.config(menu=self.menu_bar)
        
        if len(Hub.history) == 1:
            self.edit_menu.entryconfig('Undo', state='disable')
        if Hub.hidx == -1:
            self.edit_menu.entryconfig('Redo', state='disable')
            
        self.guide_canvas.bind('<Button-1>', lambda event: [self.master.focus_set(),
                                                            Hub.points.settings(select=self.p_num)])
        self.guide_canvas.bind('<Motion>', self.track_guide)
        if pf == 'Windows':
            self.guide_canvas.bind('<MouseWheel>', lambda event: 
                                   self.guide_canvas.\
                                   yview_scroll(int(-event.delta/120), 'units'))
        elif pf == 'Linux':
            self.guide_canvas.bind('<Button-4>', lambda event: 
                                   self.guide_canvas.yview_scroll(1, 'units'))
            self.guide_canvas.bind('<Button-4>', lambda event: 
                               self.guide_canvas.yview_scroll(1, 'units'))
        self.guide_im = ImageTk.PhotoImage(Image.fromarray(self.guide[:,:,::-1]))
        self.guide_canvas.itemconfig(self.guide_id, image=self.guide_im)
        self.side_im = ImageTk.PhotoImage(Image.fromarray(np.append(self.side[:,:,2::-1], 
                                                                    self.side[:,:,3:], axis=2)))
        self.side_canvas.itemconfig(self.side_id, image=self.side_im)
        self.guide_note.bind('<<NotebookTabChanged>>', self.guide_note_changed)
        
        self.buttons.bind('<Button-1>', lambda event: self.master.focus_set())
        self.c_button.configure(command=Hub.channels.settings)
        self.p_button.configure(command=Hub.points.settings)
        self.s_button.configure(command=Hub.snapshots.settings)
        
        self.e_button.configure(command=self.fit_frame)
        self.combo_zm.bind('<Return>', lambda event: self.zm_enter())
        self.combo_zm.bind('<FocusOut>', lambda event: self.zm_enter())
        self.combo_zm.bind('<<ComboboxSelected>>', lambda event: self.zm_enter())
        self.combo_th.bind('<Return>', lambda event: self.th_enter())
        self.combo_th.bind('<FocusOut>', lambda event: self.th_enter())
        self.combo_th.bind('<<ComboboxSelected>>', lambda event: self.th_enter())
        self.chk_a.configure(command=self.a_switch)
        self.chk_b.configure(command=self.b_switch)
        self.chk_p.configure(command=lambda: [Hub.put_points(), Hub.calc_guide()])
        self.chk_g.configure(command=self.g_switch)
        self.rad_b.configure(command=self.wb_switch)
        self.rad_w.configure(command=self.wb_switch)
        
        self.bar_text.set('Scale bar: {0} μm'.format(Hub.geometry['bar_len']))
        self.bar_button.configure(command=Hub.geometry.set_bar_length)
        if Hub.geometry['bar_len'] == None:
            self.bar_button.configure(state=tk.DISABLED)
        self.scale.configure(command=Hub.position.scale)
        self.scale.configure(to=self.scale_to)
        self.scale.bind('<Button-1>', Hub.position.scale_clicked)
        self.scale.bind('<ButtonRelease-1>', Hub.position.scale_released)
        self.scale_frame.bind('<Configure>', self.scale_configure)
        
        self.sec_canvas.bind('<Motion>', self.track_sec)
        self.sec_canvas.bind('<Button-1>', self.click_sec)
        self.sec_canvas.bind('<ButtonRelease-1>', self.release_sec)
        if pf == 'Windows':
            self.sec_canvas.bind('<MouseWheel>', lambda event: 
                                     self.sec_canvas.\
                                         yview_scroll(int(-event.delta/120), 'units'))
            self.sec_canvas.bind('<Shift-MouseWheel>', lambda event: 
                                     self.sec_canvas.\
                                         xview_scroll(int(-event.delta/120), 'units'))
            self.sec_canvas.bind('<Control-MouseWheel>', 
                                 lambda event: self.zm_scroll(event, int(event.delta/120)))
        elif pf == 'Linux':
            self.sec_canvas.bind('<Button-4>', lambda event: 
                                     self.sec_canvas.yview_scroll(1, 'units'))
            self.sec_canvas.bind('<Button-5>', lambda event: 
                                     self.sec_canvas.yview_scroll(-1, 'units'))
            self.sec_canvas.bind('<Shift-Button-4>', lambda event: 
                                     self.sec_canvas.xview_scroll(1, 'units'))
            self.sec_canvas.bind('<Shift-Button-5>', lambda event: 
                                     self.sec_canvas.xview_scroll(-1, 'units'))
            self.sec_canvas.bind('<Control-Button-4>', 
                                 lambda event: self.zm_scroll(event, -1))
            self.sec_canvas.bind('<Control-Button-5>', 
                                 lambda event: self.zm_scroll(event, 1))
        self.sec_canvas.config(yscrollcommand=self.bary_set)
        self.sec_canvas.config(xscrollcommand=self.barx_set)
        
        self.sec_cf.bind('<Configure>', self.sec_configure)
        
        self.master.bind('<Key>', self.key)
        self.master.bind('<KeyRelease>', Hub.position.key_release)
        
        
    def key(self, event):
        if self.master.focus_get()==self.combo_zm:
            return
        if self.master.focus_get()==self.combo_th:
            return
        key = event.keysym
        if event.state//self.flags[1]%2 == 1:
            if key == 'o':
                self.SV.open_new(self.master)
            elif key == 'r':
                self.Hub.reload()
            elif key == 's':
                self.Hub.save(self.Hub.secv_name)
            elif key == 'S':
                self.Hub.save()
            elif key == 'e':
                self.Hub.export()
            elif key == 'z':
                self.Hub.undo()
            elif key == 'y':
                self.Hub.redo()
            else:
                self.Hub.position.key_pressed(key, 2)
        else:
            if key in ['a', 'b', 'g']:
                getattr(self, 'chk_{0}'.format(key)).invoke()
            elif key in ['c', 'p', 's']:
                getattr(self, '{0}_button'.format(key)).invoke()
            elif key == 'Delete':
                self.Hub.points.del_pt(x=[self.p_num])
            elif event.state//self.flags[0]%2 == 1:
                self.Hub.position.key_pressed(key.lower(), 1)
            else:
                self.Hub.position.key_pressed(key.lower(), 0)
        
    
    def on_close(self, reboot=False):
        secv_name = self.Hub.secv_name
        if self.Hub.hidx == self.Hub.hidx_saved:
            self.master.destroy()
            del self.Hub
            close = False if reboot else True
            for w in self.SV.wins:
                close = close and not bool(w.winfo_exists())
            if close:
                self.SV.root.destroy()
            if reboot:
                self.SV.open_new(self.SV.root, secv_name)
        else:
            ans = messagebox.askyesnocancel(title='Closing', 
                                            message='Do you want to save '
                                                    'changes before you quit?',
                                            parent=self.master)
            if ans == None:
                return
            if ans:
                if self.Hub.save(secv_name):
                    self.master.destroy()
                del self.Hub
                close = False if reboot else True
                for w in self.SV.wins:
                    close = close and not bool(w.winfo_exists())
                if close:
                    self.SV.root.destroy()
                if reboot:
                    self.SV.open_new(self.SV.root, secv_name)
            else:
                self.master.destroy()
                del self.Hub
                close = False if reboot else True
                for w in self.SV.wins:
                    close = close and not bool(w.winfo_exists())
                if close:
                    self.SV.root.destroy()
                if reboot:
                    self.SV.open_new(self.SV.root, secv_name)
                    
    
    def zm_enter(self):
        if not self.lock:
            self.lock = True
            self.master.after(1, self.zm_enter_)
    
    def zm_scroll(self, event, delta):
        if not self.lock:
            self.lock = True
            x, y = event.x, event.y
            w, h = self.sec_cf.winfo_width()-4, self.sec_cf.winfo_height()-4
            fix = (x/w, y/h)
            a = int(np.argmin((np.array(self.zm_values)-float(self.zoom.get()))**2))
            a = min(max(a + delta, 0), len(self.zm_values)-1)
            zoom = self.zm_values[a]
            self.zoom.set(str(zoom))
            self.master.after(1, self.zm_enter_, (fix))
        
    
    def zm_enter_(self, fix=(0.5,0.5)):
        def unlock():
            self.lock = False
            
        try:
            if self.master.focus_get() == self.combo_zm:
                self.master.focus_set()
        except: pass
        try: zoom = int(self.zoom.get())/100
        except: 
            zoom = self.Hub.zoom
            self.zoom.set(str(int(zoom*100)))
        if zoom < self.zm_values[0]/100:
            zoom = self.zm_values[0]/100
            self.zoom.set(str(int(zoom*100)))
        elif zoom > self.zm_values[-1]/100:
            zoom = self.zm_values[-1]/100
            self.zoom.set(str(int(zoom*100)))
        
        vx0, vx1 = self.barx.get()
        vy0, vy1 = self.bary.get()
        
        w, h = self.sec_cf.winfo_width()-4, self.sec_cf.winfo_height()-4
        iw, ih = self.Hub.geometry['im_size']
        iw0, ih0 = int(iw*self.Hub.zoom), int(ih*self.Hub.zoom)
        iw, ih = int(iw*zoom), int(ih*zoom)
        x, y = w//2 - iw//2, h//2 - ih//2
        self.imx, self.imy = x, y
        
        sr0 = (x-w+50,y-h+50,x+iw0+w-50,y+ih0+h-50)
        sr = (x-w+50,y-h+50,x+iw+w-50,y+ih+h-50)
        
        fix_abs = [fix[0]*(vx1-vx0) + vx0, fix[1]*(vy1-vy0) + vy0]
        a1, a2 = iw/(sr[2]-sr[0])/iw0*(sr0[2]-sr0[0]), ih/(sr[3]-sr[1])/ih0*(sr0[3]-sr0[1])
        fix_abs[0] = (fix_abs[0] - 0.5)*a1 + 0.5
        fix_abs[1] = (fix_abs[1] - 0.5)*a2 + 0.5
        
        lx = w/(sr[2]-sr[0])
        ly = h/(sr[3]-sr[1])
        vx = (fix_abs[0] - fix[0]*lx, fix_abs[0] - fix[0]*lx + lx)
        vy = (fix_abs[1] - fix[1]*ly, fix_abs[1] - fix[1]*ly + ly)
        if vx[0] < 0:
            vx = (0, vx[1]-vx[0])
        if vx[1] > 1:
            vx = (max(vx[0]-vx[1]+1, 0), 1)
        if vy[0] < 0:
            vy = (0, vy[1]-vy[0])
        if vy[1] > 1:
            vy = (max(vy[0]-vy[1]+1, 0), 1)
        
        self.Hub.zoom = zoom
        
        u1 = int(vx[0]*(sr[2]-sr[0]) + sr[0] - x)
        u2 = int(vy[0]*(sr[3]-sr[1]) + sr[1] - y)
        self.upperleft = (u1, u2)
        x, y, iw, ih, w, h = self.Hub.put_axes_bar()
        self.Hub.scroll_config(x, y, iw, ih, w, h, vx0=vx[0], vy0=vy[0])
        self.Hub.calc_guide()
        self.master.after(10, unlock)
    
    def th_enter(self):
        try:
            if self.master.focus_get() == self.combo_th:
                self.master.focus_set()
        except: pass
        try: thickness = int(self.thickness.get())
        except: 
            thickness = self.Hub.thickness
            self.thickness.set(str(thickness))
        if thickness < 1:
            thickness = 1
            self.thickness.set(str(thickness))
        elif thickness > 1000:
            thickness = 1000
            self.thickness.set(str(thickness))
        if thickness == self.Hub.thickness:
            return None
        self.Hub.thickness = thickness
        self.Hub.calc_frame()
    
    def a_switch(self):
        self.Hub.put_axes_bar()
        
    def b_switch(self):
        self.Hub.put_axes_bar()
    
    def g_switch(self):
        if self.g_on.get():
            if self.guide_mode == 'guide':
                self.Hub.calc_guide()
            else:
                self.Hub.calc_sideview()
            self.main_frame.pack_forget()
            self.guide_note.pack(pady=10, padx=10, side=tk.RIGHT)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            self.master.minsize(850, 400)
        else:
            self.guide_note.pack_forget()
            self.master.minsize(400, 400)
            
    def wb_switch(self):
        self.Hub.calc_image()
        if self.g_on.get():
            self.Hub.calc_sideview()
        
    
    def scale_configure(self, event):
        w = self.scale_frame.winfo_width() - 70
        self.scale.config(length = w)
    
    def sec_configure(self, event):
        w, h = self.sec_cf.winfo_width()-4, self.sec_cf.winfo_height()-4
        iw, ih = self.Hub.geometry['im_size']
        if not hasattr(self.Hub, 'zoom'):
            zoom = min((w-10)/iw, (h-10)/ih)
            self.zoom.set(str(int(zoom*100)))
            self.Hub.zoom = float(self.zoom.get())/100
            zoom = self.Hub.zoom
            iw1, ih1 = int(iw*zoom), int(ih*zoom)
            self.upperleft = (int(iw1//2-w//2), int(ih1//2-h//2))
        if self.first:
            self.first = False
            if not isinstance(self.Hub.secv_name, type(None)):
                self.Hub.save(self.Hub.secv_name)
            
            self.Hub.calc_geometry()
            self.Hub.calc_guide()
        
        zoom = self.Hub.zoom
        iw, ih = int(iw*zoom), int(ih*zoom)
        x0, y0 = self.upperleft
        x, y = w//2 - iw//2, h//2 - ih//2
        self.sec_canvas.coords(self.sec_id, x+x0, y+y0)
        self.sec_canvas.coords(self.sec_back, x, y, x+iw, y+ih)
        self.sec_canvas.config(scrollregion=(x-w+50,y-h+50,x+iw+w-50,y+ih+h-50))
        self.imx, self.imy = x, y
        
    
    def fit_frame(self):
        w, h = self.sec_cf.winfo_width()-4, self.sec_cf.winfo_height()-4
        iw, ih = self.Hub.geometry['im_size']
        zoom = min((w-10)/iw, (h-10)/ih)
        iw1, ih1 = int(iw*zoom), int(ih*zoom)
        ul = (int(iw1//2-w//2), int(ih1//2-h//2))
        zs = str(int(zoom*100))
        if zs != self.zoom.get():
            self.zoom.set(zs)
            self.Hub.zoom = float(self.zoom.get())/100
            self.upperleft = ul
        else:
            self.zoom.set('100')
            self.Hub.zoom = 1.0
            self.upperleft = (int(iw//2-w//2), int(ih//2-h//2))
        x, y, iw, ih, w, h = self.Hub.put_axes_bar()
        self.Hub.scroll_config(x, y, iw, ih, w, h)
        self.Hub.calc_guide()
        
    
    def bary_set(self, v1, v2):
        self.bary.set(v1, v2)
        if not hasattr(self.Hub, 'zoom'):
            return
        self.master.after(1, self.move_upperleft)
    def barx_set(self, v1, v2):
        self.barx.set(v1, v2)
        if not hasattr(self.Hub, 'zoom'):
            return
        self.master.after(1, self.move_upperleft)
        
    def move_upperleft(self):
        vy, vx = self.bary.get(), self.barx.get()
        w, h = self.sec_cf.winfo_width()-4, self.sec_cf.winfo_height()-4
        zoom = self.Hub.zoom
        iw, ih = self.Hub.geometry['im_size']
        iw, ih = int(iw*zoom), int(ih*zoom)
        u1 = int(vx[0]*(2*w+iw-100) - w + 50)
        u2 = int(vy[0]*(2*h+ih-100) - h + 50)
        upperleft = (u1, u2)
        if upperleft != self.upperleft:
            self.upperleft = upperleft
            self.Hub.put_axes_bar()
            self.Hub.calc_guide()
    
        
    def click_sec(self, event):
        self.master.focus_set()
        
        x, y = self.sec_canvas.canvasx(event.x), self.sec_canvas.canvasy(event.y)
        x, y = x - self.imx, y - self.imy
        zoom = self.Hub.zoom
        a, b = self.Hub.geometry['im_size']
        a, b = int(a*zoom), int(b*zoom)
        if x > a or y > b or x < 0 or y < 0:
            return None
        self.click = np.array([x, y], np.float)/self.Hub.zoom
        state = event.state//self.flags[:3]%2
        if state.any():
            self.mode = np.where(state)[0][0] + 1
            if self.mode > 3:
                self.mode = 0
        else:
            self.mode = 0
        self.click_time = time.time()
        
        
    def release_sec(self, event):
        self.sec_canvas.bind('<Motion>', self.track_sec)
        if (self.shift != 0).any():
            pos = self.Hub.position.asarray()
            pos[0] -= (self.shift[0]*pos[2] + self.shift[1]*pos[1])/self.Hub.geometry['exp_rate']
            self.Hub.position.new(pos, 0)
            self.shift = np.array([0.,0.])
        elif  self.angle != 0:
            pos = self.Hub.position.asarray()
            ny, nx = pos.copy()[1:]
            pos[1] =  np.sin(self.angle)*nx + np.cos(self.angle)*ny
            pos[2] =  np.cos(self.angle)*nx - np.sin(self.angle)*ny
            self.Hub.position.new(pos, 0)
            self.angle = 0
        elif self.expand != 1:
            self.Hub.geometry.new(['exp_rate'], [self.expand*self.Hub.geometry['exp_rate']])
            self.expand = 1.
        elif (self.trim != 0).any():
            im_size = np.array(list(self.Hub.geometry['im_size']))
            im_size += self.trim
            self.Hub.geometry.new(['im_size'], [tuple(im_size)])
            self.trim[:] = 0
        elif time.time() - self.click_time < 0.5:
            if self.mode == 1:
                self.Hub.position.clicked(self.click)
            elif self.mode == 2:
                self.Hub.points.clicked(self.click)
            elif self.mode == 0:
                self.Hub.points.settings(select=self.p_num)
        self.click = None
        
    
    def track_sec(self, event):
        self.sec_canvas.unbind('<Motion>')
        self.master.after(1, self.track_sec_, (event))
    
        
    def track_sec_(self, event):
        
        def motion_bind():
            self.sec_canvas.bind('<Motion>', self.track_sec)
        
        x, y = self.sec_canvas.canvasx(event.x), self.sec_canvas.canvasy(event.y)
        x, y = x - self.imx, y - self.imy
        zoom = self.Hub.zoom
        x, y = x/zoom, y/zoom
        la, lb = self.Hub.geometry['im_size']
        iw, ih = len(self.section[0]), len(self.section)
        op, ny, nx = self.Hub.position.asarray()
        if (event.state//self.flags[3])%2 == 0:
            dc, dz, dy, dx = self.Hub.box.shape
            v = np.array([x, y], np.float) - np.array([la//2, lb//2])
            p = op + ny*v[1]/self.Hub.geometry['exp_rate'] + nx*v[0]/self.Hub.geometry['exp_rate']
            p[0] /= self.Hub.ratio
            p += np.array([dz//2, dy//2, dx//2])
            sort = np.argsort(self.Hub.channels.getnames())
            xi, yi = int(x), int(y)
            if 0 <= xi < len(self.Hub.frame[0,0]) and 0 <= yi < len(self.Hub.frame[0]):
                vals = self.Hub.frame[:,yi,xi]
            else:
                vals = np.zeros(len(self.Hub.frame))
            vals = str(np.round(vals).astype(np.int)[sort][self.Hub.ch_show[sort]])
            p = str(np.round(p).astype(np.int)[::-1])
            self.coor_text.set('[x,y,z] = {0}\n    vals = {1}'.format(p, vals))
            if len(self.Hub.sec_points) != 0:
        
                dists = np.linalg.norm(self.Hub.sec_points[:,:2] - np.array([y,x]), axis=1)
                nearest = np.argmin(dists)
    
                if dists[nearest] <= 3:
                    num = int(self.Hub.sec_points[nearest,2])
                    self.p_num = num
                    color = np.array(self.Hub.points.getcolors()[num] + [255])
                    point = self.Hub.sec_points[nearest, :2]
                    r = 4
                    l = np.arange(-2*r,2*r+1)
                    l = (l[None]**2 + l[:,None]**2)**0.5
                    s = l - r + 1
                    s[s<0] = 0
                    s[s>1] = 1
                    l -= r + 0.2
                    l[l<0] = 0
                    l[l>1] = 1
                    s = 1 - s
                    
                    a, b = point.astype(np.int)
                    square = self.section[max(a-2*r,0):a+2*r+1, max(b-2*r,0):b+2*r+1]
                    square_ = square.copy()
                    a0, b0 = a - max(a-2*r,0), b - max(b-2*r,0)
                    l1, s1 = l[max(2*r-a0,0):, max(2*r-b0,0):], s[max(2*r-a0,0):, max(2*r-b0,0):]
                    l1, s1 = l1[:len(square), :len(square[0])], s1[:len(square), :len(square[0])]
                    square2 = color[None,None]*s1[:,:,None]
                    square2[:,:,3] = 255
                    square[:] = square*l1[:,:,None] + square2*(1-l1[:,:,None])
                    self.Hub.put_axes_bar()
                    square[:] = square_
                else:
                    self.Hub.put_axes_bar()
                    self.p_num = -1
            else: self.p_num = -1
        
        elif isinstance(self.click, type(None)):
            pass
        elif self.mode == 0:
            self.shift = np.array([x, y], np.float)
            self.shift -= self.click
            if event.state//self.flags[1]%2 == 1:
                self.shift[np.argmin(np.abs(self.shift))] = 0
            pos = self.Hub.position.asarray()
            pos_ = pos.copy()
            pos[0] -= (self.shift[0]*nx + self.shift[1]*ny)/self.Hub.geometry['exp_rate']
            self.Hub.position.pos = pos.tolist()
            sec_raw = self.Hub.sec_raw
            M = np.float32([[1,0,self.shift[0]],[0,1,self.shift[1]]])
            self.Hub.sec_raw = cv2.warpAffine(sec_raw, M, (la, lb))
            self.Hub.put_points()
            if self.g_on.get():
                if self.guide_mode == 'guide':
                    self.Hub.calc_guide()
                else:
                    self.Hub.calc_sideview()
            self.Hub.position.pos = pos_.tolist()
            self.Hub.sec_raw = sec_raw
            
        elif self.mode == 1:
            v0 = self.click - np.array([la//2, lb//2])
            v = np.array([x, y], np.float) - np.array([la//2, lb//2])
            self.angle = np.angle((v[0] + 1j*v[1])/(v0[0] + 1j*v0[1]))
            if event.state//self.flags[1]%2 == 1:
                self.angle = round(self.angle/np.pi*12)*np.pi/12
            pos = self.Hub.position.asarray()
            pos_ = pos.copy()
            pos[1] =  np.sin(self.angle)*nx + np.cos(self.angle)*ny
            pos[2] =  np.cos(self.angle)*nx - np.sin(self.angle)*ny
            self.Hub.position.pos = pos.tolist()
            sec_raw = self.Hub.sec_raw
            M = cv2.getRotationMatrix2D((float(la//2), float(lb//2)), -self.angle/np.pi*180, 1)
            self.Hub.sec_raw = cv2.warpAffine(sec_raw, M, (la, lb))
            self.Hub.put_points()
            if self.g_on.get():
                if self.guide_mode == 'guide':
                    self.Hub.calc_guide()
                else:
                    self.Hub.calc_sideview()
            self.Hub.position.pos = pos_.tolist()
            self.Hub.sec_raw = sec_raw
            
        elif self.mode == 2:
            v0 = self.click - np.array([la//2, lb//2])
            v = np.array([x, y], np.float) - np.array([la//2, lb//2])
            self.expand = np.linalg.norm(v)/np.linalg.norm(v0)
            
            exp_rate = self.Hub.geometry['exp_rate']
            self.Hub.geometry.geo['exp_rate'] *= self.expand
            sec_raw = self.Hub.sec_raw
            M = cv2.getRotationMatrix2D((float(la//2), float(lb//2)), 0, self.expand)
            self.Hub.sec_raw = cv2.warpAffine(sec_raw, M, (la, lb))
            self.Hub.put_points()
            if self.g_on.get():
                if self.guide_mode == 'guide':
                    self.Hub.calc_guide()
                else:
                    self.Hub.calc_sideview()
            self.Hub.geometry.geo['exp_rate'] = exp_rate
            self.Hub.sec_raw = sec_raw
        
        elif self.mode == 3:
            r = self.click - np.array([la//2, lb//2])
            fr = np.abs(r) > np.array([la//8, lb//8])
            if fr.any():
                self.trim = np.array(list(self.Hub.geometry['im_size']))
                if fr.all():
                    self.trim = self.trim*np.array([x-iw//2,y-ih//2])/r
                elif fr[0]:
                    self.trim[0] *= (x - iw//2)/r[0]
                elif fr[1]:
                    self.trim[1] *= (y - ih//2)/r[1]
                     
                self.trim = self.trim.astype(np.int)
                self.trim[self.trim < 50] = 50
                
                im_size = self.Hub.geometry['im_size']
                self.Hub.geometry.geo['im_size'] = tuple(self.trim)
                
                zoom = self.Hub.zoom
                t0, t1 = (self.trim*zoom).astype(np.int)
                
                w, h = self.sec_cf.winfo_width()-4, self.sec_cf.winfo_height()-4
                iw, ih = int(iw*zoom), int(ih*zoom)
                im = self.sec_image.copy()
                u0, u1 = self.upperleft
                c0, c1  = iw//2 - u0, ih//2 - u1
                im[:max(c1-t1//2, 0),:,3] = 0
                im[c1+t1//2:,:,3] = 0
                im[:,:max(c0-t0//2, 0),3] = 0
                im[:,c0+t0//2:,3] = 0
                
                im = np.append(im[:,:,2::-1], im[:,:,3:], axis=2)
                self.sec_im = ImageTk.PhotoImage(Image.fromarray(im))
                
                self.upperleft = (u0+t0//2-iw//2, u1+t1//2-ih//2)
                
                x, y = w//2 - t0//2, h//2 - t1//2
                self.sec_canvas.coords(self.sec_back, x, y, x+t0, y+t1)
                self.sec_canvas.itemconfig(self.sec_id, image=self.sec_im)
                self.sec_canvas.itemconfig(self.sec_back, fill='#ffffff' if self.white.get() else '#000000')
                if self.g_on.get():
                    if self.guide_mode == 'guide':
                        self.Hub.calc_guide(rect=False)
                self.Hub.geometry.geo['im_size'] = im_size
                self.upperleft = (u0, u1)
                    
                self.trim -= np.array(list(im_size))
        
        self.master.after(10, motion_bind)
            
            
    def guide_note_changed(self, event):
        name = self.guide_note.tab(self.guide_note.select(), 'text')
        if name == 'Guide':
            self.Hub.calc_guide()
            self.guide_mode = 'guide'
        else:
            self.Hub.calc_sideview()
            self.guide_mode = 'sideview'
            
            
    def track_guide(self, event):
        points = self.Hub.guide_points.copy()
        x, y = self.guide_canvas.canvasx(event.x), self.guide_canvas.canvasy(event.y)
        
        if len(points) != 0:
        
            dists = np.linalg.norm(points[:,:2] - np.array([x,y]), axis=1)
            nearest = np.argmin(dists)

            if dists[nearest] <= 5:
                guide = self.guide.copy()
                color = np.array(self.Hub.points.getcolors()[nearest])
                name = self.Hub.points.getnames()[nearest]
                color = color//1.5
                color = (int(color[0]), int(color[1]), int(color[2]))
                p = points[nearest]
                guide = cv2.circle(guide, tuple(p[:2]), 4, (255,255,255), -1, lineType=cv2.LINE_AA)
                guide = cv2.circle(guide, tuple(p[:2]), 3, color, -1, lineType=cv2.LINE_AA)
                
                cv2.putText(guide, name, tuple(p[:2]+12), 2, 0.5, (255,255,255), 3, cv2.LINE_AA)
                cv2.putText(guide, name, tuple(p[:2]+12), 2, 0.5, color, 1, cv2.LINE_AA)
                
                self.guide_im = ImageTk.PhotoImage(Image.fromarray(guide[:,:,::-1]))
                self.guide_canvas.itemconfig(self.guide_id, image=self.guide_im)
                self.p_num = nearest
                
            else:
                self.guide_im = ImageTk.PhotoImage(Image.fromarray(self.guide[:,:,::-1]))
                self.guide_canvas.itemconfig(self.guide_id, image=self.guide_im)
                self.p_num = -1
        else:
            self.p_num = -1
            
            
    def ask_fps(self, path):
        self.fps_win = tk.Toplevel(self.master)
        self.fps_win.withdraw()
        if pf == 'Windows':
            self.fpt_win.iconbitmap(svp('img/icon.ico'))
        self.fps_win.title('mp4 settings')
        self.fps_win.geometry('250x90')
        self.fps_win.resizable(width=False, height=False)
        
        frame = ttk.Frame(self.fps_win)
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        frame1 = ttk.Frame(frame)
        frame1.pack(pady=5)
        
        fps = tk.StringVar(value='20.0')        
        entry = ttk.Entry(frame1, textvariable=fps, width=6, justify=tk.RIGHT)
        entry.pack(side=tk.LEFT)
        label = ttk.Label(frame1, text=' fps')
        label.pack(side=tk.LEFT)
        
        frame2 = ttk.Frame(frame)
        frame2.pack(pady=5)
        
        self.fps = None
        self.cancel = False
        
        def cancel():
            self.cancel = True
            self.fps_win.grab_release()
            self.fps_win.destroy()
        
        def ok():
            try:
                self.fps = float(fps.get())
                frame1.pack_forget()
                frame2.pack_forget()
            except:
                pass
            if self.fps != None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                f = float(self.fps)
                shape = (int(len(self.sec_image[0])), int(len(self.sec_image)))
                path0 = os.path.basename(path)
                
                if os.path.isfile(path0):
                    os.remove(path0)
                
                out = cv2.VideoWriter(path0, fourcc, f, shape, True)
                pb = ttk.Progressbar(frame, orient=tk.HORIZONTAL, value=0, length=100,
                                     maximum=self.scale_to, mode='determinate')
                pb.pack(fill=tk.X, pady=5)
                button = ttk.Button(frame, text='Cancel', command=cancel)
                button.pack(pady=5)
                button.focus_set()
                
                Hub = self.Hub
                pos0 = Hub.position.asarray()
                
                for i in range(self.scale_to+1):
                    pb.configure(value=i)
                    pb.update()
                    
                    pos = Hub.position.asarray()
                    op, ny, nx = pos
                    nz = -np.cross(ny, nx)
                    op[:] = Hub.scale_orient + i*nz
                    
                    Hub.position.pos = pos.tolist()
                    
                    if not Hub.calc_frame():
                        continue
                    if self.cancel:
                        break
                    
                    im = self.sec_image.copy()
                    a = im[:,:,3:]/255
                    im = im[:,:,:3]*a
                    if self.white.get():
                        im += 255*(1-a)
                    im = im.astype(np.uint8)
                    out.write(im)
                out.release()
                if os.path.isfile(path):
                    os.remove(path)
                shutil.move(path0, os.path.dirname(path))
                Hub.position.pos = pos0.tolist()
                Hub.calc_frame()
                self.fps_win.grab_release()
                self.fps_win.destroy()
                
        button1 = ttk.Button(frame2, text='Cancel', command=cancel)
        button1.pack(side=tk.LEFT)
        button2 = ttk.Button(frame2, text='OK', command=ok)
        button2.pack(side=tk.LEFT)
        
        self.fps_win.bind('<Escape>', lambda event: button1.invoke())
        def enter():
            try: self.fps_win.focus_get().invoke()
            except: button2.invoke()
        def down():
            try: 
                self.fps_win.focus_get().get()
                button2.focus_set()
            except: pass
        def left():
            try: self.fps_win.focus_get().get()
            except: button1.focus_set()
        def right():
            try: self.fps_win.focus_get().get()
            except: button2.focus_set()
        self.fps_win.bind('<Return>', lambda event: enter())
        self.fps_win.bind('<Destroy>', lambda event: cancel())
        self.fps_win.bind('<Up>', lambda event: entry.focus_set())
        self.fps_win.bind('<Down>', lambda event: down())
        self.fps_win.bind('<Left>', lambda event: left())
        self.fps_win.bind('<Right>', lambda event: right())
        
        self.fps_win.deiconify()
        self.entry = entry
        self.entry.focus_set()
        self.fps_win.grab_set()
            
    
    def ask_option(self, master, title, options, geometry=None):
        win = tk.Toplevel(master)
        win.withdraw()
        if pf == 'Windows':
            win.iconbitmap(svp('img/icon.ico'))
        win.title(title)
        if geometry != None:
            win.geometry(geometry)
        
        option = tk.IntVar(value=0)
        
        for i, opt in enumerate(options):
            tk.Radiobutton(win, variable=option, text=opt,
                           value=i).pack(anchor=tk.W, pady=5, padx=20)
        frame = ttk.Frame(win)
        frame.pack(pady=5, padx=5, side=tk.BOTTOM)
        def cancel():
            option.set(-1)
            win.grab_release()
            win.destroy()
        def ok():
            opt = option.get()
            win.grab_release()
            win.destroy()
            option.set(opt)
        ttk.Button(frame, text='Cancel', command=cancel).pack(side=tk.LEFT)
        ttk.Button(frame, text='OK', command=ok).pack(side=tk.LEFT)
        frame.bind('<Destroy>', lambda event: cancel())
        
        win.resizable(height=False, width=False)
        win.deiconify()
        win.grab_set()
        
        master.wait_window(win)
        return option.get()
    
    
        
