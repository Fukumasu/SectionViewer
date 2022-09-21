import os
import pathlib
import pickle
import traceback

import cv2
import numpy as np
from PIL import Image, ImageTk
import tifffile as tif
from tkinter import filedialog
from tkinter import messagebox

from .data import Data
from .geometry import Geometry
from .position import Position
from .channels import Channels
from .points import Points
from .stack import Stack
from .snapshots import Snapshots

from . import utils as ut


class Hub:
    def __init__(self, gui, path, secv=None):
        self.gui = gui
        
        self.data = []
        self.geometry = {}
        self.position = None
        self.channels = []
        self.points = []
        self.snapshots = []
        
        self.thickness = int(gui.thickness.get())
        if gui.zoom.get() != '':
            self.zoom = int(gui.zoom.get())/100
        
        if secv != None:
            self.data = secv['data']
            if 'geometry' in secv:
                self.geometry = secv['geometry']
            if 'position' in secv:
                self.position = secv['position']
            if 'channels' in secv:
                self.channels = secv['channels']
            if 'points' in secv:
                self.points = secv['points']
            if 'snapshots' in secv:
                self.snapshots = secv['snapshots']
            if 'memories' in secv:
                self.snapshots = secv['memories']
            self.secv_name = path
        else:
            self.data = [[path]]
            self.secv_name = None
            
            self.box = []
            self.data = Data(self)
        
        self.geometry = Geometry(self)
        self.position = Position(self)
        self.channels = Channels(self)
        self.points = Points(self)
        self.stack = Stack(self)
        self.snapshots = Snapshots(self)
        self.reload = Reload(self)
        self.hist_grouping = Hist_grouping(self)
        
        r = 3
        l = np.arange(-2*r,2*r+1)
        l = (l[None]**2 + l[:,None]**2)**0.5
        s = l - r + 1
        s[s<0] = 0
        s[s>1] = 1
        l -= r + 0.2
        l[l<0] = 0
        l[l>1] = 1
        s = 1 - s
        self.r = r
        self.l = l
        self.s = s
        
        self.g_shape = self.gui.g_shape
        self.g_im = np.empty([self.g_shape[0], self.g_shape[1],3], np.uint8)
        self.g_im2 = np.empty([3,self.g_shape[0], self.g_shape[1]], np.uint8)
        self.g_section = np.empty([self.g_shape[0], self.g_shape[1]])
        self.g_edges = np.array([[-1, 1, 2,-1, 3,-1,-1,-1], \
                                 [-1,-1,-1, 0,-1, 0,-1,-1], \
                                 [-1,-1,-1, 0,-1,-1, 0,-1], \
                                 [-1,-1,-1,-1,-1,-1,-1, 0], \
                                 [-1,-1,-1,-1,-1, 0, 0,-1], \
                                 [-1,-1,-1,-1,-1,-1,-1, 0], \
                                 [-1,-1,-1,-1,-1,-1,-1, 0], \
                                 [-1,-1,-1,-1,-1,-1,-1,-1]])
        self.g_vivid = [(160,130,110), ( 23, 23,170), ( 23,170, 23), (170, 23, 23)]
        self.g_thick = [1, 1, 1, 1]
        
        self.calc_guide()
        self.gui.master.update()
        
        if path[-5:] == '.secv':
            self.box = []
            self.data = Data(self)
        if not hasattr(self, 'zoom'):
            w, h = gui.sec_cf.winfo_width()-4, gui.sec_cf.winfo_height()-4
            iw, ih = self.geometry['im_size']
            zoom = min((w-10)/iw, (h-10)/ih)
            iw1, ih1 = int(iw*zoom), int(ih*zoom)
            ul = (int(iw1//2-w//2), int(ih1//2-h//2))
            zs = str(int(zoom*100))
            gui.zoom.set(zs)
            self.zoom = float(gui.zoom.get())/100
            gui.upperleft = ul

        if len(self.box) == 0:
            messagebox.showerror('Error', 
                                 "No data couldn't be extracted",
                                 parent=self.gui.master)
            self.load_success = False
            return
        
        if not self.calc_geometry():
            self.position = [[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]]
            self.position = Position(self)
            if not self.calc_geometry():
                messagebox.showerror('Error', 
                                     'Data shape is invalid\n CZYX = {0}'.format(self.box.shape),
                                     parent=self.gui.master)
                self.load_success = False
                return
        if self.secv_name==None:
            mx = np.amax(self.frame, axis=(1,2))
            for i in range(len(mx)):
                self.channels.val[i][3] = mx[i]
            self.channels.val = self.channels.val
            self.calc_image()
        
        self.calc_sideview()
        
        self.history = [[0,empty()]]
        self.hidx = -1
        self.hidx_saved = -1
        
        self.load_success = True
        
        
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'box':
            if hasattr(value, 'shape'):
                self.geometry['shape'] = value.shape
        
    
    def calc_geometry(self):
        geo = self.geometry
        xy_rs, z_rs = geo['res_xy'], geo['res_z']
        if None in [xy_rs, z_rs]:
            ratio = 1.
        else:
            ratio = z_rs / xy_rs
        self.ratio = ratio
        
        self.frame = np.empty([len(self.box), *geo['im_size'][::-1]], np.uint16)
        self.sec_raw = np.empty([*geo['im_size'][::-1], 4], np.uint8)
        self.s_frame = np.empty([len(self.box), 569, 400], np.uint16)
        self.s_frame[:,284] = 0
        self.s_frame1 = np.empty([len(self.box), 284, 400], np.uint16)
        self.s_frame2 = np.empty([len(self.box), 284, 400], np.uint16)
        
        exp_rate = geo['exp_rate']
        bar_len = geo['bar_len']
        
        lpx = int(bar_len/xy_rs*exp_rate) if xy_rs != None else 0
        self.lpx = lpx
        
        return self.calc_frame()
        
    
    def calc_frame(self, x=None):
        
        box = self.box
        dc, dz, dy, dx = box.shape
        pos = self.position.asarray()
        op, ny, nx = pos.copy()
        nz = -np.cross(ny, nx)
        
        pos[:,0] /= self.ratio
        nz[0] /= self.ratio
        pos[0] += np.array([dz, dy, dx])//2
        pos[1:] /= self.geometry['exp_rate']
        nz /= self.geometry['exp_rate']
        
        if type(x) == type(None):
            ch_show = np.arange(len(self.lut))[self.ch_show]
        else:
            ch_show = np.array(x)
        
        if self.thickness == 1:
            if not ut.calc_section(box, pos, self.frame, np.array(self.frame[0].shape)//2,
                                   ch_show):
                return False
        elif self.thickness <= 10:
            start = -(self.thickness//2)
            stop = start + self.thickness
            if not ut.stack_section(box, pos, nz, start, stop,
                                    self.frame, np.array(self.frame[0].shape)//2,
                                    ch_show):
                return False
        else:
            start = -(self.thickness//2)
            stop = start + self.thickness
            if not ut.fast_stack(box, pos, nz, start, stop,
                                 self.frame, np.array(self.frame[0].shape)//2,
                                 ch_show):
                return False
        
        if type(x) == type(None):
            for i in set(range(len(self.lut))) - set(ch_show):
                self.frame[i] = 0
        
        nz = -np.cross(ny, nx)
        n = np.array([nz, ny, nx])
        dz *= self.ratio
        peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],
                          [dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]], np.float)
        peaks -= op + np.array([dz//2,dy//2,dx//2])
        peaks = np.linalg.solve(n.T, peaks.T).T
        from_ = int(np.amin(peaks[:,0]))
        to = int(np.amax(peaks[:,0]))
        self.gui.scale_to = to - from_
        if hasattr(self.gui, 'scale'):
            self.gui.scale.config(to=to-from_)
        self.gui.depth.set(-from_)
        self.scale_orient = op + from_*nz
        
        self.calc_image()
        return True
        
        
    def calc_image(self):
        if self.gui.white.get():
            ut.calc_bgr_w(self.frame, self.lut, self.colors, 
                          np.arange(len(self.lut))[self.ch_show], self.sec_raw)
        else:
            ut.calc_bgr(self.frame, self.lut, self.colors, 
                        np.arange(len(self.lut))[self.ch_show], self.sec_raw)
        self.put_points()
        
    
    def put_points(self):
        if not self.gui.p_on.get() or len(self.points) == 0:
            self.gui.section = self.sec_raw.copy()
            self.sec_points = []
        else:
        
            im = self.sec_raw.copy()
            
            dc, dz, dy, dx = self.box.shape
            names = np.array(self.points.getnames())
            colors = np.array(self.points.getcolors())
            points = np.array(self.points.getcoordinates())
            
            points -= np.array([dz//2,dy//2,dx//2])
            points[:,0] *= self.ratio
            op, ny, nx = self.position.asarray()
            nz = -np.cross(ny, nx)
            n = np.array([nz, ny, nx])
            points -= op
            points = np.linalg.solve(n.T, points.T).T
            points = np.append(points, np.arange(len(points))[:,None], axis=1)
            th_show = 10 + self.thickness//2
            show = np.abs(points[:,0]) < th_show
            colors = colors[show]
            names = names[show]
            points = points[show]
            points[:,1:3] *= self.geometry['exp_rate']
            la, lb = self.geometry['im_size']
            points[:,1:3] += np.array([lb//2, la//2])
            show = np.prod(points[:,1:3]//np.array([lb, la]) == 0, axis=1, dtype=np.bool)
            colors = colors[show]
            colors = np.append(colors, np.zeros([len(colors), 1]) + 255, axis=1)
            names = names[show]
            points = points[show]
            sort = np.argsort(points[:,0])[::-1]
            points, colors, names = points[sort], colors[sort], names[sort]
            start = -(self.thickness//2)
            stop = start + self.thickness
            shallow, deep = points[:,0] < start, points[:,0] > stop - 1
            points[:,0][~shallow*~deep] = 1
            points[:,0][shallow] = (np.cos((points[:,0][shallow]-start)/10*np.pi) + 1)/2
            points[:,0][deep] = (np.cos((points[:,0][deep]-(stop-1))/10*np.pi) + 1)/2
            self.sec_points = points[points[:,0] > 0.5, 1:]
    
            r, l, s = self.r, self.l, self.s
            for point, color, name in zip(points, colors, names):
                a, b = point[1:3].astype(np.int)
                square = im[max(a-2*r,0):max(a+2*r+1,0), max(b-2*r,0):max(b+2*r+1,0)]
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
            self.gui.section = im
        
        if hasattr(self.gui, 'sec_canvas'):
            x, y, iw, ih, w, h = self.put_axes_bar()
            self.scroll_config(x, y, iw, ih, w, h)
        
        
    def put_axes_bar(self):
        gui = self.gui
        im = gui.section.copy()
        if gui.b_on.get():
            im[-25:-20, -20-self.lpx:-20,:3] = 0 if gui.white.get() else 255
            im[-25:-20, -20-self.lpx:-20,3] = 255
        
        zoom = self.zoom
        ih, iw = im.shape[:2]
        iw, ih = int(iw*zoom), int(ih*zoom)
        
        x0, y0 = gui.upperleft
        w, h = gui.sec_cf.winfo_width()-4, gui.sec_cf.winfo_height()-4
        im = cv2.warpAffine(im, np.array([[zoom,0,-x0],[0,zoom,-y0]], dtype=np.float),
                            (w, h))
        
        x = iw//2 - x0
        y = ih//2 - y0
        if gui.a_on.get():
            if 0 <= x < len(im[0]):
                a = im[:,x,:3]*(im[:,x,3:]/255)
                if gui.white.get():
                    a += 255 - im[:,x,3:]
                im[:,x,:3] = 255 - a.astype(np.uint8)
                im[:,x,3] = 255
            if 0 <= y < len(im):
                a = im[y,:,:3]*(im[y,:,3:]/255)
                if gui.white.get():
                    a += 255 - im[y,:,3:]
                im[y,:,:3] = 255 - a.astype(np.uint8)
                im[y,:,3] = 255
        
        gui.sec_image = im
        im = np.append(im[:,:,2::-1], im[:,:,3:], axis=2)
        gui.sec_im = ImageTk.PhotoImage(Image.fromarray(im))
        
        x, y = w//2 - x, h//2 - y
        gui.sec_canvas.coords(gui.sec_id, x, y)
        x, y = x - x0, y - y0
        gui.sec_canvas.coords(gui.sec_back, x, y, x+iw, y+ih)
        gui.sec_canvas.itemconfig(gui.sec_id, image=gui.sec_im)
        gui.sec_canvas.itemconfig(gui.sec_back, fill='#ffffff' if gui.white.get() else '#000000')
        
        return x, y, iw, ih, w, h
    
    def scroll_config(self, x, y, iw, ih, w, h, vx0=None, vy0=None):
        gui = self.gui
        sr = (x-w+50,y-h+50,x+iw+w-50,y+ih+h-50)
        gui.sec_canvas.config(scrollregion=sr)
        gui.imx, gui.imy = x, y
        x0, y0 = gui.upperleft
        if vx0==None:
            vx0 = (x0+x-sr[0])/(sr[2]-sr[0])
        if vy0==None:
            vy0 = (y0+y-sr[1])/(sr[3]-sr[1])
        gui.sec_canvas.xview_moveto(vx0)
        gui.sec_canvas.yview_moveto(vy0)
        
    
    def calc_guide(self, rect=True):
        pos = self.position.asarray()
        op, ny, nx = pos
        nz = -np.cross(ny, nx)
        
        exp_rate = self.geometry['exp_rate']
        
        im_size = np.array(self.geometry['im_size'])
        
        edges = self.g_edges
        vivid = self.g_vivid
        thick = self.g_thick
        
        dc, dz, dy, dx = self.geometry['shape']
        n = np.array([nz, ny, nx])
        
        points = np.array(self.points.getcoordinates())
        if len(points) == 0:
            points = np.empty([0,3])
        within = np.prod(points >= 0, axis=1, dtype=bool)* \
                 np.prod(points <= np.array([dz, dy, dx]), axis=1, dtype=bool)
        points -= np.array([dz//2,dy//2,dx//2])
        points[:,0] *= self.ratio
        points -= op
        points = np.linalg.solve(n.T, points.T).T
        
        vivid_p = np.array(self.points.getcolors(), np.uint8)
        if len(vivid_p) > 0:
            vivid_p[:] = vivid_p//1.5
            vivid_p = vivid_p.astype(np.uint8)
        
        names = np.array(self.points.getnames())
        
        dz = dz*self.ratio
        peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],[dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]])
        peaks -= op + np.array([dz//2,dy//2,dx//2])
        peaks = np.linalg.solve(n.T, peaks.T).T
        
        neg = peaks[:,0] <= 0
        pn = neg[None,:]*~neg[:,None]
        pn = np.array(np.where((pn + pn.T)*(edges>=0)))
        sec = np.average(peaks[pn,1:], axis=0, weights=np.tile(np.abs(peaks[pn[::-1],:1]), (1,2)))
        
        eye = 2.5*self.L
        center = np.average(peaks[:,1:], axis=0)
        points[:,1:] *= eye/(points[:,:1] + eye)
        peaks[:,1:] *= eye/(peaks[:,:1] + eye)
        points[:,1:] -= center
        peaks[:,1:] -= center
        
        h, w = self.g_im.shape[:2]
        e = min(w/self.L*0.8, w*exp_rate/im_size[0]*0.8, h*exp_rate/im_size[1]*0.8)
        shift = 4
        radius = int(2.5*2**shift)
        peaks = ((peaks[:,2:0:-1]*e + np.array([w,h])//2)*2**shift).astype(int)
        points = points[:,::-1]*e
        points[:,:2] += np.array([w,h])//2
        self.guide_points = points.astype(int)
        points = (points*2**shift).astype(int)
        c = (np.array([w,h])//2 - center[::-1]*e).astype(int)
        
        im_size = (e*im_size/exp_rate/2).astype(np.int)
        ul, br = (c[0] - im_size[0], c[1] - im_size[1]), (c[0] + im_size[0], c[1] + im_size[1])
        ul0 = (max(0, ul[0]), max(0, ul[1]))
        br0 = (max(0, br[0]), max(0, br[1]))
        
        ul2, br2 = ul0, br0
        if rect:
            if hasattr(self, 'zoom') and hasattr(self.gui, 'sec_cf'):
                iw, ih = self.geometry['im_size']
                iw, ih = iw*self.zoom, ih*self.zoom
                cw, ch = self.gui.sec_cf.winfo_width()-4, self.gui.sec_cf.winfo_height()-4
                x0, y0 = self.gui.upperleft
                x1, y1 = x0 + cw, y0 + ch
                x0, x1, y0, y1 = x0/iw, x1/iw, y0/ih, y1/ih
                self.ul1 = (int(ul[0] + (br[0]-ul[0])*x0), int(ul[1] + (br[1]-ul[1])*y0))
                self.br1 = (int(ul[0] + (br[0]-ul[0])*x1), int(ul[1] + (br[1]-ul[1])*y1))
                ul2 = (max(0,self.ul1[0],ul0[0]), max(0,self.ul1[1],ul0[1]))
                br2 = (min(max(0,self.br1[0]),br0[0]), min(max(0,self.br1[1]),br0[1]))
        else:
            if hasattr(self, 'ul1'):
                ul2 = (max(0,self.ul1[0],ul0[0]), max(0,self.ul1[1],ul0[1]))
                br2 = (min(max(0,self.br1[0]),br0[0]), min(max(0,self.br1[1]),br0[1]))
                
        im0 = self.g_im2
        im0[0] = 255
        
        im = self.g_im
        im[:,:,0] = im0[0]
        im[:,:,0] -= 15
        im[ul0[1]:br0[1], ul0[0]:br0[0], 0] += 15
        im[:,:,1:] = im[:,:,:1]
        
        if len(sec) > 1:
            transparent = 0.5
            section = self.g_section
            section[:] = 0
            
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
            sec = (((sec - center)[:,::-1]*e + np.array([w,h])//2)*2**shift).astype(int)
            uls, brs = (np.amin(sec, axis=0)*2**(-shift)).astype(int) - 1, (np.amax(sec, axis=0)*2**(-shift)).astype(int) + 1
            uls = np.fmax(uls, 0)
            square = (slice(uls[1],brs[1]), slice(uls[0],brs[0]))
            
            cv2.fillConvexPoly(im0[0], sec[sort], 240, lineType=cv2.LINE_AA, shift=shift)
            section[square] = 255
            section[square] -= im0[0][square]
            section[square] /= 15/transparent
        
            im[ul2[1]:br2[1],ul2[0]:br2[0],1] = \
                (255 - section[ul2[1]:br2[1],ul2[0]:br2[0]]*(35/transparent)).astype(np.uint8)
            im[ul2[1]:br2[1],ul2[0]:br2[0],::2] = 255
            section = section[:,:,None][square]
            
            im0 = im0.transpose(1,2,0)[square]
            im0[:] = im[square]
        else:
            im[ul2[1]:br2[1],ul2[0]:br2[0]] = 255
        
        order = np.argsort(points[:,2])
        within = within[order]
        p_order = order[(points[order,2]>0)*~within][::-1]
        for p, color, n in zip(points[p_order], vivid_p[p_order], names[p_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            cv2.circle(im, (p[0], p[1]), radius, color, thickness=-1, lineType=cv2.LINE_AA, shift=shift)
            # im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            # im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
        
        where = np.array(np.where((edges>=0)*~neg[None]*~neg[:,None])).T
        for pair in where:
            eg = int(edges[tuple(pair)])
            cv2.line(im, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),
                     vivid[eg], thick[eg], cv2.LINE_AA, shift=shift)
        for i in range(len(sec)):
            eg = int(edges[tuple(pn[:,i])])
            cv2.line(im, tuple(sec[i]), tuple(peaks[pn[:,i][~neg[pn[:,i]]][0]]),\
                     vivid[eg], thick[eg], cv2.LINE_AA, shift=shift)
                
        p_order = order[(points[order,2]>0)*within][::-1]
        for p, color, n in zip(points[p_order], vivid_p[p_order], names[p_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            cv2.circle(im, (p[0], p[1]), radius, color, thickness=-1, lineType=cv2.LINE_AA, shift=shift)
            # im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            # im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
          
        if len(sec) > 1:
            im[square] = (section*im0 + (1 - section)*im[square]).astype(np.uint8)
        
        im[c[1],:] = 255
        im[:,c[0]] = 255
        
        n_order = order[(points[order,2]<=0)*within][::-1]
        for p, color, n in zip(points[n_order], vivid_p[n_order], names[n_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            cv2.circle(im, (p[0], p[1]), radius, color, thickness=-1, lineType=cv2.LINE_AA, shift=shift)
            # im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            # im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
            
        for i in range(len(sec)):
            eg = int(edges[tuple(pn[:,i])])
            cv2.line(im, tuple(sec[i]), tuple(peaks[pn[:,i][neg[pn[:,i]]][0]]),\
                     vivid[eg], thick[eg], cv2.LINE_AA, shift=shift)
        where = np.array(np.where((edges>=0)*neg[None]*neg[:,None])).T
        for pair in where:
            eg = int(edges[tuple(pair)])
            cv2.line(im, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),\
                     vivid[eg], thick[eg], cv2.LINE_AA, shift=shift)
                
        n_order = order[(points[order,2]<=0)*~within][::-1]
        for p, color, n in zip(points[n_order], vivid_p[n_order], names[n_order]):
            color = (int(color[0]), int(color[1]), int(color[2]))
            cv2.circle(im, (p[0], p[1]), radius, color, thickness=-1, lineType=cv2.LINE_AA, shift=shift)
            # im[p[1]-1:p[1]+2,p[0]-2:p[0]+3] = color
            # im[p[1]-2:p[1]+3:4,p[0]-1:p[0]+2] = color
        
        im[:22,-66:] -= np.fmin(255 - self.gui.xyz, im[:22,-66:])
        
        gui = self.gui
        gui.guide = im
        
        if hasattr(gui, 'guide_canvas'):
            gui.guide_im = ImageTk.PhotoImage(Image.fromarray(im[:,:,::-1]))
            gui.guide_canvas.itemconfig(gui.guide_id, image=gui.guide_im)
            
            
    def calc_sideview(self, x=None):
        pos = self.position.asarray()
        op, ny, nx = pos
        nz = -np.cross(ny, nx)
        
        exp_rate = self.geometry['exp_rate']
        
        dc, dz, dy, dx = self.box.shape
        dz *= self.ratio
        op += np.array([dz, dy, dx])//2
        
        pos = np.array([op, nx, nz])
        pos[:,0] /= self.ratio
        pos[1:] /= exp_rate/2
        
        if type(x) == type(None):
            ch_show = np.arange(len(self.lut))[self.ch_show]
        else:
            ch_show = np.array(x)
        
        ut.fast_section(self.box, pos, self.s_frame1, np.array([142, 200]),
                        ch_show)
        self.s_frame[:,:284] = self.s_frame1
        
        pos = np.array([op, ny, nz])
        pos[:,0] /= self.ratio
        pos[1:] /= exp_rate/2
        
        ut.fast_section(self.box, pos, self.s_frame2, np.array([142, 200]),
                        ch_show)
        self.s_frame[:,285:] = self.s_frame2
        self.calc_sideimage()
        
        
    def calc_sideimage(self):
        gui = self.gui
        
        im = gui.side if hasattr(gui, 'side') else np.empty([*self.s_frame.shape[1:], 4], np.uint8)
        if gui.white.get():
            ut.calc_bgr_w(self.s_frame, self.lut, self.colors, 
                          np.arange(len(self.lut))[self.ch_show], im)
        else:
            ut.calc_bgr(self.s_frame, self.lut, self.colors, 
                        np.arange(len(self.lut))[self.ch_show], im)
        im[:,200,:3] = 0 if gui.white.get() else 255
        im[:,200,3] = 255 - im[:,200,3]
        im[284,::5,:3] = 0 if gui.white.get() else 255
        im[284,::5,3] = 255 - im[284,::5,3]
        
        if self.gui.p_on.get() and len(self.points) > 0:
            dc, dz, dy, dx = self.box.shape
            names = np.array(self.points.getnames())
            colors = np.array(self.points.getcolors())
            points = np.array(self.points.getcoordinates())
            
            op, ny, nx = self.position.asarray()
            nz = -np.cross(ny, nx)
            
            la, lb = 400, 284
            exp_rate = self.geometry['exp_rate']/2
            th_show = 10
            
            points -= np.array([dz//2,dy//2,dx//2])
            points[:,0] *= self.ratio
            points -= op
            
            for nw, im1 in zip([nx, ny], [im[:284], im[285:]]):
                pos = np.array([op, nw, nz])
                
                op, ny1, nx1 = pos
                nz1 = -np.cross(ny1, nx1)
                n = np.array([nz1, ny1, nx1])
                points1 = np.linalg.solve(n.T, points.T).T
                show = np.abs(points1[:,0]) < th_show
                colors1 = colors[show]
                names1 = names[show]
                points1 = points1[show]
                points1[:,1:] *= exp_rate
                points1[:,1:] += np.array([lb//2, la//2])
                show = np.prod(points1[:,1:]//np.array([lb, la]) == 0, axis=1, dtype=np.bool)
                colors1 = colors1[show]
                colors1 = np.append(colors1, np.zeros([len(colors1), 1]) + 255, axis=1)
                names1 = names1[show]
                points1 = points1[show]
                points1[:,0] = (np.cos(points1[:,0]/th_show*np.pi) + 1)/2
        
                r, l, s = self.r, self.l, self.s
                for point, color, name in zip(points1, colors1, names1):
                    a, b = point[1:3].astype(np.int)
                    square = im1[max(a-2*r,0):a+2*r+1, max(b-2*r,0):b+2*r+1]
                    square1 = square.copy()
                    a0, b0 = a - max(a-2*r,0), b - max(b-2*r,0)
                    l1, s1 = l[max(2*r-a0,0):, max(2*r-b0,0):], s[max(2*r-a0,0):, max(2*r-b0,0):]
                    l1, s1 = l1[:len(square), :len(square[0])], s1[:len(square), :len(square[0])]
                    square2 = color[None,None]*s1[:,:,None]
                    square2[:,:,3] = 255
                    square1 = square1*l1[:,:,None] + square2*(1-l1[:,:,None])
                    square[:] = (square*(1-point[0]) + square1*point[0]).astype(np.uint8)
                    (w, h), baseline = cv2.getTextSize(name, 2, 0.5, 2)
                    square1 = im1[max(a+7-h,0):max(a+7+baseline,0),max(b+6,0):max(b+6+w,0)]
                    square2 = square1.copy()
                    cv2.putText(im1, name, (b+6,a+7), 2, 0.5, (0,0,0,255), 2, cv2.LINE_AA)
                    cv2.putText(im1, name, (b+6,a+7), 2, 0.5, color, 1, cv2.LINE_AA)
                    square1[:] = (square2*(1-point[0]) + square1*point[0]).astype(np.uint8)
        
        gui.side = im
        
        if hasattr(gui, 'side_canvas'):
            gui.side_im = ImageTk.PhotoImage(Image.fromarray(np.append(im[:,:,2::-1], im[:,:,3:], axis=2)))
            gui.side_canvas.itemconfig(gui.side_id, image=gui.side_im)
            gui.side_canvas.itemconfig(gui.side_back, fill='#ffffff' if gui.white.get() else '#000000')
            
        
        
    def save(self, path=None):
        if path == None:
            filetypes = [('SectionViewer project file', '*.secv')]
            initialdir = self.gui.file_dir
            initialfile = os.path.splitext(self.gui.file_name)[0]
            path = filedialog.asksaveasfilename(parent=self.gui.master, 
                                                filetypes=filetypes, 
                                                initialdir=initialdir,
                                                initialfile=initialfile,
                                                title='Saving the project as SECV format',
                                                defaultextension='.secv')
            if len(path) == 0:
                return False
        
        self.hidx_saved = self.hidx
        
        secv = {}
        
        data = self.data.dat
        files = [d[0] for d in data]
        ch_load = [d[1] for d in data]
        data = []
        for f, c in zip(files, ch_load):
            if np.array(c).any():
                r = pathlib.Path(f)
                try:
                    r = r.relative_to(path)
                    r = str(r)
                    r.replace('\\', '/')
                except:
                    path1 = path
                    n = 1
                    while len(os.path.split(path1)[1]) != 0:
                        path1 = os.path.split(path1)[0]
                        try:
                            r = r.relative_to(path1)
                            break
                        except:
                            n += 1
                    if r.is_absolute():
                        r = None
                    else:
                        r = str(r)
                        for _ in range(n):
                            r = os.path.join('..', r)
                        r.replace('\\', '/')
                data += [[f, c, r]]
        data = tuple(data)
        secv['data'] = data
        
        secv['geometry'] = self.geometry.geo
        secv['geometry']['shape'] = self.box.shape
        
        pos = self.position.asarray()
        pos[:,0] /= self.ratio
        pos[0] += np.array(self.box.shape[1:])//2
        secv['position'] = pos.tolist()
        
        secv['channels'] = [[c[0], [c[1][0], c[1][1], c[1][2]],
                             c[2], c[3]] for c in self.channels.chs]
        sort = np.argsort(self.points.getnames())
        secv['points'] = [self.points.pts[s] for s in sort]
        
        sort = np.argsort(self.snapshots.names())
        secv['snapshots'] = [self.snapshots.snapshots[s] for s in sort]
        
        display = {}
        display['thickness'] = self.thickness
        display['axis'] = self.gui.a_on.get()
        display['scale bar'] = self.gui.b_on.get()
        display['points'] = self.gui.p_on.get()
        display['dock'] = self.gui.d_on.get()
        display['white back'] = self.gui.white.get()
        display['zoom'] = self.zoom
        display['upperleft'] = self.gui.upperleft
        secv['display'] = display
        
        try:
            with open(path, 'wb') as f:
                pickle.dump(secv, f, protocol=4)
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent=self.gui.master)
            return False
            
        self.gui.iDir = path
        self.gui.title = os.path.basename(path)
        with open('init_dir.txt', 'w') as f:
            f.write(os.path.dirname(path))
        self.gui.master.title(self.gui.title)
        self.secv_name = path
        
        return True
    
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
                                 parent=self.gui.master)
            return False
    
    
    def export(self):
        filetypes = [('Portable Network Graphics', '*.png'), 
                     ('JPEG files', '*.jpg'),
                     ('MP4 file format', '*.mp4'),
                     ('TIFF files', '*.tif'),
                     ('JPEG 2000 files', '*.jp2'),
                     ('Portable image format', '*.pbm'),
                     ('Sun rasters', '*.sr')]
        
        initialdir = self.gui.file_dir
        initialfile = os.path.splitext(self.gui.file_name)[0]
        path = filedialog.asksaveasfilename(parent=self.gui.master,
                                            filetypes=filetypes,
                                            initialdir=initialdir,
                                            initialfile=initialfile,
                                            title='Export the section image',
                                            defaultextension='.png')
        if len(path) > 0:
            path = path.replace('\\', '/')
            gui = self.gui
            
            if path[-4:] == '.mp4':
                gui.ask_fps(path)
                with open('init_dir.txt', 'w') as f:
                    f.write(os.path.dirname(path))
                return
            
            im = gui.section.copy()
            if gui.a_on.get():
                im[len(im)//2,:,:3] = 0 if gui.white.get() else 255
                im[len(im)//2,:,3] = 255 - im[len(im)//2,:,3]
                im[:,len(im[0])//2,:3] = 0 if gui.white.get() else 255
                im[:,len(im[0])//2,3] = 255 - im[:,len(im[0])//2,3]
            if gui.b_on.get():
                im[-25:-20, -20-self.lpx:-20,:3] = 0 if gui.white.get() else 255
                im[-25:-20, -20-self.lpx:-20,3] = 255 - im[-25:-20, -20-self.lpx:-20,3]
            opt = 1
            if path[-4:] == '.png':
                opt = gui.ask_option(gui.master, 'Saving options', 
                                     ['Transparent PNG (RGBA)',
                                      '24-bit PNG (RGB)'],
                                     geometry='250x120')
            if path[-4:] == '.tif':
                opt = gui.ask_option(gui.master, 'Saving options',
                                     ['Section image (RGB)',
                                      'Section data (16 bit)'])
                if opt == 1:
                    sort = np.argsort(self.channels.getnames())
                    try:
                        tif.imwrite(path, self.frame[sort])
                    except:
                        messagebox.showerror('Error', traceback.format_exc() + 
                                             '\nFailed to export TIFF file',
                                             parent=self.gui.master)
                        return
                    with open('init_dir.txt', 'w') as f:
                        f.write(os.path.dirname(path))
                    return
            if opt == 1:
                a = im[:,:,3:]/255
                im = im[:,:,:3]*a
                if gui.white.get():
                    im += 255*(1-a)
                im = im.astype(np.uint8)
            elif opt == -1:
                return
            
            if self.imwrite(path, im):
                with open('init_dir.txt', 'w') as f:
                    f.write(os.path.dirname(path))
        
    
    def group_history(self, n):
        self.history[-n:] = [[self.hist_grouping, self.history[-n:]]]
        self.hidx = min(-1, self.hidx + n - 1)
        self.hidx_saved = min(-1, self.hidx_saved + n - 1)
        self.gui.master.title('*' + self.gui.title if self.hidx != self.hidx_saved else self.gui.title)
        
    
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
        pass
            
class Hist_grouping:
    def __init__(self, Hub):
        self.Hub = Hub
    
    def undo(self, arg):
        for a in arg[::-1]:
            a[0].undo(a[1])
    def redo(self, arg):
        for a in arg:
            a[0].redo(a[1])
    
    
class Reload:
    def __init__(self, Hub):
        self.Hub = Hub
        
    def __call__(self):
        Hub = self.Hub
        path = Hub.secv_name
        if path == None:
            messagebox.showerror('Error', 'SECV files to be reloaded is unknown.',
                                 parent=self.Hub.gui.master)
            return
        try:
            with open(path, 'rb') as f:
                secv = pickle.load(f)
            dat = secv['data']
            geo = secv['geometry']
            pos = secv['position']
            chs = secv['channels']
            pts = secv['points']
        except:
            messagebox.showerror('Error', traceback.format_exc(),
                                 parent=self.Hub.gui.master)
            return None
        
        if 'snapshots' in secv:
            snp = secv['snapshots']
        elif 'memories' in secv:
            snp = secv['memories']
        else:
            snp = []
        
        ul = self.Hub.gui.upperleft
        iw0, ih0 = self.Hub.geometry['im_size']
        
        typ, old, new = [], [], []
        try:
            for v, m in zip([dat, geo, pos, chs, pts, snp],
                            [Hub.data, Hub.geometry, Hub.position, 
                             Hub.channels, Hub.points, Hub.snapshots]):
                old += [m.val]
                if m.reload(v): 
                    new += [m.val]
                    typ += [m]
                else: del old[-1]
        except:
            messagebox.showerror('Error', traceback.format_exc() + 
                                  '\nFailed to reload {0}'.format(path),
                                  parent=self.Hub.gui.master)
            return None
            
        if len(new) > 0:
            Hub = self.Hub
            idx, hist = Hub.hidx, Hub.history
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [typ, old, new]]]
            Hub.hidx = -1
            Hub.hidx_saved = -1
                
            gui = Hub.gui
            gui.edit_menu.entryconfig('Undo', state='normal')
            gui.edit_menu.entryconfig('Redo', state='disable')
            gui.master.title(gui.title)
            
            iw1, ih1 = self.Hub.geometry['im_size']
            self.Hub.gui.upperleft = (ul[0]-iw0//2+iw1//2, ul[1]-ih0//2+ih1//2)
            
            Hub.calc_geometry()
            if Hub.gui.d_on.get():
                if Hub.gui.guide_mode == 'guide':
                    Hub.calc_guide()
                elif Hub.gui.guide_mode == 'sideview':
                    Hub.calc_sideview()
    
    
    def undo(self, arg):
        self.reload(arg[0], arg[1])
        
    def redo(self, arg):
        self.reload(arg[0], arg[2])
        
    def reload(self, typ, new):
        ul = self.Hub.gui.upperleft
        iw0, ih0 = self.Hub.geometry['im_size']
        for t, n in zip(typ, new):
            t.val = n
        iw1, ih1 = self.Hub.geometry['im_size']
        self.Hub.gui.upperleft = (ul[0]-iw0//2+iw1//2, ul[1]-ih0//2+ih1//2)
        if not self.Hub.calc_geometry():
            self.Hub.position.pos = [[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]]
            self.Hub.calc_geometry()
        if self.Hub.gui.d_on.get():
            if self.Hub.gui.guide_mode == 'guide':
                self.Hub.calc_guide()
            elif self.Hub.gui.guide_mode == 'sideview':
                self.Hub.calc_sideview()
        
        for cl in [self.Hub.channels, self.Hub.points, self.Hub.snapshots]:
            cl.refresh_tree()
    
        
