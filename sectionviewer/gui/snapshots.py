import numpy as np

import tkinter as tk
from tkinter import ttk

from .gui import Base_GUI
from ..tools import tk_from_array, desolve_state


class Snapshots_GUI(Base_GUI):
    def __init__(self, main):
        super().__init__(main)
            
        self.main = main
        self.obj_prev = self.obj.copy()
        
        self.name_var = tk.StringVar()
        self.pos_on = tk.BooleanVar(value = True)
        self.chs_on = tk.BooleanVar(value = True)
        self.pts_on = tk.BooleanVar(value = True)
        
        self.name_var.trace('w', self.name_trace)
        
        base_frame = ttk.Frame(main.dock_note)
        self.base_frame = base_frame
        main.dock_note.add(base_frame, text='Snapshots')
        
        sub_frame = ttk.Frame(base_frame)
        sub_frame.pack(pady=10)
        
        self.treeview = ttk.Treeview(sub_frame, height=7)
        self.treeview.column('#0', width=330, stretch=False)
        self.treeview.heading('#0', text='Snapshots', anchor=tk.W)
    
        bary = tk.Scrollbar(sub_frame, orient = tk.VERTICAL)
        bary.pack(side = tk.LEFT, fill=tk.Y)
        bary.config(command = self.treeview.yview)
        self.treeview.config(yscrollcommand=bary.set)
        self.treeview.pack(padx=10, pady=5)
        
        self.treeview.bind('<Button-1>', lambda e: self.treeview.selection_set()\
                           if not desolve_state(e.state)['Control'] else None)
        self.treeview.bind('<<TreeviewSelect>>', self.select)
        self.selected = []
        
        self.refresh_tree()
            
        button_frame = ttk.Frame(base_frame)
        button_frame.pack(padx=5, pady=5, fill=tk.X)
        
        button1 = ttk.Button(button_frame, text='Delete', command=self.delete)
        button1.pack(side=tk.RIGHT)
        self.button_dl = button1
        button2 = ttk.Button(button_frame, text='Snap', command=self.snap)
        button2.pack(side=tk.RIGHT)
        
        def chk():
            pos_on = self.pos_on.get()
            chs_on = self.chs_on.get()
            pts_on = self.pts_on.get()
            if (pos_on or chs_on or pts_on) and len(self.treeview.selection()) == 1:
                self.button_ov['state'] = tk.NORMAL
                self.button_rs['state'] = tk.NORMAL
            else:
                self.button_ov['state'] = tk.DISABLED
                self.button_rs['state'] = tk.DISABLED
        
        self.pts_chk = ttk.Checkbutton(button_frame, variable=self.pts_on, text='Points',
                                       command=chk)
        self.pts_chk.pack(side=tk.RIGHT, padx=3)
        self.chs_chk = ttk.Checkbutton(button_frame, variable=self.chs_on, text='Channels',
                                       command=chk)
        self.chs_chk.pack(side=tk.RIGHT, padx=3)
        self.pos_chk = ttk.Checkbutton(button_frame, variable=self.pos_on, text='Position',
                                       command=chk)
        self.pos_chk.pack(side=tk.RIGHT, padx=3)
        
        control_frame = ttk.Frame(base_frame, relief='groove')
        self.control_frame = control_frame
        
        top_frame = ttk.Frame(control_frame)
        top_frame.pack(padx=10, pady=10, fill=tk.X)
        button3 = ttk.Button(top＿frame, text = 'Overwrite', 
                             command = self.overwrite)
        button3.pack(side=tk.RIGHT)
        self.button_ov = button3
        button4 = ttk.Button(top_frame, text = 'Restore', 
                             command = self.restore)
        button4.pack(side=tk.RIGHT)
        self.button_rs = button4
        
        self.entry_nm = ttk.Entry(top_frame, textvariable=self.name_var, width=15)
        self.entry_nm.pack(side=tk.LEFT, padx=5)
        
        note = ttk.Notebook(control_frame)
        note.pack(padx=10, pady=5, ipadx=5, ipady=5)
        
        self.im_size = (250, 300)
        
        sec_frame = ttk.Frame(note)
        self.canvas1 = tk.Canvas(sec_frame, width=self.im_size[1], height=self.im_size[0])
        self.canvas1.pack()
        note.add(sec_frame, text='Section')
        
        ske_frame = ttk.Frame(note)
        self.canvas2 = tk.Canvas(ske_frame, width=self.im_size[1], height=self.im_size[0])
        self.canvas2.pack()
        note.add(ske_frame, text='Skeleton')
        
        self.sec_id = self.canvas1.create_image(self.im_size[1]//2, self.im_size[0]//2)
        self.ske_id = self.canvas2.create_image(self.im_size[1]//2, self.im_size[0]//2)
        
    def __getattribute__(self, name):
        if name == 'obj':
            return self.main.snapshots
        return super().__getattribute__(name)
        
    def refresh_tree(self):
        self.treeview.delete(*self.treeview.get_children())
        names = self.obj.getnames()
        for i in np.argsort(names):
            self.treeview.insert('', 'end', str(i), text=' ' + names[i])
        self.treeview.selection_set()
        
    def settings(self):
        pass
    
    def set_vars(self, i):
        self.name_var.set(self.obj[i]['name'])
        sec, ske = self.obj.getpreview(i, size = self.im_size)
        self.sec = tk_from_array(sec)
        self.canvas1.itemconfig(self.sec_id, image=self.sec)
        self.ske = tk_from_array(ske)
        self.canvas2.itemconfig(self.ske_id, image=self.ske)
    
    def select(self, event):
        self.main.master.focus_set()
        selection = self.treeview.selection()
        
        if len(selection) == 0 or len(selection) > 1:
            self.pos_chk['state'] = tk.NORMAL
            self.chs_chk['state'] = tk.NORMAL
            self.pts_chk['state'] = tk.NORMAL
            self.control_frame.pack_forget()
            if len(selection) == 0:
                self.button_dl['state'] = tk.DISABLED
            else:
                self.button_dl['state'] = tk.NORMAL
            return
        
        self.button_dl['state'] = tk.NORMAL
        self.pos_chk['state'] = tk.NORMAL
        self.chs_chk['state'] = tk.NORMAL
        self.pts_chk['state'] = tk.NORMAL
        pos_on = self.pos_on.get()
        chs_on = self.chs_on.get()
        pts_on = self.pts_on.get()
        if (pos_on or chs_on or pts_on):
            self.button_ov['state'] = tk.NORMAL
            self.button_rs['state'] = tk.NORMAL
        else:
            self.button_ov['state'] = tk.DISABLED
            self.button_rs['state'] = tk.DISABLED
        self.control_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.set_vars(int(selection[0]))
        
    def name_trace(self, *args):
        x = self.treeview.selection()
        if len(x) != 1:
            return
        name = self.name_var.get()
        self.obj[int(x[0])]['name'] = name
    
    def snap(self):
        self.obj.snap()
        
    def delete(self):
        x = self.treeview.selection()
        ids = [int(i) for i in x]
        self.obj.delete(ids)
    
    def overwrite(self):
        select = self.treeview.selection()[0]
        i = int(select)
        self.obj.overwrite(i, self.pos_on.get(),
                           self.chs_on.get(), self.pts_on.get())

    def restore(self):
        select = self.treeview.selection()[0]
        i = int(select)
        self.obj.restore(i, self.pos_on.get(),
                         self.chs_on.get(), self.pts_on.get())
        self.main.cut_history = True
        
    def update(self, loc):
        obj = self.obj
        selection = self.treeview.selection()
        loc = [l for l in loc if l[0] in ['snapshots', 'display']]
        if len(obj) == len(self.treeview.get_children()):
            if len(self.treeview.get_children()) > 0:
                for l in loc:
                    if l[0] == 'snapshots':
                        i = l[1]
                        name = obj[i]['name']
                        self.treeview.item(str(i), text=' '+name)
                        if len(selection) == 0:
                            continue
                        if i != int(selection[0]):
                            continue
                    else:
                        if l[1] not in ['white_back', 'thickness', 
                                        'points', 'shown_channels']:
                            continue
                    if len(selection) > 0:
                        self.set_vars(int(selection[0]))
        else:
            self.refresh_tree()
            new_selection = []
            for i, ss in enumerate(obj):
                if ss not in self.obj_prev:
                    new_selection += [str(i)]
            self.treeview.selection_set(new_selection[:1])
        self.obj_prev = obj.copy()