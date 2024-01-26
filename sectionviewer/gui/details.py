import os

import numpy as np
import tkinter as tk
from tkinter import ttk

from .gui import Base_GUI


class Details_GUI(Base_GUI):
    def __init__(self, main):
        super().__init__(main)
            
        self.main = main
        
        self.base_frame = tk.LabelFrame(main.master, text='Details', relief='raised',
                                         fg='blue', font=('arial', 13, 'bold'))
        self.details_id = main.dock_canvas.create_window(500, 0, anchor='nw',
                                                         window = self.base_frame)
        
        self.note = ttk.Notebook(self.base_frame)
        self.note.grid(row=0, column=0, columnspan=2, padx=15, pady=10)
        frame = ttk.Frame(self.note)
        self.note.add(frame, text='General')
        
        ttk.Label(frame, text='Data shape')\
            .grid(row=0, column=0, sticky=tk.NW, padx=15, pady=5)
        px_title = ttk.Frame(frame)
        px_title.grid(row=1, column=0, sticky=tk.NW, padx=15, pady=5)
        ttk.Label(frame, text='Expansion rate\n(1 = original)')\
            .grid(row=2, column=0, sticky=tk.NW, padx=15, pady=5)
        ttk.Label(frame, text='Image size')\
            .grid(row=3, column=0, sticky=tk.NW, padx=15, pady=5)
        
        ttk.Label(frame, text=': ').grid(row=0, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=1, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=2, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=3, column=1, sticky=tk.N, pady=5)
        text = '(x,y,z) = ({0}, {1}, {2})'.format(*main.files['shape'][::-1])
        ttk.Label(frame, text = text).grid(row=0, column=2, sticky=tk.NW, padx=10, pady=5)
        px_entries = ttk.Frame(frame)
        px_entries.grid(row=1, column=2, sticky=tk.NW, padx=10, pady=5)
        exp_frame = ttk.Frame(frame)
        exp_frame.grid(row=2, column=2, sticky=tk.NW, padx=10, pady=5)
        im_size_set = ttk.Frame(frame)
        im_size_set.grid(row=3, column=2, sticky=tk.NW, padx=10, pady=5)
        
        self.d_widgets = {}
        
        self.px_x = tk.StringVar()
        self.px_y = tk.StringVar()
        self.px_z = tk.StringVar()
        self.exp_rate = tk.StringVar()
        self.iw = tk.StringVar()
        self.ih = tk.StringVar()
        
        self.d_widgets['px_x'] = ttk.Entry(px_entries, textvariable=self.px_x, 
                                               width=8, justify=tk.RIGHT)
        self.d_widgets['px_x'].grid(row=0, column=0, sticky=tk.W, pady=2)
        self.d_widgets['px_y'] = ttk.Entry(px_entries, textvariable=self.px_y, 
                                               width=8, justify=tk.RIGHT)
        self.d_widgets['px_y'].grid(row=1, column=0, sticky=tk.W, pady=2)
        self.d_widgets['px_z'] = ttk.Entry(px_entries, textvariable=self.px_z, 
                                              width=8, justify=tk.RIGHT)
        self.d_widgets['px_z'].grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(px_entries, text='  μm/px  (x)').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(px_entries, text='  μm/px  (y)').grid(row=1, column=1, sticky=tk.W)
        ttk.Label(px_entries, text='  μm/px  (z)').grid(row=2, column=1, sticky=tk.W)
        
        keys = ['{0}_px_size_in_files'.format(w) for w in ['X', 'Y', 'Z']]
        def px_sizes_in_files():
            for k, var in zip(keys, [self.px_x, self.px_y, self.px_z]):
                if not main.files[k] is None:
                    var.set(str(main.files[k]))
        ttk.Label(px_title, text='Pixel sizes').grid(row=0, column=0, sticky=tk.NW)
        self.reset_px_button = ttk.Button(px_title, text = 'Reset values',
                                command = px_sizes_in_files)
        self.reset_px_button.grid(row=1, column=0, sticky=tk.NW)
        if np.array([main.files[k] is None for k in keys]).all():
            self.reset_px_button['state'] = tk.DISABLED
        
        self.d_widgets['exp'] = ttk.Entry(exp_frame, textvariable=self.exp_rate,
                                          width=8)
        self.d_widgets['exp'].grid(row=0, column=0, sticky=tk.W)
            
        ttk.Label(im_size_set, text='width = ').grid(row=0, column=0, sticky=tk.E)
        self.d_widgets['iw'] = ttk.Entry(im_size_set, textvariable=self.iw,
                                             width=5, justify=tk.RIGHT)
        self.d_widgets['iw'].grid(row=0, column=1)
        ttk.Label(im_size_set, text=' px').grid(row=0, column=2)
        ttk.Label(im_size_set, text='height = ').grid(row=1, column=0, sticky=tk.E)
        self.d_widgets['ih'] = ttk.Entry(im_size_set, textvariable=self.ih,
                                             width=5, justify=tk.RIGHT)
        self.d_widgets['ih'].grid(row=1, column=1)
        ttk.Label(im_size_set, text=' px').grid(row=1, column=2)
        
        frame = ttk.Frame(self.note)
        self.note.add(frame, text='Files / Channels')
        
        frame1 = ttk.Frame(frame)
        self.canvas = tk.Canvas(frame1, width=250, height=200, bg='#ffffff')
        barx = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        barx.pack(side=tk.BOTTOM, fill=tk.X)
        barx.config(command=self.canvas.xview)
        bary = tk.Scrollbar(frame, orient=tk.VERTICAL)
        bary.pack(side=tk.RIGHT, fill=tk.Y)
        bary.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=bary.set)
        self.canvas.config(xscrollcommand=barx.set)
        self.canvas.pack()
        frame1.pack()
        
        self.ch_frame = tk.Frame(frame1, bg='#ffffff')
        self.canvas.create_window(0,0, window=self.ch_frame, anchor='nw')
        
        frame = ttk.Frame(self.note)
        self.note.add(frame, text='Position')
        ttk.Label(frame, text='(px)').grid(row=0, column=0, pady=5, sticky=tk.E)
        ttk.Label(frame, text='Center').grid(row=0, column=2, sticky=tk.S)
        ttk.Label(frame, text='Vertical').grid(row=0, column=3, sticky=tk.S)
        ttk.Label(frame, text='Horizontal').grid(row=0, column=4, sticky=tk.S)
        ttk.Label(frame, text='X')\
            .grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)
        ttk.Label(frame, text='Y')\
            .grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        ttk.Label(frame, text='Z')\
            .grid(row=3, column=0, sticky=tk.NW, padx=5, pady=5)
        ttk.Label(frame, text=': ').grid(row=1, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=2, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=3, column=1, sticky=tk.N, pady=5)
        
        self.pos_v = [[0,0,0],[0,0,0],[0,0,0]]
        for i in range(3):
            for j in range(3):
                self.pos_v[j][2-i] = tk.StringVar()
                self.d_widgets[(i,j)] = ttk.Entry(frame, textvariable=self.pos_v[j][2-i], width=8)
                self.d_widgets[(i,j)].grid(row=i+1, column=j+2, padx=5, pady=5)
        
        def reset():
            pos = np.array([[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]])
            pos /= main.position._anisotropy
            pos[0] += np.array(main.files['shape'])//2
            for i in range(3):
                for j in range(3):
                    self.pos_v[i][j].set(str(pos[i,j]))
        self.reset_pos_button = ttk.Button(frame, text='Reset', command=reset)
        self.reset_pos_button.grid(row=4,column=3, pady=20)
        
        self.cancel_button = ttk.Button(self.base_frame, text='Cancel',
                                        command=self.cancel)
        self.cancel_button.grid(row=1, column=0, pady=10, sticky=tk.E)
            
        self.ok_button = ttk.Button(self.base_frame, text='OK', command=self.ok)
        self.ok_button.grid(row=1, column=1, pady=10, sticky=tk.W)
        
    def settings(self):
        main = self.main
        
        self.px_x.set(str(main.geometry['X_px_size']))
        self.px_y.set(str(main.geometry['Y_px_size']))
        self.px_z.set(str(main.geometry['Z_px_size']))
        self.exp_rate.set(str(main.geometry['expansion_rate']))
        iw, ih = main.geometry['image_size']
        self.iw.set(str(iw))
        self.ih.set(str(ih))
        pos = main.position
        for i in range(3):
            for j in range(3):
                self.pos_v[i][j].set(pos[i,j])
        
        for w in self.ch_frame.pack_slaves():
            w.pack_forget()
        paths = main.files['paths']
        ch_nums = main.files['channel_nums']
        names = np.array(main.channels.getnames())
        colors = np.array(main.channels.getcolors())
        colors = (colors/255*55 + 200).astype(int)
        n = 0
        for i, p in enumerate(paths):
            tk.Label(self.ch_frame, text='  '+os.path.basename(p), 
                      bg='#ffffff').pack(anchor=tk.W, pady=3)
            for j in range(n, n + ch_nums[i]):
                color = '#' + ''.join([hex(colors[j,c])[2:] for c in range(2,-1,-1)])
                tk.Label(self.ch_frame, text=' '+names[j]+' ', bg=color).\
                    pack(anchor=tk.W, padx=25)
            n += ch_nums[i]
            tk.Label(self.ch_frame, text='', bg='#ffffff').pack(anchor=tk.W)
        
        self.base_frame.update()
        self.canvas.config(scrollregion = (
            0, 0, 
            max(250, self.ch_frame.winfo_width()),
            max(150, self.ch_frame.winfo_height())
            ))
        
        self.note.focus_set()
        
        main.master.protocol('WM_DELETE_WINDOW', self.cancel)
        main.menu_bar.entryconfig('File', state='disabled')
        main.menu_bar.entryconfig('Edit', state='disabled')
        main.menu_bar.entryconfig('Settings', state='disabled')
        main.menu_bar.entryconfig('Tools', state='disabled')
        main.sbar_entry['state'] = tk.DISABLED
        main.combo_th['state'] = tk.DISABLED
        main.chk_a['state'] = tk.DISABLED
        main.chk_b['state'] = tk.DISABLED
        main.chk_d['state'] = tk.DISABLED
        main.chk_p['state'] = tk.DISABLED
        main.rad_b['state'] = tk.DISABLED
        main.rad_w['state'] = tk.DISABLED
        main.depth_scale['state'] = tk.DISABLED
        main.reset_button['state'] = tk.DISABLED
        main.master.unbind('<Key>')
        main.view_canvas.unbind('<Motion>')
        main.view_canvas.unbind('<Button-1>')
        main.view_canvas.unbind('<ButtonRelease-1>')
        main.dock_canvas.moveto(main.dock_id, 500, 0)
        main.dock_canvas.moveto(self.details_id, 0, 0)
        main.master.bind('<Return>', self.enter)
        main.master.bind('<Left>', self.left)
        main.master.bind('<Right>', self.right)
        main.master.bind('<Up>', self.up)
        main.master.bind('<Down>', self.down)
    
    def repair(self):
        main = self.main
        
        main.dock_canvas.moveto(self.details_id, 500, 0)
        main.dock_canvas.moveto(main.dock_id, 0, 0)
        main.master.unbind('<Return>')
        main.master.unbind('<Left>')
        main.master.unbind('<Right>')
        main.master.unbind('<Up>')
        main.master.unbind('<Down>')
        main.master.protocol('WM_DELETE_WINDOW', main.on_close)
        main.menu_bar.entryconfig('File', state='active')
        main.menu_bar.entryconfig('Edit', state='active')
        main.menu_bar.entryconfig('Settings', state='active')
        main.menu_bar.entryconfig('Tools', state='active')
        main.sbar_entry['state'] = tk.NORMAL
        main.combo_th['state'] = tk.NORMAL
        main.chk_a['state'] = tk.NORMAL
        main.chk_b['state'] = tk.NORMAL
        main.chk_d['state'] = tk.NORMAL
        main.chk_p['state'] = tk.NORMAL
        main.rad_b['state'] = tk.NORMAL
        main.rad_w['state'] = tk.NORMAL
        main.depth_scale['state'] = tk.NORMAL
        main.reset_button['state'] = tk.NORMAL
        main.master.bind('<Key>', main.key)
        main.view_canvas.bind('<Motion>', main.track_view)
        main.view_canvas.bind('<Button-1>', main.click_view)
        main.view_canvas.bind('<ButtonRelease-1>', main.release_view)
    
    def cancel(self):
        self.repair()
        
    def ok(self):
        main = self.main
        
        try:
            main.geometry['X_px_size'] = float(self.px_x.get())
        except Exception: 
            pass
        try:
            main.geometry['Y_px_size'] = float(self.px_y.get())
        except Exception: 
            pass
        try:
            main.geometry['Z_px_size'] = float(self.px_z.get())
        except Exception: 
            pass
        try: 
            main.geometry['expansion_rate'] = float(self.exp_rate.get())
        except Exception: 
            pass
        try:
            main.geometry['image_size'] = (int(self.iw.get()), int(self.ih.get()))
        except Exception: 
            pass
        try:
            new = np.zeros([3,3])
            for i in range(3):
                for j in range(3):
                    new[i,j] = float(self.pos_v[i][j].get())
            main.position[:] = new
        except Exception:
            pass
        self.repair()
        
    def left(self, *args):
        w = self.base_frame.focus_get()
        if w == self.ok_button:
            self.cancel_button.focus_set()
            
    def right(self, *args):
        w = self.base_frame.focus_get()
        if w == self.cancel_button:
            self.ok_button.focus_set()
            
    def up(self, *args):
        note = self.note
        w = self.base_frame.focus_get()
        if w in [self.cancel_button, self.ok_button]:
            if note.tab(note.select(), 'text') == 'General':
                self.d_widgets['ih'].focus_set()
            elif note.tab(note.select(), 'text') == 'Files / Channels':
                note.focus_set()
            elif note.tab(note.select(), 'text') == 'Position':
                self.reset_pos_button.focus_set()
        elif w == self.d_widgets['ih']:
            self.d_widgets['iw'].focus_set()
        elif w == self.d_widgets['iw']:
            self.d_widgets['exp'].focus_set()
        elif w == self.d_widgets['exp']:
            self.d_widgets['px_z'].focus_set()
        elif w == self.d_widgets['px_z']:
            self.d_widgets['px_y'].focus_set()
        elif w == self.d_widgets['px_y']:
            self.d_widgets['px_x'].focus_set()
        elif w == self.d_widgets['px_x']:
            if str(self.reset_px_button['state']) in [tk.ACTIVE, tk.NORMAL]:
                self.reset_px_button.focus_set()
            else:
                note.focus_set()
        elif w == self.reset_pos_button:
            self.d_widgets[(2,2)].focus_set()
        elif w == self.d_widgets[(2,2)]:
            self.d_widgets[(1,2)].focus_set()
        elif w == self.d_widgets[(1,2)]:
            self.d_widgets[(0,2)].focus_set()
        elif w == self.d_widgets[(0,2)]:
            self.d_widgets[(2,1)].focus_set()
        elif w == self.d_widgets[(2,1)]:
            self.d_widgets[(1,1)].focus_set()
        elif w == self.d_widgets[(1,1)]:
            self.d_widgets[(0,1)].focus_set()
        elif w == self.d_widgets[(0,1)]:
            self.d_widgets[(2,0)].focus_set()
        elif w == self.d_widgets[(2,0)]:
            self.d_widgets[(1,0)].focus_set()
        elif w == self.d_widgets[(1,0)]:
            self.d_widgets[(0,0)].focus_set()
        elif w in [self.d_widgets[(0,0)],
                   self.reset_px_button]:
            note.focus_set()
            
    def down(self, *args):
        note = self.note
        w = self.base_frame.focus_get()
        if w == self.reset_px_button:
            self.d_widgets['px_x'].focus_set()
        elif w == self.d_widgets['px_x']:
            self.d_widgets['px_y'].focus_set()
        elif w == self.d_widgets['px_y']:
            self.d_widgets['px_z'].focus_set()
        elif w == self.d_widgets['px_z']:
            self.d_widgets['exp'].focus_set()
        elif w == self.d_widgets['exp']:
            self.d_widgets['iw'].focus_set()
        elif w == self.d_widgets['iw']:
            self.d_widgets['ih'].focus_set()
        elif w == self.d_widgets['ih']:
            self.ok_button.focus_set()
        elif w == self.d_widgets[(0,0)]:
            self.d_widgets[(1,0)].focus_set()
        elif w == self.d_widgets[(1,0)]:
            self.d_widgets[(2,0)].focus_set()
        elif w == self.d_widgets[(2,0)]:
            self.d_widgets[(0,1)].focus_set()
        elif w == self.d_widgets[(0,1)]:
            self.d_widgets[(1,1)].focus_set()
        elif w == self.d_widgets[(1,1)]:
            self.d_widgets[(2,1)].focus_set()
        elif w == self.d_widgets[(2,1)]:
            self.d_widgets[(0,2)].focus_set()
        elif w == self.d_widgets[(0,2)]:
            self.d_widgets[(1,2)].focus_set()
        elif w == self.d_widgets[(1,2)]:
            self.d_widgets[(2,2)].focus_set()
        elif w == self.d_widgets[(2,2)]:
            self.reset_pos_button.focus_set()
        elif w == self.reset_pos_button:
            self.ok_button.focus_set()
        elif w == note:
            if note.tab(note.select(), 'text') == 'General':
                if str(self.reset_px_button['state']) in [tk.ACTIVE, tk.NORMAL]:
                    self.reset_px_button.focus_set()
                else:
                    self.d_widgets['px_x'].focus_set()
            elif note.tab(note.select(), 'text') == 'Files / Channels':
                self.ok_button.focus_set()
            elif note.tab(note.select(), 'text') == 'Position':
                self.d_widgets[(0,0)].focus_set()
            
    def enter(self, *args):
        w = self.base_frame.focus_get()
        if w not in [self.ok_button, self.cancel_button,
                     self.reset_px_button, self.reset_pos_button]:
            self.ok_button.focus_set()
        else:
            w.invoke()