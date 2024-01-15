import traceback

import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ..tools import pf, base_dir, tk_from_array, ask_file_path, launch, desolve_state

class Base_GUI(ttk.Frame):
    def __init__(self, main):
        super().__init__(main.master)
        
        def wrap_method(method):
            def func(*args, **kwargs):
                try:
                    return method(*args, **kwargs)
                except Exception:
                    messagebox.showerror('Error', traceback.format_exc(),
                                         parent = main.master)
                    if main.master.winfo_exists():
                        main.master.destroy()
                    if hasattr(main, 'root'):
                        main.root.destroy()
            return func
        for name in dir(self):
            if name in dir(super()) and name != 'update':
                continue
            method = getattr(self, name)
            if not hasattr(method, '__call__'):
                continue
            object.__setattr__(self, name, wrap_method(method))
    
    
class GUI(Base_GUI):
    def open_new(self):
        file_path = ask_file_path(self.master)
        if len(file_path) > 0:
            launch(file_path = file_path)
            
    def ask_option(self, master, title, options, geometry=None):
        win = tk.Toplevel(master)
        win.withdraw()
        if pf == 'Windows':
            win.iconbitmap(base_dir + 'img/icon.ico')
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
            
    def barx_scroll(self, event):
        state = desolve_state(event.state)
        if np.count_nonzero(list(state.values())) > 1:
            return
        if pf == 'Windows':
            delta = int(-event.delta / 120)
        elif pf == 'Darwin':
            delta = int(-event.delta)
        self.calc_scroll(delta, axis = 0)
        
    def barx_scroll_up(self, event):
        state = desolve_state(event.state)
        if np.count_nonzero(list(state.values())) > 1:
            return
        self.calc_scroll(1, axis = 0)
        
    def barx_scroll_down(self, event):
        state = desolve_state(event.state)
        if np.count_nonzero(list(state.values())) > 1:
            return
        self.calc_scroll(-1, axis = 0)
    
    def bary_scroll(self, event):
        state = desolve_state(event.state)
        if np.count_nonzero(list(state.values())) > 0:
            return
        if pf == 'Windows':
            delta = int(-event.delta / 120)
        elif pf == 'Darwin':
            delta = int(-event.delta)
        self.calc_scroll(delta, axis = 1)
        
    def bary_scroll_up(self, event):
        state = desolve_state(event.state)
        if np.count_nonzero(list(state.values())) > 0:
            self.calc_scroll(1, axis = 1)
        
    def bary_scroll_down(self, event):
        state = desolve_state(event.state)
        if np.count_nonzero(list(state.values())) > 0:
            self.calc_scroll(-1, axis = 1)
        
    def calc_scroll(self, delta, axis = 0):
        delta = delta / 20
        l = self.display['window_size'][axis]
        c = self.display['center'][axis]
        zoom = self.display['zoom']
        il = self.geometry['image_size'][axis]
        il = int(il * zoom)
        v1 = (il // 2 - c + l - 50)/(il + 2*l - 100)
        v2 = (il // 2 - c + 2*l - 50)/(il + 2*l - 100)
        v1 = max(0, min(1 - v2 + v1, v1 + delta))
        [self.barx_set, self.bary_set][axis]('moveto', v1)
        
    def barx_set(self, *args):
        if args[0] != 'moveto':
            return
        moveto = float(args[1])
        iw = self.geometry['image_size'][0]
        iw = int(iw * self.display['zoom'])
        w = self.display['window_size'][0]
        mr = iw + 2*w - 100
        cx, cy = self.display['center']
        cx = iw // 2 - mr * moveto + w - 50
        self.display['center'] = cx, cy
        
    def bary_set(self, *args):
        if args[0] != 'moveto':
            return
        moveto = float(args[1])
        ih = self.geometry['image_size'][1]
        ih = int(ih * self.display['zoom'])
        h = self.display['window_size'][1]
        mr = ih + 2*h - 100
        cx, cy = self.display['center']
        cy = ih // 2 - mr * moveto + h - 50
        self.display['center'] = cx, cy
        
    def zoom_scroll(self, event):
        state = desolve_state(event.state)
        del state['Control']
        if np.count_nonzero(list(state.values())) > 1:
            return
        if pf == 'Windows':
            delta = int(event.delta / 120)
        elif pf == 'Darwin':
            delta = int(event.delta)
        self.calc_zoom_scroll(event.x, event.y, delta)
        
    def zoom_scroll_up(self, event):
        state = desolve_state(event.state)
        del state['Control']
        if np.count_nonzero(list(state.values())) > 1:
            return
        self.calc_zoom_scroll(event.x, event.y, 1)
        
    def zoom_scroll_down(self, event):
        state = desolve_state(event.state)
        del state['Control']
        if np.count_nonzero(list(state.values())) > 1:
            return
        self.calc_zoom_scroll(event.x, event.y, -1)
        
    def calc_zoom_scroll(self, x, y, delta):
        a = int(np.argmin((np.array(self.zm_values) - float(self.zoom.get()))**2))
        a = min(max(a + 2*delta, 0), len(self.zm_values)-1)
        zoom = self.zm_values[a]
        zoom0 = self.display['zoom']
        cx1, cy1 = self.display['center']
        self.zoom.set(str(zoom))
        w, h = self.display['window_size']
        fix = (x / w, y / h)
        self.calc_center(zoom0 = zoom0, cx1 = cx1, cy1 = cy1, fix = fix)
        
    def fit_frame(self):
        w, h = self.display['window_size']
        iw, ih = self.geometry['image_size']
        zoom = min((w - 10) / iw, (h - 10) / ih)
        zs = str(int(zoom * 100))
        if zs == self.zoom.get() and \
            self.display['center'] == (int(w//2), int(h//2)):
            zoom = 1.
            zs = '100'
        self.display['center'] = int(w//2), int(h//2)
        self.display['zoom'] = zoom
        self.zoom.set(zs)
        
    def zoom_trace(self, *args):
        zoom = self.zoom.get()
        try:
            if zoom == '':
                zoom = 0
            zoom = max(self.zm_values[0], min(int(zoom), self.zm_values[-1]))
            zoom /= 100
        except Exception:
            zoom = self.display['zoom']
            self.zoom.set(str(int(zoom * 100)))
            return
        self.zoom.set(str(int(zoom * 100)))
        zoom0 = self.display['zoom']
        self.display['zoom'] = zoom
        self.calc_center(zoom0 = zoom0)
        
    def calc_center(self, zoom0 = None, iw0 = None, ih0 = None,
                       w0 = None, h0 = None, cx1 = None, cy1 = None, 
                       fix = (0.5, 0.5)):
        zoom = self.display['zoom']
        if zoom0 is None:
            zoom0 = zoom
        iw, ih = self.geometry['image_size']
        if iw0 is None:
            iw0 = iw
        if ih0 is None:
            ih0 = ih
        w, h = self.display['window_size']
        if w0 is None:
            w0 = w
        if h0 is None:
            h0 = h
        cx0, cy0 = self.display['center']
        if cx1 is not None:
            cx0 = cx1
        if cy1 is not None:
            cy0 = cy1
        x = (fix[0] * w0 - cx0) / zoom0 - iw0//2
        cx = fix[0] * w - (x + iw//2) * zoom
        cx = max(-(iw * zoom + 1)//2 + 50, 
                 min(cx, w + (iw * zoom)//2 - 50))
        y = (fix[1] * h0 - cy0) / zoom0 - ih0//2
        cy = fix[1] * h - (y + ih//2) * zoom
        cy = max(-(ih * zoom + 1)//2 + 50, 
                 min(cy, h + (ih * zoom)//2 - 50))
        self.display['center'] = cx, cy
        
    def view_configure(self, event):
        calc_ct = False
        if self.display['window_size'] is not None:
            w0, h0 = self.display['window_size']
            calc_ct = True
        w, h = self.view_cf.winfo_width() - 4, self.view_cf.winfo_height() - 4
        self.display['window_size'] = w, h
        if calc_ct:
            self.calc_center(w0 = w0, h0 = h0)
            
    def sbar_len_trace(self, *args):
        sbar_len = self.sbar_len.get()
        try:
            if sbar_len == '':
                sbar_len = 0
            sbar_len = max(0, float(sbar_len))
        except Exception:
            sbar_len = self.geometry['scale_bar_length']
            self.sbar_len.set(str(sbar_len))
            return
        self.sbar_len.set(str(sbar_len))
        self.geometry['scale_bar_length'] = sbar_len
        
    def a_on_trace(self, *args):
        self.display['axis'] = self.a_on.get()
        
    def b_on_trace(self, *args):
        self.display['scale_bar'] = self.b_on.get()
        
    def p_on_trace(self, *args):
        self.display['points'] = self.p_on.get()
        
    def d_on_trace(self, *args):
        self.display['dock'] = self.d_on.get()
        if self.display['dock']:
            width = 470 if pf == 'Darwin' else 420
            self.dock_canvas.configure(width = width)
            self.dock_canvas.moveto(self.dock_id, 0, 0)
            self.master.minsize(850, 400)
        else:
            self.dock_canvas.configure(width=0)
            self.dock_canvas.moveto(self.dock_id, 500, 0)
            self.master.minsize(400, 400)
            
    def white_on_trace(self, *args):
        self.display['white_back'] = self.white_on.get()
        
        
class Color_GUI(Base_GUI):
    def __init__(self, main):
        super().__init__(main)
        preset = np.zeros([20,160,3], dtype=np.uint8)
        preset[:,:20] = [15,15,15]
        preset[:,20:40] = [255,255,255]
        preset[:,40:60] = [15,15,240]
        preset[:,60:80] = [15,240,240]
        preset[:,80:100] = [15,240,15]
        preset[:,100:120] = [240,240,15]
        preset[:,120:140] = [240,15,15]
        preset[:,140:] = [240,15,240]
        self.preset_image = tk_from_array(preset)
        preset[::2,::2] = 240
        preset[1::2,1::2] = 240
        self.preset_off = tk_from_array(preset)
    
    def auto_color(self):
        x = self.treeview.selection()
        ids = [int(i) for i in x]
        self.obj.auto_color(ids)
        
    def preset(self, event):
        if self.vars['sh'].get() != 1:
            return
        obj_ids = [int(i) for i in self.treeview.selection()]
        color = [[0,0,0], [255,255,255], [0,0,255], [0,255,255],
                 [0,255,0], [255,255,0], [255,0,0], [255,0,255]][event.x//20]
        self.obj.set_color(obj_ids, color)
                
    def nm_trace(self, *args):
        x = self.treeview.selection()
        if len(x) != 1:
            return
        name = self.vars['nm'].get()
        self.obj.set_name(int(x[0]), name)
    
    def rgb_scale(self, num):
        vn = ['bs', 'gs', 'rs'][num]
        def func(*args):
            x = self.treeview.selection()
            if len(x) == 0:
                return
            if self.vars['sh'].get() != 1:
                i = int(x[0])
                c = self.obj[i][1][num]
                self.vars[vn[0]].set(c)
                return
            color = [self.vars[v].get() 
                     for v in ['b', 'g', 'r']]
            ids = [int(i) for i in x]
            self.obj.set_color(ids, color)
        return func
    
    def rgb_enter(self, num):
        vn = ['bs', 'gs', 'rs'][num]
        def func(*args):
            x = self.treeview.selection()
            if len(x) == 0:
                return
            if self.vars['sh'].get() != 1:
                i = int(x[0])
                c = self.obj[i][1][num]
                self.vars[vn].set(str(c))
                return
            try:
                c = self.vars[vn].get()
                if c == '':
                    c = 0
                c = int(c)
                self.vars[vn[0]].set(c)
                color = [self.vars[v].get() 
                         for v in ['b', 'g', 'r']]
                ids = [int(i) for i in x]
                self.obj.set_color(ids, color)
            except Exception:
                i = int(x[0])
                self.vars[vn[0]].set(self.obj[i][1][num])
        return func
    
    def hsl_scale(self, num):
        vn = ['hs', 'ss', 'ls'][num]
        def func(*args):
            x = self.treeview.selection()
            if len(x) == 0:
                return
            if self.vars['sh'].get() != 1:
                i = int(x[0])
                c = int(self.obj[i][1]['hsl'][num] * 10)
                self.vars[vn[0]].set(c)
                return
            color = [self.vars[v].get() / 10 
                     for v in ['h', 's', 'l']]
            ids = [int(i) for i in x]
            self.obj.set_color(ids, color, as_hsl = True)
        return func
    
    def hsl_enter(self, num):
        vn = ['hs', 'ss', 'ls'][num]
        def func(*args):
            x = self.treeview.selection()
            if len(x) == 0:
                return
            if self.vars['sh'].get() != 1:
                i = int(x[0])
                c = int(self.obj[i][1]['hsl'][num] * 10)
                self.vars[vn].set(str(c / 10))
                return
            try:
                c = self.vars[vn].get()
                if c == '':
                    c = 0
                c = float(c)
                self.vars[vn[0]].set(int(c * 10))
                color = [self.vars[v].get() / 10 
                         for v in ['h', 's', 'l']]
                ids = [int(i) for i in x]
                self.obj.set_color(ids, color, as_hsl = True)
            except Exception:
                i = int(x[0])
                c = int(self.obj[i][1]['hsl'][num] * 10)
                self.vars[vn[0]].set(c)
        return func
            