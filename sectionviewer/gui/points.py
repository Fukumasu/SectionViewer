import time

import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from .gui import Color_GUI
from ..basics import CoordinateError
from ..tools import pf, base_dir, desolve_state, make_key_text, tk_from_array


class Points_GUI(Color_GUI):
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
                     'cr': tk.StringVar(),
                     'sh': tk.IntVar(value = 1)}
        
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
        
        base_frame = ttk.Frame(main.dock_note)
        self.base_frame = base_frame
        main.dock_note.add(base_frame, text='Points')
            
        sub_frame = ttk.Frame(base_frame)
        sub_frame.pack(pady=10)
        
        button_frame = ttk.Frame(sub_frame)
        button_frame.pack(side=tk.BOTTOM, anchor=tk.E, padx=10)
        self.button_mv = ttk.Button(button_frame, text='Move to', 
                                    command=self.move_to)
        self.button_mv.pack(side=tk.LEFT)
        button1 = ttk.Button(button_frame, text='Add', command=self.add)
        button1.pack(side=tk.LEFT)
        button2 = ttk.Button(button_frame, text='Delete', command=self.delete)
        button2.pack(side=tk.LEFT)
        self.button_dl = button2
        
        self.treeview = ttk.Treeview(sub_frame, height=7)
        self.treeview.column('#0', width=330, stretch=False)
        self.treeview.heading('#0', text='Points', anchor=tk.W)
        bary = tk.Scrollbar(sub_frame, orient=tk.VERTICAL)
        bary.pack(side=tk.LEFT, fill=tk.Y)
        bary.config(command=self.treeview.yview)
        self.treeview.config(yscrollcommand=bary.set)
        self.treeview.pack(padx=10, pady=5)
        
        self.treeview.bind('<Button-1>', lambda e: self.treeview.selection_set()\
                           if not desolve_state(e.state)['Control'] else None)
        self.treeview.bind('<<TreeviewSelect>>', self.select)
        self.base_frame.bind('<Control-a>', lambda event:
                             self.treeview.selection_set(self.treeview.get_children()))
        self.refresh_tree()
        
        control_frame = ttk.Frame(base_frame, relief='groove')
        self.control_frame = control_frame
            
        self.entry_nm = ttk.Entry(control_frame, textvariable=self.vars['nm'], width=30)
        self.entry_nm.pack(padx=25, pady=15, anchor=tk.W)
        
        color_note = ttk.Notebook(control_frame)
        color_note.pack(padx=10, pady=5, ipadx=5, ipady=5)
        
        rgb_frame = ttk.Frame(color_note)
        
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
        preset_canvas.create_image(0, 0, anchor='nw', image=self.preset_image)
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
        
        bottom_frame = ttk.Frame(control_frame)
        bottom_frame.pack(padx=20, pady=10, ipadx=5, ipady=5, fill=tk.X)
        self.button_cg = ttk.Button(bottom_frame, text='Change', command=self.change)
        self.button_cg.pack(pady=10, padx=10, side=tk.RIGHT)
        label = ttk.Label(bottom_frame, textvariable=self.vars['cr'])
        label.pack(pady=10, padx=10, side=tk.RIGHT)
        
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
        
        self.treeview.selection_set()
        
    def __getattribute__(self, name):
        if name == 'obj':
            return self.main.points
        return super().__getattribute__(name)
    
    def refresh_tree(self):
        names = self.obj.get_names()
        colors = np.array(self.obj.get_colors())
        self.treeview.delete(*self.treeview.get_children())
        sort = np.argsort(names)
        im = np.zeros([8,8,3], np.uint8)
        self.icons = [0]*len(sort)
        for i in sort:
            im[1:-1,1:-1] = colors[i]
            self.icons[i] = tk_from_array(im)
            self.treeview.insert('', 'end', str(i), text=' '+names[i], image=self.icons[i])
        self.treeview.selection_set()
        x = self.treeview.get_children()
        if len(x) == 0:
            self.button_mv['state'] = tk.DISABLED
        else:
            self.button_mv['state'] = tk.ACTIVE
            
    def settings(self, select = None):
        if select == -1:
            return
        if select != None:
            self.treeview.focus(select)
            self.treeview.selection_set(select)
    
    def set_vars(self, i):
        name, color, crs = self.obj[i]
        self.vars['nm'].set(name)
        self.vars['r'].set(color[2])
        self.vars['g'].set(color[1])
        self.vars['b'].set(color[0])
        self.vars['h'].set(int(color['hsl'][0]*10))
        self.vars['s'].set(int(color['hsl'][1]*10))
        self.vars['l'].set(int(color['hsl'][2]*10))
        text = '(x,y,z) = ({0:.1f}, {1:.1f}, {2:.1f})'.format(crs[2], crs[1], crs[0])
        self.vars['cr'].set(text)
    
    def select(self, event):
        self.main.master.focus_set()
        selection = self.treeview.selection()
        
        if len(selection) == 0:
            self.button_dl['state'] = tk.DISABLED
            self.control_frame.pack_forget()
            return
        else:
            self.control_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.button_dl['state'] = tk.ACTIVE
        
        i = int(selection[0])
        self.set_vars(i)
        
        if len(selection) == 1:
            self.entry_nm['state'] = tk.ACTIVE
            self.button_cg['state'] = tk.ACTIVE
        else:
            self.entry_nm['state'] = tk.DISABLED
            self.button_cg['state'] = tk.DISABLED
            
    def change(self):
        main = self.main
        obj = self.obj
        
        org_history = main.history
        main.history = [[None, None, None]]
        org_hidx = main.hidx
        main.hidx = 0
        org_hidx_saved = main.hidx_saved
        main.hidx_saved = -1
        org_hidx_kept = main.hidx_kept
        main.hidx_kept = 0
        org_meta = main.meta_kept.copy()
        
        main.dock_note.select(main.get_dock_note_tab('Guide'))
        main.dock_note.forget(main.get_dock_note_tab('Channels'))
        main.dock_note.forget(main.get_dock_note_tab('Points'))
        main.dock_note.forget(main.get_dock_note_tab('Snapshots'))
        
        x = self.treeview.selection()[0]
        i = int(x)
        
        for w in main.bottom.pack_slaves():
            w.pack_forget()
        
        name = obj[i][0]
        obj.delete(i)

        def repair():
            frame.pack_forget()
            
            main.master.protocol('WM_DELETE_WINDOW', main.on_close)
            
            main.menu_bar.entryconfig('File', state='active')
            main.menu_bar.entryconfig('Settings', state='active')
            main.menu_bar.entryconfig('Tools', state='active')
            main.sbar_entry['state'] = tk.ACTIVE
            
            main.master.unbind('<Return>')
            
            main.view_canvas.unbind('<ButtonRelease-1>')
            main.view_canvas.bind('<ButtonRelease-1>', main.release_view)
            
            main.guide_canvas.bind('<Button-1>', main.click_guide)
            main.guide_canvas.bind('<Motion>', main.track_guide)
            
            main.master.unbind('<Key>')
            main.master.bind('<Key>', main.key)
            
            main.history = org_history
            main.hidx = org_hidx
            main.hidx_saved = org_hidx_saved
            main.hidx_kept = org_hidx_kept
            main.meta_kept = org_meta
            
            main.dock_note.add(main.channels_gui.base_frame, text='Channels')
            main.dock_note.add(self.base_frame, text='Points')
            main.dock_note.add(main.snapshots_gui.base_frame, text='Snapshots')
            main.dock_note.select(main.get_dock_note_tab('Points'))
            
            self.treeview.focus_set()
        
        def ok():
            object.__setattr__(main.secv, 'metadata', org_meta.copy())
            iw, ih = main.geometry['image_size']
            coor = main.secv.calc_2d_to_3d(np.array([iw, ih])//2)
            obj[i][2] = coor
            repair()
            
        def cancel():
            object.__setattr__(main.secv, 'metadata', org_meta)
            repair()
            
        def key(event):
            if not main.record_on:
                return
            focus = str(main.master.focus_get()).rsplit('!', 1)[-1]
            key = make_key_text(event.keysym, event.state)
            if key in ['Ctrl+Z', 'Command+Z']:
                main.undo()
            elif key in ['Ctrl+Y', 'Command+Y']:
                main.redo()
            if 'entry' in focus:
                return
            elif 'combo' in focus:
                return
            main.position_key(key)
            
        def release_view(event):
            if time.time() - main.click_time < 0.5:
                if main.mode == 1:
                    iw, ih = main.secv.geometry['image_size']
                    v = main.click - np.array([iw, ih]) // 2
                    v = v / np.array([iw, ih])
                    if np.linalg.norm(v) > 0.08:
                        key = int(np.angle(v[0] + 1j * v[1]) / np.pi * 6)
                        key = ['L', 0, 'N', 'N', 0, 'H', 'H', 0, 'I', 'I', 0][key]
                        if key != 0:
                            main.position_key('Ctrl+' + key)
                elif main.mode == 2:
                    coor = main.secv.calc_2d_to_3d(main.click)
                    object.__setattr__(main.secv, 'metadata', org_meta.copy())
                    obj[i][2] = coor
                    repair()
            main.cut_history = True
            main.record_on = True
            main.click = None
            main.meta_prev = main.meta_kept
            main.update_params = {}
        
        frame = ttk.Frame(main.bottom)
        frame.pack(ipady=5)
        ttk.Button(frame, text='OK', 
                   command=ok).pack(side=tk.RIGHT, anchor=tk.N, padx=5)
        ttk.Button(frame, text='Cancel', 
                   command=cancel).pack(side=tk.RIGHT, anchor=tk.N, padx=5)
        ttk.Label(frame, text="Put point '{0}' with Ctrl+Click or 'OK' button.".format(name),
                  font=('', 11, 'bold')).pack(side=tk.RIGHT, anchor=tk.N, padx=5)
        
        ttk.Label(main.bottom, text='µm').pack(side=tk.RIGHT, anchor=tk.N, padx=5, pady=5)
        main.sbar_entry.pack(side=tk.RIGHT, anchor=tk.N, pady=5)
        ttk.Label(main.bottom, text='Scale bar:').pack(side=tk.RIGHT, anchor=tk.N, padx=5, pady=5)
        main.coor_info.pack(side=tk.LEFT, anchor=tk.N, padx=5, pady=5)
        main.depth_frame.pack(side=tk.TOP, fill=tk.X)
        
        main.master.protocol('WM_DELETE_WINDOW', cancel)
        
        main.menu_bar.entryconfig('File', state='disabled')
        main.menu_bar.entryconfig('Settings', state='disabled')
        main.menu_bar.entryconfig('Tools', state='disabled')
        main.sbar_entry['state'] = tk.DISABLED
        
        main.master.bind('<Return>', lambda event: ok())
        
        main.view_canvas.unbind('<ButtonRelease-1>')
        main.view_canvas.bind('<ButtonRelease-1>', release_view)
        
        main.guide_canvas.unbind('<Motion>')
        main.guide_canvas.unbind('<Button-1>')
        
        main.master.unbind('<Key>')
        main.master.bind('<Key>', key)
        
        main.master.update()
        
            
    def move_to(self):
        win = tk.Toplevel(self.main.master)
        win.withdraw()
        if pf == 'Windows':
            win.iconbitmap(base_dir + 'img/icon.ico')
        win.title('Move to')
        
        frame0 = ttk.Frame(win)
        frame0.pack(padx=10, pady=10)
        
        frame1 = ttk.Frame(frame0)
        frame1.pack(padx=5, pady=5)
        
        ttk.Label(frame1, text='Center').grid(column=1, row=0, sticky=tk.W)
        ttk.Label(frame1, text='On axis').grid(column=1, row=1, sticky=tk.W)
        ttk.Label(frame1, text='On plane').grid(column=1, row=2, sticky=tk.W)
        ttk.Label(frame1, text=' : ').grid(column=2, row=0)
        ttk.Label(frame1, text=' : ').grid(column=2, row=1)
        ttk.Label(frame1, text=' : ').grid(column=2, row=2)
        
        names = self.obj.get_names()
        sort = np.argsort(names)
        names = np.array(names)[sort]
        names = [str(i) +'. ' + n for i, n in enumerate(names)]
        vc = tk.StringVar(value='Current')
        va = tk.StringVar(value='None')
        vp = tk.StringVar(value='None')
        
        ttk.Combobox(frame1, textvariable=vc, state='readonly',
                     values=['Current']+names, width=20).grid(column=3, row=0)
        ttk.Combobox(frame1, textvariable=va, state='readonly',
                     values=['None']+names, width=20).grid(column=3, row=1)
        ttk.Combobox(frame1, textvariable=vp, state='readonly',
                     values=['None']+names, width=20).grid(column=3, row=2)
        
        def ok():
            p1, p2, p3 = vc.get(), va.get(), vp.get()
            ps = []
            if p1 == 'Current':
                p1 = None
            else:
                i = int(p1.split('.')[0])
                p1 = sort[i]
                ps += [p1]
            if p2 == 'None':
                p2 = None
            else:
                i = int(p2.split('.')[0])
                p2 = sort[i]
                ps += [p2]
            if p3 == 'None':
                p3 = None
            else:
                i = int(p3.split('.')[0])
                p3 = sort[i]
                ps += [p3]
            if len(np.unique(ps)) != len(ps):
                messagebox.showerror('Error', 'The same points cannot be chosen.',
                                     parent=win)
                return
            else:
                self.move_pos(p1, p2, p3)
            
            win.grab_release()
            win.destroy()
            
        def cancel():
            win.grab_release()
            win.destroy()
        
        frame2 = ttk.Frame(frame0)
        frame2.pack(padx=5, pady=5)
        ttk.Button(frame2, text='Cancel', command=cancel).pack(side=tk.LEFT)
        ttk.Button(frame2, text='OK', command=ok).pack(side=tk.LEFT)
        
        win.resizable(height=False, width=False)
        win.deiconify()
        win.grab_set()
        
    def move_pos(self, p1, p2, p3):
        main = self.main
        obj = self.obj
        op, ny, nx = main.position * main.position._anisotropy
        coors = np.array(obj.get_coordinates())
        def calc_3d_rot_mat(c, s, n):
            n /= np.linalg.norm(n)
            mat = np.array([
                [      c, -n[2]*s,  n[1]*s],
                [ n[2]*s,       c, -n[0]*s],
                [-n[1]*s,  n[0]*s,       c]
                ])
            mat += np.outer(n, n) * (1 - c)
            return mat
        if p1 is not None:
            op = coors[p1] * main.position._anisotropy
        if p2 is not None:
            p2 = coors[p2] * main.position._anisotropy
            n1 = p2 - op
            norm1 = np.linalg.norm(n1)
            if norm1 == 0:
                return
            n1 /= norm1
            ns = np.array([ny, nx, -ny, -nx])
            a = np.inner(ns, n1)
            a = np.argmax(a)
            n2 = ns[a]
            c = np.inner(n1, n2)
            s = (1 - c**2)**0.5
            n = -np.cross(n1, n2)
            R = calc_3d_rot_mat(c, s, n)
            ny = np.inner(R, ny)
            nx = np.inner(R, nx)
        if p3 is not None:
            p3 = coors[p3] * main.position._anisotropy
            n3 = p3 - op
            if p2 is None:
                norm3 = np.linalg.norm(n3)
                if norm3 == 0:
                    return
                n3 /= norm3
                nz = -np.cross(nx, ny)
                n1 = n3 - nz*np.inner(nz, n3)
                norm1 = np.linalg.norm(n1)
                if norm1 == 0:
                    return
                n1 /= norm1
            else:
                n3 -= n1*np.inner(n1, n3)
                norm3 = np.linalg.norm(n3)
                if norm3 == 0:
                    return
                n3 /= norm3
                ns = np.array([ny, nx, -ny, -nx])
                a = np.inner(ns, n3)
                a = np.argmax(a)
                n1 = ns[a]
            c = np.inner(n3, n1)
            s = (1 - c**2)**0.5
            n = -np.cross(n3, n1)
            R = calc_3d_rot_mat(c, s, n)
            ny = np.inner(R, ny)
            nx = np.inner(R, nx)
        
        pos = np.array([op, ny, nx]) / main.position._anisotropy
        main.position[:] = pos
        
    def add(self):
        selection = self.treeview.selection()
        if len(selection) > 1:
            opt = self.main.ask_option(self.main.master, 'Options', 
                                       ['Current center',
                                        'Average of selected points'],
                                       geometry='250x120')
            if opt == -1:
                return None
        else:
            opt = 0
        
        if opt == 0:
            coor = self.main.position[0]
        else:
            selection = self.treeview.selection()
            selection = [int(s) for s in selection]
            coor = np.array(self.obj.get_coordinates())[selection]
            coor = np.average(coor, axis=0)
        
        try:
            self.obj.add(coordinates = coor)
        except CoordinateError:
            pass
        self.main.p_on.set(True)
                
    def delete(self):
        x = self.treeview.selection()
        ids = [int(i) for i in x]
        self.obj.delete(point_ids = ids)
        
    def update(self, loc):
        obj = self.obj
        selection = self.treeview.selection()
        im = np.zeros([8,8,3], np.uint8)
        loc = [l for l in loc if l[0] == 'points']
        if len(obj) == len(self.treeview.get_children()):
            if len(self.treeview.get_children()) > 0:
                for l in loc:
                    i = l[1]
                    name, color, coor = obj[i]
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
            for i, pt in enumerate(obj):
                if pt not in self.obj_prev:
                    new_selection += [str(i)]
            self.treeview.selection_set(new_selection)
        self.obj_prev = obj.copy()