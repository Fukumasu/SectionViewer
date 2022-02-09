import math
import os
import pickle
import platform

import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

pf = platform.system()

class Geometry:
    def __init__(self, Hub):
        self.Hub = Hub
        geo = Hub.geometry
        
        if not 'res_xy' in geo: geo['res_xy'] = None
        if not 'res_z' in geo: geo['res_z'] = None
        if geo['res_xy'] == None and 'xy_oib' in geo: geo['res_xy'] = geo['xy_oib']
        if geo['res_z'] == None and 'z_oib' in geo: geo['res_z'] = geo['z_oib']
        
        if None in (geo['res_xy'], geo['res_z']):
            if geo['res_xy'] != None:
                geo['res_z'] = geo['res_xy']
            else:
                geo['res_xy'] = geo['res_z']
        Hub.ratio = 1. if geo['res_xy'] == None else geo['res_z']/geo['res_xy']
        
        dc, dz, dy, dx = geo['shape']
        Hub.L = (dx**2 + dy**2 + (dz*Hub.ratio)**2)**0.5
                
        if not 'im_size' in geo: 
            geo['im_size'] = (dx,dy)
        if not 'exp_rate' in geo: geo['exp_rate'] = 1
        elif geo['exp_rate'] == 0: geo['exp_rate'] = 1
        if not 'bar_len' in geo: geo['bar_len'] = None
        
        if geo['res_xy'] != None:
            if geo['bar_len'] == None:
                a = geo['res_xy']/geo['exp_rate']
                geo['bar_len'] = round(80*a, -int(np.log10(80*a)))
            Hub.lpx = int(geo['bar_len']/geo['res_xy']*geo['exp_rate'])
        else: Hub.lpx = 0
        
        self.geo = geo
        
    
    def __getattr__(self, name):
        if name == 'val':
            return object.__getattribute__(self, 'geo')
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == 'val':
            object.__setattr__(self, 'geo', val)
        else:
            object.__setattr__(self, name, val)
    
    
    def __getitem__(self, x):
        return self.geo[x]
    def __setitem__(self, x, v):
        self.geo[x] = v
    
    
    def details(self):
        Hub = self.Hub
        gui = Hub.gui
        
        self.details_win = tk.LabelFrame(gui.master, text='Details', relief='raised',
                                       fg='blue', font=('arial', 13, 'bold'))
        self.details_id = gui.dock_canvas.create_window(500, 0, anchor='nw', window=self.details_win)
        
        note = ttk.Notebook(self.details_win)
        note.grid(row=0, column=0, columnspan=2, padx=15, pady=10)
        frame = ttk.Frame(note)
        note.add(frame, text='Frame')
        
        ttk.Label(frame, text='Data shape')\
            .grid(row=0, column=0, sticky=tk.NW, padx=15, pady=5)
        resol_title = ttk.Frame(frame)
        resol_title.grid(row=1, column=0, sticky=tk.NW, padx=15, pady=5)
        ttk.Label(frame, text='Expansion rate\n(1 = original)')\
            .grid(row=2, column=0, sticky=tk.NW, padx=15, pady=5)
        ttk.Label(frame, text='Image size')\
            .grid(row=3, column=0, sticky=tk.NW, padx=15, pady=5)
        
        ttk.Label(frame, text=': ').grid(row=0, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=1, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=2, column=1, sticky=tk.N, pady=5)
        ttk.Label(frame, text=': ').grid(row=3, column=1, sticky=tk.N, pady=5)
            
        ttk.Label(frame, text='(x,y,z) = ({0}, {1}, {2})'.format(*self.Hub.box.shape[:0:-1]))\
            .grid(row=0, column=2, sticky=tk.NW, padx=10, pady=5)
        resol_entries = ttk.Frame(frame)
        resol_entries.grid(row=1, column=2, sticky=tk.NW, padx=10, pady=5)
        exp_frame = ttk.Frame(frame)
        exp_frame.grid(row=2, column=2, sticky=tk.NW, padx=10, pady=5)
        im_size_set = ttk.Frame(frame)
        im_size_set.grid(row=3, column=2, sticky=tk.NW, padx=10, pady=5)
        
        self.d_widgets = {}
        
        self.res_xy = tk.StringVar(value=str(self.geo['res_xy']))
        self.res_z = tk.StringVar(value=str(self.geo['res_z']))
        self.d_widgets['resol_xy'] = ttk.Entry(resol_entries, textvariable=self.res_xy, 
                                               width=8, justify=tk.RIGHT)
        self.d_widgets['resol_xy'].grid(row=0, column=0, sticky=tk.W, pady=2)
        self.d_widgets['resol_z'] = ttk.Entry(resol_entries, textvariable=self.res_z, 
                                              width=8, justify=tk.RIGHT)
        self.d_widgets['resol_z'].grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(resol_entries, text='  μm/px  (xy)').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(resol_entries, text='  μm/px  (z)').grid(row=1, column=1, sticky=tk.W)
        
        def oib_res():
            self.res_xy.set(str(self.geo['xy_oib']))
            self.res_z.set(str(self.geo['z_oib']))
        ttk.Label(resol_title, text='Resolution').grid(row=0, column=0, sticky=tk.NW)
        oib_button = ttk.Button(resol_title, text='Data values', command=oib_res)
        oib_button.grid(row=1, column=0, sticky=tk.NW)
        if not 'xy_oib' in self.geo:
            oib_button['state'] = tk.DISABLED
        
        self.exp_rate = tk.StringVar(value=str(self.geo['exp_rate']))
        self.d_widgets['exp'] = ttk.Entry(exp_frame, textvariable=self.exp_rate,
                                          width=8)
        self.d_widgets['exp'].grid(row=0, column=0, sticky=tk.W)
            
        ttk.Label(im_size_set, text='width = ').grid(row=0, column=0, sticky=tk.E)
        self.size_x = tk.StringVar()
        self.size_x.set(str(self.geo['im_size'][0]))
        self.d_widgets['size_x'] = ttk.Entry(im_size_set, textvariable=self.size_x,
                                             width=5, justify=tk.RIGHT)
        self.d_widgets['size_x'].grid(row=0, column=1)
        ttk.Label(im_size_set, text=' px').grid(row=0, column=2)
        ttk.Label(im_size_set, text='height = ').grid(row=1, column=0, sticky=tk.E)
        self.size_y = tk.StringVar()
        self.size_y.set(str(self.geo['im_size'][1]))
        self.d_widgets['size_y'] = ttk.Entry(im_size_set, textvariable=self.size_y,
                                             width=5, justify=tk.RIGHT)
        self.d_widgets['size_y'].grid(row=1, column=1)
        ttk.Label(im_size_set, text=' px').grid(row=1, column=2)
        
        frame = ttk.Frame(note)
        note.add(frame, text='Files / Channels')
        
        frame1 = ttk.Frame(frame)
        canvas = tk.Canvas(frame1, width=250, height=200, bg='#ffffff')
        barx = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        barx.pack(side=tk.BOTTOM, fill=tk.X)
        barx.config(command=canvas.xview)
        bary = tk.Scrollbar(frame, orient=tk.VERTICAL)
        bary.pack(side=tk.RIGHT, fill=tk.Y)
        bary.config(command=canvas.yview)
        canvas.config(yscrollcommand=bary.set)
        canvas.config(xscrollcommand=barx.set)
        canvas.pack()
        frame1.pack()
        
        ch_frame = tk.Frame(frame1, bg='#ffffff')
        data_files = self.Hub.data
        ch_load = [d[1] for d in data_files]
        data_files = [d[0] for d in data_files]
        data = []
        for f, c in zip(data_files, ch_load):
            if np.array(c).any():
                data += [[f, c]]
        names = np.array(self.Hub.channels.getnames())
        colors = np.array(self.Hub.channels.getcolors())
        colors = (colors/255*55 + 200).astype(np.int)
        
        option = tk.IntVar(value=-1)
        def replace(self):
            data = self.Hub.data.dat
            path1 = data[option.get()][0]
            filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff'])]
            path2 = filedialog.askopenfilename(parent=self.details_win, filetypes=filetypes, 
                                               initialdir=os.path.dirname(path1), title='Open')
            path2 = path2.replace('\\', '/')
            ans = messagebox.askokcancel('Replacing source file',
                                         'The project will be restarted to replace source file.',
                                         parent=self.details_win)
            if not ans:
                return
            files = [d[0] for d in data]
            files[option.get()] = path2
            ch_load = [d[1] for d in data]
            data = []
            for f, c in zip(files, ch_load):
                if np.array(c).any():
                    data += [[f, c]]
            shape = self.Hub.box.shape
            if path2[-4:] == '.oib':
                import oiffile as oif
                shape2 = oif.imread(path2).shape
            else:
                import tifffile as tif
                shape2 = tif.imread(path2).shape
            if len(shape2) == 3:
                shape2 = (1, *shape2)
            if (len(data) == 1) and (len(data[option.get()][1]) != shape2[0]):
                messagebox.showerror('Failed to replace data',
                                      'Number of channels must be exactly the same.',
                                      parent=self.details_win)
                return
            elif (len(data) > 1) and ((len(data[option.get()][1]), *shape[1:]) != shape2):
                messagebox.showerror('Failed to replace data',
                                      'Number of channels, width, height and depth must be exactly the same.',
                                      parent=self.details_win)
                return
            with open(self.Hub.secv_name, 'rb') as f:
                secv = pickle.load(f)
            self.Hub.data.dat = data
            data = tuple(data)
            secv['data'] = data
            secv['geometry']['shape'] = (shape[0], *shape2[1:])
            with open(self.Hub.secv_name, 'wb') as f:
                pickle.dump(secv, f, protocol=4)
            self.Hub.gui.on_close(reboot=True)
            
        
        self.replace_button = ttk.Button(frame, text='Replace', command=lambda: replace(self))
        self.replace_button['state'] = tk.DISABLED
        
        self.pre_opt = -1
        def command(self):
            if self.pre_opt == option.get():
                option.set(-1)
            else:
                self.pre_opt = option.get()
            if option.get() == -1:
                self.replace_button['state'] = tk.DISABLED
            else:
                self.replace_button['state'] = tk.ACTIVE
        
        n = 0
        for i, d in enumerate(data):
            tk.Radiobutton(ch_frame, text='  '+os.path.basename(d[0]), 
                           bg='#ffffff', variable=option, value=i,
                           command=lambda: command(self)).pack(anchor=tk.W, pady=3)
            for cl in d[1]:
                if cl == 0:
                    continue
                color = '#' + ''.join([hex(colors[n,j])[2:] for j in range(2,-1,-1)])
                tk.Label(ch_frame, text=' '+names[n]+' ', bg=color).\
                    pack(anchor=tk.W, padx=25)
                n += 1
            tk.Label(ch_frame, text='', bg='#ffffff').pack(anchor=tk.W)
        canvas.create_window(0,0, window=ch_frame, anchor='nw')
        
        self.replace_button.pack(anchor=tk.E) 
        
        frame = ttk.Frame(note)
        note.add(frame, text='Position')
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
        
        pos = self.Hub.position.asarray()
        pos[:,0] /= self.Hub.ratio
        dc, dz, dy, dx = self.Hub.box.shape
        pos[0] += np.array([dz, dy, dx])//2
        self.pos_v = [[0,0,0],[0,0,0],[0,0,0]]
        for i in range(3):
            for j in range(3):
                self.pos_v[j][2-i] = tk.StringVar(value=str(pos[j,2-i]))
                self.d_widgets[(i,j)] = ttk.Entry(frame, textvariable=self.pos_v[j][2-i], width=8)
                self.d_widgets[(i,j)].grid(row=i+1, column=j+2, padx=5, pady=5)
        
        def initialize():
            pos = np.array([[dz//2, dy//2, dx//2],[0,1,0],[0,0,1]])
            for i in range(3):
                for j in range(3):
                    self.pos_v[j][i].set(str(pos[j,i]))
        ttk.Button(frame, text='initialize', comman=initialize).grid(row=4,column=3, pady=20)
        
        def repair():
            gui.dock_canvas.delete(self.details_id)
            gui.dock_canvas.moveto(gui.dock_id, 0, 0)
            Hub.put_points()
            gui.master.unbind('<Return>')
            gui.master.unbind('<Left>')
            gui.master.unbind('<Right>')
            gui.master.unbind('<Up>')
            gui.master.unbind('<Down>')
            gui.master.protocol('WM_DELETE_WINDOW', gui.on_close)
            gui.menu_bar.entryconfig('File', state='active')
            gui.menu_bar.entryconfig('Edit', state='active')
            gui.menu_bar.entryconfig('Settings', state='active')
            gui.menu_bar.entryconfig('Tools', state='active')
            gui.bar_entry['state'] = tk.ACTIVE
            gui.combo_th['state'] = tk.ACTIVE
            gui.chk_a['state'] = tk.ACTIVE
            gui.chk_b['state'] = tk.ACTIVE
            gui.chk_d['state'] = tk.ACTIVE
            gui.chk_p['state'] = tk.ACTIVE
            gui.rad_b['state'] = tk.ACTIVE
            gui.rad_w['state'] = tk.ACTIVE
            gui.d_switch()
            gui.master.bind('<Key>', gui.key)
            gui.scale.pack(side=tk.LEFT)
            gui.sec_canvas.bind('<Motion>', gui.track_sec)
            gui.sec_canvas.bind('<Button-1>', gui.click_sec)
            gui.sec_canvas.bind('<ButtonRelease-1>', gui.release_sec)
        
        def cancel():
            repair()
        
        self.cancel_button = ttk.Button(self.details_win, text='Cancel', command = cancel)
        self.cancel_button.grid(row=1, column=0, pady=10, sticky=tk.E)
        
        def ok():
            key, new = [], []
            h = len(self.Hub.history)
            try:
                new += [float(self.res_xy.get())]
                key += ['res_xy']
            except: pass
            try:
                new += [float(self.res_z.get())]
                key += ['res_z']
            except: pass
            try: 
                new += [float(self.exp_rate.get())]
                key += ['exp_rate']
            except: pass
            try:
                new += [(int(self.size_x.get()), int(self.size_y.get()))]
                key += ['im_size']
            except: pass
            self.new(key, new)
            try:
                new = np.zeros([3,3])
                for i in range(3):
                    for j in range(3):
                        new[i,j] = float(self.pos_v[i][j].get())
                new[0] -= np.array([dz, dy, dx])//2
                new[:,0] *= self.Hub.ratio
                self.Hub.position.new(new.tolist(), 0)
            except:
                pass
            if len(self.Hub.history) - h == 2:
                self.Hub.group_history(2)
            repair()
            
        self.ok_button = ttk.Button(self.details_win, text='OK', command=ok)
        self.ok_button.grid(row=1, column=1, pady=10, sticky=tk.W)
        
        self.details_win.update()
        canvas.config(scrollregion=(0,0,
                                    max(250,ch_frame.winfo_width()),
                                    max(150,ch_frame.winfo_height())))
        
        note.focus_set()
        
        
        def left():
            w = self.details_win.focus_get()
            if w == self.ok_button:
                self.cancel_button.focus_set()
                
        def right():
            w = self.details_win.focus_get()
            if w == self.cancel_button:
                self.ok_button.focus_set()
                
        def up():
            w = self.details_win.focus_get()
            if w in [self.cancel_button, self.ok_button]:
                if note.tab(note.select(), 'text') == 'Frame':
                    self.d_widgets['size_y'].focus_set()
                elif note.tab(note.select(), 'text') == 'Files / Channels':
                    note.focus_set()
                elif note.tab(note.select(), 'text') == 'Position':
                    self.d_widgets[(2,2)].focus_set()
            elif w == self.d_widgets['size_y']:
                self.d_widgets['size_x'].focus_set()
            elif w == self.d_widgets['size_x']:
                self.d_widgets['exp'].focus_set()
            elif w == self.d_widgets['exp']:
                self.d_widgets['resol_z'].focus_set()
            elif w == self.d_widgets['resol_z']:
                self.d_widgets['resol_xy'].focus_set()
            elif w == self.d_widgets[(2,2)]:
                self.d_widgets[(1,2)].focus_set()
            elif w == self.d_widgets[(2,1)]:
                self.d_widgets[(1,1)].focus_set()
            elif w == self.d_widgets[(2,0)]:
                self.d_widgets[(1,0)].focus_set()
            elif w == self.d_widgets[(1,2)]:
                self.d_widgets[(0,2)].focus_set()
            elif w == self.d_widgets[(1,1)]:
                self.d_widgets[(0,1)].focus_set()
            elif w == self.d_widgets[(1,0)]:
                self.d_widgets[(0,0)].focus_set()
            elif w in [self.d_widgets['resol_xy'],
                       self.d_widgets[(0,0)],
                       self.d_widgets[(0,1)],
                       self.d_widgets[(0,2)]]:
                note.focus_set()
                
        def down():
            w = self.details_win.focus_get()
            if w == self.d_widgets['size_y']:
                self.ok_button.focus_set()
            elif w == self.d_widgets['size_x']:
                self.d_widgets['size_y'].focus_set()
            elif w == self.d_widgets['exp']:
                self.d_widgets['size_x'].focus_set()
            elif w == self.d_widgets['resol_z']:
                self.d_widgets['exp'].focus_set()
            elif w == self.d_widgets['resol_xy']:
                self.d_widgets['resol_z'].focus_set()
            elif w in [self.d_widgets[(2,0)],
                       self.d_widgets[(2,1)],
                       self.d_widgets[(2,2)]]:
                self.ok_button.focus_set()
            elif w == self.d_widgets[(1,2)]:
                self.d_widgets[(2,2)].focus_set()
            elif w == self.d_widgets[(1,1)]:
                self.d_widgets[(2,1)].focus_set()
            elif w == self.d_widgets[(1,0)]:
                self.d_widgets[(2,0)].focus_set()
            elif w == self.d_widgets[(0,2)]:
                self.d_widgets[(1,2)].focus_set()
            elif w == self.d_widgets[(0,1)]:
                self.d_widgets[(1,1)].focus_set()
            elif w == self.d_widgets[(0,0)]:
                self.d_widgets[(1,0)].focus_set()
            elif w == note:
                if note.tab(note.select(), 'text') == 'Frame':
                    self.d_widgets['resol_xy'].focus_set()
                elif note.tab(note.select(), 'text') == 'Files / Channels':
                    self.ok_button.focus_set()
                elif note.tab(note.select(), 'text') == 'Position':
                    self.d_widgets[(0,0)].focus_set()
                
        def enter():
            w = self.details_win.focus_get()
            if w != self.ok_button and 2 != self.cancel_button:
                self.ok_button.focus_set()
            else:
                w.invoke()
                
        gui.master.protocol('WM_DELETE_WINDOW', cancel)
        gui.menu_bar.entryconfig('File', state='disabled')
        gui.menu_bar.entryconfig('Edit', state='disabled')
        gui.menu_bar.entryconfig('Settings', state='disabled')
        gui.menu_bar.entryconfig('Tools', state='disabled')
        gui.bar_entry['state'] = tk.DISABLED
        gui.combo_th['state'] = tk.DISABLED
        gui.chk_a['state'] = tk.DISABLED
        gui.chk_b['state'] = tk.DISABLED
        gui.chk_d['state'] = tk.DISABLED
        gui.chk_p['state'] = tk.DISABLED
        gui.rad_b['state'] = tk.DISABLED
        gui.rad_w['state'] = tk.DISABLED
        gui.master.unbind('<Key>')
        gui.scale.pack_forget()
        gui.sec_canvas.unbind('<Motion>')
        gui.sec_canvas.unbind('<Button-1>')
        gui.sec_canvas.unbind('<ButtonRelease-1>')
        if not gui.d_on.get():
            gui.d_on.set(True)
            gui.d_switch()
            gui.d_on.set(False)
        gui.dock_canvas.moveto(gui.dock_id, 500, 0)
        gui.dock_canvas.moveto(self.details_id, 0, 0)
        gui.master.bind('<Return>', lambda event: enter())
        gui.master.bind('<Left>', lambda event: left())
        gui.master.bind('<Right>', lambda event: right())
        gui.master.bind('<Up>', lambda event: up())
        gui.master.bind('<Down>', lambda event: down())
        
        
    def set_bar_length(self, *args):
        new = self.Hub.gui.bar_text.get()[:10]
        self.Hub.gui.bar_text.set_bar(new)
        try:
            new = float(new)
        except:
            return
        if self.geo['bar_len'] == new:
            return
        Hub = self.Hub
        idx, hist = Hub.hidx, Hub.history
        if idx == -1 and hist[-1][0] == self \
            and 'bar_len' in hist[-1][1][0] and Hub.hidx_saved != -1:
            hist[-1][1][2][0] = new
        else:
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [['bar_len'], [self.geo['bar_len']], [new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
        
        if self.geo['bar_len'] == None:
            Hub.gui.bar_entry.configure(state=tk.NORMAL)
            
        self.geo['bar_len'] = new
        
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        Hub.lpx = int(self.geo['bar_len']/self.geo['res_xy']*self.geo['exp_rate'])
        Hub.put_axes_bar()
            
    def bar_entry_out(self, event):
        self.Hub.gui.bar_text.set_bar(self.geo['bar_len'])
    
    def new(self, key, new):
        Hub = self.Hub
        
        old = [self.geo[k] for k in key]
        
        for k, n in zip(key, new):
            self.geo[k] = n
        if 'res_xy' in key and not 'res_z' in key and self.geo['res_z'] == None:
            new += [self.geo['res_xy']]
            key += ['res_z']
            old += [None]
            self.geo['res_z'] = self.geo['res_xy']
        if not 'res_xy' in key and 'res_z' in key and self.geo['res_xy'] == None:
            new += [self.geo['res_z']]
            key += ['res_xy']
            old += [None]
            self.geo['res_xy'] = self.geo['res_z']
        if ('exp_rate' in key or 'res_xy' in key) \
            and not 'bar_len' in key and self.geo['res_xy'] != None:
            xy_rs, exp = self.geo['res_xy'], self.geo['exp_rate']
            new += [round(80*xy_rs/exp, -math.floor(np.log10(80*xy_rs/exp)))]
            key += ['bar_len']
            old += [self.geo['bar_len']]
            self.geo['bar_len'] = new[-1]
            self.Hub.gui.bar_text.set_bar(self.geo['bar_len'])
            
            
        if old == new:
            return None
        
        idx, hist = Hub.hidx, Hub.history
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        
        if 'bar_len' in key and None in old:
            Hub.gui.bar_entry.configure(state=tk.NORMAL)
            
        hist += [[self, [key, old, new]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else: 
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
        
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        if key == ['bar_len']:
            Hub.lpx = int(self.geo['bar_len']/self.geo['res_xy']*self.geo['exp_rate'])
            Hub.put_axes_bar()
        else:
            if 'im_size' in key:
                num = key.index('im_size')
                n1, n2 = new[num]
                o1, o2 = old[num]
                n1, n2 = n1*Hub.zoom, n2*Hub.zoom
                o1, o2 = o1*Hub.zoom, o2*Hub.zoom
                w, h = gui.sec_cf.winfo_width()-4, gui.sec_cf.winfo_height()-4
                n1, n2 = w//2 - n1//2, h//2 - n2//2
                o1, o2 = w//2 - o1//2, h//2 - o2//2
                gui.upperleft = (int(gui.upperleft[0] + o1 - n1), 
                                 int(gui.upperleft[1] + o2 - n2))
                
            if not self.Hub.calc_geometry():
                for k, o in zip(key, old):
                    self.geo[k] = o
                del hist[-1]
                Hub.hidx_saved += 1
                if 'bar_len' in key and None in old:
                    Hub.gui.bar_button.configure(state=tk.DISABLED)
                if len(hist) == 1:
                    gui.edit_menu.entryconfig('Undo', state='disable')
                if Hub.hidx == Hub.hidx_saved:
                    gui.master.title(gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
                self.Hub.calc_geometry()
                    
            if gui.d_on.get():
                if self.Hub.gui.guide_mode == 'guide':
                    self.Hub.calc_guide()
                elif self.Hub.gui.guide_mode == 'sideview':
                    self.Hub.calc_sideview()
        
            
    def undo(self, arg):
        for k, n in zip(arg[0], arg[1]):
            self.geo[k] = n
        if 'bar_len' in arg[0]:
            self.Hub.gui.bar_text.set_bar(self.geo['bar_len'])
            if self.geo['bar_len'] == None:
                self.Hub.gui.bar_entry.configure(state=tk.DISABLED)
        if arg[0] == ['bar_len']:
            self.Hub.lpx = int(self.geo['bar_len']/self.geo['res_xy']*self.geo['exp_rate'])
            self.Hub.put_axes_bar()
        else:
            if 'im_size' in arg[0]:
                Hub = self.Hub
                gui = Hub.gui
                num = arg[0].index('im_size')
                n1, n2 = arg[1][num]
                o1, o2 = arg[2][num]
                n1, n2 = n1*Hub.zoom, n2*Hub.zoom
                o1, o2 = o1*Hub.zoom, o2*Hub.zoom
                w, h = gui.sec_cf.winfo_width()-4, gui.sec_cf.winfo_height()-4
                n1, n2 = w//2 - n1//2, h//2 - n2//2
                o1, o2 = w//2 - o1//2, h//2 - o2//2
                gui.upperleft = (int(gui.upperleft[0] + o1 - n1), 
                                 int(gui.upperleft[1] + o2 - n2))
            self.Hub.calc_geometry()
            if self.Hub.gui.d_on.get():
                if self.Hub.gui.guide_mode == 'guide':
                    self.Hub.calc_guide()
                elif self.Hub.gui.guide_mode == 'sideview':
                    self.Hub.calc_sideview()
        
    def redo(self, arg):
        if 'bar_len' in arg[0] and self.geo['bar_len'] == None:
            self.Hub.gui.bar_entry.configure(state=tk.NORMAL)
        for k, n in zip(arg[0], arg[2]):
            self.geo[k] = n
        if 'bar_len' in arg[0]:
            self.Hub.gui.bar_text.set_bar(self.geo['bar_len'])
        if arg[0] == ['bar_len']:
            self.Hub.lpx = int(self.geo['bar_len']/self.geo['res_xy']*self.geo['exp_rate'])
            self.Hub.put_axes_bar()
        else:
            if 'im_size' in arg[0]:
                Hub = self.Hub
                gui = Hub.gui
                num = arg[0].index('im_size')
                n1, n2 = arg[2][num]
                o1, o2 = arg[1][num]
                n1, n2 = n1*Hub.zoom, n2*Hub.zoom
                o1, o2 = o1*Hub.zoom, o2*Hub.zoom
                w, h = gui.sec_cf.winfo_width()-4, gui.sec_cf.winfo_height()-4
                n1, n2 = w//2 - n1//2, h//2 - n2//2
                o1, o2 = w//2 - o1//2, h//2 - o2//2
                gui.upperleft = (int(gui.upperleft[0] + o1 - n1), 
                                 int(gui.upperleft[1] + o2 - n2))
            self.Hub.calc_geometry()
            if self.Hub.gui.d_on.get():
                if self.Hub.gui.guide_mode == 'guide':
                    self.Hub.calc_guide()
                elif self.Hub.gui.guide_mode == 'sideview':
                    self.Hub.calc_sideview()
                
    def reload(self, geo):
        Hub = self.Hub
        
        if not 'res_xy' in geo: geo['res_xy'] = None
        if not 'res_z' in geo: geo['res_z'] = None
        if geo['res_xy'] == None and 'xy_oib' in geo: geo['res_xy'] = geo['xy_oib']
        if geo['res_z'] == None and 'z_oib' in geo: geo['res_z'] = geo['z_oib']
        
        if None in (geo['res_xy'], geo['res_z']):
            if geo['res_xy'] != None:
                geo['res_z'] = geo['res_xy']
            else:
                geo['res_xy'] = geo['res_z']
        Hub.ratio = 1. if None in (geo['res_xy'], geo['res_z']) else geo['res_z']/geo['res_xy']
        if hasattr(Hub, 'box'):
            dc, dz, dy, dx = Hub.box.shape
            Hub.L = (dx**2 + dy**2 + (dz*Hub.ratio)**2)**0.5
                
        if not 'im_size' in geo: geo['im_size'] = (dx,dy)
        if not 'exp_rate' in geo: geo['exp_rate'] = 1
        elif geo['exp_rate'] == 0: geo['exp_rate'] = 1
        if not 'bar_len' in geo: geo['bar_len'] = None
        
        if geo['res_xy'] != None:
            if geo['bar_len'] == None:
                a = geo['res_xy']/geo['exp_rate']
                geo['bar_len'] = round(80*a, -int(np.log10(80*a)))
            Hub.lpx = int(geo['bar_len']/geo['res_xy']*geo['exp_rate'])
        else: Hub.lpx = 0
        
        if self.geo == geo:
            return False
        
        self.geo = geo
        return True
