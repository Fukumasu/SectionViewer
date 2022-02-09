import traceback

import cv2
import numpy as np
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from . import utils as ut


class Snapshots:
    def __init__(self, Hub):
        self.Hub = Hub
        self.snapshots= Hub.snapshots
        
        self.use_pos = True
        self.use_chs = True
        self.use_pts = True
        
        self.name_var = tk.StringVar()
        def set_nm(new):
            self.name_var.trace_vdelete('w', self.name_var.trace_id)
            self.name_var.set(new)
            self.name_var.trace_id = self.name_var.trace('w', self.ss_name)
        self.name_var.trace_id = self.name_var.trace('w', self.ss_name)
        self.name_var.set_nm = set_nm
        self.pos_on = tk.BooleanVar()
        self.chs_on = tk.BooleanVar()
        self.pts_on = tk.BooleanVar()
        
        # settings
        
        frame0 = ttk.Frame(Hub.gui.dock_note)
        self.set_frame = frame0
        Hub.gui.dock_note.add(frame0, text='Snapshots')
        
        frame1 = ttk.Frame(frame0)
        frame1.pack(pady=10)
        
        self.treeview = ttk.Treeview(frame1, height=6)
        self.treeview.column('#0', width=330, stretch=False)
        self.treeview.heading('#0', text='Saved configurations', anchor=tk.W)
    
        bary = tk.Scrollbar(frame1, orient=tk.VERTICAL)
        bary.pack(side=tk.LEFT, fill=tk.Y)
        bary.config(command=self.treeview.yview)
        self.treeview.config(yscrollcommand=bary.set)
        self.treeview.pack(padx=10, pady=5)
        
        self.treeview.bind('<Button-1>', lambda e: self.treeview.selection_set()\
                          if e.state//Hub.gui.flags[3]%2!=1 else None)
        self.treeview.bind('<<TreeviewSelect>>', self.ss_select)
        self.treeview.bind('<Control-a>', lambda event:
                           self.treeview.selection_set(self.treeview.get_children()))
        self.selected = []
        
        for i in np.argsort(self.names()):
            self.treeview.insert('', 'end', str(i), text=' '+self.snapshots[i]['name'])
            
        frame3 = ttk.Frame(frame0)
        frame3.pack(padx=10, pady=5, fill=tk.X)
        
        button1 = ttk.Button(frame3, text='Delete', command=self.del_ss)
        button1.pack(side=tk.RIGHT, padx=5)
        self.button_dl = button1
        button2 = ttk.Button(frame3, text='Snap', command=self.add_ss)
        button2.pack(side=tk.RIGHT, padx=5)
        
        self.pos_on.set(self.use_pos)
        self.chs_on.set(self.use_chs)
        self.pts_on.set(self.use_pts)
        
        def chk():
            self.use_pos = self.pos_on.get()
            self.use_chs = self.chs_on.get()
            self.use_pts = self.pts_on.get()
            if (self.pos_on.get() or self.chs_on.get() or self.pts_on.get())\
                and len(self.treeview.selection()) == 1:
                self.button_ov['state'] = tk.ACTIVE
                self.button_rs['state'] = tk.ACTIVE
            else:
                self.button_ov['state'] = tk.DISABLED
                self.button_rs['state'] = tk.DISABLED
        
        self.pts_chk = ttk.Checkbutton(frame3, variable=self.pts_on, text='Points',
                                       command=chk)
        self.pts_chk.pack(side=tk.RIGHT, padx=5)
        self.chs_chk = ttk.Checkbutton(frame3, variable=self.chs_on, text='Channels',
                                       command=chk)
        self.chs_chk.pack(side=tk.RIGHT, padx=5)
        self.pos_chk = ttk.Checkbutton(frame3, variable=self.pos_on, text='Position',
                                       command=chk)
        self.pos_chk.pack(side=tk.RIGHT, padx=5)
        
        
        
        frame2 = ttk.Frame(frame0, relief='groove')
        self.frame2 = frame2
        
        frame4 = ttk.Frame(frame2)
        frame4.pack(padx=10, pady=10, fill=tk.X)
        button3 = ttk.Button(frame4, text='Override', command=self.override_ss)
        button3.pack(side=tk.RIGHT, padx=5)
        self.button_ov = button3
        button4 = ttk.Button(frame4, text='Restore', command=self.restore_ss)
        button4.pack(side=tk.RIGHT, padx=5)
        self.button_rs = button4
        
        self.entry_nm = ttk.Entry(frame4, textvariable=self.name_var, width=30)
        self.entry_nm.pack(side=tk.LEFT, padx=5)
        
        note = ttk.Notebook(frame2)
        note.pack(padx=10, pady=5, ipadx=5, ipady=5)
        
        self.im_size = (250, 350)
        
        prev_frame = ttk.Frame(note)
        self.canvas1 = tk.Canvas(prev_frame, width=self.im_size[1], height=self.im_size[0])
        self.canvas1.pack()
        note.add(prev_frame, text='Preview')
        
        guide_frame = ttk.Frame(note)
        self.canvas2 = tk.Canvas(guide_frame, width=self.im_size[1], height=self.im_size[0])
        self.canvas2.pack()
        note.add(guide_frame, text='Guide')
        
        self.im1_back = self.canvas1.create_rectangle(0,0,self.im_size[1],self.im_size[0], width=0)
        self.im1_id = self.canvas1.create_image(self.im_size[1]//2, self.im_size[0]//2)
        self.im2_id = self.canvas2.create_image(self.im_size[1]//2, self.im_size[0]//2)
        
    
    def __getattr__(self, name):
        if name == 'val':
            return object.__getattribute__(self, 'snapshots')
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == 'val':
            self.snapshots = val
        else:
            object.__setattr__(self, name, val)
      
        
    def names(self):
        return [ss['name'] for ss in self.snapshots]
    
    
    def settings(self):
        gui = self.Hub.gui
        if len(gui.dock_note.tabs()) < 2:
            return
        gui.dock_note.select(gui.dock_note.tabs()[3])
        self.refresh_tree()
        self.treeview.selection_set(self.selected)
            
            
    def refresh_tree(self):
        self.treeview.delete(*self.treeview.get_children())
        for i in np.argsort(self.names()):
            self.treeview.insert('', 'end', str(i), text=' '+self.snapshots[i]['name'])
        self.treeview.selection_set()
    
    
    def ss_select(self, event):
        selection = self.treeview.selection()
        self.selected = selection
        
        if len(selection) == 0:
            self.button_dl['state'] = tk.DISABLED
            self.pos_chk['state'] = tk.ACTIVE
            self.chs_chk['state'] = tk.ACTIVE
            self.pts_chk['state'] = tk.ACTIVE
            self.frame2.pack_forget()
            return
        elif len(selection) == 1:
            self.button_dl['state'] = tk.ACTIVE
            self.pos_chk['state'] = tk.ACTIVE
            self.chs_chk['state'] = tk.ACTIVE
            self.pts_chk['state'] = tk.ACTIVE
            self.pos_on.set(self.use_pos)
            self.chs_on.set(self.use_chs)
            self.pts_on.set(self.use_pts)
            if (self.use_pos or self.use_chs or self.use_pts):
                self.button_ov['state'] = tk.ACTIVE
                self.button_rs['state'] = tk.ACTIVE
            else:
                self.button_ov['state'] = tk.DISABLED
                self.button_rs['state'] = tk.DISABLED
            self.frame2.pack(padx=10, pady=5, fill=tk.X)
        else:
            if str(self.pos_chk['state']) == 'active':
                self.use_pos = self.pos_on.get()
                self.use_chs = self.chs_on.get()
                self.use_pts = self.pts_on.get()
                self.pos_on.set(False)
                self.chs_on.set(False)
                self.pts_on.set(True)
                self.pos_chk['state'] = tk.DISABLED
                self.chs_chk['state'] = tk.DISABLED
                self.pts_chk['state'] = tk.DISABLED
            self.button_dl['state'] = tk.ACTIVE
            self.button_ov['state'] = tk.ACTIVE
            self.button_rs['state'] = tk.ACTIVE
            self.frame2.pack(padx=10, pady=5, ipadx=5, ipady=5, fill=tk.X)
        
        secv = self.snapshots[int(self.treeview.selection()[0])]
        self.name_var.set_nm(secv['name'])
        im1 = self.preview_im(secv)
        im1 = np.append(im1[:,:,2::-1], im1[:,:,3:], axis=2)
        self.im1 = ImageTk.PhotoImage(Image.fromarray(im1))
        l1, l2, h, w = *self.im_size, *im1.shape[:2]
        self.canvas1.coords(self.im1_back, l2//2 - w//2, l1//2 - h//2, 
                            l2//2 + (w+1)//2, l1//2 + (h+1)//2)
        self.canvas1.itemconfig(self.im1_id, image=self.im1)
        im2 = self.preview_guide(secv)
        self.im2 = ImageTk.PhotoImage(Image.fromarray(im2[:,:,::-1]))
        self.canvas2.itemconfig(self.im2_id, image=self.im2)
        
    
    def ss_name(self, a, b, c):
        name = self.name_var.get()
        
        x = self.treeview.selection()
        if len(x) > 1:
            return None
        i = int(x[0])
        
        old = self.snapshots[i]['name']
        new = name
        
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
            self.name_var.set_nm(new)
        self.snapshots[int(x[0])]['name'] = new
    
    
    def add_ss(self):
        Hub = self.Hub
        
        secv = {}
        
        data = Hub.data.dat
        files = [d[0] for d in data]
        ch_load = [d[1] for d in data]
        data = []
        for f, c in zip(files, ch_load):
            if np.array(c).any():
                data += [[f, c]]
        data = tuple(data)
        secv['data'] = data
        
        secv['geometry'] = Hub.geometry.geo.copy()
        
        pos = Hub.position.asarray()
        pos[:,0] /= Hub.ratio
        pos[0] += np.array(Hub.box.shape[1:])//2
        secv['position'] = pos.tolist()
        
        channels = [[c[0], [c[1][0], c[1][1], c[1][2]], c[2], c[3]] for c in Hub.channels.chs]
        secv['channels'] = channels
        
        points = [[p[0], [p[1][0], p[1][1], p[1][2]], [p[2][0], p[2][1], p[2][2]]] for p in Hub.points.pts]
        secv['points'] = points
        
        names = self.names()
        nm = 'cf0'
        i = 1
        while nm in names:
            nm = 'cf{0}'.format(i)
            i += 1
        secv['name'] = nm
        
        idx, hist = Hub.hidx, Hub.history
        
        x = [len(self.snapshots)]
        
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        hist += [[self, [self.del_snapshots, [x], self.add_snapshots, [x, [secv]]]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else: 
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.add_snapshots(x, [secv])
        
        
    def add_snapshots(self, x, ss):
        for s, i in zip(ss,x):
            self.snapshots = self.snapshots[:i] + [s] + self.snapshots[i:]
        
        self.refresh_tree()
        self.selected = x
        self.treeview.selection_set(x)
        
    
    def del_ss(self):
        Hub = self.Hub
        x = self.treeview.selection()
        x = np.sort([int(i) for i in x]).tolist()
        ss = [self.snapshots[i] for i in x]
        
        hist, idx = Hub.history, Hub.hidx
        
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        hist += [[self, [self.add_snapshots, [x, ss], self.del_snapshots, [x]]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else:
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.del_snapshots(x)
        
        
    def del_snapshots(self, x):
        for i in x[::-1]:
            self.snapshots = self.snapshots[:i] + self.snapshots[i+1:]
        
        select = np.array([int(s) for s in self.treeview.selection()])
        for i in x[::-1]:
            if i in select:
                j = np.where(select==i)[0][0]
                select = np.append(select[:j], select[j+1:])
            select[select>i] -= 1
            
        self.refresh_tree()
        x = list(select)
        self.selected = x
        self.treeview.selection_set(x)

    
    def override_ss(self):
        Hub = self.Hub
        
        select = self.treeview.selection()
        x = []
        old = []
        new = []
        for s in select:
            i = int(s)
            x += [i]
            
            old += [self.snapshots[i]]
            new += [{}]
            
            new[-1]['name'] = old[-1]['name']
            
            if self.pos_on.get():
                new[-1]['geometry'] = Hub.geometry.geo.copy()
                pos = Hub.position.asarray()
                pos[:,0] /= Hub.ratio
                pos[0] += np.array(Hub.box.shape[1:])//2
                new[-1]['position'] = pos.tolist()
            else:
                new[-1]['geometry'] = old[-1]['geometry'].copy()
                new[-1]['position'] = np.array(old[-1]['position']).tolist()
            
            if self.chs_on.get():
                data = Hub.data.dat
                files = [d[0] for d in data]
                ch_load = [d[1] for d in data]
                data = []
                for f, c in zip(files, ch_load):
                    if np.array(c).any():
                        data += [[f, c]]
                data = tuple(data)
                new[-1]['data'] = data
                channels = [[c[0], [c[1][0], c[1][1], c[1][2]],
                             c[2], c[3]] for c in Hub.channels.chs]
                new[-1]['channels'] = channels
            else:
                new[-1]['data'] = old[-1]['data']
                channels = [[c[0], [c[1][0], c[1][1], c[1][2]],
                             c[2], c[3]] for c in old[-1]['channels']]
                new[-1]['channels'] = channels
                
            if self.pts_on.get():
                points = [[p[0], [p[1][0], p[1][1], p[1][2]], 
                           [p[2][0], p[2][1], p[2][2]]] for p in Hub.points.pts]
                new[-1]['points'] = points
            else:
                points = [[p[0], [p[1][0], p[1][1], p[1][2]], 
                           [p[2][0], p[2][1], p[2][2]]] for p in old[-1]['points']]
                new[-1]['points'] = points
            
        hist, idx = Hub.history, Hub.hidx
            
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        hist += [[self, [self.change_snapshot, [x, old], self.change_snapshot, [x, new]]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else: 
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
        
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.change_snapshot(x, new)
        
        
    def change_snapshot(self, x, secvs):
        for i, secv in zip(x, secvs):
            self.snapshots[i] = secv
        self.pre_selection = []
        self.selected = [str(x[0])]
        self.treeview.selection_set(str(x[0]))


    def restore_ss(self):
        Hub = self.Hub
        select = self.treeview.selection()
        if len(select) == 1:
            secv = self.snapshots[int(select[0])]
            try:
                dat = secv['data']
                geo = secv['geometry'].copy()
                pos = np.array(secv['position']).tolist()
                chs = [[c[0], [c[1][0], c[1][1], c[1][2]],
                        c[2], c[3]] for c in secv['channels']]
                pts = [[p[0], [p[1][0], p[1][1], p[1][2]], 
                       [p[2][0], p[2][1], p[2][2]]] for p in secv['points']]
            except Exception as e:
                messagebox.showerror('Error', traceback.format_exception_only(type(e), e)[0],
                                     parent=Hub.gui.palette)
                return
        else:
            pts = []
            for s in select:
                pts += [[p[0], [p[1][0], p[1][1], p[1][2]], 
                       [p[2][0], p[2][1], p[2][2]]] for p in self.snapshots[int(s)]['points']]
                
        typ, old, new = [], [], []
        
        a, b = [], []
        if self.pos_on.get():
            a += [geo, pos]
            b += [Hub.geometry, Hub.position]
        if self.chs_on.get():
            a = [dat] + a + [chs]
            b = [Hub.data] + b + [Hub.channels]
        if self.pts_on.get():
            a += [pts]
            b += [Hub.points]
        
        ul = Hub.gui.upperleft
        iw0, ih0 = Hub.geometry['im_size']
        try:
            for v, m in zip(a, b):
                old += [m.val]
                if m.reload(v): 
                    new += [m.val]
                    typ += [m]
                else: del old[-1]
        except Exception as e:
            messagebox.showerror('Error', traceback.format_exception_only(type(e), e)[0],
                                 parent=Hub.gui.palette)
            return None
        
        if len(new) > 0:
            Hub = self.Hub
            idx, hist = Hub.hidx, Hub.history
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.jump, [typ, old], self.jump, [typ, new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
                
            gui = Hub.gui
            gui.edit_menu.entryconfig('Undo', state='normal')
            gui.edit_menu.entryconfig('Redo', state='disable')
            gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
            
            iw1, ih1 = self.Hub.geometry['im_size']
            self.Hub.gui.upperleft = (ul[0]-iw0//2+iw1//2, ul[1]-ih0//2+ih1//2)
            
            Hub.calc_geometry()
            if Hub.gui.d_on.get():
                if Hub.gui.guide_mode == 'guide':
                    Hub.calc_guide()
                elif Hub.gui.guide_mode == 'sideview':
                    Hub.calc_sideview()
            for cl in [Hub.channels, Hub.points]:
                names = cl.getnames()
                colors = np.array(cl.getcolors())
                cl.treeview.delete(*cl.treeview.get_children())
                sort = np.argsort(cl.getnames())
                im = np.zeros([8,8,3], np.uint8)
                cl.icons = [0]*len(sort)
                for i in sort:
                    im[1:-1,1:-1] = colors[i]
                    cl.icons[i] = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
                    cl.treeview.insert('', 'end', str(i), text=' '+names[i], image=cl.icons[i])
                cl.treeview.selection_set()
    
    def jump(self, typ, new):
        ul = self.Hub.gui.upperleft
        iw0, ih0 = self.Hub.geometry['im_size']
        for t, n in zip(typ, new):
            t.val = n
        iw1, ih1 = self.Hub.geometry['im_size']
        self.Hub.gui.upperleft = (ul[0]-iw0//2+iw1//2, ul[1]-ih0//2+ih1//2)
        self.Hub.calc_geometry()
        if self.Hub.gui.d_on.get():
            if self.Hub.gui.guide_mode == 'guide':
                self.Hub.calc_guide()
            elif self.Hub.gui.guide_mode == 'sideview':
                self.Hub.calc_sideview()
        
        for cl in [self.Hub.channels, self.Hub.points]:
            cl.refresh_tree()
    
    
    def preview_im(self, secv):
        Hub = self.Hub
        
        geo = secv['geometry']
        xy_rs, z_rs = geo['res_xy'], geo['res_z']
        if None in [xy_rs, z_rs]:
            ratio = 1.
        else:
            ratio = z_rs / xy_rs
        
        frame = np.empty([len(Hub.box), *geo['im_size'][::-1]], np.uint16)
        
        exp_rate = geo['exp_rate']
        bar_len = geo['bar_len']
        
        lpx = int(bar_len/xy_rs*exp_rate) if xy_rs != None else 0
        
        box = Hub.box
        dc, dz, dy, dx = box.shape
        pos = secv['position']
        pos = np.float64(pos)
        pos[0] -= np.array([dz, dy, dx])//2
        pos[:,0] *= ratio
        pos[2] /= np.linalg.norm(pos[2])
        pos[1] = pos[1] - pos[2]*np.inner(pos[1], pos[2])
        pos[1] /= np.linalg.norm(pos[1])
        op, ny, nx = pos.copy()
        nz = -np.cross(ny, nx)
        
        pos[:,0] /= ratio
        nz[0] /= ratio
        pos[0] += np.array([dz, dy, dx])//2
        pos[1:] /= exp_rate
        nz /= exp_rate
        
        if Hub.thickness == 1:
            if not ut.calc_section(box, pos, frame, np.array(frame[0].shape)//2,
                                   np.arange(len(Hub.lut))[Hub.ch_show]):
                return False
        elif Hub.thickness <= 10:
            start = -(Hub.thickness//2)
            stop = start + Hub.thickness
            if not ut.stack_section(box, pos, nz, start, stop,
                                    frame, np.array(frame[0].shape)//2,
                                    np.arange(len(Hub.lut))[Hub.ch_show]):
                return False
        else:
            start = -(Hub.thickness//2)
            stop = start + Hub.thickness
            if not ut.fast_stack(box, pos, nz, start, stop,
                                 frame, np.array(frame[0].shape)//2,
                                 np.arange(len(Hub.lut))[Hub.ch_show]):
                return False
        
        gui = Hub.gui
        
        chs = secv['channels']
        colors = np.array([c[1] for c in chs], dtype=np.uint8)
        vrange = np.array([c[2:4] for c in chs])
        lut = np.arange(65536)[None]
        diff = vrange[:,1] - vrange[:,0]
        lut = ((1/diff[:,None])*(lut - vrange[:,:1]))
        lut[lut<1/255] = 1/255
        lut[lut>1] = 1
        im = np.empty([*frame.shape[1:], 4], np.uint8)
        if gui.white.get():
            ut.calc_bgr_w(frame, lut, colors, np.arange(len(lut)), im)
        else:
            ut.calc_bgr(frame, lut, colors, np.arange(len(lut)), im)
        
        if gui.b_on.get():
            im[-25:-20, -20-lpx:-20,:3] = 0 if gui.white.get() else 255
            im[-25:-20, -20-lpx:-20,3] = 255 - im[-25:-20, -20-lpx:-20,3]
        
        lb, la = im[:,:,0].shape
        a = min(self.im_size[1]/la, self.im_size[0]/lb)
        la = round(la*a)
        lb = round(lb*a)
        im = cv2.resize(im, (la, lb))
        exp_rate *= a
        
        pts = secv['points']
        
        if len(pts) != 0:
            
            dc, dz, dy, dx = Hub.box.shape
            names = np.array([p[0] for p in pts])
            colors = np.array([p[1] for p in pts])
            points = np.array([p[2] for p in pts])
            
            points -= np.array([dz//2,dy//2,dx//2])
            points[:,0] *= ratio
            pos = secv['position']
            pos = np.float64(pos)
            pos[0] -= np.array([dz, dy, dx])//2
            pos[:,0] *= ratio
            pos[2] /= np.linalg.norm(pos[2])
            pos[1] = pos[1] - pos[2]*np.inner(pos[1], pos[2])
            pos[1] /= np.linalg.norm(pos[1])
            op, ny, nx = pos.copy()
            nz = -np.cross(ny, nx)
            n = np.array([nz, ny, nx])
            points -= op
            points = np.linalg.solve(n.T, points.T).T
            points = np.append(points, np.arange(len(points))[:,None], axis=1)
            th_show = 9 + Hub.thickness
            show = np.abs(points[:,0]) < th_show
            colors = colors[show]
            names = names[show]
            points = points[show]
            points[:,1:3] *= exp_rate
            points[:,1:3] += np.array([lb//2, la//2])
            show = np.prod(points[:,1:3]//np.array([lb, la]) == 0, axis=1, dtype=np.bool)
            colors = colors[show]
            colors = np.append(colors, np.zeros([len(colors), 1]) + 255, axis=1)
            names = names[show]
            points = points[show]
            
            start = -(Hub.thickness//2)
            stop = start + Hub.thickness
            shallow, deep = points[:,0] < start, points[:,0] > stop - 1
            points[:,0][~shallow*~deep] = 1
            points[:,0][shallow] = (np.cos((points[:,0][shallow]-start)/10*np.pi) + 1)/2
            points[:,0][deep] = (np.cos((points[:,0][deep]-(stop+1))/th_show*np.pi) + 1)/2
    
            r, l, s = Hub.r, Hub.l, Hub.s
            for point, color, name in zip(points, colors, names):
                a, b = point[1:3].astype(np.int)
                square = im[max(a-2*r,0):a+2*r+1, max(b-2*r,0):b+2*r+1]
                square1 = square.copy()
                a0, b0 = a - max(a-2*r,0), b - max(b-2*r,0)
                l1, s1 = l[max(2*r-a0,0):, max(2*r-b0,0):], s[max(2*r-a0,0):, max(2*r-b0,0):]
                l1, s1 = l1[:len(square), :len(square[0])], s1[:len(square), :len(square[0])]
                square2 = color[None,None]*s1[:,:,None]
                square2[:,:,3] = 255
                square1 = square1*l1[:,:,None] + square2*(1-l1[:,:,None])
                square[:] = (square*(1-point[0]) + square1*point[0]).astype(np.uint8)
                (w, h), baseline = cv2.getTextSize(name, 2, 0.5, 2)
                square1 = im[max(a+7-h,0):max(a+7+baseline,0),max(b+6,0):max(b+6+w,0)]
                square2 = square1.copy()
                cv2.putText(im, name, (b+6,a+7), 2, 0.5, (0,0,0,255), 2, cv2.LINE_AA)
                cv2.putText(im, name, (b+6,a+7), 2, 0.5, color, 1, cv2.LINE_AA)
                square1[:] = (square2*(1-point[0]) + square1*point[0]).astype(np.uint8)
        
        self.canvas1.itemconfig(self.im1_back, fill='#ffffff' if gui.white.get() else '#000000')
        
        return im
    
    def preview_guide(self, secv):
        Hub = self.Hub
        
        geo = secv['geometry']
        xy_rs, z_rs = geo['res_xy'], geo['res_z']
        if None in [xy_rs, z_rs]:
            ratio = 1.
        else:
            ratio = z_rs / xy_rs
            
        dc, dz, dy, dx = Hub.box.shape
        
        pos = secv['position']
        pos = np.float64(pos)
        pos[0] -= np.array([dz, dy, dx])//2
        pos[:,0] *= ratio
        pos[2] /= np.linalg.norm(pos[2])
        pos[1] = pos[1] - pos[2]*np.inner(pos[1], pos[2])
        pos[1] /= np.linalg.norm(pos[1])
        op, ny, nx = pos
        nz = -np.cross(ny, nx)
        
        exp_rate = geo['exp_rate']
        im_size = np.array(geo['im_size'])
        
        edges = Hub.g_edges
        vivid = Hub.g_vivid
        thick = Hub.g_thick
        
        n = np.array([nz, ny, nx])
        
        pts = secv['points']
        points = np.array([p[2] for p in pts])
        if len(points) == 0:
            points = np.empty([0,3])
        within = np.prod(points >= 0, axis=1, dtype=bool)* \
                 np.prod(points <= np.array([dz, dy, dx]), axis=1, dtype=bool)
        points -= np.array([dz//2,dy//2,dx//2])
        points[:,0] *= ratio
        points -= op
        points = np.linalg.solve(n.T, points.T).T
        
        vivid_p = np.array([p[1] for p in pts], np.uint8)
        if len(vivid_p) > 0:
            vivid_p[:] = vivid_p//1.5
            vivid_p = vivid_p.astype(np.uint8)
        
        names = np.array([p[0] for p in pts])
        
        dz = dz*ratio
        peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],[dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]])
        peaks -= op + np.array([dz//2,dy//2,dx//2])
        peaks = np.linalg.solve(n.T, peaks.T).T
        
        neg = peaks[:,0] <= 0
        pn = neg[None,:]*~neg[:,None]
        pn = np.array(np.where((pn + pn.T)*(edges>=0)))
        sec = np.average(peaks[pn,1:], axis=0, weights=np.tile(np.abs(peaks[pn[::-1],:1]), (1,2)))
        
        sort = [0]
        remain = list(range(1,len(sec)))
        v0 = sec[1] - sec[0]
        v0 /= np.linalg.norm(v0)
        for _ in range(len(sec)-1):
            v1 = sec[remain] - sec[sort[-1]][None]
            v1 /= np.linalg.norm(v1, axis=1)[:,None]
            n = remain[np.argmin(np.inner(v1, v0))]
            sort += [n]
            remain.remove(n)
            v0 = sec[sort[-2]] - sec[sort[-1]]
            v0 /= np.linalg.norm(v0)
        
        eye = 2.5*Hub.L
        c = np.average(peaks[:,1:], axis=0)
        points[:,1:] -= c
        peaks[:,1:] -= c
        points[:,1:] *= eye/(points[:,:1] + eye)
        peaks[:,1:] *= eye/(peaks[:,:1] + eye)
        
        h, w = 280, 400
        e = min(w/Hub.L*0.8, w*exp_rate/im_size[0]*0.8, h*exp_rate/im_size[1]*0.8)
        peaks = (peaks[:,2:0:-1]*e).astype(np.int) + np.array([w,h])//2
        points = (points[:,::-1]*e).astype(np.int)
        points[:,:2] +=  np.array([w,h])//2
        sec = ((sec - c)[:,::-1]*e).astype(np.int) + np.array([w,h])//2
        c = (np.array([w,h])//2 - c[::-1]*e).astype(np.int)
        
        im_size = (e*im_size/exp_rate/2).astype(np.int)
        
        im0 = np.empty([h, w], np.uint8)
        im0[:] = 240
        cv2.fillConvexPoly(im0, sec[sort], 220, lineType=cv2.LINE_AA)
        transparent = 0.7
        section = (240 - im0)/(20/transparent)
        section = section[:,:,None]
        
        im = np.empty([h, w, 3], np.uint8)
        im[:,:,::2] = (section*15 + 240).astype(np.uint8)
        im[:,:,1] = im0
        
        im0 = im.copy()
        
        order = np.argsort(points[:,2])
        within = within[order]
        p_order = order[(points[order,2]>0)*~within][::-1]
        for p, color, n in zip(points[p_order], vivid_p[p_order], names[p_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
        
        where = np.array(np.where((edges>=0)*~neg[None]*~neg[:,None])).T
        for pair in where:
            eg = int(edges[tuple(pair)])
            cv2.line(im, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),
                     vivid[eg], thick[eg], cv2.LINE_AA)
        for i in range(len(sec)):
            eg = int(edges[tuple(pn[:,i])])
            cv2.line(im, tuple(sec[i]), tuple(peaks[pn[:,i][~neg[pn[:,i]]][0]]),\
                     vivid[eg], thick[eg], cv2.LINE_AA)
                
        p_order = order[(points[order,2]>0)*within][::-1]
        for p, color, n in zip(points[p_order], vivid_p[p_order], names[p_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
            
        im = (section*im0 + (1 - section)*im).astype(np.uint8)
        
        im[c[1],:] = 255
        im[:,c[0]] = 255
        
        n_order = order[(points[order,2]<=0)*within][::-1]
        for p, color, n in zip(points[n_order], vivid_p[n_order], names[n_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
            
        for i in range(len(sec)):
            eg =int(edges[tuple(pn[:,i])])
            cv2.line(im, tuple(sec[i]), tuple(peaks[pn[:,i][neg[pn[:,i]]][0]]),\
                     vivid[eg], thick[eg], cv2.LINE_AA)
        where = np.array(np.where((edges>=0)*neg[None]*neg[:,None])).T
        for pair in where:
            eg = int(edges[tuple(pair)])
            cv2.line(im, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),\
                     vivid[eg], thick[eg], cv2.LINE_AA)
                
        n_order = order[(points[order,2]<=0)*~within][::-1]
        for p, color, n in zip(points[n_order], vivid_p[n_order], names[n_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
        
        im[:22,-66:] -= np.fmin(255 - Hub.gui.xyz, im[:22,-66:])
        
        a = min(self.im_size[0]/len(im), self.im_size[1]/len(im[0]))
        im = cv2.resize(im, (int(len(im[0])*a), int(len(im)*a)))
        
        return im
    
    
    def undo(self, arg):
        arg[0](*arg[1])
        
    def redo(self, arg):
        arg[2](*arg[3])
        
    def reload(self, snp):
        if self.snapshots == snp:
            return False
        
        self.snapshots = snp
        self.refresh_tree()
        return True
