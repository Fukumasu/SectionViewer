import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


class Channels:
    def __init__(self, Hub):
        self.Hub = Hub
        chs = Hub.channels
        
        if hasattr(Hub, 'geometry'):
            dc = Hub.geometry['shape'][0]
        elif hasattr(Hub, 'stacks'):
            data = Hub.stacks
            dc = len(data[0])
            
        if len(chs) != dc:
            c = self.auto_color([], dc) if dc > 1 else [[255]*3]
            chs = [['ch{0}'.format(i), c[i], 0, 65535] for i in range(dc)]
        else:
            for c in chs:
                c[0] = str(c[0])
                c[1] = [int(c[1][i])%256 for i in range(3)]
                c[2], c[3] = int(c[2]), int(c[3])
        
        self.chs = chs
        self.chs_trash = {}
        
        self.variables = {'nm': tk.StringVar(),
                       'b' : tk.IntVar(),
                       'g' : tk.IntVar(),
                       'r' : tk.IntVar(),
                       'bs': tk.StringVar(),
                       'gs': tk.StringVar(),
                       'rs': tk.StringVar(),
                       'vn': tk.IntVar(),
                       'vx': tk.IntVar(),
                       'vns': tk.StringVar(),
                       'vxs': tk.StringVar(),
                       'h' : tk.IntVar(),
                       's' : tk.IntVar(),
                       'l' : tk.IntVar(),
                       'hs': tk.StringVar(),
                       'ss': tk.StringVar(),
                       'ls': tk.StringVar(),
                       'sh': tk.IntVar()}
        
        self.variables['nm'].trace('w', self.ch_name)
        self.variables['r'].trace('w', lambda *args: self.variables['rs'].set(str(self.variables['r'].get())))
        self.variables['g'].trace('w', lambda *args: self.variables['gs'].set(str(self.variables['g'].get())))
        self.variables['b'].trace('w', lambda *args: self.variables['bs'].set(str(self.variables['b'].get())))
        self.variables['h'].trace('w', lambda *args: self.variables['hs'].set(str(self.variables['h'].get()/10)))
        self.variables['s'].trace('w', lambda *args: self.variables['ss'].set(str(self.variables['s'].get()/10)))
        self.variables['l'].trace('w', lambda *args: self.variables['ls'].set(str(self.variables['l'].get()/10)))
        self.variables['vn'].trace('w', lambda *args: self.variables['vns'].set(str(self.variables['vn'].get())))
        self.variables['vx'].trace('w', lambda *args: self.variables['vxs'].set(str(self.variables['vx'].get())))
        
        self.scalemax = [[224,255],[896,1023],[3584,4095],[14336,16383],[57344,65535]]
        self.to_lock = False
        self.entry_channel = 0
        
        # settings
        
        frame0 = ttk.Frame(Hub.gui.palette)
        self.set_frame = frame0
        
        frame1 = ttk.Frame(frame0)
        frame1.pack(side=tk.LEFT)
        
        if hasattr(self.Hub, 'data'):
            frameb = ttk.Frame(frame1)
            frameb.pack(side=tk.BOTTOM, anchor=tk.E, padx=10)
            button1 = ttk.Button(frameb, text='Add', command=self.add_ch)
            button1.pack(side=tk.LEFT)
            button2 = ttk.Button(frameb, text='Delete', command=self.del_ch)
            button2.pack(side=tk.LEFT)
            self.button_dl = button2
    
        self.treeview = ttk.Treeview(frame1, height=15)
        self.treeview.column('#0', width=200, stretch=False)
        self.treeview.heading('#0', text='Channels', anchor=tk.W)
        
        bary = tk.Scrollbar(frame1, orient=tk.VERTICAL)
        bary.pack(side=tk.LEFT, fill=tk.Y)
        bary.config(command=self.treeview.yview)
        self.treeview.config(yscrollcommand=bary.set)
        self.treeview.pack(padx=10, pady=5)
        
        self.treeview.bind('<Button-1>', lambda e: self.treeview.selection_set()\
                          if e.state//4%2!=1 else None)
        self.treeview.bind('<<TreeviewSelect>>', self.ch_select)
        
        names = self.getnames()
        colors = np.array(self.getcolors())
        
        sort = np.argsort(self.getnames())
        im = np.zeros([8,8,3], np.uint8)
        self.icons = [0]*len(sort)
        for i in sort:
            im[1:-1,1:-1] = colors[i]
            self.icons[i] = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
            self.treeview.insert('', 'end', str(i), text=' '+names[i], image=self.icons[i])
        
        frame2 = ttk.Frame(frame0)
        frame2.pack(side=tk.LEFT, pady=10)
        self.frame2 = frame2
        
        frame3 = ttk.Frame(frame2)
        frame3.pack(padx=10, pady=5, ipadx=5, ipady=5)
        self.entry_nm = ttk.Entry(frame3, textvariable=self.variables['nm'])
        self.entry_nm.pack(side=tk.LEFT)
        self.checkbutton = ttk.Checkbutton(frame3, variable=self.variables['sh'], 
                                        onvalue=1, offvalue=0,
                                        text='Show', command=self.showhide)
        self.checkbutton.pack(side=tk.RIGHT)
        
        note = ttk.Notebook(frame2)
        note.pack(padx=10, pady=5, ipadx=5, ipady=5)
        
        def select_entry():
            self.entry_channel = self.treeview.selection()
        
        def color_entry(c):
            try:
                if self.entry_channel == self.treeview.selection():
                    if c in 'rgb':
                        new = float(self.variables[c + 's'].get())
                        new = int(max(0, min(new, 255)))
                        self.variables[c].set(new)
                        self.variables[c + 's'].set(str(new))
                        self.rgb()
                    elif c in 'hsl':
                        new = float(self.variables[c + 's'].get())*10
                        mx = 3599 if c=='h' else 1000
                        new = int(max(0, min(new, mx)))
                        self.variables[c].set(new)
                        self.variables[c + 's'].set(str(new/10))
                        self.hsl()
                    elif c == 'vn':
                        new = float(self.variables['vns'].get())
                        new = int(max(0, min(new, 65534)))
                        if self.variables['vx'].get() <= new:
                            self.variables['vx'].set(new + 1)
                            self.variables['vxs'].set(str(new + 1))
                        self.variables['vn'].set(new)
                        self.ch_vrange()
                        self.variables['vns'].set(str(new))
                    elif c == 'vx':
                        new = float(self.variables['vxs'].get())
                        new = int(max(1, min(new, 65535)))
                        if self.variables['vn'].get() >= new:
                            self.variables['vn'].set(new - 1)
                            self.variables['vns'].set(str(new - 1))
                        self.variables['vx'].set(new)
                        self.ch_vrange()
                        self.variables['vxs'].set(str(new))
                        for a, to in self.scalemax:
                            if new <= a:
                                break
                        self.vmin_scale.configure(to=to)
                        self.vmax_scale.configure(to=to)
                else:
                    self.entry_channel = self.treeview.selection()
            except:
                if c in 'rgbvnvx':
                    self.variables[c + 's'].set(str(self.variables[c].get()))
                elif c in 'hsl':
                    self.variables[c + 's'].set(str(self.variables[c].get()))
        
        rgb_frame = ttk.Frame(note)
        self.rgb_frame = rgb_frame
        
        ttk.Label(rgb_frame, text='  R:  ').grid(column=0, row=1)
        ttk.Label(rgb_frame, text='  G:  ').grid(column=0, row=2)
        ttk.Label(rgb_frame, text='  B:  ').grid(column=0, row=3)
        ttk.Scale(rgb_frame, length=190, variable=self.variables['r'], from_=0, to=255,
                 orient='horizontal', command=self.rgb).grid(column=1, row=1, pady=7)
        ttk.Scale(rgb_frame, length=190, variable=self.variables['g'], from_=0, to=255,
                 orient='horizontal', command=self.rgb).grid(column=1, row=2, pady=7)
        ttk.Scale(rgb_frame, length=190, variable=self.variables['b'], from_=0, to=255,
                 orient='horizontal', command=self.rgb).grid(column=1, row=3, pady=7)
        self.entry_r = ttk.Entry(rgb_frame, textvariable=self.variables['rs'], width=5)
        self.entry_r.grid(column=2, row=1, padx=3)
        self.entry_g = ttk.Entry(rgb_frame, textvariable=self.variables['gs'], width=5)
        self.entry_g.grid(column=2, row=2, padx=3)
        self.entry_b = ttk.Entry(rgb_frame, textvariable=self.variables['bs'], width=5)
        self.entry_b.grid(column=2, row=3, padx=3)
        self.entry_r.bind('<Return>', lambda event: color_entry('r'))
        self.entry_r.bind('<FocusIn>', lambda event: select_entry())
        self.entry_r.bind('<FocusOut>', lambda event: color_entry('r'))
        self.entry_g.bind('<Return>', lambda event: color_entry('g'))
        self.entry_g.bind('<FocusIn>', lambda event: select_entry())
        self.entry_g.bind('<FocusOut>', lambda event: color_entry('g'))
        self.entry_b.bind('<Return>', lambda event: color_entry('b'))
        self.entry_b.bind('<FocusIn>', lambda event: select_entry())
        self.entry_b.bind('<FocusOut>', lambda event: color_entry('b'))
        ttk.Button(rgb_frame, text='Auto', command=self.set_auto).grid(column=1, row=4, 
                                                                      columnspan=2, pady=2, sticky=tk.E)
        note.add(rgb_frame, text='RGB')
        
        hsl_frame = ttk.Frame(note)
        self.hsl_frame = hsl_frame
        
        ttk.Label(hsl_frame, text=' H:  ').grid(column=0, row=1)
        ttk.Label(hsl_frame, text=' S:  ').grid(column=0, row=2)
        ttk.Label(hsl_frame, text=' L:  ').grid(column=0, row=3)
        ttk.Scale(hsl_frame, length=190, variable=self.variables['h'], from_=0, to=3599,
                 orient='horizontal', command=self.hsl).grid(column=1, row=1, pady=7)
        ttk.Scale(hsl_frame, length=190, variable=self.variables['s'], from_=0, to=1000,
                 orient='horizontal', command=self.hsl).grid(column=1, row=2, pady=7)
        ttk.Scale(hsl_frame, length=190, variable=self.variables['l'], from_=0, to=1000,
                 orient='horizontal', command=self.hsl).grid(column=1, row=3, pady=7)
        self.entry_h = ttk.Entry(hsl_frame, textvariable=self.variables['hs'], width=5)
        self.entry_h.grid(column=2, row=1, padx=3)
        self.entry_s = ttk.Entry(hsl_frame, textvariable=self.variables['ss'], width=5)
        self.entry_s.grid(column=2, row=2, padx=3)
        self.entry_l = ttk.Entry(hsl_frame, textvariable=self.variables['ls'], width=5)
        self.entry_l.grid(column=2, row=3, padx=3)
        self.entry_h.bind('<Return>', lambda event: color_entry('h'))
        self.entry_h.bind('<FocusIn>', lambda event: select_entry())
        self.entry_h.bind('<FocusOut>', lambda event: color_entry('h'))
        self.entry_s.bind('<Return>', lambda event: color_entry('s'))
        self.entry_s.bind('<FocusIn>', lambda event: select_entry())
        self.entry_s.bind('<FocusOut>', lambda event: color_entry('s'))
        self.entry_l.bind('<Return>', lambda event: color_entry('l'))
        self.entry_l.bind('<FocusIn>', lambda event: select_entry())
        self.entry_l.bind('<FocusOut>', lambda event: color_entry('l'))
        ttk.Button(hsl_frame, text='Auto', command=self.set_auto).grid(column=1, row=4, 
                                                                      columnspan=2, pady=2, sticky=tk.E)
        note.add(hsl_frame, text='HSL')
        
        vnx_frame = ttk.Frame(frame2)
        vnx_frame.pack(padx=10, pady=5, ipadx=5, ipady=5)
        
        vmax = self.getvranges()[0][1]
        for a, to in self.scalemax:
            if vmax <= a:
                break
        ttk.Label(vnx_frame, text=' vmin: ').grid(column=0, row=0)
        ttk.Label(vnx_frame, text=' vmax: ').grid(column=0, row=1)
        self.vmin_scale = ttk.Scale(vnx_frame, length=190, variable=self.variables['vn'], from_=0, to=to,
                                    orient='horizontal', command=self.vmin)
        self.vmin_scale.grid(column=1, row=0, pady=7)
        self.vmax_scale=ttk.Scale(vnx_frame, length=190, variable=self.variables['vx'], from_=0, to=to,
                                  orient='horizontal', command=self.vmax)
        self.vmax_scale.grid(column=1, row=1, pady=7)
        def press():
            self.to_lock=True
        def release():
            self.to_lock = False
            vmax = self.variables['vx'].get()
            for a, to in self.scalemax:
                if vmax <= a:
                    break
            self.vmin_scale.configure(to=to)
            self.vmax_scale.configure(to=to)
        self.vmax_scale.bind('<Button-1>', lambda event: press())
        self.vmax_scale.bind('<ButtonRelease-1>', lambda event: release())
        self.entry_vn = ttk.Entry(vnx_frame, textvariable=self.variables['vns'], width=5)
        self.entry_vn.grid(column=2, row=0, padx=3)
        self.entry_vx = ttk.Entry(vnx_frame, textvariable=self.variables['vxs'], width=5)
        self.entry_vx.grid(column=2, row=1, padx=3)
        self.entry_vn.bind('<Return>', lambda event: color_entry('vn'))
        self.entry_vn.bind('<FocusIn>', lambda event: select_entry())
        self.entry_vn.bind('<FocusOut>', lambda event: color_entry('vn'))
        self.entry_vx.bind('<Return>', lambda event: color_entry('vx'))
        self.entry_vx.bind('<FocusIn>', lambda event: select_entry())
        self.entry_vx.bind('<FocusOut>', lambda event: color_entry('vx'))
        self.vnx_frame = vnx_frame
        self.note = note
        
    
    def __getattr__(self, name):
        if name == 'val':
            return object.__getattribute__(self, 'chs')
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == 'val':
            self.chs = val
        else:
            object.__setattr__(self, name, val)
        if name == 'chs':
            self.Hub.colors = np.array(self.getcolors(), np.uint8)
            vrange = np.array(self.getvranges())
            lut = np.arange(65536)[None]
            diff = vrange[:,1] - vrange[:,0]
            lut = ((1/diff[:,None])*(lut - vrange[:,:1]))
            lut[lut<1/255] = 1/255
            lut[lut>1] = 1
            self.Hub.lut = lut
    
    def __getitem__(self, x):
        return self.chs[x]
    
    def __len__(self):
        return len(self.chs)
    
    def getnames(self):
        return [c[0] for c in self.chs]
    def getcolors(self):
        return [c[1] for c in self.chs]
    def getvranges(self):
        return [c[2:] for c in self.chs]
    
    def settings(self):
        gui = self.Hub.gui
        gui.palette.title('Channels')
        for w in gui.palette.pack_slaves():
            w.pack_forget()
        self.set_frame.pack(pady=10, padx=5)
        gui.palette.unbind('<Control-a>')
        gui.palette.bind('<Control-a>', lambda event: self.treeview.selection_set(self.treeview.get_children()))
        self.refresh_tree()
    
        gui.palette.deiconify()
        gui.palette.grab_set()
        x = self.treeview.get_children()
        self.treeview.focus(x[0])
        self.treeview.selection_set(x[0])
        
    
    def refresh_tree(self):
        names = self.getnames()
        colors = np.array(self.getcolors())
        self.treeview.delete(*self.treeview.get_children())
        sort = np.argsort(self.getnames())
        im = np.zeros([8,8,3], np.uint8)
        self.icons = [0]*len(sort)
        for i in sort:
            im[1:-1,1:-1] = colors[i]
            self.icons[i] = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
            self.treeview.insert('', 'end', str(i), text=' '+names[i], image=self.icons[i])
        self.treeview.selection_set()
        
    
    def ch_select(self, event):
        selection = self.treeview.selection()
        
        if len(selection) == 0:
            self.frame2.pack_forget()
            return
        else:
            self.frame2.pack()
        
        if hasattr(self, 'button_dl'):
            if len(selection) < len(self.treeview.get_children()):
                self.button_dl['state'] = tk.ACTIVE
            else:
                self.button_dl['state'] = tk.DISABLED
        
        x = [int(i) for i in selection]
        i = x[0]
        bgr = self.chs[i][1]
        hsl = self.bgr2hsl(bgr)
        
        self.variables['nm'].set(self.chs[i][0])
        self.variables['r'].set(bgr[2])
        self.variables['g'].set(bgr[1])
        self.variables['b'].set(bgr[0])
        self.variables['vn'].set(self.chs[i][2])
        self.variables['vx'].set(self.chs[i][3])
        for a, to in self.scalemax:
            if self.chs[i][3] <= a:
                break
        self.vmin_scale.configure(to=to)
        self.vmax_scale.configure(to=to)
        self.variables['h'].set(int(hsl[0]*10))
        self.variables['s'].set(int(hsl[1]*10))
        self.variables['l'].set(int(hsl[2]*10))
        
        self.checkbutton['state'] = tk.ACTIVE
        
        if self.Hub.ch_show[x].all():
            self.variables['sh'].set(1)
            for w in self.rgb_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.ACTIVE
            for w in self.hsl_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.ACTIVE
            for w in self.vnx_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.ACTIVE
        else:
            if self.Hub.ch_show[x].any():
                self.variables['sh'].set(-1)
            else:
                self.variables['sh'].set(0)
            for w in self.rgb_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.DISABLED
            for w in self.hsl_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.DISABLED
            for w in self.vnx_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.DISABLED
        
        if len(selection) == 1:
            self.entry_nm['state'] = tk.ACTIVE
        else:
            self.entry_nm['state'] = tk.DISABLED
    
    
    def set_auto(self):
        x = self.treeview.selection()
        nums = [int(i) for i in x]
        old = [self.chs[i][1:] for i in nums]
        
        fix = []
        for i in self.treeview.get_children():
            if not i in x:
                fix += [list(self.chs[i][1])]
        new = len(x)
        new = self.auto_color(fix, new)
        new = [[nw, *self.chs[n][2:]] for nw, n in zip(new, nums)]
        
        if old == new:
            return None
        
        Hub = self.Hub
        idx, hist = Hub.hidx, Hub.history
        if idx == -1 and hist[-1][1][0] == self.set_color and hist[-1][1][1][0] == x:
            hist[-1][1][3][1] = new
        else:
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.set_color, [x, old], self.set_color, [x, new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_color(x, new)
              
                
    def showhide(self, *args):
        selection = self.treeview.selection()
        x = [int(i) for i in selection]
        self.Hub.ch_show[x] = self.variables['sh'].get()
        if self.variables['sh'].get():
            self.entry_nm['state'] = tk.ACTIVE
            for w in self.rgb_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.ACTIVE
            for w in self.hsl_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.ACTIVE
            for w in self.vnx_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.ACTIVE
            if (self.Hub.frame[x[0]] == 0).all():
                self.Hub.calc_frame(x=x)
                if hasattr(self.Hub.gui, 'g_on'):
                    if self.Hub.gui.g_on.get():
                        self.Hub.calc_sideview(x=x)
            else:
                self.Hub.calc_image()
                if hasattr(self.Hub.gui, 'g_on'):
                    if self.Hub.gui.g_on.get():
                        self.Hub.calc_sideimage()
        else:
            self.entry_nm['state'] = tk.DISABLED
            for w in self.rgb_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.DISABLED
            for w in self.hsl_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.DISABLED
            for w in self.vnx_frame.grid_slaves():
                if not 'scale' in str(w)[-6:]:
                    w['state'] = tk.DISABLED
            self.Hub.calc_image()
            if hasattr(self.Hub.gui, 'g_on'):
                if self.Hub.gui.g_on.get():
                    self.Hub.calc_sideimage()
    
              
    def ch_name(self, *args):
        x = self.treeview.selection()
        if len(x) > 1:
            return None
        
        i = int(x[0])
        old = self.chs[i][0]
        new = self.variables['nm'].get()
        
        if old == new:
            return None
        
        Hub = self.Hub
        idx, hist = Hub.hidx, Hub.history
        if idx == -1 and hist[-1][1][0] == self.set_name \
            and hist[-1][1][1][0] == x and Hub.hidx_saved != -1:
            hist[-1][1][3][1] = new
        else:
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.set_name, [x, old], self.set_name, [x, new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_name(x, new)
        
        
    def set_name(self, x, new):
        self.treeview.item(x[0], text=' '+new)
        if x != self.treeview.selection():
            self.treeview.selection_set(x)
        else:
            self.variables['nm'].set(new)
            
        i = int(x[0])
        self.chs[i][0] = new
        
        
    def rgb(self, *args):
        if not self.variables['sh'].get():
            i = int(self.treeview.selection()[0])
            self.variables['b'].set(self.chs[i][1][0])
            self.variables['g'].set(self.chs[i][1][1])
            self.variables['r'].set(self.chs[i][1][2])
            return
        a  = [self.variables['b'].get()]
        a += [self.variables['g'].get()]
        a += [self.variables['r'].get()]
        a = self.bgr2hsl(a)
        self.variables['h'].set(int(a[0]*10))
        self.variables['s'].set(int(a[1]*10))
        self.variables['l'].set(int(a[2]*10))
        self.ch_color()
    def hsl(self, *args):
        if not self.variables['sh'].get():
            i = int(self.treeview.selection()[0])
            a = list(self.chs[i][1])
            a = self.bgr2hsl(a)
            self.variables['h'].set(int(a[0]*10))
            self.variables['s'].set(int(a[1]*10))
            self.variables['l'].set(int(a[2]*10))
            return
        a  = [self.variables['h'].get()/10]
        a += [self.variables['s'].get()/10]
        a += [self.variables['l'].get()/10]
        a = self.hsl2bgr(a)
        self.variables['b'].set(a[0])
        self.variables['g'].set(a[1])
        self.variables['r'].set(a[2])
        self.ch_color()
        
    def ch_color(self, *args):
        x = self.treeview.selection()
        nums = [int(i) for i in x]
        old = [self.chs[i][1] for i in nums]
        new = [[self.variables['b'].get(), self.variables['g'].get(), self.variables['r'].get()]]*len(nums)
        
        if old == new:
            return None
        
        Hub = self.Hub
        idx, hist = Hub.hidx, Hub.history
        if idx == -1 and hist[-1][1][0] == self.set_color \
            and hist[-1][1][1][0] == x and Hub.hidx_saved != -1:
            hist[-1][1][3][1] = new
        else:
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.set_color, [x, old], self.set_color, [x, new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_color(x, new)
        
    def set_color(self, x, new):
        l = len(new)
        im = np.zeros([8,8,3], np.uint8)
        nums = [int(i) for i in x]
        for i, st in enumerate(x):
            j = nums[i]
            self.chs[j][1] = [new[i%l][0], new[i%l][1], new[i%l][2]]
            im[1:-1,1:-1] = new[i%l]
            self.icons[int(st)] = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
            self.treeview.item(st, image=self.icons[int(st)])
        
        if x != self.treeview.selection():
            self.treeview.selection_set(x)
        else:
            i = int(x[0])
            bgr = self.chs[i][1]
            hsl = self.bgr2hsl(bgr)
            
            self.variables['r'].set(bgr[2])
            self.variables['g'].set(bgr[1])
            self.variables['b'].set(bgr[0])
            self.variables['h'].set(int(hsl[0]*10))
            self.variables['s'].set(int(hsl[1]*10))
            self.variables['l'].set(int(hsl[2]*10))
            self.variables['sh'].set(bool(self.Hub.ch_show[i]))
            
        self.chs = self.chs
        self.Hub.calc_image()
        if hasattr(self.Hub.gui, 'g_on'):
            if self.Hub.gui.g_on.get():
                self.Hub.calc_sideview()
                
    
    def vmin(self, *args):
        if not self.variables['sh'].get():
            i = int(self.treeview.selection()[0])
            self.variables['vn'].set(self.chs[i][2])
            return
        if self.variables['vn'].get() >= self.variables['vx'].get():
            self.variables['vn'].set(self.variables['vx'].get()-1)
        self.ch_vrange()
    def vmax(self, *args):
        if not self.variables['sh'].get():
            i = int(self.treeview.selection()[0])
            self.variables['vx'].set(self.chs[i][3])
            return
        if self.variables['vn'].get() >= self.variables['vx'].get():
            self.variables['vx'].set(self.variables['vn'].get()+1)
        self.ch_vrange()
    
    def ch_vrange(self, *args):
        x = self.treeview.selection()
        nums = [int(i) for i in x]
        old = [self.chs[i][2:] for i in nums]
        new = [[self.variables['vn'].get(), self.variables['vx'].get()]]*len(nums)
        
        if old == new:
            return None
        
        Hub = self.Hub
        idx, hist = Hub.hidx, Hub.history
        if idx == -1 and hist[-1][1][0] == self.set_vrange \
            and hist[-1][1][1][0] == x and Hub.hidx_saved != -1:
            hist[-1][1][3][1] = new
        else:
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.set_vrange, [x, old], self.set_vrange, [x, new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_vrange(x, new)
                
    def set_vrange(self, x, new):
        l = len(new)
        nums = [int(i) for i in x]
        for i, st in enumerate(x):
            j = nums[i]
            self.chs[j][2] = new[i%l][0]
            self.chs[j][3] = new[i%l][1]
        
        if x != self.treeview.selection():
            self.treeview.selection_set(x)
        else:
            i = int(x[0])
            
            if not self.to_lock:
                for a, to in self.scalemax:
                    if self.chs[i][3] <= a:
                        break
                self.vmin_scale.configure(to=to)
                self.vmax_scale.configure(to=to)
            self.variables['vn'].set(self.chs[i][2])
            self.variables['vx'].set(self.chs[i][3])
            self.variables['sh'].set(bool(self.Hub.ch_show[i]))
            
        self.chs = self.chs
        self.Hub.calc_image()
        if hasattr(self.Hub.gui, 'g_on'):
            if self.Hub.gui.g_on.get():
                self.Hub.calc_sideview()
        
    
    def add_ch(self):
        Hub = self.Hub
        
        filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']),
                     ('All files', '*')]
        initialdir = Hub.gui.file_dir
        data_files = filedialog.askopenfilenames(parent=Hub.gui.palette, 
                                                 filetypes=filetypes, 
                                                 initialdir=initialdir, 
                                                 title='Add channels')
        if len(data_files) == 0:
            return
        
        data_files = list(data_files)
        for i, f in enumerate(data_files):
            f = f.replace('\\', '/')
            data_files[i] = f
        
        dat = [[d] for d in data_files]
        dc = Hub.data.load(dat, add=True)
        if dc == 0:
            return
        
        fix = [list(c[1]) for c in self.chs]
        c = self.auto_color(fix, dc)
        nm = []
        n = 0
        while len(nm) < dc:
            name = 'ch{0}'.format(n)
            if not name in self.getnames():
                nm += [name]
            n += 1
        
        chs = [[nm[i], c[i], 0, 65535] for i in range(dc)]
        
        idx, hist = Hub.hidx, Hub.history
        
        ntrash = len(hist) + idx + 1
        self.chs_trash[ntrash] = chs.copy()
        
        x = list(range(len(Hub.data.getchload()) - len(chs), len(Hub.data.getchload())))
        self.chs = self.chs + chs
        
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        hist += [[self, [self.del_channels, [x], self.add_channels, [x]]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else: 
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.add_channels(x, needload=False)
        mx = np.amax(self.Hub.frame[-dc:], axis=(1,2))
        for i in range(-1,-len(mx)-1,-1):
            self.chs[i][3] = mx[i]
        self.chs_trash[ntrash] = self.chs[-dc:].copy()
        self.chs = self.chs
        self.Hub.calc_image()
        
        
    def add_channels(self, x, needload=True):
        if needload:
            h = len(self.Hub.history) + self.Hub.hidx
            box = self.Hub.box
            chs = self.chs
            ch_show = self.Hub.ch_show
            ch_load = self.Hub.data.getchload()
            data = self.Hub.data.dat
            lens = [0]
            for d in data:
                lens += [len(d[1]) + lens[-1]]
            new_box, new_chs, new_show = [], [], []
            i, n, m = 0, 0, 0
            for f in range(len(lens)-1):
                l = True
                while i < lens[f+1]:
                    if ch_load[i]:
                        j = 1
                        while i+j < len(ch_load):
                            if not ch_load[i+j]:
                                break
                            j += 1
                        new_box += [box[n:n+j]]
                        new_chs += chs[n:n+j]
                        new_show += [ch_show[n:n+j]]
                        n += j
                        i += j
                    elif i in x:
                        j = 1
                        while (i + j in x) and (i + j < lens[f+1]):
                            j += 1
                        if l:
                            new = self.Hub.data.load_from_path(data[f][0])
                            if type(new) == type(None):
                                raise
                            l = False
                        new_box += [new[i-lens[f]:i+j-lens[f]]]
                        new_chs += self.chs_trash[h][m:m+j]
                        new_show += [np.ones([j], np.bool)]
                        m += j
                        i += j
                    else:
                        i += 1
            
            box = np.concatenate(new_box)
            chs = new_chs
            ch_show = np.concatenate(new_show)
            
            self.Hub.box = box
            self.chs = chs
            self.Hub.ch_show = ch_show
        
        ch_load = self.Hub.data.getchload()
        ch_load = np.array(ch_load)
        ch_load[x] = 1
        n = 0
        for d in self.Hub.data.dat:
            l = len(d[1])
            d[1] = tuple(ch_load[n:n+l])
            n += l
        
        self.Hub.calc_geometry()
        if hasattr(self.Hub.gui, 'g_on'):
            if self.Hub.gui.g_on.get():
                self.Hub.calc_sideview()
        
        self.refresh_tree()
        x=self.Hub.data.getchnum(x).tolist()
        self.treeview.selection_set(x)
        
    
    
    def del_ch(self):
        Hub = self.Hub
        x = self.treeview.selection()
        x = np.sort([int(i) for i in x]).tolist()
        ch_load = np.array(self.Hub.data.getchload())
        x = np.arange(len(ch_load))[ch_load==1][x].tolist()
        
        box = self.Hub.box
        dbox = np.zeros([0, *box[0].shape], dtype=box.dtype)
        dchs = []
        n = 0
        for i in range(len(ch_load)):
            if ch_load[i]:
                if i in x:
                    dbox = np.append(dbox, box[n:n+1], axis=0)
                    dchs += [self.chs[n].copy()]
                n += 1
        
        idx, hist = Hub.hidx, Hub.history
        self.chs_trash[len(hist) + idx + 1] = dchs
        
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        hist += [[self, [self.add_channels, [x], self.del_channels, [x]]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else: 
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.del_channels(x)
        
    
    def del_channels(self, x):
        box = self.Hub.box
        chs = self.chs
        ch_show = self.Hub.ch_show
        n = 0
        ch_load = self.Hub.data.getchload()
        for i, ch in enumerate(ch_load):
            if ch:
                if i in x:
                    box = np.append(box[:n], box[n+1:], axis=0)
                    chs = chs[:n] + chs[n+1:]
                    ch_show = np.append(ch_show[:n], ch_show[n+1:])
                else:
                    n += 1
        self.Hub.box = box
        self.chs = chs
        self.Hub.ch_show = ch_show
        
        ch_load = self.Hub.data.getchload()
        ch_load = np.array(ch_load)
        ch_load[x] = 0
        n = 0
        for d in self.Hub.data.dat:
            l = len(d[1])
            d[1] = tuple(ch_load[n:n+l])
            n += l
            
        self.Hub.calc_geometry()
        if hasattr(self.Hub.gui, 'g_on'):
            if self.Hub.gui.g_on.get():
                self.Hub.calc_sideview()
            
        select = np.array([int(s) for s in self.treeview.selection()])
        n = 0
        for i in range(len(ch_load)):
            if i in x:
                if n in select:
                    j = np.where(select==n)[0][0]
                    select = np.append(select[:j], select[j+1:])
                select[select>n] -= 1
            elif ch_load[i]:
                n += 1
        self.refresh_tree()
        x=list(select)
        self.treeview.selection_set(x)
        
    
    def undo(self, arg):
        arg[0](*arg[1])
        
    def redo(self, arg):
        arg[2](*arg[3])
        
    def reload(self, chs):
        Hub = self.Hub
        
        if hasattr(Hub, 'box'):
            box = Hub.box
            dc = len(box)
            if len(chs) != dc:
                c = self.auto_color([], dc)
                m, M = np.amin(box, axis=(1,2,3)), np.amax(box, axis=(1,2,3))
                chs = [['ch{0}'.format(i), c[i], m[i], M[i]] for i in range(dc)]
            else:
                for c in chs:
                    c[0] = str(c[0])
                    c[1] = [int(c[1][i])%256 for i in range(3)]
                    c[2], c[3] = int(c[2]), int(c[3])
        
        if self.chs == chs:
            return False
        self.chs = chs
        self.refresh_tree()
        return True
        
    
    def auto_color(self, fix, new, offset=120):
        if len(fix) > 0:
            a = self.bgr2hsl(fix)
            a = a[(a[:,1]>50)*(np.abs(a[:,2]-50)<25),0]
        else: a = []
        if len(a) == 0:
            b = np.linspace(offset, offset+360, new, endpoint=False)%360
        else:
            a = np.sort(a).astype(np.int)
            b = a[1:] - a[:-1]
            b = np.append(b, 360 - np.sum(b))
            c = np.ones(len(b), np.int)
            d = b/c
            for _ in range(new):
                m = np.argmax(d)
                c[m] += 1
                d[m] = b[m]/c[m]
            b = np.zeros(0)
            for i in range(0,len(a)-1):
                b = np.append(b, np.linspace(a[i],a[i+1],c[i],endpoint=False)[1:])
            b = np.append(b, np.linspace(a[-1],a[0]+360,c[-1],endpoint=False)[1:]%360)
        b = np.append(b[:,None], np.zeros([len(b),2]), axis=1)
        b[:,1] = 100
        b[:,2] = 50
        return self.hsl2bgr(b).tolist()
    
    
    def bgr2hsl(self, colors):
        colors = np.array(colors)
        if colors.ndim == 1:
            ndim = 1
            colors = colors[None]
        else: ndim = 2
        assert len(colors[0]) == 3
        m = np.argmin(colors, axis=1)
        M = np.argmax(colors, axis=1)
        a = m == M
        res = np.zeros(colors.shape)
        res[a, 2] = colors[a, m[a]]*100/255
        m, M = m[~a], M[~a]
        cM, cm = colors[~a,M], colors[~a,m]
        res[~a,0] = 60*(colors[~a,(m+1)%3] - colors[~a,(m-1)%3])/(cM - cm)\
                    + np.array([60, 300, 180])[m]
        res[~a,1] = 100*(cM - cm)/(255 - np.abs(cM + cm - 255))
        res[~a,2] = (cm + cM)*(10/51)
        
        if ndim == 1:
            res = res[0]
        
        return res
    
    
    def hsl2bgr(self, colors):
        colors = np.array(colors)
        if colors.ndim == 1:
            ndim = 1
            colors = colors[None]
        else: ndim = 2
        assert len(colors[0]) == 3
        a = colors[:,1]*(100 - abs(2*colors[:,2] - 100))*255/20000
        colors[:,2] *= 255/100
        res = np.zeros(colors.shape)
        b = a!=0
        res[~b] = colors[~b,2][:,None]
        colors = colors[b]
        res1 = res[b]
        a = a[b]
        M = colors[:,2] + a
        m = colors[:,2] - a
        n = m + (M-m)*(1 - np.abs(1 - (colors[:,0]%120)/60))
        res1[:,0] = m
        c = ((colors[:,0]//60)%2 == 0)
        res1[c,1] = n[c]
        res1[c,2] = M[c]
        res1[~c,1] = M[~c]
        res1[~c,2] = n[~c]
        a = (colors[:,0]//120).astype(np.int)
        c = np.arange(len(res1))
        res[b] = np.concatenate([res1[c,a%3][:,None], res1[c,(a+1)%3][:,None],
                                 res1[c,(a+2)%3][:,None]], axis=1)
        
        if ndim == 1:
            res = res[0]
        
        return np.round(res).astype(np.uint8)
        
    
    
        
        
