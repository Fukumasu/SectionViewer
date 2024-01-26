import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from .gui import Color_GUI
from ..tools import desolve_state, tk_from_array


class Channels_GUI(Color_GUI):
    def __init__(self, main):
        super().__init__(main)
            
        self.main = main
        self.obj_prev = self.obj.copy()
        
        self.vars = {'nm': tk.StringVar(),
                     'b' : tk.IntVar(),
                     'g' : tk.IntVar(),
                     'r' : tk.IntVar(),
                     'bs': tk.StringVar(),
                     'gs': tk.StringVar(),
                     'rs': tk.StringVar(),
                     'h' : tk.IntVar(),
                     's' : tk.IntVar(),
                     'l' : tk.IntVar(),
                     'hs': tk.StringVar(),
                     'ss': tk.StringVar(),
                     'ls': tk.StringVar(),
                     'n': tk.IntVar(),
                     'x': tk.IntVar(),
                     'ns': tk.StringVar(),
                     'xs': tk.StringVar(),
                     'sh': tk.IntVar()}
        
        self.vars['nm'].trace('w', self.nm_trace)
        self.vars['r'].trace('w', lambda *args: 
                             self.vars['rs'].set(str(self.vars['r'].get())))
        self.vars['g'].trace('w', lambda *args: 
                             self.vars['gs'].set(str(self.vars['g'].get())))
        self.vars['b'].trace('w', lambda *args: 
                             self.vars['bs'].set(str(self.vars['b'].get())))
        self.vars['h'].trace('w', lambda *args: 
                             self.vars['hs'].set(str(self.vars['h'].get()/10)))
        self.vars['s'].trace('w', lambda *args: 
                             self.vars['ss'].set(str(self.vars['s'].get()/10)))
        self.vars['l'].trace('w', lambda *args: 
                             self.vars['ls'].set(str(self.vars['l'].get()/10)))
        self.vars['n'].trace('w', lambda *args: 
                             self.vars['ns'].set(str(self.vars['n'].get())))
        self.vars['x'].trace('w', lambda *args: 
                             self.vars['xs'].set(str(self.vars['x'].get())))
        self.vars['sh'].trace('w', self.sh_trace)
        
        base_frame = ttk.Frame(main.dock_note)
        self.base_frame = base_frame
        main.dock_note.add(base_frame, text='Channels')
            
        sub_frame = ttk.Frame(base_frame)
        sub_frame.pack(pady=10)
        
        if hasattr(self.main, 'secv'):
            button_frame = ttk.Frame(sub_frame)
            button_frame.pack(side=tk.BOTTOM, anchor=tk.E, padx=10)
            button1 = ttk.Button(button_frame, text='Add', command=self.add)
            button1.pack(side=tk.LEFT)
            button2 = ttk.Button(button_frame, text='Delete', command=self.delete)
            button2.pack(side=tk.LEFT)
            self.button_dl = button2
        
        self.treeview = ttk.Treeview(sub_frame, height=7)
        self.treeview.column('#0', width=330, stretch=False)
        self.treeview.heading('#0', text='Channels', anchor=tk.W)
        bary = tk.Scrollbar(sub_frame, orient=tk.VERTICAL)
        bary.pack(side=tk.LEFT, fill=tk.Y)
        bary.config(command=self.treeview.yview)
        self.treeview.config(yscrollcommand=bary.set)
        self.treeview.pack(padx=10, pady=5)
        
        self.treeview.bind('<Button-1>', lambda e: self.treeview.selection_set()\
                           if not desolve_state(e.state)['Control'] else None)
        self.treeview.bind('<<TreeviewSelect>>', self.select)
        self.refresh_tree()
        
        control_frame = ttk.Frame(base_frame, relief='groove')
        self.control_frame = control_frame
        
        frame = ttk.Frame(control_frame)
        frame.pack(padx=20, pady=10, ipadx=5, ipady=5, fill=tk.X)
        self.entry_nm = ttk.Entry(frame, textvariable=self.vars['nm'], width=30)
        self.entry_nm.pack(side = tk.LEFT)
        self.checkbutton = ttk.Checkbutton(frame, variable=self.vars['sh'], 
                                           onvalue=1, offvalue=0, text='Show')
        self.checkbutton.pack(side=tk.RIGHT)
        
        color_note = ttk.Notebook(control_frame)
        color_note.pack(padx=10, pady=5, ipadx=5, ipady=5)
        
        rgb_frame = ttk.Frame(color_note)
        self.rgb_frame = rgb_frame
        
        ttk.Label(rgb_frame, text='  R:  ').grid(column=0, row=1)
        ttk.Label(rgb_frame, text='  G:  ').grid(column=0, row=2)
        ttk.Label(rgb_frame, text='  B:  ').grid(column=0, row=3)
        ttk.Scale(rgb_frame, length=210, variable=self.vars['r'],
                  from_=0, to=255, orient='horizontal',
                  command=self.rgb_scale(2)).grid(column=1, row=1, pady=7)
        ttk.Scale(rgb_frame, length=210, variable=self.vars['g'],
                  from_=0, to=255, orient='horizontal',
                  command=self.rgb_scale(1)).grid(column=1, row=2, pady=7)
        ttk.Scale(rgb_frame, length=210, variable=self.vars['b'],
                  from_=0, to=255, orient='horizontal',
                  command=self.rgb_scale(0)).grid(column=1, row=3, pady=7)
        self.entry_r = ttk.Entry(rgb_frame, textvariable=self.vars['rs'], width=5)
        self.entry_r.grid(column=2, row=1, padx=3)
        self.entry_g = ttk.Entry(rgb_frame, textvariable=self.vars['gs'], width=5)
        self.entry_g.grid(column=2, row=2, padx=3)
        self.entry_b = ttk.Entry(rgb_frame, textvariable=self.vars['bs'], width=5)
        self.entry_b.grid(column=2, row=3, padx=3)
        preset_canvas = tk.Canvas(rgb_frame, width=160, height=20, cursor='hand2')
        self.preset_id = preset_canvas.create_image(0, 0, anchor='nw', image=self.preset_image)
        preset_canvas.grid(column=0, row=4, columnspan=2, padx=20, sticky=tk.SW)
        preset_canvas.bind('<Button-1>', self.preset)
        auto_button = ttk.Button(rgb_frame, text='Auto', command=self.auto_color)
        auto_button.grid(column=1, row=4, columnspan=2, pady=2, sticky=tk.E)
        color_note.add(rgb_frame, text='RGB')
        
        hsl_frame = ttk.Frame(color_note)
        self.hsl_frame = hsl_frame
        
        ttk.Label(hsl_frame, text=' H:  ').grid(column=0, row=1)
        ttk.Label(hsl_frame, text=' S:  ').grid(column=0, row=2)
        ttk.Label(hsl_frame, text=' L:  ').grid(column=0, row=3)
        ttk.Scale(hsl_frame, length=210, variable=self.vars['h'], 
                  from_=0, to=3599, orient='horizontal',
                  command=self.hsl_scale(0)).grid(column=1, row=1, pady=7)
        ttk.Scale(hsl_frame, length=210, variable=self.vars['s'], 
                  from_=0, to=1000, orient='horizontal',
                  command=self.hsl_scale(1)).grid(column=1, row=2, pady=7)
        ttk.Scale(hsl_frame, length=210, variable=self.vars['l'], 
                  from_=0, to=1000, orient='horizontal',
                  command=self.hsl_scale(2)).grid(column=1, row=3, pady=7)
        self.entry_h = ttk.Entry(hsl_frame, textvariable=self.vars['hs'], width=5)
        self.entry_h.grid(column=2, row=1, padx=3)
        self.entry_s = ttk.Entry(hsl_frame, textvariable=self.vars['ss'], width=5)
        self.entry_s.grid(column=2, row=2, padx=3)
        self.entry_l = ttk.Entry(hsl_frame, textvariable=self.vars['ls'], width=5)
        self.entry_l.grid(column=2, row=3, padx=3)
        preset_canvas = tk.Canvas(hsl_frame, width=160, height=20, cursor='hand2')
        preset_canvas.create_image(0, 0, anchor='nw', image=self.preset_image)
        preset_canvas.grid(column=0, row=4, columnspan=2, padx=20, sticky=tk.SW)
        preset_canvas.bind('<Button-1>', self.preset)
        auto_button = ttk.Button(hsl_frame, text='Auto', command=self.auto_color)
        auto_button.grid(column=1, row=4, columnspan=2, pady=2, sticky=tk.E)
        color_note.add(hsl_frame, text='HSL')
        
        self.scalemax = [[224,255],[896,1023],[3584,4095],[14336,16383],[57344,65535]]
        
        bottom_frame = ttk.Frame(control_frame)
        self.bottom_frame = bottom_frame
        
        bottom_frame.pack(padx=20, pady=10, ipadx=5, ipady=5, fill=tk.X)
        ttk.Label(bottom_frame, text=' vmin: ').grid(column=0, row=0)
        ttk.Label(bottom_frame, text=' vmax: ').grid(column=0, row=1)
        self.vmin_scale = ttk.Scale(bottom_frame, length=210, from_=0,
                                    variable=self.vars['n'],
                                    command=self.vrg_scale(0),
                                    orient='horizontal')
        self.vmin_scale.grid(column=1, row=0, pady=7)
        self.vmax_scale = ttk.Scale(bottom_frame, length=210, from_=0,
                                    variable=self.vars['x'],
                                    command=self.vrg_scale(1),
                                    orient='horizontal')
        self.vmax_scale.grid(column=1, row=1, pady=7)
        self.entry_n = ttk.Entry(bottom_frame, textvariable=self.vars['ns'], width=5)
        self.entry_n.grid(column=2, row=0, padx=3)
        self.entry_x = ttk.Entry(bottom_frame, textvariable=self.vars['xs'], width=5)
        self.entry_x.grid(column=2, row=1, padx=3)
        
        self.entry_r.bind('<Return>', self.rgb_enter(2))
        self.entry_r.bind('<Button-1>', self.rgb_enter(2))
        self.entry_r.bind('<FocusOut>', self.rgb_enter(2))
        self.entry_g.bind('<Return>', self.rgb_enter(1))
        self.entry_g.bind('<Button-1>', self.rgb_enter(1))
        self.entry_g.bind('<FocusOut>', self.rgb_enter(1))
        self.entry_b.bind('<Return>', self.rgb_enter(0))
        self.entry_b.bind('<Button-1>', self.rgb_enter(0))
        self.entry_b.bind('<FocusOut>', self.rgb_enter(0))
        self.entry_h.bind('<Return>', self.hsl_enter(0))
        self.entry_h.bind('<Button-1>', self.hsl_enter(0))
        self.entry_h.bind('<FocusOut>', self.hsl_enter(0))
        self.entry_s.bind('<Return>', self.hsl_enter(1))
        self.entry_s.bind('<Button-1>', self.hsl_enter(1))
        self.entry_s.bind('<FocusOut>', self.hsl_enter(1))
        self.entry_l.bind('<Return>', self.hsl_enter(2))
        self.entry_l.bind('<Button-1>', self.hsl_enter(2))
        self.entry_l.bind('<FocusOut>', self.hsl_enter(2))
        self.entry_n.bind('<Return>', self.vrg_enter(0))
        self.entry_n.bind('<Button-1>', self.vrg_enter(0))
        self.entry_n.bind('<FocusOut>', self.vrg_enter(0))
        self.entry_x.bind('<Return>', self.vrg_enter(1))
        self.entry_x.bind('<Button-1>', self.vrg_enter(1))
        self.entry_x.bind('<FocusOut>', self.vrg_enter(1))
        
        def release(*args):
            vmax = self.vars['x'].get()
            for a, to in self.scalemax:
                if vmax <= a:
                    break
            self.vmin_scale.configure(to=to)
            self.vmax_scale.configure(to=to)
        self.vmax_scale.bind('<ButtonRelease-1>', release)
        self.entry_x.bind('<FocusOut>', release)
        
        self.treeview.selection_set()
        
    def __getattribute__(self, name):
        if name == 'obj':
            return self.main.channels
        return super().__getattribute__(name)
    
    def refresh_tree(self):
        names = self.obj.getnames()
        colors = np.array(self.obj.getcolors())
        self.treeview.delete(*self.treeview.get_children())
        sort = np.argsort(names)
        im = np.zeros([8,8,3], np.uint8)
        self.icons = [0]*len(sort)
        for i in sort:
            im[1:-1,1:-1] = colors[i]
            self.icons[i] = tk_from_array(im)
            self.treeview.insert('', 'end', str(i), text=' '+names[i], image=self.icons[i])
        self.treeview.selection_set()
            
    def settings(self):
        pass
    
    def set_vars(self, i):
        name, color, vrange = self.obj[i]
        self.vars['nm'].set(name)
        self.vars['r'].set(color[2])
        self.vars['g'].set(color[1])
        self.vars['b'].set(color[0])
        self.vars['h'].set(int(color['hsl'][0]*10))
        self.vars['s'].set(int(color['hsl'][1]*10))
        self.vars['l'].set(int(color['hsl'][2]*10))
        self.vars['n'].set(vrange[0])
        self.vars['x'].set(vrange[1])
        self.vars['sh'].set(self.main.display['shown_channels'][i])
    
    def select(self, event):
        self.main.master.focus_set()
        selection = self.treeview.selection()
        
        if len(selection) == 0:
            self.control_frame.pack_forget()
            if hasattr(self, 'button_dl'):
                self.button_dl['state'] = tk.DISABLED
            return
        else:
            self.control_frame.pack(padx=10, pady=10, fill=tk.X)
        
        if hasattr(self, 'button_dl'):
            self.button_dl['state'] = tk.NORMAL
        
        selec = [int(i) for i in selection]
        i = selec[0]
        self.set_vars(i)
        vmax = self.obj[i][2][1]
        for a, to in self.scalemax:
            if vmax <= a:
                break
        self.vmin_scale.configure(to=to)
        self.vmax_scale.configure(to=to)
        
        self.checkbutton['state'] = tk.NORMAL
        
        if len(selection) == 1:
            self.entry_nm['state'] = tk.NORMAL
        else:
            self.entry_nm['state'] = tk.DISABLED
    
    def vrg_scale(self, num):
        vn = ['ns', 'xs'][num]
        mnx = [min, max][num]
        one = [-1, 1][num]
        def func(*args):
            x = self.treeview.selection()
            if len(x) == 0:
                return
            i = int(x[0])
            if self.vars['sh'].get() != 1:
                c = self.obj[i][2][num]
                self.vars[vn[0]].set(c)
                return
            c = mnx(self.obj[i][2][1 - num] + one, 
                    self.vars[vn[0]].get())
            self.vars[vn[0]].set(c)
            c = self.vars[vn[0]].get()
            for i in x:
                i = int(i)
                self.obj[i][2][num] = c
        return func
    
    def vrg_enter(self, num):
        vn = ['ns', 'xs'][num]
        def func(*args):
            x = self.treeview.selection()
            if len(x) == 0:
                return
            if self.vars['sh'].get() != 1:
                i = int(x[0])
                c = self.obj[i][2][num]
                self.vars[vn].set(str(c))
                return
            try:
                c = self.vars[vn].get()
                if c == '':
                    c = 0
                c = int(c)
                self.vars[vn[0]].set(c)
                for i in x:
                    i = int(i)
                    self.obj[i][2][num] = c
            except Exception:
                i = int(x[0])
                self.vars[vn[0]].set(self.obj[i][2][num])
        return func
    
    def sh_trace(self, *args):
        x = self.treeview.selection()
        if len(x) == 0:
            return
        selec = [int(i) for i in x]
        sh = self.vars['sh'].get()
        if sh not in (0, 1):
            return
        sh = bool(sh)
        ch_show = list(self.main.display['shown_channels'])
        for i in selec:
            ch_show[i] = sh
        
        self.main.display['shown_channels'] = tuple(ch_show)
        
        ch_show = np.array(self.main.display['shown_channels'])[selec]
        if ch_show.all():
            self.vars['sh'].set(1)
            for frame in [self.rgb_frame, self.hsl_frame, self.bottom_frame]:
                for w in frame.grid_slaves():
                    s = str(w).split('!')[-1][:5]
                    if s in ['butto', 'entry', 'label']:
                        w['state'] = tk.NORMAL
                    if s == 'canva':
                        w.config(cursor = 'hand2')
                        w.itemconfig(self.preset_id, image=self.preset_image)
        else:
            if ch_show.any():
                self.vars['sh'].set(-1)
            else:
                self.vars['sh'].set(0)
            for frame in [self.rgb_frame, self.hsl_frame, self.bottom_frame]:
                for w in frame.grid_slaves():
                    s = str(w).split('!')[-1][:5]
                    if s in ['butto', 'entry', 'label']:
                        w['state'] = tk.DISABLED
                    if s == 'canva':
                        w.config(cursor = 'arrow')
                        w.itemconfig(self.preset_id, image=self.preset_off)
        if hasattr(self.main, 'reset_button'):
            if not ch_show.any():
                self.main.reset_button['state'] = tk.DISABLED
            else:
                self.main.reset_button['state'] = tk.NORMAL
        
    def add(self):
        main = self.main
        
        filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']),
                     ('All files', '*')]
        initialdir = main.file_dir
        add_paths = filedialog.askopenfilenames(parent = main.master, 
                                                filetypes = filetypes, 
                                                initialdir = initialdir, 
                                                title = 'Adding data files')
        if len(add_paths) == 0:
            return
        
        add_paths = list(add_paths)
        for i, f in enumerate(add_paths):
            f = f.replace('\\', '/')
            add_paths[i] = f
        
        paths = main.files['paths']
        for p in add_paths:
            if p in paths:
                message = 'File \n{0} \nis already loaded.'.format(p)
                messagebox.showinfo(title = 'Same data file', message = message)
                return
        main.files.add(add_paths)
        
    def delete(self):
        main = self.main
        
        x = self.treeview.selection()
        selec = [int(i) for i in x]
        file_ids = []
        ch_ids = []
        m = 0
        for i, n in enumerate(main.files['channel_nums']):
            file_ids += [i] * n
            ch_ids += [[j for j in range(m, m + n)]]
            m += n
        file_ids = np.sort(np.unique(np.array(file_ids)[selec]))
        ch_ids = [ch_ids[i] for i in file_ids]
        for c in ch_ids[1:]:
            ch_ids[0] += c
        ch_ids = [str(c) for c in ch_ids[0]]
        self.treeview.selection_set(ch_ids)
        
        if len(file_ids) == len(self.main.files['paths']):
            message = 'Deleting all data is not allowed:\n'
            for i in file_ids:
                path = main.files['paths'][i]
                message = message + '- ' + path + '\n'
            if len(file_ids) == 1:
                title = 'Canceled deleting file'
            else:
                title = 'Canceled deleting files'
            messagebox.showerror(title = title, 
                                 message = message,
                                 parent = main.master)
            return
        if len(file_ids) == 1:
            message = 'Are you sure you want to delete data from the following file?\n'
            title = 'Deleting 1 file'
        else:
            message = 'Are you sure you want to delete data from the following files?\n'
            title = 'Deleting {0} files'.format(len(file_ids))
        for i in file_ids:
            path = main.files['paths'][i]
            message = message + '- ' + path + '\n'
        ans = messagebox.askyesno(title = title,
                                  message = message,
                                  parent = main.master)
        if not ans:
            return
        main.files.delete(file_ids)
        
    def update(self, loc):
        obj = self.obj
        selection = self.treeview.selection()
        im = np.zeros([8,8,3], np.uint8)
        loc = [l for l in loc if l[0] == 'channels']
        if len(obj) == len(self.treeview.get_children()):
            if len(self.treeview.get_children()) > 0:
                for l in loc:
                    i = l[1]
                    name, color, vrange = obj[i]
                    im[1:-1, 1:-1] = list(color)
                    self.icons[i] = tk_from_array(im)
                    self.treeview.item(str(i), text=' '+name, image=self.icons[i])
                    if len(selection) == 0:
                        continue
                    if i != int(selection[0]):
                        continue
                    self.set_vars(i)
        else:
            self.refresh_tree()
            new_selection = []
            for i, ch in enumerate(obj):
                if ch not in self.obj_prev:
                    new_selection += [str(i)]
            self.treeview.selection_set(new_selection)
        self.obj_prev = obj.copy()