import gzip
import pickle
import time
import uuid

import numpy as np
import tkinter as tk
from tkinter import ttk

from ..tools import launch, base_dir, tk_from_array, synthesize_image
from .gui import Base_GUI
from .. import utils as ut


class Stack_GUI(Base_GUI):
    
    def __init__(self, main):
        super().__init__(main)
        
        self.main = main
        self.interrupt = False
        self.active = False
        self.base_frame = tk.LabelFrame(main.master, text='Stack', relief='raised',
                                        fg='blue', font=('arial', 13, 'bold'))
        self.stack_id = main.dock_canvas.create_window(500, 0, anchor='nw', 
                                                       window = self.base_frame)
        im_size = 350, 300
        self.im_size = im_size
        
        note = ttk.Notebook(self.base_frame)
        note.pack(padx=30)
        
        vert_frame = ttk.Frame(note)
        self.canvas1 = tk.Canvas(vert_frame, width = im_size[0], height = im_size[1])
        self.im1_id = self.canvas1.create_image(0, 0, anchor='nw')
        self.canvas1.pack()
        note.add(vert_frame, text='Vertical')
        
        horz_frame = ttk.Frame(note)
        self.canvas2 = tk.Canvas(horz_frame, width = im_size[0], height = im_size[1])
        self.im2_id = self.canvas2.create_image(0, 0, anchor='nw')
        self.canvas2.pack()
        note.add(horz_frame, text='Horizontal')
        
        self.vars = {
            'start': tk.IntVar(),
            'stop': tk.IntVar(), 
            'frames': tk.StringVar(),
            'trans': tk.BooleanVar(), 
            'mode': tk.StringVar()}
        
        control_frame = ttk.Frame(self.base_frame)
        self.control_frame = control_frame
        ttk.Label(control_frame, text='Start: ').grid(column=0, row=0, sticky=tk.E)
        ttk.Label(control_frame, text='Stop: ').grid(column=0, row=1, sticky=tk.E)
        self.start_scale = tk.Scale(control_frame, length = 330, 
                                    variable = self.vars['start'],
                                    orient = 'horizontal', 
                                    command = self.start_trace)
        self.start_scale.grid(column=1, row=0, columnspan=6, sticky=tk.W)
        self.stop_scale = tk.Scale(control_frame, length = 330, 
                                   variable = self.vars['stop'],
                                   orient = 'horizontal', 
                                   command = self.stop_trace)
        self.stop_scale.grid(column=1, row=1, columnspan=6, sticky=tk.W)
                                                                 
        ttk.Label(control_frame, text='Frames: ').grid(column=3, row=2, sticky=tk.E, pady=10)
        fnms = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        ttk.Combobox(control_frame, values=fnms, width=5, state='readonly',
                     textvariable=self.vars['frames']).grid(column=4, row=2, sticky=tk.W, pady=10)
        
        tk.Radiobutton(control_frame, image=self.main.ver_image, variable=self.vars['trans'], 
                       value=False, indicatoron=False).grid(column=5, row=2, sticky=tk.E)
        tk.Radiobutton(control_frame, image=self.main.hor_image, variable=self.vars['trans'], 
                       value=True, indicatoron=False).grid(column=6, row=2, sticky=tk.W)
        
        for w in control_frame.grid_slaves()[:-4]:
            w['state'] = tk.DISABLED
        
        self.buttons = []
        
        ok_frame = ttk.Frame(self.base_frame)
        self.buttons += [ttk.Button(ok_frame, text='Cancel', command=self.cancel)]
        self.buttons[-1].pack(side=tk.LEFT)
        self.buttons += [ttk.Button(ok_frame, text='OK', command=self.ok)]
        self.buttons[-1].pack(side=tk.LEFT)
        
        self.radio_frame = ttk.Frame(self.base_frame)
        self.radio_frame.pack(padx=10, anchor=tk.W)
        def pro_select():
            for w in control_frame.grid_slaves()[:-4]:
                w['state'] = tk.DISABLED
        def spa_select():
            for w in control_frame.grid_slaves()[2:-4]:
                w['state'] = tk.NORMAL
            for w in control_frame.grid_slaves()[:2]:
                w['state'] = tk.DISABLED
        def rot_select():
            for w in control_frame.grid_slaves()[:-4]:
                w['state'] = tk.NORMAL
        self.buttons += [ttk.Radiobutton(self.radio_frame, 
                                         text = 'Projection', value = 'projection', 
                                         variable = self.vars['mode'], 
                                         command = pro_select)]
        self.buttons[-1].pack(side=tk.LEFT, padx=5)
        self.buttons += [ttk.Radiobutton(self.radio_frame, 
                                         text = 'Span', value = 'span',
                                         variable = self.vars['mode'], 
                                         command = spa_select)]
        self.buttons[-1].pack(side=tk.LEFT)
        self.buttons += [ttk.Radiobutton(self.radio_frame, 
                                         text = 'Rotation', value = 'rotation',
                                         variable = self.vars['mode'], 
                                         command = rot_select)]
        self.buttons[-1].pack(side=tk.LEFT)
        
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        ok_frame.pack(pady=10)
    
    def settings(self):
        main = self.main
        
        op, ny, nx = main.position
        from_, to = main.position.depth_range
        self.start_scale.configure(from_ = from_, to = to)
        self.stop_scale.configure(from_ = from_, to = to)
        self.org_op = op.copy()
        
        im_size = self.im_size
        exp_rate = im_size[0] / (to - from_)
        self.exp_rate = exp_rate
        secv1 = self.main.secv.copy()
        secv1.geometry['image_size'] = im_size
        secv1.geometry['expansion_rate'] = exp_rate
        secv1.display['thickness'] = 10
        op, ny, nx = secv1.position.copy()
        nz = secv1.position.basis[0]
        self.center = int(abs(from_) * exp_rate)
        center = np.array([im_size[1]//2, self.center], int)
        
        secv1.position[:] = np.array([op, ny, nz])
        secv1._allocate_frames()
        secv1._calc_frame(center = center)
        secv1._calc_image()
        self.image1 = secv1.view_image_raw.copy()
        self.image1[:, center[1]] = 255 - self.image1[:, center[1]]
        self.im1 = tk_from_array(self.image1)
        self.image1[:, center[1]] = 255 - self.image1[:, center[1]]
        
        secv1.position[:] = np.array([op, nx, nz])
        secv1._calc_frame(center = center)
        secv1._calc_image()
        self.image2 = secv1.view_image_raw.copy()
        self.image2[:, center[1]] = 255 - self.image2[:, center[1]]
        self.im2 = tk_from_array(self.image2)
        self.image2[:, center[1]] = 255 - self.image2[:, center[1]]
        
        self.vars['start'].set(0)
        self.vars['stop'].set(0)
        self.vars['frames'].set('10')
        self.vars['trans'].set(False)
        
        self.interrupt = True
        self.canvas1.itemconfig(self.im1_id, image = self.im1)
        self.canvas2.itemconfig(self.im2_id, image = self.im2)
        
        main.record_on = False
        
        self.buttons[0]['state'] = tk.NORMAL
        self.buttons[1]['state'] = tk.NORMAL
        for w in self.radio_frame.pack_slaves():
            w['state'] = tk.NORMAL
        for w in self.control_frame.grid_slaves():
            w['state'] = tk.NORMAL
        self.buttons[2].invoke()
        
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
        main.dock_canvas.moveto(self.stack_id, 0, 0)
        main.master.bind('<Return>', self.enter)
        main.master.bind('<Left>', self.left)
        main.master.bind('<Right>', self.right)
        main.master.bind('<Up>', self.up)
        main.master.bind('<Down>', self.down)
        self.num = 1
        
        self.buttons[1].focus_set()
        self.active = True
        
        
    def repair(self):
        main = self.main
        main.secv.metadata = main.meta_kept._format()
        main.update(level = 3)
        main.record_on = True
        
        main.dock_canvas.moveto(self.stack_id, 500, 0)
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
        
        self.active = False
        
    
    def cancel(self):
        self.interrupt = True
        try: 
            if len(self.stacks) > 0:
                return
        except Exception: 
            pass
        self.repair()
        
    def ok(self):
        self.buttons[0]['state'] = tk.DISABLED
        self.buttons[1]['state'] = tk.DISABLED
        for w in self.radio_frame.pack_slaves():
            w['state'] = tk.DISABLED
        for w in self.control_frame.grid_slaves():
            w['state'] = tk.DISABLED
        self.buttons[0].focus_set()
        self.main.master.unbind('<Left>')
        self.main.master.unbind('<Right>')
        self.main.master.unbind('<Up>')
        self.main.master.unbind('<Down>')
        self.main.secv.metadata = self.main.meta_kept._format()
        if self.vars['mode'].get() == 'projection':
            self.projection()
        elif self.vars['mode'].get() == 'span':
            self.span()
        elif self.vars['mode'].get() == 'rotation':
            self.rotation()
        self.repair()
    
    def enter(self, *args):
        if self.num in [0, 1]:
            self.buttons[self.num].invoke()
    def left(self, *args):
        self.num = [1, 0, 4, 2, 3][self.num]
        if self.num in [2, 3, 4]:
            self.buttons[self.num].invoke()
        self.buttons[self.num].focus_set()
    def right(self, *args):
        self.num = [1, 0, 3, 4, 2][self.num]
        if self.num in [2, 3, 4]:
            self.buttons[self.num].invoke()
        self.buttons[self.num].focus_set()
    def up(self, *args):
        if self.vars['mode'].get() == 'projection':
            self.num = 2
        elif self.vars['mode'].get() == 'span':
            self.num = 3
        elif self.vars['mode'].get() == 'rotation':
            self.num = 4
        self.buttons[self.num].focus_set()
    def down(self, *args):
        self.num = 1
        self.buttons[self.num].focus_set()
        
    
    def start_trace(self, v):
        if self.vars['start'].get() >= self.vars['stop'].get():
            self.vars['start'].set(self.vars['stop'].get())
        depth = self.vars['start'].get()
        nz = self.main.position.basis[0]
        self.main.position[0] = self.org_op + nz * depth
        
    def stop_trace(self, v):
        if self.vars['start'].get() >= self.vars['stop'].get():
            self.vars['stop'].set(self.vars['start'].get())
        depth = self.vars['stop'].get()
        nz = self.main.position.basis[0]
        self.main.position[0] = self.org_op + nz * depth
        
    def update(self):
        if not self.active:
            return
        
        start = int(self.vars['start'].get()*self.exp_rate) + self.center
        stop = int(self.vars['stop'].get()*self.exp_rate) + self.center
        
        image1 = self.image1
        start, stop = min(start, len(image1[0])-1), min(stop, len(image1[0])-1)
        image1[:,start] = 255 - image1[:,start]
        if start != stop:
            image1[:,stop] = 255 - image1[:,stop]
        self.im1 = tk_from_array(image1)
        self.canvas1.itemconfig(self.im1_id, image=self.im1)
        image1[:,start] = 255 - image1[:,start]
        if start != stop:
            image1[:,stop] = 255 - image1[:,stop]
        
        image2 = self.image2
        image2[:,start] = 255 - image2[:,start]
        if start != stop:
            image2[:,stop] = 255 - image2[:,stop]
        self.im2 = tk_from_array(image2)
        self.canvas2.itemconfig(self.im2_id, image=self.im2)
        image2[:,start] = 255 - image2[:,start]
        if start != stop:
            image2[:,stop] = 255 - image2[:,stop]
        
    def launch_stac(self, stacks):
        main = self.main
        stac = [stacks, main.channels._format(), main.geometry._format(),
                {'white back': main.display['white_back']}]
        path = base_dir + 'temp/{0}.stac'.format(str(uuid.uuid4()))
        byt = pickle.dumps(stac, protocol=4)
        byt = gzip.compress(byt, compresslevel=1)
        with open(path, 'wb') as f:
            f.write(byt)
        launch(file_path = path)
        
    def projection(self):
        frame = ttk.Frame(self.base_frame)
        frame.pack(fill=tk.X, padx=10, pady=10)
        Label = ttk.Label(frame, text='Calculating...')
        Label.pack(anchor=tk.E, padx=10)
        self.base_frame.update()
        stacks = self.calc_projection()
        self.launch_stac(stacks)
    
    def calc_projection(self):
        secv = self.main.secv
        
        axes = secv.position.copy()
        nz = secv.position.basis[0].copy()
        exp_rate = secv.geometry['expansion_rate']
        axes[1:] /= exp_rate
        start, stop = self.vars['start'].get(), self.vars['stop'].get()
        if exp_rate < 1:
            nz /= exp_rate
            start = int(start * exp_rate)
            stop = int(stop * exp_rate)
        voxels = secv.voxels.base
        stacked = np.empty_like(secv.view_frame)
        ut.stack_section(voxels, axes, nz, start, stop, stacked, 
                         np.array(stacked[0].shape)//2,
                         np.arange(len(secv.channels)))
        return stacked[None]
        
    def span(self):
        secv = self.main.secv
        frame = ttk.Frame(self.base_frame)
        frame.pack(fill=tk.X, padx=10, pady=10)
        Label = ttk.Label(frame, text='Calculating...')
        Label.pack(anchor=tk.E, padx=10)
        self.base_frame.update()
        
        start, stop = self.vars['start'].get(), self.vars['stop'].get()
        num = int(self.vars['frames'].get())
        axes = secv.position.copy()
        nz = secv.position.basis[0].copy()
        axes[1:] /= secv.geometry['expansion_rate']
        nz /= secv.geometry['expansion_rate']
        axes[0] += nz * start
        voxels = secv.voxels.base
        nz *= (stop - start + 1)/num
        stacks = np.empty([num, *secv.view_frame.shape],
                          dtype = np.uint16)
        ut.span_section(voxels, axes, nz, 0, num, stacks,
                        np.array(stacks[0,0].shape)//2, np.arange(len(secv.channels)))
        self.launch_stac(stacks)
        Label.pack_forget()
        
    def rotation(self):
        secv = self.main.secv
        
        frame = ttk.Frame(self.base_frame)
        frame.pack(fill=tk.X, padx=10, pady=10)
        Label = ttk.Label(frame, text='Preparing...')
        Label.pack(anchor=tk.E, padx=10)
        self.base_frame.update()
        
        op, trimmed_voxels = self.trim_voxels()
        self.interrupt = False
        
        
        num = int(self.vars['frames'].get())
        angles = np.linspace(-np.pi, np.pi, num, endpoint = False)
        for i in range(1, len(angles)):
            a = np.abs(angles[:i] - (angles[i] - np.pi)) < 10e-5
            if np.count_nonzero(a) > 0:
                break
        num1 = i
        angles = angles[:num1]
        stacks = np.zeros([num1, *secv.view_frame.shape], dtype = np.uint16)
        
        if self.vars['trans'].get():
            stacks = stacks.transpose(0,1,3,2)
            op = [op[0], op[2], op[1]]
            
        nc, sz, sy, sx = trimmed_voxels.shape
        
        axes = np.array([op, [0.,1.,0.], [0.,0.,1.]])
        op, ny0, nx0 = axes.copy()
        nz0 = np.cross(ny0, nx0)
            
        Label.pack_forget()
        self.pb = ttk.Progressbar(frame, orient = tk.HORIZONTAL, value = 0,
                                  maximum = num1, mode = 'determinate')
        self.pb.pack(fill = tk.X)
        self.ml_tx = tk.StringVar(value = '(0 / {0})'.format(num1))
        Label = ttk.Label(frame, textvariable = self.ml_tx)
        Label.pack(anchor = tk.E, padx = 10)
        self.buttons[0]['state'] = tk.NORMAL
        self.base_frame.update()
        
        zero = time.time()
        t, t2, x, xt, a1 = 0, 0, 0, 0, 0
        
        for count, ang in enumerate(angles):
            axes[2] = np.cos(ang)*nx0 + np.sin(ang)*nz0
            op, ny, nx = axes.copy()
            nz = -np.cross(ny, nx)
            n = np.array([nz, ny, nx])
            peaks = np.array([[ 0,  0,  0], [ 0,  0, sx],
                              [ 0, sy,  0], [ 0, sy, sx],
                              [sz,  0,  0], [sz,  0, sx],
                              [sz, sy,  0], [sz, sy, sx]], dtype=float)
            peaks -= op + np.array([sz//2, sy//2, sx//2])
            peaks = np.linalg.solve(n.T, peaks.T).T
            start = int(np.amin(peaks[:,0]))
            stop = int(np.amax(peaks[:,0]))
        
            stacked = self.calc_rotation(trimmed_voxels, axes, start, stop)
            self.main.update()
            if self.interrupt:
                break
            stacks[count] = stacked
            t1 = time.time() - zero
            try:
                tp = t1 - (count + 1) / a1
                if tp > 900:
                    t += tp
                    xt += ((count * (count + 1))//2) * tp
                    t2 = (xt - x * t) / a1 + t**2
            except Exception:
                pass
            t = (t * count + t1) / (count + 1)
            t2 = (t2 * count + t1**2) / (count + 1)
            x = (x * count + count) / (count + 1)
            xt = (xt * count + count * t1) / (count + 1)
            count += 1
            self.pb.configure(value = count)
            self.pb.update()
            try:
                a1 = (xt - x * t) / (t2 - t**2)
                sec = int((num1 - count) / a1)
                self.ml_tx.set('Remaining {0}:{1:0>2}:{2:0>2}  ({3} / {4})'\
                               .format(sec//3600, sec//60%60, sec%60, count, num1))
            except Exception:
                pass
        
        del trimmed_voxels
        
        if not self.interrupt:
            stacks = np.append(stacks, stacks[:num - i, :, :, ::-1], axis=0)
        
        Label.pack_forget()
        self.pb.pack_forget()
        self.repair()
        
        if len(stacks) > 0:
            
            if self.vars['trans'].get():
                stacks = stacks.transpose(0,1,3,2)
            self.launch_stac(stacks)
        
    def trim_voxels(self):
        secv = self.main.secv
        
        axes = secv.position.copy()
        nz = secv.position.basis[0]
        start, stop = self.vars['start'].get(), self.vars['stop'].get()
        
        nc, sz, sy, sx = secv.voxels.shape
        
        exp_rate = secv.geometry['expansion_rate']
        la0, lb0 = secv.geometry['image_size']
        
        if exp_rate < 1:
            if self.vars['trans'].get():
                axes[1] *= exp_rate
                lb0 = int(lb0 / exp_rate)
            else:
                axes[2] *= exp_rate
                la0 = int(la0 / exp_rate)
        
        axes[1:] /= exp_rate
        n = np.array([nz, axes[1], axes[2]])
            
        peaks = np.array([[ 0,  0,  0],[ 0,  0, sx],
                          [ 0, sy,  0],[ 0, sy, sx],
                          [sz,  0,  0],[sz,  0, sx],
                          [sz, sy,  0],[sz, sy, sx]], dtype=float)
        peaks -= axes[0]
        peaks = np.linalg.solve(n.T, peaks.T).T[:,1:] + np.array([lb0, la0])//2
        m = np.fmax(np.amin(peaks, axis=0), 0)
        M = np.fmin(np.amax(peaks, axis=0), np.array([lb0, la0]))
        
        la, lb = int(M[1] - m[1]), int(M[0] - m[0])
        if self.vars['trans'].get():
            la, lb = lb, la
            la0, lb0 = lb0, la0
            axes = axes[[0,2,1]]
        c = (np.array([lb0//2, la0//2]) - m).astype(int)
        
        trimmed_voxels = np.empty([stop - start + 1, nc, lb, la], dtype=np.uint16)
        
        ut.span_section(secv.voxels.base, axes, nz, start, stop, 
                        trimmed_voxels, c, np.arange(nc))
        
        trimmed_voxels = trimmed_voxels.transpose(1,0,2,3)
        
        opz = stop - (stop - start + 1)//2
        opy = c[0] - lb//2
        opx = c[1] - la//2
        
        return [opz, opy, opx], trimmed_voxels
    
    def calc_rotation(self, voxels, axes, start, stop):
        secv = self.main.secv
        nc, sz, sy, sx = voxels.shape
        
        im_size = secv.geometry['image_size']
        if not self.vars['trans'].get():
            im_size = im_size[::-1]
        exp_rate = secv.geometry['expansion_rate']
        
        axes = axes.copy()
        nz = -np.cross(axes[1], axes[2])
        axes[0] += np.array([sz, sy, sx])//2
        stacked = np.empty([nc, *im_size], dtype = np.uint16).view()
        
        if exp_rate < 1:
            axes[2] /= exp_rate
            nz /= exp_rate
            start = int(start * exp_rate)
            stop = int(stop * exp_rate)
        ut.stack_section2(voxels, axes, nz, start, stop, stacked)
        image = np.empty([*stacked.shape[1:], 4], np.uint8).view()
        image = synthesize_image(stacked, secv.channels, secv.display, image)
        if self.vars['trans'].get():
            image = image.transpose(1, 0, 2)
        object.__setattr__(secv, 'view_image', image)
        
        return stacked
    