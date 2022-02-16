import gzip
import os
import pickle
import platform
import shutil
import time
import traceback

import cv2
import numpy as np
from PIL import Image, ImageTk
import tifffile as tif
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from .channels import Channels
from .geometry import Geometry
from . import utils as ut

pf = platform.system()

class Stack:
    
    def __init__(self, Hub):
        self.Hub = Hub
        self.cancel = False
    
    def settings(self):
        Hub = self.Hub
        gui = Hub.gui
        
        self.stack_win = tk.LabelFrame(gui.master, text='Stack', relief='raised',
                                       fg='blue', font=('arial', 13, 'bold'))
        self.stack_id = gui.dock_canvas.create_window(500, 0, anchor='nw', window=self.stack_win)
        
        op, ny, nx = Hub.position.asarray()
        nz = -np.cross(ny, nx)
        n = np.array([nz, ny, nx])
        dc, dz, dy, dx = Hub.box.shape
        peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],
                          [dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]], np.float)
        peaks[4:,0] *= Hub.ratio
        peaks -= op + np.array([(dz*Hub.ratio)//2,dy//2,dx//2])
        peaks = np.linalg.solve(n.T, peaks.T).T
        from_ = int(np.amin(peaks[:,0]))
        to = int(np.amax(peaks[:,0]))
        
        la, lb = 350, 300
        lut = Hub.lut
        colors = Hub.colors
        self.expansion = la/(to - from_)
        self.center = int(abs(from_)*self.expansion)
        
        pos = np.array([op, ny, nz])
        pos[:,0] /= Hub.ratio
        pos[0] += np.array([dz, dy, dx])//2
        pos[1:] *= (to - from_)/la
        self.frame1 = np.empty([dc, lb, la], np.uint16)
        ut.calc_section(Hub.box, pos, self.frame1, 
                        np.array([lb//2, self.center], np.int),
                        np.arange(len(lut))[Hub.ch_show])
        image1 = np.empty([*self.frame1.shape[1:], 4], np.uint8)
        if gui.white.get():
            ut.calc_bgr_w(self.frame1, lut, colors, np.arange(len(lut))[Hub.ch_show], image1)
        else:
            ut.calc_bgr(self.frame1, lut, colors, np.arange(len(lut))[Hub.ch_show], image1)
        self.image1 = image1.copy()
        image1[:,self.center] = 255 - image1[:,self.center]
        
        pos = np.array([op, nx, nz])
        pos[:,0] /= Hub.ratio
        pos[0] += np.array([dz, dy, dx])//2
        pos[1:] *= (to - from_)/la
        self.frame2 = np.empty([dc, lb, la], np.uint16)
        ut.calc_section(Hub.box, pos, self.frame2, 
                        np.array([lb//2, self.center], np.int),
                        np.arange(len(lut))[Hub.ch_show])
        image2 = np.empty([*self.frame2.shape[1:], 4], np.uint8)
        if gui.white.get():
            ut.calc_bgr_w(self.frame2, lut, colors, np.arange(len(lut))[Hub.ch_show], image2)
        else:
            ut.calc_bgr(self.frame2, lut, colors, np.arange(len(lut))[Hub.ch_show], image2)
        self.image2 = image2.copy()
        image2[:,self.center] = 255 - image2[:,self.center]
        
        note = ttk.Notebook(self.stack_win)
        note.pack(padx=30)
        
        vert_frame = ttk.Frame(note)
        image1 = np.append(image1[:,:,2::-1], image1[:,:,3:], axis=2)
        self.im1 = ImageTk.PhotoImage(Image.fromarray(image1))
        self.canvas1 = tk.Canvas(vert_frame, width=la, height=lb)
        fill = '#ffffff' if gui.white.get() else '#000000'
        self.canvas1.create_rectangle(0, 0, la, lb, fill=fill, width=0)
        self.im1_id = self.canvas1.create_image(0, 0, anchor='nw', image=self.im1)
        self.canvas1.pack()
        note.add(vert_frame, text='Vertical')
        
        horiz_frame = ttk.Frame(note)
        image2 = np.append(image2[:,:,2::-1], image2[:,:,3:], axis=2)
        self.im2 = ImageTk.PhotoImage(Image.fromarray(image2))
        self.canvas2 = tk.Canvas(horiz_frame, width=la, height=lb)
        fill = '#ffffff' if gui.white.get() else '#000000'
        self.canvas2.create_rectangle(0, 0, la, lb, fill=fill, width=0)
        self.im2_id = self.canvas2.create_image(0, 0, anchor='nw', image=self.im2)
        self.canvas2.pack()
        note.add(horiz_frame, text='Horizontal')
        
        self.s_var = [tk.IntVar(), tk.IntVar(), tk.IntVar(), tk.IntVar()]
        self.s_var[0].set(0)
        self.s_var[1].set(0)
        self.s_var[2].set(180)
        self.s_var[3].set(15)
        
        frame1 = ttk.Frame(self.stack_win)
        ttk.Label(frame1, text='Start: ').grid(column=0, row=0, sticky=tk.E)
        ttk.Label(frame1, text='Stop: ').grid(column=0, row=1, sticky=tk.E)
        tk.Scale(frame1, length=330, variable=self.s_var[0], from_=from_, to=to,
                 orient='horizontal', command=self.st_start).grid(column=1, row=0, 
                                                                  columnspan=6, sticky=tk.W)
        tk.Scale(frame1, length=330, variable=self.s_var[1], from_=from_, to=to,
                 orient='horizontal', command=self.st_stop).grid(column=1, row=1,
                                                                 columnspan=6, sticky=tk.W)
                                                                 
        ttk.Label(frame1, text='Angle (°): ').grid(column=1, row=2, sticky=tk.E, pady=10)
        angles = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]
        self.angle = tk.StringVar(value='180')
        self.angle.trace('w', lambda *args: self.s_var[2].set(int(self.angle.get())))
        ttk.Combobox(frame1, values=angles, width=5, state='readonly',
                     textvariable=self.angle).grid(column=2, row=2, sticky=tk.W, pady=10)
        ttk.Label(frame1, text='Frames: ').grid(column=3, row=2, sticky=tk.E, pady=10)
        fnms = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]
        self.fnm = tk.StringVar(value='15')
        self.fnm.trace('w', lambda *args: self.s_var[3].set(int(self.fnm.get())))
        ttk.Combobox(frame1, values=fnms, width=5, state='readonly',
                     textvariable=self.fnm).grid(column=4, row=2, sticky=tk.W, pady=10)
        
        self.trans = tk.BooleanVar(value=False)
        tk.Radiobutton(frame1, image=self.Hub.gui.ver_image, variable=self.trans, 
                       value=False, indicatoron=False).grid(column=5, row=2, sticky=tk.E)
        tk.Radiobutton(frame1, image=self.Hub.gui.hor_image, variable=self.trans, 
                       value=True, indicatoron=False).grid(column=6, row=2, sticky=tk.W)
        
        for w in frame1.grid_slaves()[:-4]:
            w['state'] = tk.DISABLED
        
        self.buttons = []
        self.i_s = 1
        
        frame2 = ttk.Frame(self.stack_win)
        def cancel():
            self.cancel = True
            try: 
                if len(self.stacks) > 0:
                    return None
            except: pass
            self.repair()
        def ok():
            self.buttons[0]['state'] = tk.DISABLED
            self.buttons[1]['state'] = tk.DISABLED
            for w in frame0.pack_slaves():
                w.state(['disabled'])
            for w in frame1.grid_slaves():
                w.configure(state='disabled')
            self.buttons[0].focus_set()
            gui.master.unbind('<Left>')
            gui.master.unbind('<Right>')
            gui.master.unbind('<Up>')
            gui.master.unbind('<Down>')
            if self.stack_mode.get() == 'S':
                self.stack_single()
            elif self.stack_mode.get() == 'M':
                self.stack_multi()
            elif self.stack_mode.get() == 'A':
                self.stack_span()
        self.buttons += [ttk.Button(frame2, text='Cancel', command=cancel)]
        self.buttons[-1].pack(side=tk.LEFT)
        self.buttons += [ttk.Button(frame2, text='OK', command=ok)]
        self.buttons[-1].pack(side=tk.LEFT)
        
        frame0 = ttk.Frame(self.stack_win)
        frame0.pack(padx=10, anchor=tk.W)
        self.stack_mode = tk.StringVar()
        self.stack_mode.set('S')
        def S():
            for w in frame1.grid_slaves()[:-4]:
                w['state'] = tk.DISABLED
        def M():
            for w in frame1.grid_slaves()[:-4]:
                w['state'] = tk.ACTIVE
        self.buttons += [ttk.Radiobutton(frame0, text='Single projection', value='S', 
                               variable=self.stack_mode, command=S)]
        self.buttons[-1].pack(side=tk.LEFT, padx=5)
        self.buttons += [ttk.Radiobutton(frame0, text='Span', value='A',
                               variable=self.stack_mode, command=S)]
        self.buttons[-1].pack(side=tk.LEFT)
        self.buttons += [ttk.Radiobutton(frame0, text='Rotation', value='M',
                               variable=self.stack_mode, command=M)]
        self.buttons[-1].pack(side=tk.LEFT)
        
        frame1.pack(fill=tk.X, padx=10, pady=10)
        frame2.pack(pady=10)
        
        self.cancel = True
        
        def enter():
            if self.i_s in [0,1]:
                self.buttons[self.i_s].invoke()
        def left():
            if self.i_s == 1:
                self.i_s = 0
            elif self.i_s == 3:
                self.i_s = 2
                self.buttons[self.i_s].invoke()
            elif self.i_s == 4:
                self.i_s = 3
                self.buttons[self.i_s].invoke()
            self.buttons[self.i_s].focus_set()
        def right():
            if self.i_s == 0:
                self.i_s = 1
            elif self.i_s == 2:
                self.i_s = 3
                self.buttons[self.i_s].invoke()
            elif self.i_s == 3:
                self.i_s = 4
                self.buttons[self.i_s].invoke()
            self.buttons[self.i_s].focus_set()
        def up():
            if self.i_s in [0,1]:
                if self.stack_mode.get() == 'S':
                    self.i_s = 2
                elif self.stack_mode.get() == 'A':
                    self.i_s = 3
                elif self.stack_mode.get() == 'M':
                    self.i_s = 4
                self.buttons[self.i_s].focus_set()
        def down():
            if self.i_s in [2,3,4]:
                self.i_s = 1
                self.buttons[self.i_s].focus_set()
        
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
        gui.dock_canvas.moveto(self.stack_id, 0, 0)
        gui.master.bind('<Return>', lambda event: enter())
        gui.master.bind('<Left>', lambda event: left())
        gui.master.bind('<Right>', lambda event: right())
        gui.master.bind('<Up>', lambda event: up())
        gui.master.bind('<Down>', lambda event: down())
        
        self.buttons[1].focus_set()
        
        
    def repair(self):
        Hub = self.Hub
        gui = Hub.gui
        gui.dock_canvas.delete(self.stack_id)
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
        
        
    def stack_single(self):
        Hub = self.Hub
        
        frame = ttk.Frame(self.stack_win)
        frame.pack(fill=tk.X, padx=10, pady=10)
        Label = ttk.Label(frame, text='Calculating...')
        Label.pack(anchor=tk.E, padx=10)
        
        Hub.put_points()
        self.stack_win.update()
        
        self.calc_single()
        
        self.repair()
        
        chs = [[c[0], [c[1][0], c[1][1], c[1][2]],
                c[2], c[3]] for c in Hub.channels.chs]
        
        stac = [self.stacked[None], chs, Hub.geometry.geo,
                {'white back': Hub.gui.white.get(), 'mode': 'single', 'trans': 0}]
        path = str(time.time()) + '.stac'
        try:
            byt = pickle.dumps(stac, protocol=4)
            byt = gzip.compress(byt, compresslevel=1)
            with open(path, 'wb') as f:
                f.write(byt)
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent=self.master)
            return
        gui = self.Hub.gui
        gui.SV.open_new(gui.master, file_path=path+' pop')
        
        
    def stack_multi(self):
        Hub = self.Hub
        
        frame = ttk.Frame(self.stack_win)
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        Label = ttk.Label(frame, text='Preparing...')
        Label.pack(anchor=tk.E, padx=10)
        
        Hub.put_points()
        self.stack_win.update()
        
        op = self.trim_box()
        self.cancel = False
            
        self.stacks = np.zeros([0, *Hub.frame.shape], Hub.frame.dtype)
        
        if self.trans.get():
            self.stacks = self.stacks.transpose(0,1,3,2)
            op = [op[0], op[2], op[1]]
            
        dc, dz, dy, dx = self.box_trim.shape
        
        pos = np.array([op, [0.,1.,0.], [0.,0.,1.]])
        op, ny0, nx0 = pos.copy()
        nz0 = np.cross(ny0, nx0)
        
        angle, self.num = self.s_var[2].get(), self.s_var[3].get()
        angles = np.linspace(-angle/2, angle/2, self.num + 1)/180*np.pi
        if angle == 180:
            angles = angles[:-1]
            self.num -= 1
            
        self.t, self.t2, self.x, self.xt, self.a1 = 0, 0, 0, 0, 0
        Label.pack_forget()
        self.pb = ttk.Progressbar(frame, orient=tk.HORIZONTAL, value=0,
                                  maximum=self.num, mode='determinate')
        self.pb.pack(fill=tk.X)
        self.ml_tx = tk.StringVar(value='(0 / {0})'.format(self.num))
        Label = ttk.Label(frame, textvariable=self.ml_tx)
        Label.pack(anchor=tk.E, padx=10)
        self.buttons[0]['state'] = tk.ACTIVE
        self.stack_win.update()
        
        self.zero = time.time()
        
        for self.n, ang in enumerate(angles):
            pos[2] = np.cos(ang)*nx0 + np.sin(ang)*nz0
            op, ny, nx = pos.copy()
            nz = -np.cross(ny, nx)
            n = np.array([nz, ny, nx])
            
            peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],
                              [dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]], np.float)
            peaks -= op + np.array([dz//2,dy//2,dx//2])
            peaks = np.linalg.solve(n.T, peaks.T).T
            start = int(np.amin(peaks[:,0]))
            stop = int(np.amax(peaks[:,0]))
        
            stacked = self.calc_multi(pos, start, stop)
            if self.cancel:
                break
            self.stacks = np.append(self.stacks, stacked[None], axis=0)
        
        del self.box_trim
        
        if angle == 180 and not self.cancel:
            self.stacks = np.append(self.stacks, self.stacks[:1,:,:,::-1], axis=0)
        
        self.repair()
        
        if len(self.stacks) > 0:
            
            if self.trans.get():
                self.stacks = self.stacks.transpose(0,1,3,2).copy()
            
            chs = [[c[0], [c[1][0], c[1][1], c[1][2]],
                    c[2], c[3]] for c in Hub.channels.chs]
            
            trans = int(angle == 180 and not self.cancel)
            if trans:
                trans += int(self.trans.get())
                
            stac = [self.stacks, chs, Hub.geometry.geo,
                    {'white back': Hub.gui.white.get(), 'mode':'rotation', 
                     'trans': trans}]
            path = str(time.time()) + '.stac'
            try:
                byt = pickle.dumps(stac, protocol=4)
                byt = gzip.compress(byt, compresslevel=1)
                with open(path, 'wb') as f:
                    f.write(byt)
            except:
                messagebox.showerror('Error', traceback.format_exc(),
                                     parent=self.master)
                return
            gui = self.Hub.gui
            gui.SV.open_new(gui.master, file_path=path+' pop')
                
        Hub.put_points()
        
    
    def stack_span(self):
        Hub = self.Hub
        
        frame = ttk.Frame(self.stack_win)
        frame.pack(fill=tk.X, padx=10, pady=10)
        Label = ttk.Label(frame, text='Calculating...')
        Label.pack(anchor=tk.E, padx=10)
        
        Hub.put_points()
        self.stack_win.update()
        
        pos = Hub.position.asarray()
        start, stop = self.s_var[0].get(), self.s_var[1].get()
        nz = -np.cross(pos[1], pos[2])
        
        dc, dz, dy, dx = Hub.box.shape 
        
        pos[:,0] /= Hub.ratio
        pos[0] += np.array([dz//2, dy//2, dx//2])
        nz[0] /= Hub.ratio
        pos[1:] /= Hub.geometry['exp_rate']
        
        box = Hub.box
        
        stacks = np.empty([stop - start + 1, *Hub.frame.shape], dtype=np.uint16)
        ut.span_section(box, pos, nz, start, stop + 1, stacks,
                        np.array(stacks[0,0].shape)//2, np.arange(dc))
        
        self.repair()
            
        chs = [[c[0], [c[1][0], c[1][1], c[1][2]],
                c[2], c[3]] for c in Hub.channels.chs]
        
        stac = [stacks, chs, Hub.geometry.geo,
                {'white back': Hub.gui.white.get(), 'mode': 'span', 'trans': 0}]
        path = str(time.time()) + '.stac'
        try:
            byt = pickle.dumps(stac, protocol=4)
            byt = gzip.compress(byt, compresslevel=1)
            with open(path, 'wb') as f:
                f.write(byt)
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent=self.master)
            return
        gui = self.Hub.gui
        gui.SV.open_new(gui.master, file_path=path+' pop')
                
        Hub.put_points()
        
    
    def st_start(self, v):
        if self.s_var[0].get() >= self.s_var[1].get():
            self.s_var[0].set(self.s_var[1].get())
        pos = self.Hub.position.asarray()
        a = self.s_var[0].get()*np.cross(pos[1], pos[2])
        pos[0] -= a
        
        self.calc_frame(pos)
        
    def st_stop(self, v):
        if self.s_var[0].get() >= self.s_var[1].get():
            self.s_var[1].set(self.s_var[0].get())
        pos = self.Hub.position.asarray()
        a = self.s_var[1].get()*np.cross(pos[1], pos[2])
        pos[0] -= a
        
        self.calc_frame(pos)
        
    def calc_frame(self, pos):
        Hub = self.Hub
        box = Hub.box
        dc, dz, dy, dx = box.shape
        
        pos = np.float64(pos)
        pos[:,0] /= Hub.ratio
        pos[0] += np.array([dz, dy, dx])//2
        pos[1:] /= Hub.geometry['exp_rate']
        
        frame = np.empty(Hub.frame.shape, dtype=np.uint16)
        ut.calc_section(box, pos, frame, np.array(frame[0].shape)//2,
                        np.arange(len(Hub.lut))[Hub.ch_show])
        if Hub.gui.white.get():
            ut.calc_bgr_w(frame, Hub.lut, Hub.colors, np.arange(len(Hub.lut))[Hub.ch_show], Hub.gui.section)
        else:
            ut.calc_bgr(frame, Hub.lut, Hub.colors, np.arange(len(Hub.lut))[Hub.ch_show], Hub.gui.section)
        Hub.put_axes_bar()
        
        start = int(self.s_var[0].get()*self.expansion) + self.center
        stop = int(self.s_var[1].get()*self.expansion) + self.center
        
        image1 = self.image1.copy()
        image1[:,start] = 255 - image1[:,start]
        if start != stop:
            image1[:,stop] = 255 - image1[:,stop]
        image1 = np.append(image1[:,:,2::-1], image1[:,:,3:], axis=2)
        self.im1 = ImageTk.PhotoImage(Image.fromarray(image1))
        self.canvas1.itemconfig(self.im1_id, image=self.im1)
        
        image2 = self.image2.copy()
        image2[:,start] = 255 - image2[:,start]
        if start != stop:
            image2[:,stop] = 255 - image2[:,stop]
        image2 = np.append(image2[:,:,2::-1], image2[:,:,3:], axis=2)
        self.im2 = ImageTk.PhotoImage(Image.fromarray(image2))
        self.canvas2.itemconfig(self.im2_id, image=self.im2)
        
        
    def calc_single(self):
        Hub = self.Hub
        
        # eye = 2.5*Hub.L
        
        pos = Hub.position.asarray()
        start, stop = self.s_var[0].get(), self.s_var[1].get()
        nz = -np.cross(pos[1], pos[2])
        
        dc, dz, dy, dx = Hub.box.shape 
        
        pos[:,0] /= Hub.ratio
        pos[0] += np.array([dz//2, dy//2, dx//2])
        nz[0] /= Hub.ratio
        pos[1:] /= Hub.geometry['exp_rate']
        
        box = Hub.box
        
        if Hub.geometry['exp_rate'] < 1:
            nz /= Hub.geometry['exp_rate']
            start = int(start*Hub.geometry['exp_rate'])
            stop = int(stop*Hub.geometry['exp_rate'])
        
        stacked = np.empty(Hub.frame.shape, dtype=np.uint16)
        ut.stack_section(box, pos, nz, start, stop, stacked, np.array(stacked[0].shape)//2,
                         np.arange(len(Hub.lut)))
        
        self.stacked = stacked
        
    
    def trim_box(self):
        Hub = self.Hub
        
        pos = Hub.position.asarray()
        nz = -np.cross(pos[1], pos[2])
        start, stop = self.s_var[0].get(), self.s_var[1].get()
        
        dc, dz, dy, dx = Hub.box.shape
        
        la0, lb0 = Hub.geometry['im_size']
        
        if Hub.geometry['exp_rate'] < 1:
            if self.trans.get():
                pos[1] *= Hub.geometry['exp_rate']
                lb0 = int(lb0/Hub.geometry['exp_rate'])
            else:
                pos[2] *= Hub.geometry['exp_rate']
                la0 = int(la0/Hub.geometry['exp_rate'])
        
        pos[:,0] /= Hub.ratio
        pos[0] += np.array([dz, dy, dx])//2
        op, ny, nx = pos
        nz[0] /= Hub.ratio
        n = np.array([nz, ny, nx])
        pos[1:] /= Hub.geometry['exp_rate']
            
        peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],[dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]], np.float)
        peaks -= op
        peaks = np.linalg.solve(n.T, peaks.T).T[:,1:] + np.array([lb0,la0])//2
        m, M = np.fmax(np.amin(peaks, axis=0), 0), np.fmin(np.amax(peaks, axis=0), np.array([lb0,la0]))
        
        la, lb = int(M[1] - m[1]), int(M[0] - m[0])
        if self.trans.get():
            la, lb = lb, la
            la0, lb0 = lb0, la0
            pos = pos[[0,2,1]]
        c = (np.array([lb0//2, la0//2]) - m).astype(np.int)
        
        box_trim = np.empty([stop-start+1, dc, lb, la], dtype=np.uint16)
        
        ut.span_section(Hub.box, pos, nz, start, stop, box_trim, c, np.arange(dc))
        
        self.box_trim = box_trim.transpose(1,0,2,3)
        
        opz = self.s_var[1].get() - (stop-start+1)//2
        opy = c[0] - lb//2
        opx = c[1] - la//2
        
        return [opz, opy, opx]
        
    
    def calc_multi(self, pos, start, stop):
        Hub = self.Hub
        # eye = 2.5*Hub.L
        box = self.box_trim
        dc, dz, dy, dx = box.shape
        
        imsize = Hub.geometry['im_size']
        if not self.trans.get():
            imsize = imsize[::-1]
        
        pos = np.array(pos)
        nz = -np.cross(pos[1], pos[2])
        pos[0] += np.array([dz, dy, dx])//2
        stacked = np.empty([dc, *imsize], dtype=np.uint16)
        
        if Hub.geometry['exp_rate'] < 1:
            pos[2] /= Hub.geometry['exp_rate']
            nz /= Hub.geometry['exp_rate']
            start = int(start*Hub.geometry['exp_rate'])
            stop = int(stop*Hub.geometry['exp_rate'])
        ut.stack_section2(box, pos, nz, start, stop, stacked)
        
        im = np.empty([*stacked.shape[1:], 4], np.uint8)
        if Hub.gui.white.get():
            ut.calc_bgr_w(stacked, Hub.lut, Hub.colors, np.arange(len(Hub.lut))[Hub.ch_show], im)
        else:
            ut.calc_bgr(stacked, Hub.lut, Hub.colors, np.arange(len(Hub.lut))[Hub.ch_show], im)
        if self.trans.get():
            im = im.transpose(1,0,2)
        Hub.gui.section = im
        Hub.put_axes_bar()
        
        t = time.time() - self.zero
        try:
            tp = t - (self.n+1)/self.a1
            if tp > 900:
                self.t += tp
                self.xt += ((self.n*(self.n+1))//2)*tp
                self.t2 = (self.xt - self.x*self.t)/self.a1 + self.t**2
        except: pass
        self.t = (self.t*self.n + t)/(self.n + 1)
        self.t2 = (self.t2*self.n + t**2)/(self.n + 1)
        self.x = (self.x*self.n + self.n)/(self.n + 1)
        self.xt = (self.xt*self.n + self.n*t)/(self.n + 1)
        self.n += 1
        self.pb.configure(value=int(self.n))
        self.pb.update()
        try:
            self.a1 = (self.xt - self.x*self.t)/(self.t2 - self.t**2)
            sec = int((self.num - self.n)/self.a1)
            self.ml_tx.set('Remaining {0}:{1:0>2}:{2:0>2}  ({3} / {4})'\
                           .format(sec//3600, sec//60%60, sec%60, self.n, self.num))
        except: pass
        return stacked
    
    
class STAC(ttk.Frame):
    def __init__(self, SV, master, file_path, pop=False):
        
        self.SV = SV
        
        self.file_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        
        resources = cv2.imread('img/resources.png')
        e_image = resources[:14,174:188]
        self.e_image = ImageTk.PhotoImage(Image.fromarray(e_image[:,:,::-1]))
        
        self.key_time = 0
        self.event_time = -np.inf
        self.b_on = tk.BooleanVar()
        self.b_on.set(True)
        self.d_on = tk.BooleanVar()
        self.d_on.set(True)
        self.white = tk.BooleanVar()
        self.white.set(False)
        self.zoom = tk.StringVar()
        self.upperleft = (0,0)
        self.lock = False
        
        self.first = True
        
        super().__init__(master)
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self.create_widgets()
        self.master.update()
        
        def close():
            if self.master.winfo_exists: 
                self.master.destroy()
            self.SV.root.destroy()
        try:
            self.Hub = Hub_stack(self, file_path, pop=pop)
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent=self.master)
            close()
            return
        if not self.Hub.load_success:
            close()
            return
        
        if pop:
            self.file_path = None
            self.title = 'stack'
            self.master.title('*' + self.title)
            self.Hub.hidx_saved = -2
        else:
            self.file_path = file_path
            self.title = self.file_name
            self.master.title(self.title)
        
        self.create_commands()
        self.stack_cf.focus_set()
        
        if pf == 'Windows':
            self.flags = np.array([1,4,131072,4,256])
        elif pf == 'Darwin':
            self.flags = np.array([1,4,16,8,256])
        elif pf == 'Linux':
            self.flags = np.array([1,4,8,4,256])
            
        
    def create_widgets(self):
        
        self.menu_bar = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        self.menu_bar.add_cascade(label='Edit', menu=self.edit_menu)
        self.master.config(menu=self.menu_bar)
        
        # Dock
        self.dock_frame = tk.Frame(self.master)
        self.dock_frame.pack(padx=10, pady=2, side=tk.RIGHT)
        width = 470 if pf == 'Darwin' else 420
        self.dock_canvas = tk.Canvas(self.dock_frame, width=width, height=590)
        self.dock_canvas.pack(side=tk.LEFT)
        self.dock_note = ttk.Notebook(self.master)
        self.dock_canvas.create_window(0, 0, anchor='nw', window=self.dock_note)
        bary = tk.Scrollbar(self.dock_frame, orient=tk.VERTICAL)
        bary.pack(side=tk.RIGHT, fill=tk.Y)
        bary.config(command=self.dock_canvas.yview)
        self.dock_canvas.config(yscrollcommand=bary.set)
        self.dock_canvas.config(scrollregion=(0,0,0,590))
        
        # Main
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.top = ttk.Frame(self.main_frame)
        self.top.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)
        
        self.display = ttk.LabelFrame(self.top, text='Display')
        self.display.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(self.display, text='Zoom (%)').grid(column=0, row=0, padx=5, sticky=tk.W)
        ttk.Button(self.display, width=4, image=self.e_image, command=self.fit_frame).grid(column=1, row=0, sticky=tk.W)
        self.zm_values = [  10,  13,  16,  20,  25,  32,  40,  50,  63,  79,
                           100, 126, 158, 200, 251, 316, 398, 501, 631, 794,
                          1000,1259,1585,1995]
        self.combo_zm = ttk.Combobox(self.display, values=self.zm_values, width=12, textvariable=self.zoom)
        self.combo_zm.bind('<Return>', lambda event: self.zm_enter())
        self.combo_zm.bind('<FocusOut>', lambda event: self.zm_enter())
        self.combo_zm.bind('<<ComboboxSelected>>', lambda event: self.zm_enter())
        self.combo_zm.grid(column=0, row=1, columnspan=2, padx=5, sticky=tk.W)
        self.chk_b = ttk.Checkbutton(self.display, variable=self.b_on, text='Scale bar (B)',
                                     command=self.b_switch)
        self.chk_b.grid(column=2, row=0, padx=5, sticky=tk.W)
        self.chk_d = ttk.Checkbutton(self.display, variable=self.d_on, text='Dock (D)',
                                     command=self.d_switch)
        self.chk_d.grid(column=2, row=1, padx=5, sticky=tk.W)
        self.rad_b = ttk.Radiobutton(self.display, text='Black', value=False, 
                                     variable=self.white, command=self.wb_switch)
        self.rad_b.grid(column=3, row=0, padx=5, sticky=tk.W)
        self.rad_w = ttk.Radiobutton(self.display, text='White', value=True, 
                                     variable=self.white, command=self.wb_switch)
        self.rad_w.grid(column=3, row=1, padx=5, sticky=tk.W)
        
        self.bottom = ttk.Frame(self.main_frame)
        self.bottom.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, expand=True)
        
        self.saving = tk.StringVar(value='')
        ttk.Label(self.bottom, textvariable=self.saving).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.bar_frame = ttk.Frame(self.bottom)
        self.bar_frame.pack(side=tk.RIGHT)
        ttk.Label(self.bar_frame, text='µm').pack(side=tk.RIGHT, anchor=tk.N, padx=5, pady=5)
        self.bar_text = tk.StringVar()
        self.bar_text.set('0')
        self.bar_entry = ttk.Entry(self.bar_frame, textvariable=self.bar_text,
                                   width=10, justify=tk.RIGHT)
        self.bar_entry.pack(side=tk.RIGHT, anchor=tk.N, pady=5)
        ttk.Label(self.bar_frame, text='Scale bar:').pack(side=tk.RIGHT, anchor=tk.N, padx=5, pady=5)
        
        self.stack_frame = ttk.Frame(self.main_frame)
        self.stack_frame.pack(padx=2, pady=3)
        self.stack_cf = ttk.Frame(self.stack_frame)
        self.stack_canvas = tk.Canvas(self.stack_cf, width=2000, height=2000)
        self.barx = tk.Scrollbar(self.stack_frame, orient=tk.HORIZONTAL)
        self.barx.pack(side=tk.BOTTOM, fill=tk.X)
        self.bary = tk.Scrollbar(self.stack_frame, orient=tk.VERTICAL)
        self.bary.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stack_canvas.pack(side=tk.LEFT, anchor=tk.NW)
        self.stack_cf.pack(side=tk.LEFT)
        
        fill ='#ffffff' if self.white.get() else '#000000'
        self.im_back = self.stack_canvas.create_rectangle(0, 0, 0, 0, fill=fill, width=0)
        self.im_id = self.stack_canvas.create_image(0, 0, anchor='nw')
        
        if self.d_on.get():
            self.master.minsize(850, 400)
        else:
            self.master.minsize(400, 400)
        
    
    def create_commands(self):
        Hub = self.Hub
        
        self.file_menu.add_command(label='Open', 
                                   command=lambda: self.SV.open_new(self.master), 
                                   accelerator='Ctrl+O')
        self.file_menu.add_command(label='Save', 
                                   command=lambda: self.save(self.file_path), 
                                   accelerator='Ctrl+S')
        self.file_menu.add_command(label='Save As', 
                                   command=self.save, 
                                   accelerator='Ctrl+Shift+S')
        self.file_menu.add_command(label='Export', 
                                   command=self.export, 
                                   accelerator='Ctrl+E')
        
        self.edit_menu.add_command(label='Undo', 
                                   command=Hub.undo, 
                                   accelerator='Ctrl+Z')
        self.edit_menu.add_command(label='Redo', 
                                   command=Hub.redo, 
                                   accelerator='Ctrl+Y')
        
        self.edit_menu.entryconfig('Undo', state='disable')
        self.edit_menu.entryconfig('Redo', state='disable')
        
        if len(Hub.stacks) > 1:
            self.mlt_frm = tk.IntVar(value=0)
            tk.Scale(self.top, variable=self.mlt_frm, from_=0, to=self.to, 
                     command=Hub.mlt_update, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        def set_bar(new):
            self.bar_text.trace_vdelete('w', self.bar_text.trace_id)
            self.bar_text.set(new)
            self.bar_text.trace_id = self.bar_text.trace('w', Hub.geometry.set_bar_length)
        self.bar_text.trace_id = self.bar_text.trace('w', Hub.geometry.set_bar_length)
        self.bar_text.set_bar = set_bar
        self.bar_text.set_bar(Hub.geometry['bar_len'])
        if Hub.geometry['bar_len'] == None:
            self.bar_entry.configure(state=tk.DISABLED)
        self.bar_entry.bind('<FocusOut>', Hub.geometry.bar_entry_out)
        
        self.barx.config(command=self.stack_canvas.xview)
        self.bary.config(command=self.stack_canvas.yview)
        self.stack_canvas.config(yscrollcommand=self.bary_set)
        self.stack_canvas.config(xscrollcommand=self.barx_set)
        
        if pf == 'Windows':
            self.stack_canvas.bind('<MouseWheel>', lambda event: 
                                     self.stack_canvas.\
                                         yview_scroll(int(-event.delta/120), 'units'))
            self.stack_canvas.bind('<Shift-MouseWheel>', lambda event: 
                                     self.stack_canvas.\
                                         xview_scroll(int(-event.delta/120), 'units'))
            self.stack_canvas.bind('<Control-MouseWheel>', 
                                   lambda event: self.zm_scroll(event, int(event.delta/120)))
        elif pf == 'Darwin':
            self.stack_canvas.bind('<MouseWheel>', lambda event: 
                                     self.stack_canvas.\
                                         yview_scroll(int(-event.delta), 'units'))
            self.stack_canvas.bind('<Shift-MouseWheel>', lambda event: 
                                     self.stack_canvas.\
                                         xview_scroll(int(-event.delta), 'units'))
            self.stack_canvas.bind('<Command-MouseWheel>', 
                                 lambda event: self.zm_scroll(event, int(event.delta)))
        elif pf == 'Linux':
            self.stack_canvas.bind('<Button-4>', lambda event: 
                                       self.stack_canvas.yview_scroll(1, 'units'))
            self.stack_canvas.bind('<Button-5>', lambda event: 
                                       self.stack_canvas.yview_scroll(-1, 'units'))
            self.stack_canvas.bind('<Shift-Button-4>', lambda event: 
                                       self.stack_canvas.xview_scroll(1, 'units'))
            self.stack_canvas.bind('<Shift-Button-5>', lambda event: 
                                       self.stack_canvas.xview_scroll(-1, 'units'))
            self.stack_canvas.bind('<Control-Button-4>', 
                                   lambda event: self.zm_scroll(event, -1))
            self.stack_canvas.bind('<Control-Button-5>', 
                                   lambda event: self.zm_scroll(event, 1))
        
        self.stack_cf.bind('<Configure>', self.stack_configure)
        
        self.master.bind('<Key>', self.key)
        
    
    def key(self, event):
        t = time.time()
        if event.time - self.key_time < 40:
            return
        self.event_time = max(self.event_time, event.time - t*1000)
        
        done = True
        key = event.keysym
        if event.state//self.flags[3]%2 == 1:
            if key == 'o':
                self.SV.open_new(self.master)
            elif key == 's':
                self.saving.set('Saving...')
                self.master.update()
                self.master.after(10, self.save, self.file_path)
            elif key == 'S':
                self.saving.set('Saving...')
                self.master.update()
                self.master.after(10, self.save)
            elif key == 'e':
                self.export()
            elif key == 'z':
                self.Hub.undo()
            elif key == 'y':
                self.Hub.redo()
            else:
                done = False
        else:
            focus = str(self.master.focus_get()).rsplit('!', 1)[-1]
            if 'entry' in focus:
                return
            elif 'combo' in focus:
                return
            if key in ['b', 'd']:
                getattr(self, 'chk_{0}'.format(key)).invoke()
            elif key in ['c']:
                if self.d_on.get():
                    return
                self.d_on.set(True)
                self.d_switch()
            elif key == 'Left':
                if hasattr(self, 'mlt_frm'):
                    self.Hub.mlt_scale(-1)
                else:
                    done = False
            elif key == 'Right':
                if hasattr(self, 'mlt_frm'):
                    self.Hub.mlt_scale(1)
                else:
                    done = False
        if done:
            self.key_time = time.time()*1000 + self.event_time
        
        
    def on_close(self):
        if self.Hub.hidx == self.Hub.hidx_saved:
            self.master.destroy()
            del self.Hub
            self.SV.root.destroy()
        else:
            ans = messagebox.askyesnocancel(title='Closing', 
                                            message='Do you want to save '
                                                    'changes before you quit?',
                                            parent=self.master)
            if ans == None:
                return
            if ans:
                if self.save(self.file_path):
                    self.master.destroy()
                    del self.Hub
                    self.SV.root.destroy()
            else:
                self.master.destroy()
                del self.Hub
                self.SV.root.destroy()
            
            
    def b_switch(self):
        self.Hub.put_axes_bar()
        
    def d_switch(self):
        if self.d_on.get():
            width = 470 if pf == 'Darwin' else 420
            self.dock_canvas.configure(width=width)
            self.dock_canvas.moveto(self.dock_id, 0, 0)
            self.master.minsize(850, 400)
        else:
            self.dock_canvas.configure(width=0)
            self.dock_canvas.moveto(self.dock_id, 500, 0)
            self.master.minsize(400, 400)
        
    def wb_switch(self):
        self.Hub.calc_image()
        
    def zm_enter(self):
        if not self.lock:
            self.lock = True
            self.master.after(1, self.zm_enter_)
    
    def zm_scroll(self, event, delta):
        if not self.lock:
            self.lock = True
            x, y = event.x, event.y
            w, h = self.stack_cf.winfo_width()-4, self.stack_cf.winfo_height()-4
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
        
        w, h = self.stack_cf.winfo_width()-4, self.stack_cf.winfo_height()-4
        ih, iw = self.image.shape[:2]
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
        self.master.after(10, unlock)
        
        
    def stack_configure(self, event):
        w, h = self.stack_cf.winfo_width()-4, self.stack_cf.winfo_height()-4
        ih, iw = self.image.shape[:2]
        if not hasattr(self.Hub, 'zoom'):
            zoom = min((w-10)/iw, (h-10)/ih)
            self.zoom.set(str(int(zoom*100)))
            self.Hub.zoom = float(self.zoom.get())/100
        if self.first:
            self.first = False        
            self.Hub.put_axes_bar()
        
        zoom = self.Hub.zoom
        iw, ih = int(iw*zoom), int(ih*zoom)
        x0, y0 = self.upperleft
        x, y = w//2 - iw//2, h//2 - ih//2
        self.stack_canvas.coords(self.im_id, x+x0, y+y0)
        self.stack_canvas.coords(self.im_back, x, y, x+iw, y+ih)
        self.stack_canvas.config(scrollregion=(x-w+50,y-h+50,x+iw+w-50,y+ih+h-50))
        self.imx, self.imy = x, y
        
    
    def fit_frame(self):
        w, h = self.stack_cf.winfo_width()-4, self.stack_cf.winfo_height()-4
        ih, iw = self.image.shape[:2]
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
        w, h = self.stack_cf.winfo_width()-4, self.stack_cf.winfo_height()-4
        zoom = self.Hub.zoom
        ih, iw = self.image.shape[:2]
        iw, ih = int(iw*zoom), int(ih*zoom)
        u1 = int(vx[0]*(2*w+iw-100) - w + 50)
        u2 = int(vy[0]*(2*h+ih-100) - h + 50)
        upperleft = (u1, u2)
        if upperleft != self.upperleft:
            self.upperleft = upperleft
            self.Hub.put_axes_bar()
        
        
    def save(self, path=None):
        if path == None:
            filetypes = [('SV multi-stack', '*.stac')]
            
            if os.path.isfile('init_dir.txt'):
                with open('init_dir.txt', 'r') as f:
                    initialdir = f.read()
                if not os.path.isdir(initialdir):
                    initialdir = os.path.dirname(self.iDir)
            else:
                initialdir = self.file_dir
            initialfile = os.path.splitext(self.file_name)[0]
            path = filedialog.asksaveasfilename(parent=self.master,
                                                filetypes=filetypes,
                                                initialdir=initialdir,
                                                initialfile=initialfile,
                                                title='Save',
                                                defaultextension='.stac')
        
        if len(path) > 0:
            path = path.replace('\\', '/')
            meta = {'scale bar': self.b_on.get(), 'white back': self.white.get(), 
                    'zoom':self.Hub.zoom, 'upperleft': self.upperleft,
                    'mode':self.mode, 'trans':self.trans}
            try:
                byt = pickle.dumps([self.Hub.stacks, self.Hub.channels.chs, 
                                    self.Hub.geometry.geo, meta], protocol=4)
                byt = gzip.compress(byt, compresslevel=1)
                with open(path, 'wb') as f:
                    f.write(byt)
            except:
                messagebox.showerror('Error', traceback.format_exc(),
                                     parent=self.master)
                return False
            self.saving.set('')
            with open('init_dir.txt', 'w') as f:
                f.write(os.path.dirname(path))
            self.title = os.path.basename(path)
            
            self.file_path = path
            self.file_dir = os.path.dirname(path)
            self.file_name = os.path.basename(path)
            
            self.Hub.hidx_saved = self.Hub.hidx
            self.master.title(self.title)
            
            return True
        else:
            return False
        
        
        
    def imwrite(self, filename, img, params=None):
        try:
            ext = os.path.splitext(filename)[1]
            result, n = cv2.imencode(ext, img, params)
    
            if result:
                with open(filename, mode='w+b') as f:
                    n.tofile(f)
                return True
            else:
                return False
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent=self.master)
            return False
        
        
    def export(self):
        if len(self.Hub.stacks) > 1:
            filetypes = [('Portable Network Graphics', '*.png'), 
                         ('JPEG files', '*.jpg'),
                         ('MP4 file format', '*.mp4'),
                         ('TIFF files', '*.tif'),
                         ('JPEG 2000 files', '*.jp2'),
                         ('Portable image format', '*.pbm'),
                         ('Sun rasters', '*.sr')]
        else:
            filetypes = [('Portable Network Graphics', '*.png'), 
                         ('JPEG files', '*.jpg'),
                         ('TIFF files', '*.tif'),
                         ('JPEG 2000 files', '*.jp2'),
                         ('Portable image format', '*.pbm'),
                         ('Sun rasters', '*.sr')]
        
        if os.path.isfile('init_dir.txt'):
            with open('init_dir.txt', 'r') as f:
                initialdir = f.read()
            if not os.path.isdir(initialdir):
                initialdir = self.file_dir
        else:
            initialdir = self.file_dir
        initialfile = os.path.splitext(self.file_name)[0]
        path = filedialog.asksaveasfilename(parent=self.master, 
                                            filetypes=filetypes,
                                            initialdir=initialdir,
                                            initialfile=initialfile,
                                            title='Export the image',
                                            defaultextension='.png')
        if len(path) > 0:
            path = path.replace('\\', '/')
            if path[-4:] == '.mp4':
                self.ask_fps(path)
                with open('init_dir.txt', 'w') as f:
                    f.write(os.path.dirname(path))
                return
            Hub = self.Hub
            im = self.image.copy()
            if self.b_on.get():
                im[-25:-20, -20-Hub.lpx:-20,:3] = 0 if self.white.get() else 255
                im[-25:-20, -20-Hub.lpx:-20,3] = 255 - im[-25:-20, -20-Hub.lpx:-20,3]
            opt = 1
            if path[-4:] == '.png':
                opt = self.ask_option(self.master, 'Saving options', 
                                      ['Transparent PNG (RGBA)',
                                       '24-bit PNG (RGB)'],
                                      geometry='250x120')
            if path[-4:] == '.tif':
                opt = self.ask_option(self.master, 'Saving options',
                                      ['Section image (RGB)',
                                       'Section data (16 bit)'])
                if opt == 1:
                    sort = np.argsort(Hub.channels.getnames())
                    try:
                        tif.imwrite(path, Hub.frame[sort])
                    except:
                        messagebox.showerror('Error', traceback.format_exc() + 
                                             '\nFailed to export TIFF file',
                                             parent=self.master)
                        return
                    with open('init_dir.txt', 'w') as f:
                        f.write(os.path.dirname(path))
                    return
            if opt == 1:
                a = im[:,:,3:]/255
                im = im[:,:,:3]*a
                if self.white.get():
                    im += 255*(1-a)
                im = im.astype(np.uint8)
            elif opt == -1:
                return
            
            if self.imwrite(path, im):
                with open('init_dir.txt', 'w') as f:
                    f.write(os.path.dirname(path))
            
            
    def ask_fps(self, path):
        self.fps_win = tk.Toplevel(self.master)
        self.fps_win.withdraw()
        if pf == 'Windows':
            self.fps_win.iconbitmap('img/icon.ico')
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
                shape = (int(len(self.image[0])), int(len(self.image)))
                path0 = os.path.basename(path)
                
                if os.path.isfile(path0):
                    os.remove(path0)
                    
                out = cv2.VideoWriter(path0, fourcc, f, shape, True)
                pb = ttk.Progressbar(frame, orient=tk.HORIZONTAL, value=0, length=100,
                                     maximum=self.to, mode='determinate')
                pb.pack(fill=tk.X, pady=5)
                button = ttk.Button(frame, text='Cancel', command=cancel)
                button.pack(pady=5)
                button.focus_set()
                
                for i in range(self.to+1):
                    pb.configure(value=i)
                    pb.update()
                    if i < len(self.Hub.stacks):
                        self.Hub.frame = self.Hub.stacks[i]
                    else:
                        self.Hub.frame = self.Hub.stacks[i-len(self.Hub.stacks)+1]
                        self.Hub.frame = self.Hub.frame[:,::-1].copy() if self.trans==2 else self.Hub.frame[:,:,::-1].copy()
                    self.Hub.calc_image()
                    if self.cancel:
                        break
                    im = self.image.copy()
                    if self.b_on.get():
                        im[-25:-20, -20-self.Hub.lpx:-20, :3] = 0 if self.white.get() else 255
                        im[-25:-20, -20-self.Hub.lpx:-20, 3] = 255
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
            win.iconbitmap('img/icon.ico')
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
            
        
class Hub_stack:
    def __init__(self, gui, path, pop=False):
        self.gui = gui
        if pop:
            with open(path, 'rb') as f:
                byt = f.read()
            byt = gzip.decompress(byt)
            self.stacks, self.channels, self.geometry, *args = pickle.loads(byt)
            os.remove(path)
        else:
            with open(path, 'rb') as f:
                byt = f.read()
            byt = gzip.decompress(byt)
            self.stacks, self.channels, self.geometry, *args = pickle.loads(byt)
        
        self.channels = Channels(self)
        self.geometry = Geometry(self)
        
        if len(args) == 0:
            gui.white.set(False)
        else:
            if 'white back' in args[0]:
                gui.white.set(args[0]['white back'])
            else:
                gui.white.set(False)
            if 'scale bar' in args[0]:
                gui.b_on.set(args[0]['scale bar'])
            if 'zoom' in args[0]:
                gui.zoom.set(str(int(args[0]['zoom']*100)))
                self.zoom = int(gui.zoom.get())/100
            if 'upperleft' in args[0]:
                gui.upperleft = args[0]['upperleft']
            if 'mode' in args[0]:
                gui.mode = args[0]['mode']
            else:
                gui.mode = 'rotation' if len(self.stacks) > 1 else 'single'
            if 'trans' in args[0]:
                gui.trans = args[0]['trans']
            else:
                gui.trans = 0
                if gui.mode == 'rotation':
                    if (self.stacks[0]==self.stacks[-1][:,::-1]).all():
                        gui.trans = 2
                    elif (self.stacks[0]==self.stacks[-1][:,:,::-1]).all():
                        gui.trans = 1
            gui.to = len(self.stacks) - 1 if gui.trans==0 else len(self.stacks)*2 - 3
        
        if not hasattr(self, 'zoom'):
            w, h = gui.stack_cf.winfo_width()-4, gui.stack_cf.winfo_height()-4
            iw, ih = self.geometry['im_size']
            zoom = min((w-10)/iw, (h-10)/ih)
            iw1, ih1 = int(iw*zoom), int(ih*zoom)
            ul = (int(iw1//2-w//2), int(ih1//2-h//2))
            zs = str(int(zoom*100))
            gui.zoom.set(zs)
            self.zoom = float(gui.zoom.get())/100
            gui.upperleft = ul
        
        self.ch_show = np.ones(len(self.channels), np.bool)
        self.frame = self.stacks[0]
        
        self.history = [[0,empty()]]
        self.hidx = -1
        self.hidx_saved = -1
        
        self.calc_image()
        self.calc_frame = self.calc_image
        self.load_success = True
        
    
    def calc_image(self, x=None):
        if not hasattr(self.gui, 'image'):
            self.gui.image = np.empty([*self.frame.shape[1:], 4], np.uint8)
        if self.gui.white.get():
            ut.calc_bgr_w(self.frame, self.lut, self.colors,
                          np.arange(len(self.lut))[self.ch_show], self.gui.image)
        else:
            ut.calc_bgr(self.frame, self.lut, self.colors,
                        np.arange(len(self.lut))[self.ch_show], self.gui.image)
        if hasattr(self.gui, 'stack_canvas'):
            x, y, iw, ih, w, h = self.put_axes_bar()
            self.scroll_config(x, y, iw, ih, w, h)
    
    
    def put_axes_bar(self):
        im = self.gui.image.copy()
        if self.gui.b_on.get():
            im[-25:-20, -20-self.lpx:-20,:3] = 0 if self.gui.white.get() else 255
            im[-25:-20, -20-self.lpx:-20,3] = 255 - im[-25:-20, -20-self.lpx:-20,3]
        
        zoom = self.zoom
        ih, iw = im.shape[:2]
        iw, ih = int(iw*zoom), int(ih*zoom)
        
        x0, y0 = self.gui.upperleft
        w, h = self.gui.stack_cf.winfo_width()-4, self.gui.stack_cf.winfo_height()-4
        im = cv2.warpAffine(im, np.array([[zoom,0,-x0],[0,zoom,-y0]], dtype=np.float),
                            (w, h))
        x, y = w//2 - iw//2, h//2 - ih//2
        self.gui.stack_canvas.coords(self.gui.im_id, x+x0, y+y0)
        self.gui.stack_canvas.coords(self.gui.im_back, x, y, x+iw, y+ih)
        im = np.append(im[:,:,2::-1], im[:,:,3:], axis=2)
        self.gui.stack_im = ImageTk.PhotoImage(Image.fromarray(im))
        self.gui.stack_canvas.itemconfig(self.gui.im_id, image=self.gui.stack_im)
        fill = '#ffffff' if self.gui.white.get() else '#000000'
        self.gui.stack_canvas.itemconfig(self.gui.im_back, fill=fill)
        
        return x, y, iw, ih, w, h
        
    def scroll_config(self, x, y, iw, ih, w, h, vx0=None, vy0=None):
        gui = self.gui
        sr = (x-w+50,y-h+50,x+iw+w-50,y+ih+h-50)
        gui.stack_canvas.config(scrollregion=sr)
        gui.imx, gui.imy = x, y
        x0, y0 = gui.upperleft
        if vx0==None:
            vx0 = (x0+x-sr[0])/(sr[2]-sr[0])
        if vy0==None:
            vy0 = (y0+y-sr[1])/(sr[3]-sr[1])
        gui.stack_canvas.xview_moveto(vx0)
        gui.stack_canvas.yview_moveto(vy0)
        
    
    def mlt_scale(self, sign):
        if sign < 0:
            self.gui.mlt_frm.set((self.gui.mlt_frm.get() - 1)%(self.gui.to + 1))
        elif sign > 0:
            self.gui.mlt_frm.set((self.gui.mlt_frm.get() + 1)%(self.gui.to + 1))
        self.mlt_update(0)
    
        
    def mlt_update(self, v):
        i = self.gui.mlt_frm.get()
        if i < len(self.stacks):
            self.frame = self.stacks[i]
        else:
            self.frame = self.stacks[i-len(self.stacks)+1]
            self.frame = self.frame[:,::-1].copy() if self.gui.trans==2 else self.frame[:,:,::-1].copy()
        self.calc_image()
        
        
    def undo(self):
        if self.hidx > -len(self.history):
            try:
                self.history[self.hidx][0].undo(self.history[self.hidx][1])
            except:
                return
            self.hidx -= 1
            
            self.gui.edit_menu.entryconfig('Redo', state='normal')
            if self.hidx == -len(self.history):
                self.gui.edit_menu.entryconfig('Undo', state='disable')
            self.gui.master.title('*' + self.gui.title if self.hidx != self.hidx_saved else self.gui.title)
    
    def redo(self):
        if self.hidx != -1:
            self.hidx += 1
            try:
                self.history[self.hidx][0].redo(self.history[self.hidx][1])
            except:
                self.hidx -= 1
                return
            
            self.gui.edit_menu.entryconfig('Undo', state='normal')
            if self.hidx == -1:
                self.gui.edit_menu.entryconfig('Redo', state='disable')
            self.gui.master.title('*' + self.gui.title if self.hidx != self.hidx_saved else self.gui.title)
            
            
class empty:
    def __init__(self):
        pass
    def __getitem__(self, x):
        return None

