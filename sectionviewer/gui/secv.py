import os
import traceback

import cv2
import numpy as np
import tifffile as tif
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..core import SECV
from ..basics import CoordinateError
from ..tools import base_dir, init_dir, save_init, resources, pf
from ..tools import draw_points, tk_from_array, desolve_state, make_key_text
from .gui import GUI
from .channels import Channels_GUI
from .points import Points_GUI
from .snapshots import Snapshots_GUI
from .details import Details_GUI
from .stack import Stack_GUI


class SECV_GUI(GUI):
    
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
        
        self.file_path = file_path
        self.file_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        
        self.master.title(self.file_name)
        
        k_image = resources[204:373] if pf == 'Darwin' else resources[35:204]
        self.k_image = tk_from_array(k_image)
        e_image = resources[:14,174:188]
        self.e_image = tk_from_array(e_image)
        hor_image = resources[:20,188:208]
        self.hor_image = tk_from_array(hor_image)
        ver_image = resources[:20,208:228]
        self.ver_image = tk_from_array(ver_image)
        
        try:
            secv = SECV(file_path, master = master)
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent = master)
            if master.winfo_exists():
                master.destroy()
            root.destroy()
            return
            
        self.secv = secv
        self.meta_kept = secv.metadata.copy()
        
        self.thickness = tk.StringVar(value = str(self.display['thickness']))
        self.sbar_len = tk.StringVar(value = str(self.geometry['scale_bar_length']))
        self.a_on = tk.BooleanVar(value = self.display['axis'])
        self.b_on = tk.BooleanVar(value = self.display['scale_bar'])
        self.p_on = tk.BooleanVar(value = self.display['points'])
        self.d_on = tk.BooleanVar(value = self.display['dock'])
        self.white_on = tk.BooleanVar(value = self.display['white_back'])
        self.sideview_on = tk.BooleanVar(value = self.display['sideview'])
        self.zoom = tk.StringVar(value = str(int(self.display['zoom']*100)))
        self.depth = tk.IntVar(value = -self.position.depth_range[0])
        
        self.click = None
        self.dragging = False
        self.mode = 0
        
        self.record_on = True
        self.record_on_prev = True
        self.update_params = {}
        
        self.history = [[None, None, None]]
        self.hidx = 0
        self.hidx_saved = 0
        self.hidx_kept = 0
        self.cut_history = False
        
        self.terminate = False
        
        self.root.withdraw()
        
        self.create_widgets()
        self.create_commands()
        
        self.channels_gui = Channels_GUI(self)
        self.points_gui = Points_GUI(self)
        self.snapshots_gui = Snapshots_GUI(self)
        self.details_gui = Details_GUI(self)
        self.stack_gui = Stack_GUI(self)
                    
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self.update([['new']], level = 7)
        self.master.after(1, self.monitor)
        
        if self.secv.files['secv_path'] is not None:
            self.secv.save(file_path)
            save_init(file_path)
        
    def __getattribute__(self, name):
        if name in ['files', 'geometry', 'display', 'position',
                    'channels', 'points', 'snapshots']:
            return self.secv.metadata[name]
        return object.__getattribute__(self, name)
        
    def create_widgets(self):
        
        self.menu_bar = tk.Menu(self.master)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff = 0)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff = 0)
        self.settings_menu = tk.Menu(self.menu_bar, tearoff = 0)
        self.tools_menu = tk.Menu(self.menu_bar, tearoff = 0)
        
        self.menu_bar.add_cascade(label = 'File', menu = self.file_menu)
        self.menu_bar.add_cascade(label = 'Edit', menu = self.edit_menu)
        self.menu_bar.add_cascade(label = 'Settings', menu = self.settings_menu)
        self.menu_bar.add_cascade(label = 'Tools', menu = self.tools_menu)
        
        self.master.config(menu = self.menu_bar)
        
        # Dock
        self.dock_frame = tk.Frame(self.master)
        self.dock_frame.pack(padx = 5, pady = 5, side = tk.RIGHT)
        width = 470 if pf == 'Darwin' else 420
        self.dock_canvas = tk.Canvas(self.dock_frame, 
                                     width = width, height = 615)
        self.dock_canvas.pack(side = tk.LEFT)
        
        self.dock_note = ttk.Notebook(self.master)
        self.dock_id = self.dock_canvas.create_window(0, 0, anchor = 'nw', 
                                                      window = self.dock_note)
        bary = tk.Scrollbar(self.dock_frame, orient = tk.VERTICAL)
        bary.pack(side = tk.RIGHT, fill = tk.Y)
        bary.config(command = self.dock_canvas.yview)
        self.dock_canvas.config(yscrollcommand = bary.set)
        self.dock_canvas.config(scrollregion = (0, 0, 0, 615))
        if self.display['dock']:
            width = 470 if pf == 'Darwin' else 420
            self.dock_canvas.configure(width = width)
            self.dock_canvas.moveto(self.dock_id, 0, 0)
        else:
            self.dock_canvas.configure(width = 0)
            self.dock_canvas.moveto(self.dock_id, 500, 0)
        
        self.guide_frame = ttk.Frame(self.dock_note)
        self.guide_upper = ttk.Frame(self.guide_frame)
        self.guide_upper.pack(anchor = tk.W, padx = 10)
        self.rad_g = ttk.Radiobutton(self.guide_upper, 
                                     text = 'Skeleton', value = False, 
                                     variable = self.sideview_on)
        self.rad_g.pack(side = tk.LEFT)
        self.rad_s = ttk.Radiobutton(self.guide_upper, 
                                     text = 'Side view', value = True, 
                                     variable = self.sideview_on)
        self.rad_s.pack(side = tk.LEFT)
        self.skeleton_canvas = tk.Canvas(self.guide_frame, 
                                         width = 400, height = 569)
        self.skeleton_id = self.skeleton_canvas.create_image(0, 0, anchor = 'nw')
        self.skeleton_canvas.create_image(0, 400, 
                                          anchor = 'nw', image = self.k_image)
        self.side_canvas = tk.Canvas(self.guide_frame, 
                                     width = 400, height = 569)
        self.side_id = self.side_canvas.create_image(0, 0, anchor = 'nw')
        if self.display['sideview']:
            self.side_canvas.pack()
        else:
            self.skeleton_canvas.pack()
        self.dock_note.add(self.guide_frame, text = 'Guide')
        self.display['guide'] = True
        
        # Main
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill = tk.BOTH, expand = True)
        
        self.top = ttk.Frame(self.main_frame)
        self.top.pack(side = tk.TOP, anchor = tk.N, 
                      fill = tk.X, expand = True)
        
        self.display_frame = ttk.LabelFrame(self.top, text = 'Display')
        self.display_frame.pack(side = tk.LEFT, padx = 10, ipady = 3)
        
        zm_text = ttk.Label(self.display_frame, text = 'Zoom [%]')
        self.e_button = ttk.Button(self.display_frame, 
                                   width = 4, image = self.e_image)
        self.zm_values = [  10,   13,   16,   20,  25,  32,  40,  50,  63,  79,
                           100,  126,  158,  200, 251, 316, 398, 501, 631, 794,
                          1000, 1259, 1585, 1995]
        self.combo_zm = ttk.Combobox(self.display_frame, 
                                     values = self.zm_values, width = 12, 
                                     textvariable = self.zoom)
        th_text = ttk.Label(self.display_frame, text = 'Thickness [px]')
        values = [  1,        2,        3,   4,   5,   7,
                   10,  15,  20,  25,  30,  40,  50,  70,
                  100, 150, 200, 250, 300, 400, 500, 700, 1000]
        self.combo_th = ttk.Combobox(self.display_frame, 
                                     values = values, width = 12, 
                                     textvariable = self.thickness)
        self.chk_a = ttk.Checkbutton(self.display_frame, 
                                     variable = self.a_on, text = 'Axes (A)')
        self.chk_b = ttk.Checkbutton(self.display_frame, 
                                     variable = self.b_on, text = 'Scale bar (B)')
        self.chk_p = ttk.Checkbutton(self.display_frame, 
                                     variable = self.p_on, text = 'Points')
        self.chk_d = ttk.Checkbutton(self.display_frame, 
                                     variable = self.d_on, text = 'Dock (D)')
        self.rad_b = ttk.Radiobutton(self.display_frame, 
                                     text = 'Black', value = False, 
                                     variable = self.white_on)
        self.rad_w = ttk.Radiobutton(self.display_frame, 
                                     text = 'White', value = True, 
                                     variable = self.white_on)
        self.e_button.grid(column = 1, row = 0, sticky = tk.W)
        
        zm_text.grid(column = 0, row = 0, padx = 5, sticky = tk.W)
        self.combo_zm.grid(column = 0, row = 1, columnspan = 2, 
                           padx = 5, sticky = tk.W)
        th_text.grid(column = 2, row = 0, padx = 5, sticky = tk.W)
        self.combo_th.grid(column = 2, row = 1, padx = 5, sticky = tk.W)
        self.chk_a.grid(column = 3, row = 0, padx = 5, sticky = tk.W)
        self.chk_b.grid(column = 3, row = 1, padx = 5, sticky = tk.W)
        self.chk_p.grid(column = 4, row = 0, padx = 5, sticky = tk.W)
        self.chk_d.grid(column = 4, row = 1, padx = 5, sticky = tk.W)
        self.rad_b.grid(column = 5, row = 0, padx = 5, sticky = tk.W)
        self.rad_w.grid(column = 5, row = 1, padx = 5, sticky = tk.W)
        
        self.bottom = ttk.Frame(self.main_frame)
        self.bottom.pack(side = tk.BOTTOM, anchor = tk.S,  
                         fill = tk.X, expand = True)
        
        um_text = ttk.Label(self.bottom, text = 'µm')
        self.sbar_entry = ttk.Entry(self.bottom, textvariable = self.sbar_len,
                                    width = 10, justify = tk.RIGHT)
        sb_text = ttk.Label(self.bottom, text = 'Scale bar:')
        self.coor_text = tk.StringVar()
        self.coor_text.set('[x,y,z] =\n    vals =')
        self.coor_info = ttk.Label(self.bottom, 
                                   textvariable = self.coor_text, width = 30)
        self.depth_frame = ttk.Frame(self.bottom)
        
        um_text.pack(side = tk.RIGHT, anchor = tk.N, padx = 5, pady = 5)
        self.sbar_entry.pack(side = tk.RIGHT, anchor = tk.N, pady = 5)
        sb_text.pack(side = tk.RIGHT, anchor = tk.N, padx = 5, pady = 5)
        self.coor_info.pack(side = tk.LEFT, anchor = tk.N, padx = 5, pady = 5)
        self.depth_frame.pack(side = tk.TOP, fill = tk.X)
        
        dr = self.position.depth_range
        self.depth_scale = tk.Scale(self.depth_frame, length=2000, variable=self.depth,
                                    from_ = 0, to = dr[1] - dr[0],
                                    orient = 'horizontal', showvalue = False)
        self.reset_button = ttk.Button(self.depth_frame, text = 'Reset pos')
        
        self.depth_scale.pack(side = tk.TOP)
        self.reset_button.pack()
        
        self.view_frame = ttk.Frame(self.main_frame)
        self.view_frame.pack(padx = 2, pady = 3)
        
        self.view_cf = ttk.Frame(self.view_frame)
        self.barx = tk.Scrollbar(self.view_frame, orient = tk.HORIZONTAL)
        self.bary = tk.Scrollbar(self.view_frame, orient = tk.VERTICAL)
        
        self.barx.pack(side = tk.BOTTOM, fill = tk.X)
        self.bary.pack(side = tk.RIGHT, fill = tk.Y)
        self.view_cf.pack(side = tk.LEFT)
        
        self.view_canvas = tk.Canvas(self.view_cf, 
                                     width = 2000, height = 2000, cursor = 'tcross')
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
        secv = self.secv
        
        if pf == 'Darwin':
            ctrl = 'Command+'
        else:
            ctrl = 'Ctrl+'
        
        self.file_menu.add_command(label = 'Open',
                                   command = self.open_new,
                                   accelerator = ctrl+'O')
        self.file_menu.add_command(label = 'Reload',
                                   command = self.reload,
                                   accelerator = ctrl+'R')
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
                                   accelerator=ctrl+'Z')
        self.edit_menu.add_command(label = 'Redo', 
                                   command = self.redo, 
                                   accelerator = ctrl+'Y')
        self.edit_menu.entryconfig('Undo', state='disable')
        self.edit_menu.entryconfig('Redo', state='disable')
        
        self.settings_menu.add_command(label = 'Channels', 
                                       command = self.open_channels,
                                       accelerator = 'C')
        self.settings_menu.add_command(label='Points', 
                                       command = self.open_points,
                                       accelerator='P')
        self.settings_menu.add_command(label = 'Details', 
                                       command = self.open_details)
        
        self.tools_menu.add_command(label = 'Snapshots', 
                                    command = self.open_snapshots,
                                    accelerator = 'S')
        self.tools_menu.add_command(label = 'Stack', 
                                    command = self.open_stack)
        
        self.skeleton_im = tk_from_array(secv.skeleton_image)
        self.skeleton_canvas.itemconfig(self.skeleton_id, image = self.skeleton_im)
        
        self.side_im = tk_from_array(secv.sideview_image)
        self.side_canvas.itemconfig(self.side_id, image = self.side_im)
        
        self.e_button.configure(command = self.fit_frame)
        self.depth_scale.configure(command = self.depth_trace)
        self.reset_button.configure(command = self.reset_pos)
        self.barx.config(command = self.barx_set)
        self.bary.config(command = self.bary_set)
        
        self.zoom.trace_id = self.zoom.trace('w', self.zoom_trace)
        self.thickness.trace_id = self.thickness.trace('w', self.thickness_trace)
        self.sbar_len.trace_id = self.sbar_len.trace('w', self.sbar_len_trace)
        self.a_on.trace_id = self.a_on.trace('w', self.a_on_trace)
        self.b_on.trace_id = self.b_on.trace('w', self.b_on_trace)
        self.p_on.trace_id = self.p_on.trace('w', self.p_on_trace)
        self.d_on.trace_id = self.d_on.trace('w', self.d_on_trace)
        self.white_on.trace_id = self.white_on.trace('w', self.white_on_trace)
        self.sideview_on.trace_id = self.sideview_on.trace('w', self.sideview_on_trace)
        
        if self.geometry._min_px_size == None:
            self.sbar_entry.configure(state = tk.DISABLED)
        
        self.skeleton_canvas.bind('<Button-1>', self.click_skeleton)
        self.dock_note.bind('<<NotebookTabChanged>>', self.dock_note_changed)
        self.depth_frame.bind('<Configure>', self.depth_configure)
        self.view_canvas.bind('<Button-1>', self.click_view)
        self.view_canvas.bind('<ButtonRelease-1>', self.release_view)
        
        def wrap_bind(widget, event_name, method):
            def func1(*args, **kwargs):
                method(*args, **kwargs)
                self.master.after(5, widget.bind, event_name, func)
            def func(*args, **kwargs):
                widget.unbind(event_name)
                self.master.after(5, func1, *args, **kwargs)
            widget.bind(event_name, func)
            return func
        
        self.view_configure = \
            wrap_bind(self.view_cf, '<Configure>', self.view_configure)
        self.track_skeleton = \
            wrap_bind(self.skeleton_canvas, '<Motion>', self.track_skeleton)
        self.track_view = \
            wrap_bind(self.view_canvas, '<Motion>', self.track_view)
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
        if not self.record_on:
            return
        key = make_key_text(event.keysym, event.state)
        
        if key in ['Ctrl+O', 'Command+O']:
            self.open_new()
        elif key in ['Ctrl+R', 'Command+R']:
            self.reload()
        elif key in ['Ctrl+S', 'Command+S']:
            self.save()
        elif key in ['Shift+Ctrl+S', 'Shift+Command+S']:
            self.save(ask_name = True)
        elif key in ['Ctrl+E', 'Command+E']:
            self.export()
        elif key in ['Ctrl+Z', 'Command+Z']:
            self.undo()
        elif key in ['Ctrl+Y', 'Command+Y']:
            self.redo()
        elif key in ['Ctrl+A', 'Command+A'] and self.display['dock']:
            name = self.dock_note.tab(self.dock_note.select(), 'text')
            if name in ['Channels', 'Points']:
                treeview = getattr(self, name.lower() + '_gui').treeview
                treeview.selection_set(treeview.get_children())
            
        focus = str(self.master.focus_get()).rsplit('!', 1)[-1]
        if 'entry' in focus:
            return
        elif 'combo' in focus:
            return
            
        if key in ['A', 'B', 'D']:
            getattr(self, 'chk_{0}'.format(key.lower())).invoke()
        elif key in ['G', 'C', 'P', 'S']:
            {'G': self.open_guide,
             'C': self.open_channels,
             'P': self.open_points,
             'S': self.open_snapshots}[key]()
        elif key in ['DELETE', 'BACKSPACE']:
            if self.display['point_focus'] != -1:
                self.points.delete(point_ids = [self.display['point_focus']])
            elif self.display['dock']:
                name = self.dock_note.tab(self.dock_note.select(), 'text')
                if name in ['Channels', 'Points', 'Snapshots']:
                    getattr(self, name.lower() + '_gui').delete()
        else:
            self.position_key(key)
    
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
                if self.secv.save():
                    self.terminate = True
            else:
                self.terminate = True
                
    def save(self, ask_name = False):
        if ask_name or os.path.splitext(self.file_path)[1] != '.secv':
            filetypes = [('SectionViewer project file', '*.secv')]
            initialfile = os.path.splitext(self.file_name)[0]
            path = filedialog.asksaveasfilename(
                parent = self.master, 
                filetypes = filetypes, 
                initialdir = init_dir(),
                initialfile = initialfile,
                title = 'Saving the project as SECV format',
                defaultextension = '.secv'
                )
            if len(path) == 0:
                return False
            path = path.replace('\\', '/')
        else:
            path = self.file_path
        self.secv.save(path)
        self.hidx_saved = self.hidx
        self.file_path = path
        self.file_name = os.path.basename(path)
        self.file_dir = os.path.dirname(path)
        save_init(path)
        self.master.title(self.file_name)
        
        return True
    
    def reload(self):
        try:
            display = self.secv.meta_prev.display._format()
            self.secv.reload()
            self.secv.display = display
            self.hidx_saved = self.hidx + 1
            self.cut_history = True
        except Exception:
            messagebox.showerror('Error', traceback.format_exc(),
                                  parent = self.master)
            self.terminate = True
            self.master.destroy()
            self.root.destroy()
    
    
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
        filetypes = [('Portable Network Graphics', '*.png'), 
                     ('JPEG files', '*.jpg'),
                     ('MP4 file format', '*.mp4'),
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
            title = 'Exporting the section image',
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
                                      ['Section image (RGB)',
                                       'Section data (16 bit)'])
                if opt == 1:
                    frame = self.secv.view_frame
                    sort = np.argsort(self.channels.getnames())
                    try:
                        tif.imwrite(path, frame[sort])
                    except:
                        messagebox.showerror('Error', traceback.format_exc() + 
                                             '\nFailed to export TIFF file',
                                             parent = self.master)
                        return
                    save_init(path)
                    return
            
            image = self.secv.view_image
            if self.imwrite(path, image):
                save_init(path)
                
    def position_key(self, key):
        if np.count_nonzero(self.display['shown_channels']) == 0:
            return
        keys = key.split('+')
        if len(keys) > 2:
            return
        if len(keys) == 1:
            flag = ''
            key = keys[0]
        else:
            flag = keys[0]
            key = keys[1]
        if flag not in ['', 'Shift', 'Ctrl']:
            return
        if key in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'K', 'J']:
            if flag == 'Ctrl':
                return
            amount = 1 if flag == 'Shift' else 4
            amount *=  1 if key in ['K', 'UP', 'LEFT'] else -1
            if key in ['J', 'K']:
                axis = 0
            elif key in ['UP', 'DOWN']:
                axis = 1
            else:
                axis = 2
            self.position.shift(amount, axis)
        elif key in ['H', 'L', 'I', 'N']:
            if flag == 'Shift':
                ang = 180 / 256
            elif flag == 'Ctrl':
                ang = 180 / 2
            else:
                ang = 180 / 32
            ang *= 1 if key in ['H', 'I'] else -1
            axis = 1 if key in ['H', 'L'] else 2
            self.position.rotate(ang, axis)
            
    def reset_pos(self, *args):
        if np.count_nonzero(self.display['shown_channels']) > 0:
            self.position.reset()
    
    def thickness_trace(self, *args):
        thickness = self.thickness.get()
        try:
            if thickness == '':
                thickness = 0
            thickness = max(1, min(int(thickness), 1000))
        except:
            thickness = self.display['thickness']
            self.thickness.set(str(thickness))
            return
        self.thickness.set(str(thickness))
        self.display['thickness'] = thickness
            
    def sideview_on_trace(self, *args):
        self.display['sideview'] = self.sideview_on.get()
        if self.display['sideview']:
            self.skeleton_canvas.pack_forget()
            self.side_canvas.pack()
        else:
            self.side_canvas.pack_forget()
            self.skeleton_canvas.pack()
    
    def depth_trace(self, *args):
        if np.count_nonzero(self.display['shown_channels']) == 0:
            self.depth.set(-self.position.depth_range[0])
            return
        depth = self.depth.get()
        op = self.position[0]
        nz = self.position.basis[0]
        from_ = self.position.depth_range[0]
        self.position[0] = op + nz*(depth + from_)
    
    def depth_configure(self, *args):
        w = self.depth_frame.winfo_width() - 70
        self.depth_scale.config(length = w)
        
    def screen_to_image_coor(self, x, y, secv = None):
        if secv is None:
            secv = self.secv
        zoom = secv.display['zoom']
        x /= zoom
        y /= zoom
        cx, cy = secv.display['center']
        iw, ih = secv.geometry['image_size']
        x += iw//2 - cx / zoom
        y += ih//2 - cy / zoom
        return x, y
    
    def image_to_screen_coor(self, x, y, secv = None):
        if secv is None:
            secv = self.secv
        zoom = secv.display['zoom']
        cx, cy = secv.display['center']
        iw, ih = secv.geometry['image_size']
        x -= iw//2 - cx / zoom
        y -= ih//2 - cy / zoom
        x *= zoom
        y *= zoom
        return x, y
    
    def click_view(self, event):
        self.master.focus_set()
        
        if np.count_nonzero(self.display['shown_channels']) == 0:
            return
        self.master.unbind('<Key>')
        x, y = event.x, event.y
        x, y = self.screen_to_image_coor(x, y)
        iw, ih = self.geometry['image_size']
        if x > iw or y > ih or x < 0 or y < 0:
            return
        self.click = np.array([x, y], dtype = float)
        self.dragging = False
        self.record_on = False
        state = desolve_state(event.state)
        state = (state['Shift'], state['Ctrl'], state['Alt'], state['Command'])
        if state == (False, False, False, False):
            self.mode = 0
        elif state == (True, False, False, False):
            self.mode = 1
        elif state == (False, True, False, False):
            self.mode = 2
        elif state == (False, False, True, False):
            self.mode = 3
        self.image_kept = self.secv.view_image_raw.copy()
    
    def release_view(self, event):
        if not self.dragging:
            if self.mode == 0 and self.display['point_focus'] != -1:
                self.open_points(select = self.display['point_focus'])
            elif self.mode == 1:
                iw, ih = self.geometry['image_size']
                v = self.click - np.array([iw, ih]) // 2
                v = v / np.array([iw, ih])
                if np.linalg.norm(v) > 0.08:
                    key = int(np.angle(v[0] + 1j * v[1]) / np.pi * 6)
                    key = ['L', 0, 'N', 'N', 0, 'H', 'H', 0, 'I', 'I', 0][key]
                    if key != 0:
                        self.position_key('Ctrl+' + key)
            elif self.mode == 2:
                coor = self.secv.calc_2d_to_3d(self.click)
                try:
                    self.points.add(coordinate = coor)
                except CoordinateError:
                    pass
        if self.click is not None:
            self.cut_history = True
            self.click = None
            object.__setattr__(self.secv, 'meta_prev', self.meta_kept.copy())
        self.dragging = False
        self.update_params = {}
        self.record_on = True
        self.master.bind('<Key>', self.key)
    
    def track_view(self, event):
        secv = self.secv
        meta_k = self.meta_kept
        
        op, ny, nx = meta_k.position
        exp_rate = meta_k.geometry['expansion_rate']
        iw, ih = meta_k.geometry['image_size']
        
        x, y = event.x, event.y
        x, y = self.screen_to_image_coor(x, y, secv = meta_k)
        self.dragging = self.dragging or (self.click != 
                                          np.array([x, y], dtype = float)).any()
        state = desolve_state(event.state)
        if not state['Click']:
            p = secv.calc_2d_to_3d(np.array([x,y]))
            sort = np.argsort(self.channels.getnames())
            xi, yi = int(x), int(y)
            if 0 <= xi < iw and 0 <= yi < ih:
                vals = secv.view_frame[:, yi, xi]
            else:
                vals = np.zeros(len(self.channels))
            ch_show = np.array(self.display['shown_channels'])
            vals = str(np.round(vals).astype(int)[sort][ch_show[sort]])
            p = str(np.round(p).astype(int)[::-1])
            self.coor_text.set('[x,y,z] = {0}\n    vals = {1}'.format(p, vals))
            
            if len(self.display._shown_points_ids) != 0:
                dists = np.linalg.norm(self.display._shown_points_coors
                                       - np.array([y, x]), axis=1)
                nearest = np.argmin(dists)
    
                if dists[nearest] * self.display['zoom'] <= 3:
                    num = int(self.display._shown_points_ids[nearest])
                    self.display['point_focus'] = num
                else:
                    self.display['point_focus'] = -1
            else: 
                self.display['point_focus'] = -1
            return
        
        if self.click is None:
            return
        if not hasattr(self, 'image_kept'):
            return
        image = self.image_kept
        
        center = np.array([iw, ih])//2
        click = self.click - center
        cursol = np.array([x, y]) - center
        object.__setattr__(self.secv, 'meta_prev', self.secv.metadata.copy())
        
        if self.mode != 3:
            if self.mode == 0:
                shift = cursol - click
                if state['Ctrl']:
                    shift[np.argmin(np.abs(shift))] = 0
                self.position[0] = op - (shift[0]*nx + shift[1]*ny) / exp_rate
                M = np.float32([[1, 0, shift[0]],[0, 1, shift[1]]])
                
            elif self.mode == 1:
                angle = np.angle((cursol[0] + 1j*cursol[1]) / (click[0] + 1j*click[1]))
                if state['Ctrl']:
                    angle = round(angle/np.pi*12)*np.pi/12
                ny1 =  np.sin(angle)*nx + np.cos(angle)*ny
                nx1 =  np.cos(angle)*nx - np.sin(angle)*ny
                self.position[1:] = ny1, nx1
                M = cv2.getRotationMatrix2D((float(iw//2), float(ih//2)), 
                                            -angle/np.pi*180, 1)
                
            elif self.mode == 2:
                expand = np.linalg.norm(cursol) / np.linalg.norm(click)
                self.geometry['expansion_rate'] = exp_rate * expand
                M = cv2.getRotationMatrix2D((float(iw//2), float(ih//2)), 0, expand)
            
            back = [255, 255, 255] if meta_k.display['white_back'] else [0, 0, 0]
            cv2.warpAffine(image, M, (iw, ih), dst = self.raw_image,
                           borderMode = cv2.BORDER_CONSTANT, borderValue = back)
            object.__setattr__(secv, 'view_image_raw', self.raw_image)
            self.update_params = {'level': 5}
            
        else:
            fr = np.abs(click) > np.array([iw, ih])//8
            if fr.any():
                imsize = np.array([iw, ih], dtype = int)
                trim = imsize.astype(float)
                if fr.all():
                    trim[:] *= cursol / click
                elif fr[0]:
                    trim[0] *= cursol[0] / click[0]
                elif fr[1]:
                    trim[1] *= cursol[1] / click[1]
                trim = imsize + 2*((trim - imsize) / 2).astype(int)
                trim[trim < 50] = 50
                self.geometry['image_size'] = tuple(trim)
                
                zoom = meta_k.display['zoom']
                cx, cy = meta_k.display['center']
                iw, ih = int(iw * zoom), int(ih * zoom)
                ul = np.array([cx - iw // 2, cy - ih // 2])
                warp = np.array([[zoom, 0., ul[0]], [0., zoom, ul[1]]])
                self.update_params = {'level': 6, 'warp': warp}
            else:
                return
    
    def click_skeleton(self, event):
        self.focus_set()
        self.open_points(select = self.display['point_focus'])
    
    def track_skeleton(self, event):
        points = self.display._skeleton_points
        x, y = event.x, event.y
        if len(points) != 0:
            dists = np.linalg.norm(points[:,:2] - np.array([x, y]), axis=1)
            nearest = np.argmin(dists)
            if dists[nearest] <= 5:
                self.display['point_focus'] = nearest
            else:
                self.display['point_focus'] = -1
        else:
            self.display['point_focus'] = -1
            
    def get_dock_note_tab(self, name):
        tabs = self.dock_note.tabs()
        tabdict = {}
        for tab in tabs:
            tabdict[self.dock_note.tab(tab, 'text')] = tab
        return tabdict[name]
            
    def dock_note_changed(self, event):
        if not self.display['dock']:
            self.d_on.set(True)
        name = self.dock_note.tab(self.dock_note.select(), 'text')
        if name == 'Guide':
            self.display['guide'] = True
        else:
            self.display['guide'] = False
    
    def open_guide(self):
        self.dock_note.select(self.get_dock_note_tab('Guide'))
        
    def open_channels(self):
        self.dock_note.select(self.get_dock_note_tab('Channels'))
        self.channels_gui.settings()
        
    def open_points(self, select = -1):
        self.dock_note.select(self.get_dock_note_tab('Points'))
        self.points_gui.settings(select = select)
        
    def open_snapshots(self):
        self.dock_note.select(self.get_dock_note_tab('Snapshots'))
        self.snapshots_gui.settings()
        
    def open_details(self):
        self.details_gui.settings()
        
    def open_stack(self):
        self.stack_gui.settings()
            
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
                from_ = self.position.depth_range[0]
                to = self.position.depth_range[1]
                maximum = to - from_
                
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
                
                self.record_on = False
                pos = self.position
                nz = pos.basis[0]
                orient = pos[0] + pos.depth_range[0] * nz
                
                for i in range(maximum + 1):
                    pb.configure(value = i)
                    pb.update()
                    pos[0] = orient + i*nz
                    if not self.update([['position', 0]]):
                        continue
                    if self.cancel:
                        break
                    out.write(self.secv.view_image)
                out.release()
                
                pos[0] = self.meta_kept.position[0]
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
            obj = self.secv.metadata
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
            obj = self.secv.metadata
            for k in l[:-1]:
                obj = obj[k]
            obj[l[-1]] = new
    
    def monitor(self):
        meta = self.secv.metadata.copy()
        meta_p, meta_k = self.secv.meta_prev, self.meta_kept
        loc = meta._locate_difference(meta_p)
        if len(loc) > 0 or (not self.record_on_prev and self.record_on) \
           or self.hidx != self.hidx_kept:
            success = self.update(loc, **self.update_params)
            if success:
                self.record_on_prev = self.record_on
                if self.record_on:
                    self.update_history(meta, meta_k)
            else:
                self.secv.metadata = self.meta_kept._format()
                self.update(level = 3)
            if self.record_on:
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
        
    def update(self, 
               loc: list = [], 
               level: int = None,
               warp: np.ndarray = None,
               ) -> bool:
        
        if level is None:
            level = self.secv._get_update_level(loc)
        try:
            success = self.secv.update(level = level)
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
        if warp is None:
            warp = np.array([[zoom, 0., ul[0]], [0., zoom, ul[1]]])
        back = [255, 255, 255] if self.display['white_back'] else [0, 0, 0]
        
        cv2.warpAffine(self.secv.view_image_raw, warp, (w, h), 
                       dst = self.main_image,
                       borderMode = cv2.BORDER_CONSTANT,
                       borderValue = back)
        
        if self.display['points'] and len(self.display._shown_points_ids) > 0:
            
            ids = self.display._shown_points_ids
            point_names = np.array(self.points.getnames())
            point_colors = np.array(self.points.getcolors())
            point_coors = self.points.coorsonimage()
            thickness = self.display['thickness']
            
            point_coors[:,2], point_coors[:,1] = self.image_to_screen_coor(point_coors[:,2], 
                                                                           point_coors[:,1])
            
            draw_points(self.main_image, point_coors[ids], point_colors[ids],
                        point_names[ids], thickness=thickness)
            
            p_num = self.display['point_focus']
            if 0 <= p_num < len(self.points):    
                ps = slice(p_num, p_num + 1)
                draw_points(self.main_image, point_coors[ps], point_colors[ps],
                            point_names[ps], thickness=thickness, r = 6)
        
        ul = np.fmax(0, ul)
        br = np.fmax(0, br)
        self.main_image[:ul[1]] = 240
        self.main_image[br[1]:] = 240
        self.main_image[:,:ul[0]] = 240
        self.main_image[:,br[0]:] = 240
        
        if self.display['axis']:
            if 0 <= cx < w:
                self.main_image[:,cx] = 255 - self.main_image[:,cx]
            if 0 <= cy < h:
                self.main_image[cy] = 255 - self.main_image[cy]
        
        self.view_im = tk_from_array(self.main_image)
        self.view_canvas.itemconfig(self.view_id, image = self.view_im)
        
        iw0, ih0 = self.geometry['image_size']
        if not hasattr(self, 'raw_image'):
            self.raw_image = np.zeros([ih0, iw0, 3], np.uint8)
        if self.raw_image.shape[:2] != (ih0, iw0):
            self.raw_image = np.zeros([ih0, iw0, 3], np.uint8)
        
        v1 = (iw//2 + w - 50 - cx) / (iw + 2*w - 100)
        v2 = v1 + w / (iw + 2*w - 100)
        self.barx.set(v1, v2)
        v1 = (ih//2 + h - 50 - cy)/(ih + 2*h - 100)
        v2 = v1 + h / (ih + 2*h - 100)
        self.bary.set(v1, v2)
        
        if level <= 3 and self.record_on:
            from_, to = self.position.depth_range
            if hasattr(self, 'depth_scale'):
                self.depth_scale.config(to = to - from_)
            self.depth.set(-from_)
        
        if self.display['guide']:
            if self.display['sideview']:
                self.side_im = tk_from_array(self.secv.sideview_image)
                self.side_canvas.itemconfig(self.side_id, image = self.side_im)
            else:
                self.skeleton_im = tk_from_array(self.secv.skeleton_image)
                self.skeleton_canvas.itemconfig(self.skeleton_id, image = self.skeleton_im)
        
        if self.record_on:
            self.sbar_len.set(str(self.geometry['scale_bar_length']))
            self.channels_gui.update(loc)
            self.points_gui.update(loc)
            self.snapshots_gui.update(loc)
        self.stack_gui.update()
        
        return True
        
    def update_history(self, meta, meta_k):
        loc = meta._locate_difference(meta_k)
        loc1 = [l for l in loc if l[0] != 'display']
        loc1 = [l for l in loc1 if l[0] != 'files' or
                                   l == ['files', 'paths']]
        loc1 = [l for l in loc1 if l != ['channels']]
        if ['files', 'paths'] in loc1:
            loc1 += [['display', 'shown_channels']]
        if ['points'] in loc1:
            loc1 += [['display', 'shown_points']]
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
                elif loc1[0][0] in ['geometry', 'position']:
                    merge = len(loc1) == 1
                elif loc1[0][0] == 'channels':
                    merge = len(np.unique([l[2] for l in loc1])) == 1
                elif loc1[0][0] == 'points':
                    merge = ['points'] not in loc1
                    if merge:
                        u = np.unique([l[2] for l in loc1])
                        merge = len(u) == 1 and u[0] in (0, 1)
                elif loc1[0][0] == 'snapshots':
                    merge = loc1[0] != ['snapshots']
                    if merge:
                        for l in loc1:
                            merge *= l[2] == 'name'
                    
            merge *= self.history[-1][0] == loc1
            merge *= not self.cut_history
            merge *= self.hidx == len(self.history) - 1
            merge *= self.hidx_saved != self.hidx
                
            if merge:
                self.history[-1][2] = news
            else:
                p = [l[1] for l in loc1 if l[0] == 'position']
                if len(p) > 1:
                    p = slice(np.amin(p), np.amax(p) + 1, p[1] - p[0])
                    po = np.array(
                        [olds[i] for i in range(len(olds)) 
                         if loc1[i][0] == 'position']
                        )
                    pn = np.array(
                        [news[i] for i in range(len(news)) 
                         if loc1[i][0] == 'position']
                        )
                    olds = [olds[i] for i in range(len(olds)) 
                            if loc1[i][0] != 'position']
                    news = [news[i] for i in range(len(news)) 
                            if loc1[i][0] != 'position']
                    loc1 = [l for l in loc1 if l[0] != 'position']
                    loc1 += [['position', p]]
                    olds += [po]
                    news += [pn]
                
                self.hidx += 1
                self.history = self.history[: self.hidx]
                self.history += [[loc1, olds, news]]
                if self.hidx_saved >= len(self.history):
                    self.hidx_saved = -1
        self.cut_history = False
        self.meta_kept = meta.copy()
        self.hidx_kept = self.hidx