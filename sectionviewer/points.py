import time

import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class Points:
    def __init__(self, Hub):
        self.Hub = Hub
        pts = Hub.points
        
        for p in pts:
            p[0] = str(p[0])
            p[1] = [int(p[1][i])%256 for i in range(3)]
            p[2] = [float(p[2][i]) for i in range(3)]
        self.pts = pts
        
        self.add_center = tk.BooleanVar(value=True)
        self.variables = {"nm": tk.StringVar(),
                       "b" : tk.IntVar(),
                       "g" : tk.IntVar(),
                       "r" : tk.IntVar(),
                       "bs": tk.StringVar(),
                       "gs": tk.StringVar(),
                       "rs": tk.StringVar(),
                       "h" : tk.IntVar(),
                       "s" : tk.IntVar(),
                       "l" : tk.IntVar(),
                       "hs": tk.StringVar(),
                       "ss": tk.StringVar(),
                       "ls": tk.StringVar(),
                       "cr": tk.StringVar()}
        
        self.variables["nm"].trace("w", self.pt_name)
        self.variables["r"].trace("w", lambda *args: self.variables["rs"].set(str(self.variables["r"].get())))
        self.variables["g"].trace("w", lambda *args: self.variables["gs"].set(str(self.variables["g"].get())))
        self.variables["b"].trace("w", lambda *args: self.variables["bs"].set(str(self.variables["b"].get())))
        self.variables["h"].trace("w", lambda *args: self.variables["hs"].set(str(self.variables["h"].get()/10)))
        self.variables["s"].trace("w", lambda *args: self.variables["ss"].set(str(self.variables["s"].get()/10)))
        self.variables["l"].trace("w", lambda *args: self.variables["ls"].set(str(self.variables["l"].get()/10)))
        
        # settings
        
        frame0 = ttk.Frame(Hub.gui.palette)
        self.set_frame = frame0
            
        frame1 = ttk.Frame(frame0)
        frame1.pack(side=tk.LEFT)
        
        frameb = ttk.Frame(frame1)
        frameb.pack(side=tk.BOTTOM, anchor=tk.E, padx=10)
        self.button_mv = ttk.Button(frameb, text="Move to", command=self.move_to)
        self.button_mv.pack(side=tk.LEFT)
        button1 = ttk.Button(frameb, text="Add", command=self.add_pt)
        button1.pack(side=tk.LEFT)
        button2 = ttk.Button(frameb, text="Delete", command=self.del_pt)
        button2.pack(side=tk.LEFT)
        self.button_dl = button2
        
        self.treeview = ttk.Treeview(frame1, height=15)
        self.treeview.column("#0", width=200, stretch=False)
        self.treeview.heading("#0", text="Points", anchor=tk.W)
        bary = tk.Scrollbar(frame1, orient=tk.VERTICAL)
        bary.pack(side=tk.LEFT, fill=tk.Y)
        bary.config(command=self.treeview.yview)
        self.treeview.config(yscrollcommand=bary.set)
        self.treeview.pack(padx=10, pady=5)
        self.treeview.bind("<Button-1>", lambda e: self.treeview.selection_set()\
                          if e.state//4%2!=1 else None)
        self.treeview.bind("<<TreeviewSelect>>", self.pt_select)
        
        names = self.getnames()
        colors = np.array(self.getcolors())
        
        sort = np.argsort(names)
        im = np.zeros([8,8,3], np.uint8)
        self.icons = [0]*len(sort)
        
        for i in sort:
            im[1:-1,1:-1] = colors[i]
            self.icons[i] = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
            self.treeview.insert("", "end", str(i), text=" "+names[i], image=self.icons[i])
        
        frame2 = ttk.Frame(frame0)
        frame2.pack(side=tk.TOP, pady=10)
        self.frame2 = frame2
            
        self.entry_nm = ttk.Entry(frame2, textvariable=self.variables["nm"])
        self.entry_nm.grid(row=0, column=0, columnspan=2, pady=10)
        
        note = ttk.Notebook(frame2)
        note.grid(row=1, column=0, columnspan=2, padx=10, pady=5, ipadx=5, ipady=5)
        self.pt_note = note
        
        def select_entry():
            self.entry_channel = self.treeview.selection()
        
        def color_entry(c):
            try:
                if self.entry_channel == self.treeview.selection():
                    if c in "rgb":
                        new = float(self.variables[c + "s"].get())
                        new = int(max(0, min(new, 255)))
                        self.variables[c].set(new)
                        self.variables[c + "s"].set(str(new))
                        self.rgb()
                    elif c in "hsl":
                        new = float(self.variables[c + "s"].get())*10
                        mx = 3599 if c=="h" else 1000
                        new = int(max(0, min(new, mx)))
                        self.variables[c].set(new)
                        self.variables[c + "s"].set(str(new/10))
                        self.hsl()
                else:
                    self.entry_channel = self.treeview.selection()
            except:
                if c in "rgb":
                    self.variables[c + "s"].set(str(self.variables[c].get()))
                elif c in "hsl":
                    self.variables[c + "s"].set(str(self.variables[c].get()))
        
        rgb_frame = ttk.Frame(note)
        self.rgb_frame = rgb_frame
        
        ttk.Label(rgb_frame, text="  R:  ").grid(column=0, row=1)
        ttk.Label(rgb_frame, text="  G:  ").grid(column=0, row=2)
        ttk.Label(rgb_frame, text="  B:  ").grid(column=0, row=3)
        ttk.Scale(rgb_frame, length=190, variable=self.variables["r"], from_=0, to=255,
                 orient="horizontal", command=self.rgb).grid(column=1, row=1, pady=7)
        ttk.Scale(rgb_frame, length=190, variable=self.variables["g"], from_=0, to=255,
                 orient="horizontal", command=self.rgb).grid(column=1, row=2, pady=7)
        ttk.Scale(rgb_frame, length=190, variable=self.variables["b"], from_=0, to=255,
                 orient="horizontal", command=self.rgb).grid(column=1, row=3, pady=7)
        self.entry_r = ttk.Entry(rgb_frame, textvariable=self.variables["rs"], width=5)
        self.entry_r.grid(column=2, row=1, padx=3)
        self.entry_g = ttk.Entry(rgb_frame, textvariable=self.variables["gs"], width=5)
        self.entry_g.grid(column=2, row=2, padx=3)
        self.entry_b = ttk.Entry(rgb_frame, textvariable=self.variables["bs"], width=5)
        self.entry_b.grid(column=2, row=3, padx=3)
        self.entry_r.bind("<Return>", lambda event: color_entry("r"))
        self.entry_r.bind("<FocusIn>", lambda event: select_entry())
        self.entry_r.bind("<FocusOut>", lambda event: color_entry("r"))
        self.entry_g.bind("<Return>", lambda event: color_entry("g"))
        self.entry_g.bind("<FocusIn>", lambda event: select_entry())
        self.entry_g.bind("<FocusOut>", lambda event: color_entry("g"))
        self.entry_b.bind("<Return>", lambda event: color_entry("b"))
        self.entry_b.bind("<FocusIn>", lambda event: select_entry())
        self.entry_b.bind("<FocusOut>", lambda event: color_entry("b"))
        ttk.Button(rgb_frame, text="Auto", command=self.pt_auto).grid(column=1, row=4, 
                                                                      columnspan=2, pady=2, sticky=tk.E)
        note.add(rgb_frame, text="RGB")
        
        hsl_frame = ttk.Frame(note)
        self.hsl_frame = hsl_frame
        
        ttk.Label(hsl_frame, text=" H:  ").grid(column=0, row=1)
        ttk.Label(hsl_frame, text=" S:  ").grid(column=0, row=2)
        ttk.Label(hsl_frame, text=" L:  ").grid(column=0, row=3)
        ttk.Scale(hsl_frame, length=190, variable=self.variables["h"], from_=0, to=3599,
                 orient="horizontal", command=self.hsl).grid(column=1, row=1, pady=7)
        ttk.Scale(hsl_frame, length=190, variable=self.variables["s"], from_=0, to=1000,
                 orient="horizontal", command=self.hsl).grid(column=1, row=2, pady=7)
        ttk.Scale(hsl_frame, length=190, variable=self.variables["l"], from_=0, to=1000,
                 orient="horizontal", command=self.hsl).grid(column=1, row=3, pady=7)
        self.entry_h = ttk.Entry(hsl_frame, textvariable=self.variables["hs"], width=5)
        self.entry_h.grid(column=2, row=1, padx=3)
        self.entry_s = ttk.Entry(hsl_frame, textvariable=self.variables["ss"], width=5)
        self.entry_s.grid(column=2, row=2, padx=3)
        self.entry_l = ttk.Entry(hsl_frame, textvariable=self.variables["ls"], width=5)
        self.entry_l.grid(column=2, row=3, padx=3)
        self.entry_h.bind("<Return>", lambda event: color_entry("h"))
        self.entry_h.bind("<FocusIn>", lambda event: select_entry())
        self.entry_h.bind("<FocusOut>", lambda event: color_entry("h"))
        self.entry_s.bind("<Return>", lambda event: color_entry("s"))
        self.entry_s.bind("<FocusIn>", lambda event: select_entry())
        self.entry_s.bind("<FocusOut>", lambda event: color_entry("s"))
        self.entry_l.bind("<Return>", lambda event: color_entry("l"))
        self.entry_l.bind("<FocusIn>", lambda event: select_entry())
        self.entry_l.bind("<FocusOut>", lambda event: color_entry("l"))
        ttk.Button(hsl_frame, text="Auto", command=self.pt_auto).grid(column=1, row=4, 
                                                                      columnspan=2, pady=2, sticky=tk.E)
        note.add(hsl_frame, text="HSL")
        
        label = ttk.Label(frame2, textvariable=self.variables["cr"])
        label.grid(row=2, column=0, pady=10, padx=10, sticky=tk.E)
        self.button_cg = ttk.Button(frame2, text="Change", command=self.change)
        self.button_cg.grid(row=2, column=1, pady=10, padx=10, sticky=tk.E)
        
    
    def __getattr__(self, name):
        if name == "val":
            return object.__getattribute__(self, "pts")
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == "val":
            object.__setattr__(self, "pts", val)
        else:
            object.__setattr__(self, name, val)
    
    def __getitem__(self, x):
        return self.pts[x]
    
    def __len__(self):
        return len(self.pts)
    
    def getnames(self):
        return [p[0] for p in self.pts]
    def getcolors(self):
        return [p[1] for p in self.pts]
    def getcoordinates(self):
        return [p[2] for p in self.pts]
    
    
    def settings(self, select=None):
        gui = self.Hub.gui
        if select == -1:
            return None
        gui.palette.title("Points")
        for w in gui.palette.pack_slaves():
            w.pack_forget()
        self.set_frame.pack(pady=10, padx=5)
        gui.palette.unbind("<Control-a>")
        gui.palette.bind("<Control-a>", lambda event: self.treeview.selection_set(self.treeview.get_children()))
        self.refresh_tree()
    
        x = self.treeview.get_children()
        if len(x) == 0:
            self.button_mv["state"] = tk.DISABLED
        else:
            self.button_mv["state"] = tk.ACTIVE
    
        gui.palette.deiconify()
        gui.palette.grab_set()
        
        if select == None:
            if len(x) > 0:
                self.treeview.focus(x[0])
                self.treeview.selection_set(x[0])
            else:
                self.treeview.selection_set()
        else:
            self.treeview.focus(select)
            self.treeview.selection_set(select)
            
            
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
            self.treeview.insert("", "end", str(i), text=" "+names[i], image=self.icons[i])
        self.treeview.selection_set()
        x = self.treeview.get_children()
        if len(x) == 0:
            self.button_mv["state"] = tk.DISABLED
        else:
            self.button_mv["state"] = tk.ACTIVE
            
        
    def pt_select(self, event):
        selection = self.treeview.selection()
        
        if len(selection) == 0:
            self.button_dl["state"] = tk.DISABLED
            self.frame2.pack_forget()
            return
        else:
            self.frame2.pack()
        
        self.button_dl["state"] = tk.ACTIVE
        
        i = int(selection[0])
        p = self.pts[i][2]
        bgr = self.pts[i][1]
        hsl = self.Hub.channels.bgr2hsl(bgr)
        
        self.variables["nm"].set(self.pts[i][0])
        self.variables["r"].set(bgr[2])
        self.variables["g"].set(bgr[1])
        self.variables["b"].set(bgr[0])
        self.variables["h"].set(int(hsl[0]*10))
        self.variables["s"].set(int(hsl[1]*10))
        self.variables["l"].set(int(hsl[2]*10))
        self.variables["cr"].set("(x,y,z) = ({0:.1f}, {1:.1f}, {2:.1f})".format(p[2], p[1], p[0]))
        
        if len(selection) == 1:
            self.entry_nm["state"] = tk.ACTIVE
            self.button_cg["state"] = tk.ACTIVE
        else:
            self.entry_nm["state"] = tk.DISABLED
            self.button_cg["state"] = tk.DISABLED
                
                
    def pt_auto(self):
        x = self.treeview.selection()
        old = [self.pts[int(i)][1] for i in x]
        
        fix = []
        for i in self.treeview.get_children():
            if i not in x:
                fix += [list(self.pts[int(i)][1])]
        new = len(x)
        new = self.Hub.channels.auto_color(fix, new, offset=180)
        
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
        gui.edit_menu.entryconfig("Undo", state="normal")
        gui.edit_menu.entryconfig("Redo", state="disable")
        gui.master.title("*" + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_color(x, new)
                
                
    def pt_name(self, *args):
        x = self.treeview.selection()
        if len(x) > 1 or len(x) == 0:
            return None
        
        old = self.pts[int(x[0])][0]
        new = self.variables["nm"].get()
        
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
        gui.edit_menu.entryconfig("Undo", state="normal")
        gui.edit_menu.entryconfig("Redo", state="disable")
        gui.master.title("*" + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_name(x, new)
        
        
    def set_name(self, x, new):
        self.treeview.item(x[0], text=" "+new)
        if x != self.treeview.selection():
            self.treeview.selection_set(x)
        else:
            self.variables["nm"].set(new)
        self.pts[int(x[0])][0] = new
    
        self.Hub.put_points()
        self.Hub.calc_guide()
        guide = self.Hub.gui.guide.copy()
        color = np.array(self.Hub.points.getcolors()[int(x[0])])
        points = self.Hub.guide_points.copy()
        color = color//1.5
        color = (int(color[0]), int(color[1]), int(color[2]))
        p = points[int(x[0])]
        guide = cv2.circle(guide, tuple(p[:2]), 4, (255,255,255), -1, lineType=cv2.LINE_AA)
        guide = cv2.circle(guide, tuple(p[:2]), 3, color, -1, lineType=cv2.LINE_AA)
        
        cv2.putText(guide, new, tuple(p[:2]+12), 2, 0.5, (255,255,255), 3, cv2.LINE_AA)
        cv2.putText(guide, new, tuple(p[:2]+12), 2, 0.5, color, 1, cv2.LINE_AA)
        
        self.Hub.gui.guide_im = ImageTk.PhotoImage(Image.fromarray(guide[:,:,::-1]))
        self.Hub.gui.guide_canvas.itemconfig(self.Hub.gui.guide_id, image=self.Hub.gui.guide_im)
        
        
    def rgb(self, *args):
        a  = [self.variables["b"].get()]
        a += [self.variables["g"].get()]
        a += [self.variables["r"].get()]
        a = self.Hub.channels.bgr2hsl(a)
        self.variables["h"].set(int(a[0]*10))
        self.variables["s"].set(int(a[1]*10))
        self.variables["l"].set(int(a[2]*10))
        self.pt_color()
    def hsl(self, *args):
        a  = [self.variables["h"].get()/10]
        a += [self.variables["s"].get()/10]
        a += [self.variables["l"].get()/10]
        a = self.Hub.channels.hsl2bgr(a)
        self.variables["b"].set(a[0])
        self.variables["g"].set(a[1])
        self.variables["r"].set(a[2])
        self.pt_color()
        
    def pt_color(self, *args):
        x = self.treeview.selection()
        old = [self.pts[int(i)][1] for i in x]
        new = [[self.variables["b"].get(), self.variables["g"].get(), self.variables["r"].get()]]
        
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
        gui.edit_menu.entryconfig("Undo", state="normal")
        gui.edit_menu.entryconfig("Redo", state="disable")
        gui.master.title("*" + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.set_color(x, new)
        
    def set_color(self, x, new):
        l = len(new)
        im = np.zeros([8,8,3], np.uint8)
        for i, st in enumerate(x):
            j = int(st)
            self.pts[j][1] = [new[i%l][0], new[i%l][1], new[i%l][2]]
            im[1:-1,1:-1] = new[i%l]
            self.icons[j] = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
            self.treeview.item(st, image=self.icons[j])
        
        if x != self.treeview.selection():
            self.treeview.selection_set(x)
        else:
            i = int(x[0])
            bgr = self.pts[i][1]
            hsl = self.Hub.channels.bgr2hsl(bgr)
            
            self.variables["r"].set(bgr[2])
            self.variables["g"].set(bgr[1])
            self.variables["b"].set(bgr[0])
            self.variables["h"].set(hsl[0])
            self.variables["s"].set(hsl[1])
            self.variables["l"].set(hsl[2])
            
        self.Hub.calc_image()
        if self.Hub.gui.g_on.get():
            if self.Hub.gui.guide_mode == "guide":
                self.Hub.calc_guide()
            else:
                self.Hub.calc_sideview()
            
            
    def change(self):
        Hub = self.Hub
        gui = Hub.gui
        
        i = self.treeview.selection()[0]
        self.pre_selection = 0
        
        gui.palette.grab_release()
        gui.palette.withdraw()
        
        for w in gui.bottom.pack_slaves():
            w.pack_forget()
            
        name = self.getnames()[int(i)]
        
        hst_org = Hub.history.copy()
        hdx_org = Hub.hidx, Hub.hidx_saved
        pos_org = Hub.position.asarray().tolist()
        exp_org = Hub.geometry["exp_rate"]
        ims_org = Hub.geometry["im_size"]
        pts_org = self.pts.copy()
        
        Hub.history = [[0,empty()]]
        Hub.hidx = -1
        Hub.hidx_saved = -1
        gui.edit_menu.entryconfig("Undo", state="disable")
        gui.edit_menu.entryconfig("Redo", state="disable")
        
        self.pts = pts_org[:int(i)] + pts_org[int(i)+1:]
        Hub.put_points()
        
        def ok():
            gui.master.protocol("WM_DELETE_WINDOW", gui.on_close)
            Hub.history = hst_org
            Hub.hidx, Hub.hidx_saved = hdx_org
            self.pts = pts_org
            
            a, b = Hub.geometry["im_size"]
            click = np.array([a,b])//2
            self.clicked(click, num=int(i))
            
            Hub.position.pos = pos_org
            Hub.geometry.geo["exp_rate"] = exp_org
            Hub.geometry.geo["im_size"] = ims_org
            Hub.calc_geometry()
            if gui.g_on.get():
                if gui.guide_mode == "guide":
                    Hub.calc_guide()
                else:
                    Hub.calc_sideview()
            repair()
            gui.palette.deiconify()
            self.treeview.focus_set()
            gui.palette.grab_set()
            self.treeview.focus(i)
            self.treeview.selection_set(i)
        def cancel():
            gui.master.protocol("WM_DELETE_WINDOW", gui.on_close)
            Hub.history = hst_org
            Hub.hidx, Hub.hidx_saved = hdx_org
            Hub.position.pos = pos_org
            Hub.geometry.geo["exp_rate"] = exp_org
            Hub.geometry.geo["im_size"] = ims_org
            self.pts = pts_org
            Hub.calc_geometry()
            if gui.g_on.get():
                if gui.guide_mode == "guide":
                    Hub.calc_guide()
                else:
                    Hub.calc_sideview()
            repair()
            gui.palette.deiconify()
            self.treeview.focus_set()
            gui.palette.grab_set()
            self.treeview.focus(i)
            self.treeview.selection_set(i)
        def release(event):
            gui.sec_canvas.bind("<Motion>", gui.track_sec)
            if (gui.shift != 0).any():
                pos = Hub.position.asarray()
                pos[0] -= (gui.shift[0]*pos[2] + gui.shift[1]*pos[1])/Hub.geometry["expansion"]
                Hub.position.new(pos.tolist(), 0)
                gui.shift = np.array([0.,0.])
            elif  gui.angle != 0:
                pos = Hub.position.asarray()
                ny, nx = pos.copy()[1:]
                pos[1] =  np.sin(gui.angle)*nx + np.cos(gui.angle)*ny
                pos[2] =  np.cos(gui.angle)*nx - np.sin(gui.angle)*ny
                Hub.position.new(pos.tolist(), 0)
                gui.angle = 0
            elif gui.expand != 1:
                Hub.geometry.new(["exp_rate"], [gui.expand*Hub.geometry["exp_rate"]])
                gui.expand = 1.
            elif (gui.trim != 0).any():
                im_size = np.array(list(Hub.geometry["im_size"]))
                im_size += gui.trim
                Hub.geometry.new(["im_size"], [tuple(im_size)])
                gui.trim[:] = 0
            elif time.time() - gui.click_time < 0.5:
                if gui.mode == 1:
                    Hub.position.clicked(gui.click)
                elif gui.mode == 2:
                    gui.master.protocol("WM_DELETE_WINDOW", gui.on_close)
                    Hub.history = hst_org
                    Hub.hidx, Hub.hidx_saved = hdx_org
                    self.pts = pts_org
                    if isinstance(gui.click, type(None)):
                        return
                    self.clicked(gui.click, num=int(i))
                    Hub.position.pos = pos_org
                    Hub.geometry.geo["exp_rate"] = exp_org
                    Hub.geometry.geo["im_size"] = ims_org
                    Hub.calc_geometry()
                    if gui.g_on.get():
                        if gui.guide_mode == "guide":
                            Hub.calc_guide()
                        else:
                            Hub.calc_sideview()
                    repair()
                    gui.palette.deiconify()
                    self.treeview.focus_set()
                    gui.palette.grab_set()
                    self.treeview.focus(i)
                    self.treeview.selection_set(i)
            gui.click = None
        
        frame = ttk.Frame(gui.bottom)
        frame.pack(ipady=5)
        ttk.Button(frame, text="OK", 
                   command=ok).pack(side=tk.RIGHT, anchor=tk.N, padx=5)
        ttk.Button(frame, text="Cancel", 
                   command=cancel).pack(side=tk.RIGHT, anchor=tk.N, padx=5)
        ttk.Label(frame, text="Put point '{0}' with Ctrl+Click or 'OK' button.".format(name),
                  font=("", 11, "bold")).pack(side=tk.RIGHT, anchor=tk.N, padx=5)
        
        gui.bar_button.pack(side=tk.RIGHT, anchor=tk.N, padx=5, pady=5)
        gui.coor_info.pack(side=tk.LEFT, anchor=tk.N, padx=5, pady=5)
        gui.scale_frame.pack(side=tk.TOP, fill=tk.X)
        
        gui.master.protocol("WM_DELETE_WINDOW", cancel)
        
        gui.menu_bar.entryconfig("File", state="disabled")
        gui.menu_bar.entryconfig("Settings", state="disabled")
        gui.menu_bar.entryconfig("Tools", state="disabled")
        for button in gui.buttons.grid_slaves():
            button["state"] = tk.DISABLED
        gui.bar_button["state"] = tk.DISABLED
        
        gui.master.bind('<Return>', lambda event: ok())
        
        gui.sec_canvas.unbind('<ButtonRelease-1>')
        gui.sec_canvas.bind('<ButtonRelease-1>', release)
        
        gui.guide_canvas.unbind("<Motion>")
        gui.guide_canvas.unbind("<Button-1>")
        
        def repair():
            frame.pack_forget()
            
            gui.master.protocol("WM_DELETE_WINDOW", gui.on_close)
            
            gui.menu_bar.entryconfig("File", state="active")
            gui.menu_bar.entryconfig("Settings", state="active")
            gui.menu_bar.entryconfig("Tools", state="active")
            for button in gui.buttons.grid_slaves():
                button["state"] = tk.ACTIVE
            gui.bar_button["state"] = tk.ACTIVE
            
            gui.master.unbind('<Return>')
            
            gui.sec_canvas.unbind('<ButtonRelease-1>')
            gui.sec_canvas.bind('<ButtonRelease-1>', gui.release_sec)
            
            gui.guide_canvas.bind("<Motion>", gui.track_guide)
            gui.guide_canvas.bind("<Button-1>", lambda event: self.settings(select=gui.p_num))
        
            
    def move_to(self):
        win = tk.Toplevel(self.Hub.gui.palette)
        win.withdraw()
        win.iconbitmap(self.Hub.gui.SV.mDir + "img/SectionViewer.ico")
        win.title("Move to")
        
        frame0 = ttk.Frame(win)
        frame0.pack(padx=10, pady=10)
        
        frame1 = ttk.Frame(frame0)
        frame1.pack(padx=5, pady=5)
        
        ttk.Label(frame1, text="Center").grid(column=1, row=0, sticky=tk.W)
        ttk.Label(frame1, text="On axis").grid(column=1, row=1, sticky=tk.W)
        ttk.Label(frame1, text="On plane").grid(column=1, row=2, sticky=tk.W)
        ttk.Label(frame1, text=" : ").grid(column=2, row=0)
        ttk.Label(frame1, text=" : ").grid(column=2, row=1)
        ttk.Label(frame1, text=" : ").grid(column=2, row=2)
        
        names = self.getnames()
        sort = np.argsort(names)
        names = np.array(names)[sort]
        names = [str(i) +". " + n for i, n in enumerate(names)]
        vc = tk.StringVar(value="Current")
        va = tk.StringVar(value="None")
        vp = tk.StringVar(value="None")
        
        ttk.Combobox(frame1, textvariable=vc, state="readonly",
                     values=["Current"]+names, width=20).grid(column=3, row=0)
        ttk.Combobox(frame1, textvariable=va, state="readonly",
                     values=["None"]+names, width=20).grid(column=3, row=1)
        ttk.Combobox(frame1, textvariable=vp, state="readonly",
                     values=["None"]+names, width=20).grid(column=3, row=2)
        
        def ok():
            p1, p2, p3 = vc.get(), va.get(), vp.get()
            ps = []
            if p1 == "Current":
                p1 = None
            else:
                i = int(p1.split(".")[0])
                p1 = sort[i]
                ps += [p1]
            if p2 == "None":
                p2 = None
            else:
                i = int(p2.split(".")[0])
                p2 = sort[i]
                ps += [p2]
            if p3 == "None":
                p3 = None
            else:
                i = int(p3.split(".")[0])
                p3 = sort[i]
                ps += [p3]
            if len(np.unique(ps)) != len(ps):
                messagebox.showerror("Error", "Same point cannot be chosen.")
                return None
            else:
                self.move_pos(p1, p2, p3)
            
            win.grab_release()
            win.destroy()
            self.Hub.gui.palette.grab_set()
            
        def cancel():
            win.grab_release()
            win.destroy()
            self.Hub.gui.palette.grab_set()
        
        frame2 = ttk.Frame(frame0)
        frame2.pack(padx=5, pady=5)
        ttk.Button(frame2, text="Cancel", command=cancel).pack(side=tk.LEFT)
        ttk.Button(frame2, text="OK", command=ok).pack(side=tk.LEFT)
        
        win.resizable(height=False, width=False)
        win.deiconify()
        win.grab_set()
        
    def move_pos(self, p1, p2, p3):
        op, ny, nx = self.Hub.position.asarray()
        dc, dz, dy, dx = self.Hub.box.shape
        coors = np.array(self.getcoordinates())
        if p1 != None:
            op = coors[p1]
            op -= np.array([dz, dy, dx])//2
            op[0] *= self.Hub.ratio
        if p2 != None:
            p2 = coors[p2]
            p2 -= np.array([dz, dy, dx])//2
            p2[0] *= self.Hub.ratio
            n1 = p2 - op
            norm1 = np.linalg.norm(n1)
            if norm1 == 0:
                return None
            n1 /= norm1
            a = np.array([ny, nx, -ny, -nx])
            a = np.inner(a, n1)
            a = np.argmax(a)
            n2 = [ny, nx, -ny, -nx][a]
            c = np.inner(n1, n2)
            s = (1 - c**2)**0.5
            n = -np.cross(n1, n2)
            n /= np.linalg.norm(n)
            R = np.array([[c+n[0]**2*(1-c),  n[0]*n[1]*(1-c)-n[2]*s, n[2]*n[0]*(1-c)+n[1]*s],
                          [n[0]*n[1]*(1-c)+n[2]*s,  c+n[1]**2*(1-c), n[1]*n[2]*(1-c)-n[0]*s],
                          [n[2]*n[0]*(1-c)-n[1]*s, n[1]*n[2]*(1-c)+n[0]*s, c+n[2]**2*(1-c)]])
            ny = np.inner(R, ny)
            nx = np.inner(R, nx)
        if p3 != None:
            p3 = coors[p3]
            p3 -= np.array([dz, dy, dx])//2
            p3[0] *= self.Hub.ratio
            n3 = p3 - op
            if isinstance(p2, type(None)):
                nz = -np.cross(nx, ny)
                norm3 = np.linalg.norm(n3)
                if norm3 == 0:
                    return None
                n3 /= norm3
                n1 = n3 - nz*np.inner(nz, n3)
                norm1 = np.linalg.norm(n1)
                if norm1 == 0:
                    return None
                n1 /= norm1
            else:
                n3 -= n1*np.inner(n1, n3)
                norm3 = np.linalg.norm(n3)
                if norm3 == 0:
                    return None
                n3 /= norm3
                a = np.array([ny, nx, -ny, -nx])
                a = np.inner(a, n3)
                a = np.argmax(a)
                n1 = [ny, nx, -ny, -nx][a]
            c = np.inner(n3, n1)
            s = (1 - c**2)**0.5
            n = -np.cross(n3, n1)
            n /= np.linalg.norm(n)
            R = np.array([[c+n[0]**2*(1-c),  n[0]*n[1]*(1-c)-n[2]*s, n[2]*n[0]*(1-c)+n[1]*s],
                          [n[0]*n[1]*(1-c)+n[2]*s,  c+n[1]**2*(1-c), n[1]*n[2]*(1-c)-n[0]*s],
                          [n[2]*n[0]*(1-c)-n[1]*s, n[1]*n[2]*(1-c)+n[0]*s, c+n[2]**2*(1-c)]])
            ny = np.inner(R, ny)
            nx = np.inner(R, nx)
        
        pos = np.array([op, ny, nx])
        self.Hub.position.new(pos.tolist(), 0)
        
            
    def add_pt(self):
        
        def add(opt):
            dc, dz, dy, dx = self.Hub.box.shape
            if opt == 0:
                coor = self.Hub.position.asarray()[0]
                coor[0] /= self.Hub.ratio
                coor += np.array([dz, dy, dx])//2
            else:
                selection = self.treeview.selection()
                selection = [int(s) for s in selection]
                coor = np.array(self.getcoordinates())[selection]
                coor = np.average(coor, axis=0)
                
            if (coor < -np.array([dz//2, dy//2, dx//2])).any() or \
                (coor > np.array([dz, dy, dx]) + np.array([dz//2, dy//2, dx//2])).any():
                return
                
            name = "p0"
            names = self.getnames()
            i = 1
            while name in names:
                name = "p{0}".format(i)
                i += 1
            color = self.Hub.channels.auto_color(self.getcolors(), 1, offset=180)[0]
            p = [name, list(color), list(coor)]
            x = [len(self.pts)]
            
            self.add_center.set(True)
            self.Hub.gui.p_on.set(True)
            
            Hub = self.Hub
            hist, idx = Hub.history, Hub.hidx
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.del_points, [x], self.add_points, [x, [p]]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
            gui = Hub.gui
            gui.edit_menu.entryconfig("Undo", state="normal")
            gui.edit_menu.entryconfig("Redo", state="disable")
            gui.master.title("*" + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
            
            self.add_points(x, [p])
            
        selection = self.treeview.selection()
        if len(selection) > 1:
            opt = self.Hub.gui.ask_option(self.Hub.gui.palette, "Options", 
                                          ["Current center",
                                           "Average of selected points"],
                                          geometry="250x120")
            if opt == -1:
                return None
            add(opt)
        else:
            add(0)
                
                
    def del_pt(self, x=None):
        Hub = self.Hub
        if x == None:
            x = self.treeview.selection()
            x = [int(i) for i in x]
        elif x == [-1]:
            return None
        x = np.sort(x).tolist()
        ps = [self.pts[i] for i in x]
        
        hist, idx = Hub.history, Hub.hidx
        
        if idx != -1:
            hist[idx:] = hist[idx:idx+1]
        hist += [[self, [self.add_points, [x, ps], self.del_points, [x]]]]
        if Hub.hidx_saved > idx:
            Hub.hidx_saved = -1 - len(hist)
        else: 
            Hub.hidx_saved -= idx + 2
        Hub.hidx = -1
            
        gui = Hub.gui
        gui.edit_menu.entryconfig("Undo", state="normal")
        gui.edit_menu.entryconfig("Redo", state="disable")
        gui.master.title("*" + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.del_points(x)
    
    
    def clicked(self, click, num=None):
        Hub = self.Hub
        
        la, lb = Hub.geometry["im_size"]
        dc, dz, dy, dx = Hub.box.shape
        op, ny, nx = Hub.position.asarray()
        v = click - np.array([la//2, lb//2])
        coor = op + (ny*v[1] + nx*v[0])/Hub.geometry["exp_rate"]
        coor[0] /= Hub.ratio
        coor += np.array([dz//2, dy//2, dx//2])
        if (coor < -np.array([dz//2, dy//2, dx//2])).any() or \
            (coor > np.array([dz, dy, dx]) + np.array([dz//2, dy//2, dx//2])).any():
            return
        Hub.gui.p_on.set(True)
        
        hist, idx = Hub.history, Hub.hidx
        
        if num==None:
            name = "p0"
            names = self.getnames()
            i = 1
            while name in names:
                name = "p{0}".format(i)
                i += 1
            color = self.Hub.channels.auto_color(self.getcolors(), 1, offset=180)[0]
            p = [name, list(color), list(coor)]
            x = [len(self.pts)]
            
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.del_points, [x], self.add_points, [x,[p]]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
            self.add_points(x, [p])
            
        else:
            old = list(self.pts[num][2])
            new = list(coor)
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [self.change_coor, [num, old], self.change_coor, [num, new]]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
            
            self.change_coor(num, new)
            
        gui = Hub.gui
        gui.edit_menu.entryconfig("Undo", state="normal")
        gui.edit_menu.entryconfig("Redo", state="disable")
        gui.master.title("*" + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
    
    def add_points(self, x, ps):
        for p, i in zip(ps,x):
            self.pts = self.pts[:i] + [p] + self.pts[i:]
        self.Hub.put_points()
        if self.Hub.gui.g_on.get():
            if self.Hub.gui.guide_mode == "guide":
                self.Hub.calc_guide()
            else:
                self.Hub.calc_sideview()
                
        self.refresh_tree()
        self.treeview.selection_set(x)
        
    
    def del_points(self, x):
        for i in x[::-1]:
            self.pts = self.pts[:i] + self.pts[i+1:]
            
        self.Hub.put_points()
        if self.Hub.gui.g_on.get():
            if self.Hub.gui.guide_mode == "guide":
                self.Hub.calc_guide()
            else:
                self.Hub.calc_sideview()
            
        select = np.array([int(s) for s in self.treeview.selection()])
        for i in x[::-1]:
            if i in select:
                j = np.where(select==i)[0][0]
                select = np.append(select[:j], select[j+1:])
            select[select>i] -= 1
        self.refresh_tree()
        x = list(select)
        self.treeview.selection_set(x)
    
    def change_coor(self, num, coor):
        self.pts[num][2] = coor
        self.Hub.put_points()
        if self.Hub.gui.g_on.get():
            if self.Hub.gui.guide_mode == "guide":
                self.Hub.calc_guide()
            else:
                self.Hub.calc_sideview()
        if tuple(str(num)) != self.treeview.selection():
            self.treeview.selection_set(str(num))
        else:
            p = self.pts[num][2]
            self.variables["cr"].set("(x,y,z) = ({0:.1f}, {1:.1f}, {2:.1f})".format(p[2], p[1], p[0]))
    
        
    def undo(self, arg):
        arg[0](*arg[1])
        
    def redo(self, arg):
        arg[2](*arg[3])
        
    def reload(self, pts):
        
        for p in pts:
            p[0] = str(p[0])
            p[1] = [int(p[1][i])%256 for i in range(3)]
            p[2] = [float(p[2][i]) for i in range(3)]
        
        if self.pts == pts:
            return False
        self.pts = pts
        self.refresh_tree()
        return True
    
    
class empty:
    def __init__(self):
        pass
    def __getitem__(self, x):
        return None
