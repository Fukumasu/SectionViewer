import os
import traceback

import cv2
import numpy as np
import tifffile as tif
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from ..core import STAC
from ..tools import pf, base_dir, init_dir, save_init, resources
from ..tools import tk_from_array, make_key_text
from .gui import GUI
from .channels import Channels_GUI

class STAC_GUI(GUI):
    
    def __init__(self, root, file_path):
        
        master = tk.Toplevel(root)
        self.root = root
        self.master = master
        super().__init__(self)
        
        w, h = root.screenwidth, root.screenheight
        master.geometry('{0}x{1}+0+0'.format(w, h))
        if pf == 'Windows':
            master.iconbitmap(base_dir + 'img/icon.ico')
            master.state('zoomed')
            
        e_image = resources[:14,174:188]
        self.e_image = tk_from_array(e_image)
        
        try:
            stac = STAC(file_path)
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent = master)
            if master.winfo_exists():
                master.destroy()
            root.destroy()
            return
        
        self.stac = stac
        self.meta_prev = stac.metadata.copy()
        self.meta_kept = stac.metadata.copy()
        
        file_path = stac.files['stac_path']
        self.file_path = file_path
        if file_path is None:
            self.file_dir = None
            self.file_name = 'New_stack'
        else:
            self.file_dir = os.path.dirname(file_path)
            self.file_name = os.path.basename(file_path)
        self.master.title(self.file_name)
        
        self.index = tk.IntVar(value = stac.display['index'])
        self.sbar_len = tk.StringVar(value = str(stac.geometry['scale_bar_length']))
        self.b_on = tk.BooleanVar(value = stac.display['scale_bar'])
        self.d_on = tk.BooleanVar(value = stac.display['dock'])
        self.white_on = tk.BooleanVar(value = stac.display['white_back'])
        self.zoom = tk.StringVar(value = str(int(stac.display['zoom']*100)))
        
        self.record_on = True
        self.record_on_prev = True
        
        self.history = [[None, None, None]]
        self.hidx = 0
        self.hidx_saved = 0 if file_path is not None else -1
        self.hidx_kept = 0
        
        self.terminate = False
        
        self.root.withdraw()
        
        self.create_widgets()
        self.create_commands()
        
        self.channels_gui = Channels_GUI(self)
        
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self.update()
        self.master.after(1, self.monitor)
        
        save_init(file_path)
        
    def __getattribute__(self, name):
        if name in ['files', 'geometry', 'display', 'channels']:
            return self.stac.metadata[name]
        return object.__getattribute__(self, name)
        
    def create_widgets(self):
        
        self.menu_bar = tk.Menu(self.master)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff = 0)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff = 0)
        self.settings_menu = tk.Menu(self.menu_bar, tearoff = 0)
        
        self.menu_bar.add_cascade(label = 'File', menu = self.file_menu)
        self.menu_bar.add_cascade(label = 'Edit', menu = self.edit_menu)
        self.menu_bar.add_cascade(label = 'Settings', menu = self.settings_menu)
        
        self.master.config(menu = self.menu_bar)
        
        # Dock
        self.dock_frame = tk.Frame(self.master)
        self.dock_frame.pack(padx = 10, pady = 2, side = tk.RIGHT)
        width = 470 if pf == 'Darwin' else 420
        self.dock_canvas = tk.Canvas(self.dock_frame, width = width, height = 590)
        self.dock_canvas.pack(side = tk.LEFT)
        
        self.dock_note = ttk.Notebook(self.master)
        self.dock_id = self.dock_canvas.create_window(0, 0, anchor = 'nw', 
                                                      window = self.dock_note)
        bary = tk.Scrollbar(self.dock_frame, orient = tk.VERTICAL)
        bary.pack(side = tk.RIGHT, fill = tk.Y)
        bary.config(command = self.dock_canvas.yview)
        self.dock_canvas.config(yscrollcommand = bary.set)
        self.dock_canvas.config(scrollregion = (0, 0, 0, 590))
        if self.display['dock']:
            width = 470 if pf == 'Darwin' else 420
            self.dock_canvas.configure(width = width)
            self.dock_canvas.moveto(self.dock_id, 0, 0)
        else:
            self.dock_canvas.configure(width = 0)
            self.dock_canvas.moveto(self.dock_id, 500, 0)
        
        # Main
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.top = ttk.Frame(self.main_frame)
        self.top.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)
        
        self.display_frame = ttk.LabelFrame(self.top, text='Display')
        self.display_frame.pack(side=tk.LEFT, padx=10)
        
        if len(self.stac.stacks) > 1:
            self.index_scale = tk.Scale(self.top, variable = self.index, 
                                        from_ = 0, to = len(self.stac.stacks) - 1, 
                                        orient='horizontal')
            self.index_scale.pack(fill=tk.X, padx=10, pady=5)
        
        zm_text = ttk.Label(self.display_frame, text = 'Zoom (%)')
        self.e_button = ttk.Button(self.display_frame, 
                                   width = 4, image = self.e_image)
        self.e_button.grid(column=1, row=0, sticky=tk.W)
        self.zm_values = [  10,   13,   16,   20,  25,  32,  40,  50,  63,  79,
                           100,  126,  158,  200, 251, 316, 398, 501, 631, 794,
                          1000, 1259, 1585, 1995]
        self.combo_zm = ttk.Combobox(self.display_frame, 
                                     values = self.zm_values, width = 12, 
                                     textvariable = self.zoom)
        self.chk_b = ttk.Checkbutton(self.display_frame,
                                     variable = self.b_on, text = 'Scale bar (B)')
        self.chk_d = ttk.Checkbutton(self.display_frame, 
                                     variable = self.d_on, text = 'Dock (D)')
        self.rad_b = ttk.Radiobutton(self.display_frame, 
                                     text = 'Black', value = False, 
                                     variable = self.white_on)
        self.rad_w = ttk.Radiobutton(self.display_frame, 
                                     text = 'White', value = True, 
                                     variable = self.white_on)
        
        zm_text.grid(column = 0, row = 0, padx = 5, sticky = tk.W)
        self.combo_zm.grid(column = 0, row = 1, columnspan = 2, 
                           padx = 5, sticky = tk.W)
        self.chk_b.grid(column = 2, row = 0, padx = 5, sticky = tk.W)
        self.chk_d.grid(column = 2, row = 1, padx = 5, sticky = tk.W)
        self.rad_b.grid(column = 3, row = 0, padx = 5, sticky = tk.W)
        self.rad_w.grid(column = 3, row = 1, padx = 5, sticky = tk.W)
        
        self.bottom = ttk.Frame(self.main_frame)
        self.bottom.pack(side = tk.BOTTOM, anchor = tk.S, 
                         fill = tk.X, expand = True)
        
        self.saving = tk.StringVar(value = '')
        sv_text = ttk.Label(self.bottom, textvariable = self.saving)
        self.sbar_frame = ttk.Frame(self.bottom)
        
        sv_text.pack(side = tk.LEFT, padx = 5, pady = 5)
        self.sbar_frame.pack(side = tk.RIGHT)
        
        um_text = ttk.Label(self.sbar_frame, text='µm')
        self.sbar_entry = ttk.Entry(self.sbar_frame, textvariable = self.sbar_len,
                                    width = 10, justify = tk.RIGHT)
        sb_text = ttk.Label(self.sbar_frame, text='Scale bar:')
        
        um_text.pack(side = tk.RIGHT, anchor = tk.N, padx = 5, pady = 5)
        self.sbar_entry.pack(side = tk.RIGHT, anchor = tk.N, pady = 5)
        sb_text.pack(side = tk.RIGHT, anchor = tk.N, padx = 5, pady = 5)
        
        self.view_frame = ttk.Frame(self.main_frame)
        self.view_frame.pack(padx = 2, pady = 3)
        
        self.view_cf = ttk.Frame(self.view_frame)
        self.barx = tk.Scrollbar(self.view_frame, orient=tk.HORIZONTAL)
        self.bary = tk.Scrollbar(self.view_frame, orient=tk.VERTICAL)
        
        self.view_cf.pack(side = tk.LEFT)
        self.barx.pack(side = tk.BOTTOM, fill = tk.X)
        self.bary.pack(side = tk.RIGHT, fill = tk.Y)
        
        self.view_canvas = tk.Canvas(self.view_cf, 
                                     width = 2000, height = 2000)
        self.view_canvas.pack(side = tk.LEFT, anchor = tk.NW)
        
        self.view_id = self.view_canvas.create_image(0, 0, anchor = 'nw')
        if self.d_on.get():
            self.master.minsize(850, 400)
        else:
            self.master.minsize(400, 400)
        
        super().update()
        w, h = self.view_cf.winfo_width() - 4, self.view_cf.winfo_height() - 4
        self.display['window_size'] = w, h
        if self.display['center'] is None:
            self.fit_frame()
    
    def create_commands(self):
        stac = self.stac
        
        if pf == 'Darwin':
            ctrl = 'Command+'
        else:
            ctrl = 'Ctrl+'
        
        self.file_menu.add_command(label = 'Open', 
                                   command = self.open_new, 
                                   accelerator = ctrl + 'O')
        self.file_menu.add_command(label='Save', 
                                   command = self.save, 
                                   accelerator = ctrl+'S')
        self.file_menu.add_command(label = 'Save As',
                                   command = lambda: self.save(ask_name = True), 
                                   accelerator = ctrl+'Shift+S')
        self.file_menu.add_command(label = 'Export', 
                                   command = self.export, 
                                   accelerator = ctrl+'E')
        
        self.edit_menu.add_command(label = 'Undo', 
                                   command = self.undo, 
                                   accelerator = ctrl+'Z')
        self.edit_menu.add_command(label = 'Redo', 
                                   command = self.redo, 
                                   accelerator = ctrl+'Y')
        self.edit_menu.entryconfig('Undo', state='disable')
        self.edit_menu.entryconfig('Redo', state='disable')
        
        self.settings_menu.add_command(label = 'Channels', 
                                       command = self.open_channels,
                                       accelerator = 'C')
        
        self.e_button.configure(command = self.fit_frame)
        self.barx.config(command = self.barx_set)
        self.bary.config(command = self.bary_set)
        
        self.index.trace_id = self.index.trace('w', self.index_trace)
        self.zoom.trace_id = self.zoom.trace('w', self.zoom_trace)
        self.sbar_len.trace_id = self.sbar_len.trace('w', self.sbar_len_trace)
        self.b_on.trace_id = self.b_on.trace('w', self.b_on_trace)
        self.d_on.trace_id = self.d_on.trace('w', self.d_on_trace)
        self.white_on.trace_id = self.white_on.trace('w', self.white_on_trace)
        
        if stac.geometry._min_px_size == None:
            self.sbar_entry.configure(state = tk.DISABLED)
        
        def wrap_bind(widget, event_name, method):
            def func(*args, **kwargs):
                widget.unbind(event_name)
                ret = method(*args, **kwargs)
                self.master.after(10, widget.bind, event_name, func)
                return ret
            widget.bind(event_name, func)
            return func
        
        self.view_configure = \
            wrap_bind(self.view_cf, '<Configure>', self.view_configure)
        self.key = \
            wrap_bind(self.master, '<Key>', self.key)
        
        if pf == 'Windows':
            self.bary_scroll = \
                wrap_bind(self.view_canvas, '<MouseWheel>', self.bary_scroll)
            self.barx_scroll = \
                wrap_bind(self.view_canvas, '<Shift-MouseWheel>', self.barx_scroll)
            self.zoom_scroll = \
                wrap_bind(self.view_canvas, '<Control-MouseWheel>', self.zoom_scroll)
        elif pf == 'Darwin':
            self.bary_scroll = \
                wrap_bind(self.view_canvas, '<MouseWheel>', self.bary_scroll)
            self.barx_scroll = \
                wrap_bind(self.view_canvas, '<Shift-MouseWheel>', self.barx_scroll)
            self.zoom_scroll = \
                wrap_bind(self.view_canvas, '<Command-MouseWheel>', self.zoom_scroll)
        elif pf == 'Linux':
            self.bary_scroll_up = \
                wrap_bind(self.view_canvas, '<Button-4>', self.bary_scroll_up)
            self.bary_scroll_down = \
                wrap_bind(self.view_canvas, '<Button-5>', self.bary_scroll_down)
            self.barx_scroll_up = \
                wrap_bind(self.view_canvas, '<Shift-Button-4>', self.barx_scroll_up)
            self.barx_scroll_down = \
                wrap_bind(self.view_canvas, '<Shift-Button-5>', self.barx_scroll_down)
            self.zoom_scroll_up = \
                wrap_bind(self.view_canvas, '<Control-Button-4>', self.zoom_scroll_up)
            self.zoom_scroll_down = \
                wrap_bind(self.view_canvas, '<Control-Button-5>', self.zoom_scroll_down)
        
     
    def key(self, event):
        key = make_key_text(event.keysym, event.state)
        
        if key in ['Ctrl+O', 'Command+O']:
            self.open_new()
        elif key in ['Ctrl+S', 'Command+S']:
            self.saving.set('Saving...')
            self.master.update()
            self.master.after(10, self.save)
        elif key in ['Shift+Ctrl+S', 'Shift+Command+S']:
            self.saving.set('Saving...')
            self.master.update()
            self.master.after(10, self.save, True)
        elif key in ['Ctrl+E', 'Command+E']:
            self.export()
        elif key in ['Ctrl+Z', 'Command+Z']:
            self.undo()
        elif key in ['Ctrl+Y', 'Command+Y']:
            self.redo()
            
        focus = str(self.master.focus_get()).rsplit('!', 1)[-1]
        if 'entry' in focus:
            return
        elif 'combo' in focus:
            return
        if key in ['B', 'D']:
            getattr(self, 'chk_{0}'.format(key.lower())).invoke()
        elif key == 'C':
            self.open_channels()
        
        elif key == 'LEFT':
            self.index.set(self.display['index'] - 1)
        elif key == 'RIGHT':
            self.index.set(self.display['index'] + 1)
            
    def on_close(self):
        if self.hidx == self.hidx_saved:
            self.terminate = True
        else:
            ans = messagebox.askyesnocancel(title = 'Closing', 
                                            message = 'Do you want to save '
                                                      'changes before you quit?',
                                            parent = self.master)
            if ans == None:
                return
            if ans:
                if self.stac.save():
                    self.terminate = True
            else:
                self.terminate = True
            
    def save(self, ask_name = False):
        initialfile = os.path.splitext(self.file_name)[0]
        if self.file_path is None:
            ask_name = True
        else:
            if os.path.splitext(self.file_path)[1] != 'stac':
                ask_name = True
        if ask_name:
            filetypes = [('SectionViewer stack file', '*.secv')]
            initialfile = initialfile
            path = filedialog.asksaveasfilename(
                parent = self.master, 
                filetypes = filetypes, 
                initialdir = init_dir(),
                initialfile = initialfile,
                title = 'Saving stacks as STAC format',
                defaultextension = '.stac'
                )
            if len(path) == 0:
                return False
            path = path.replace('\\', '/')
        else:
            path = self.file_path
        self.stac.save(path)
        self.hidx_saved = self.hidx
        self.file_path = path
        self.file_name = os.path.basename(path)
        self.file_dir = os.path.dirname(path)
        save_init(path)
        self.master.title(self.file_name)
        
        return True
    
    def imwrite(self, filename, img, params=None):
        try:
            ext = os.path.splitext(filename)[1]
            result, n = cv2.imencode(ext, img, params)
    
            if result:
                with open(filename, mode = 'w+b') as f:
                    n.tofile(f)
                return True
            else:
                return False
        except Exception:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent = self.master)
            return False
    
    def export(self):
        if len(self.stac.stacks) > 1:
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
        
        initialfile = os.path.splitext(self.file_name)[0]
        path = filedialog.asksaveasfilename(
            parent = self.master,
            filetypes = filetypes,
            initialdir = init_dir(),
            initialfile = initialfile,
            title = 'Exporting the stack image',
            defaultextension = '.png'
            )
        if len(path) > 0:
            path = path.replace('\\', '/')
            
            if path[-4:] == '.mp4':
                self.ask_fps(path)
                save_init(path)
                return
            
            if path[-4:] == '.tif':
                opt = self.ask_option(self.master, 'Saving options',
                                      ['Stack image (RGB)',
                                       'Stack data (16 bit)'])
                if opt == 1:
                    frame = self.stac.stacks[self.display['index']]
                    sort = np.argsort(self.channels.get_names())
                    try:
                        tif.imwrite(path, frame[sort])
                    except:
                        messagebox.showerror('Error', traceback.format_exc() + 
                                             '\nFailed to export TIFF file',
                                             parent = self.master)
                        return
                    save_init(path)
                    return
            
            image = self.stac.view_image
            if self.imwrite(path, image):
                save_init(path)
                
    def index_trace(self, *args):
        self.display['index'] = self.index.get()
        self.index.set(self.display['index'])
                
    def open_channels(self):
        if not self.display['dock']:
            self.d_on.set(True)
        self.channels_gui.settings()
            
    def ask_fps(self, path):
        self.fps_win = tk.Toplevel(self.master)
        self.fps_win.withdraw()
        if pf == 'Windows':
            self.fps_win.iconbitmap(base_dir + 'img/icon.ico')
        self.fps_win.title('mp4 settings')
        self.fps_win.geometry('250x90')
        self.fps_win.resizable(width = False, height = False)
        
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
                
                shape = self.geometry['image_size']
                maximum = len(self.stac.stacks) - 1
                
                out = cv2.VideoWriter(path, fourcc, f, shape, True)
                pb = ttk.Progressbar(frame, 
                                     orient = tk.HORIZONTAL, 
                                     value = 0, 
                                     length = 100,
                                     maximum = maximum, 
                                     mode = 'determinate')
                pb.pack(fill = tk.X, pady = 5)
                button = ttk.Button(frame, text = 'Cancel', command = cancel)
                button.pack(pady = 5)
                button.focus_set()
                
                pre_index = self.display['index']
                self.record_on = False
                
                for i in range(maximum + 1):
                    pb.configure(value = i)
                    pb.update()
                    self.display['index'] = i
                    if not self.update():
                        continue
                    if self.cancel:
                        break
                    out.write(self.stac.view_image)
                out.release()
                
                self.display['index'] = pre_index
                self.record_on = True
                
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
        
    def undo(self):
        if self.hidx == 0:
            return
        if self.hidx != self.hidx_kept:
            return
        self.hidx -= 1
        loc, olds, news = self.history[self.hidx + 1]
        for l, old in zip(loc, olds):
            obj = self.stac.metadata
            for k in l[:-1]:
                obj = obj[k]
            obj[l[-1]] = old
        
    def redo(self):
        if self.hidx == len(self.history) - 1:
            return
        if self.hidx != self.hidx_kept:
            return
        self.hidx += 1
        loc, olds, news = self.history[self.hidx]
        for l, new in zip(loc, news):
            obj = self.stac.metadata
            for k in l[:-1]:
                obj = obj[k]
            obj[l[-1]] = new
    
    def monitor(self):
        meta = self.stac.metadata.copy()
        meta_p, meta_k = self.meta_prev, self.meta_kept
        loc = meta._locate_difference(meta_p)
        if len(loc) > 0 or (not self.record_on_prev and self.record_on) \
           or self.hidx != self.hidx_kept:
            success = self.update(loc)
            if success:
                self.meta_prev = meta.copy()
                self.record_on_prev = self.record_on
                if self.record_on:
                    self.update_history(meta, meta_k)
            else:
                self.stac.metadata = self.meta_kept._format()
                self.update()
            
            if self.hidx == len(self.history) - 1:
                self.edit_menu.entryconfig('Redo', state='disable')
            else:
                self.edit_menu.entryconfig('Redo', state='normal')
            if self.hidx == 0:
                self.edit_menu.entryconfig('Undo', state='disable')
            else:
                self.edit_menu.entryconfig('Undo', state='normal')
            if self.hidx != self.hidx_saved:
                self.master.title('*' + self.file_name)
            else:
                self.master.title(self.file_name)
        if self.terminate:
            self.master.destroy()
            self.root.destroy()
        else:
            self.master.after(10, self.monitor)
        
    def update(self, loc: list = []) -> bool:
        
        try:
            success = self.stac.update()
        except Exception:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent = self.master)
            success = False
        if not success:
            return False
        
        w, h = self.display['window_size']
        cx, cy = self.display['center']
        zoom = self.display['zoom']
        iw, ih = self.geometry['image_size']
        
        if not hasattr(self, 'main_image'):
            self.main_image = np.zeros([h, w, 3], np.uint8)
        if self.main_image.shape[:2] != (h, w):
            self.main_image = np.zeros([h, w, 3], np.uint8)
        
        iw, ih = int(iw * zoom), int(ih * zoom)
        ul = np.array([cx - iw // 2, cy - ih // 2])
        br = ul + np.array([iw, ih])
        warp = np.array([[zoom, 0., ul[0]], [0., zoom, ul[1]]])
        back = [255, 255, 255] if self.display['white_back'] else [0, 0, 0]
        
        cv2.warpAffine(self.stac.view_image, warp, (w, h), 
                       dst = self.main_image,
                       borderMode = cv2.BORDER_CONSTANT,
                       borderValue = back)
        ul = np.fmax(0, ul)
        br = np.fmax(0, br)
        self.main_image[:ul[1]] = 240
        self.main_image[br[1]:] = 240
        self.main_image[:,:ul[0]] = 240
        self.main_image[:,br[0]:] = 240
        
        self.view_im = tk_from_array(self.main_image)
        self.view_canvas.itemconfig(self.view_id, image = self.view_im)
        
        v1 = (iw//2 + w - 50 - cx) / (iw + 2*w - 100)
        v2 = v1 + w / (iw + 2*w - 100)
        self.barx.set(v1, v2)
        v1 = (ih//2 + h - 50 - cy)/(ih + 2*h - 100)
        v2 = v1 + h / (ih + 2*h - 100)
        self.bary.set(v1, v2)
        
        self.sbar_len.set(str(self.geometry['scale_bar_length']))
        self.channels_gui.update(loc)
        
        return True
        
    def update_history(self, meta, meta_k):
        loc = meta._locate_difference(meta_k)
        loc1 = [l for l in loc if l[0] != 'display']
        loc1 = [l for l in loc1 if l[0] != 'files']
        loc1 = [l for l in loc1 if l != ['channels']]
        
        if len(loc1) > 0 and self.hidx == self.hidx_kept:
            olds, news = [], []
            for l in loc1:
                old, new = meta_k[l[0]].copy(), meta[l[0]].copy()
                for i in range(1, len(l)):
                    old, new = old[l[i]], new[l[i]]
                olds += [old]
                news += [new]
            
            merge = len(np.unique([l[0] for l in loc1])) == 1
            if merge:
                if loc1[0][0] == 'files':
                    merge = False
                elif loc1[0][0] == 'geometry':
                    merge = len(loc1) == 1
                elif loc1[0][0] == 'channels':
                    merge = len(np.unique([[l[0],l[2]] for l in loc1],
                                           axis = 0)) == 1
                    
            merge *= self.history[-1][0] == loc1
            merge *= not self.cut_history
            merge *= self.hidx == len(self.history) - 1
            merge *= self.hidx_saved != self.hidx
                
            if merge:
                self.history[-1][2] = news
            else:
                self.hidx += 1
                self.history = self.history[: self.hidx]
                self.history += [[loc1, olds, news]]
                if self.hidx_saved >= len(self.history):
                    self.hidx_saved = -1
        self.cut_history = False
        self.meta_kept = meta.copy()
        self.hidx_kept = self.hidx