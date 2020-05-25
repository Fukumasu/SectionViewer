import numpy as np
import cv2
import sys, os
import oiffile as oif
import tifffile as tif
import pickle
import tkinter, tkinter.filedialog

# データから表示する明るさを参照する Look-up table を計算する関数
def LUT(max_value, vmin, vmax):
    lut = np.arange(max_value+1)[None]
    diff = vmax - vmin
    lut = ((1/diff[:,None])*(lut - vmin[:,None]))
    lut[lut<0] = 0
    lut[lut>1] = 1
    return lut

def load_svst(text):
    a = {}
    exec(text, {'__builtins__':None}, a)
    return a["channels"], a["points"], a["settings"], a["pos"], a["init_pos"]

class SectionViewer:
    
    def __init__(self, file_name):
        
        self._xyz = cv2.imread("img/xyz.png")
        
        c_button = np.zeros([21,21,3], np.uint8)
        c_button[2:-2,2:-2] = cv2.imread("img/c_button.png")
        self._c_button = c_button
        
        s_button = np.zeros([21,21,3], np.uint8)
        s_button[2:-2,2:-2] = cv2.imread("img/s_button.png")
        self._s_button = s_button
        
        x_button = np.zeros([21,21,3], np.uint8)
        x_button[2:-2,2:-2] = cv2.imread("img/x_button.png")
        self._x_button = x_button
        
        if len(file_name[0]) == 1:
            file_name = [file_name]
        self._file_name = file_name
        
        boxes = []
        xy_rs, z_rs = None, None
        
        for f in file_name:
            if f[-4:] == ".oib":
                boxes += [oif.imread(f)]
                
                
                try:
                    with oif.OifFile(f) as oib:
                        axes = oib.axes
                        shape = oib.shape
                        data = oib.mainfile
                    shape = dict(np.append(np.array(list(axes))[:,None], np.array(shape)[:,None], axis=1))
                    axes = dict(np.append(np.array(list(axes))[::-1][:,None], np.arange(len(axes))[:,None], axis=1))
        
                    pxs = axes.copy()
                    try:
                        pxs["C"] = 0
                    except:
                        1
                    for ax in ["Z", "Y", "X"]:
                        ax_data = data['Axis {0} Parameters Common'.format(axes[ax])]
                        px = abs((ax_data["EndPosition"] - ax_data["StartPosition"])/float(shape[ax]))
                        if ax_data["UnitName"] == "nm":
                            px /= 1000
                        pxs[ax] = px
                    xy_rs = (pxs["X"] + pxs["Y"])/2
                    z_rs = pxs["Z"]
                except:
                    1
    
            elif f[-4:] == ".tif" or f[-5:] == ".tiff":
                boxes += [tif.imread(f)]
            elif f[-7:] == ".pickle":
                with open(f, "rb") as g:
                    boxes += [pickle.load(g)]
        
        box = boxes[0]
        del boxes[0]
        if len(box.shape) == 3:
            box = box[None]
        ch_lens = [len(box)]
        while len(boxes) > 0:
            b = boxes[0]
            if len(b.shape) == 3:
                b = b[None]
            ch_lens += [len(b)]
            box = np.append(box, b, axis=0)
            del b, boxes[0]
        
        dc, dz, dy, dx = box.shape
        self._box = box
        self._shape = dc, dz, dy, dx
        self._ch_lens = ch_lens
        
        ch_cl, ch_vn, ch_vx, ch_mx = [], [], [], []
        pt_nm, pt_cd, pt_cl = [], [], []
        win_size, exp_rate, bar_len = None, None, None
        pos, ips = None, None
        
        for f in file_name:
            svst = os.path.splitext(f)[0]
            svst += ".svst"
            if os.path.isfile(svst):
                with open(svst, "r") as st:
                    text = st.read()
                chs, pts, sts, pos_, ips_ = load_svst(text)
                try:    ch_cl += chs["colors"]
                except: ch_cl += [None]
                try:    ch_vn += chs["vmins"]
                except: ch_vn += [None]
                try:    ch_vx += chs["vmaxs"]
                except: ch_vx += [None]
                try:    ch_mx += chs["maxs"]
                except: ch_mx += [None]
                if len(pt_nm) == 0:
                    try:    pt_nm = pts["names"]
                    except: 1
                if len(pt_cd) == 0:
                    try:    pt_cd = pts["coordinates"]
                    except: 1
                if len(pt_cl) == 0:
                    try:    pt_cl = pts["colors"]
                    except: 1
                try:    xy_rs = sts["xy"]
                except: 1
                try:    z_rs  = sts["x"]
                except: 1
                if win_size == None:
                    try:    win_size = sts["window size"]
                    except: 1
                if exp_rate == None:
                    try:    exp_rate = sts["expansion"]
                    except: 1
                if bar_len == None:
                    try:     bar_len = sts["bar length"]
                    except:  1
                if pos_ != None:
                    pos = pos_
                if ips_ != None:
                    ips = ips_
        
        if None in ch_cl or len(ch_cl) != dc:
            ch_cl = np.zeros([dc, 3], np.uint8) + 255
            ch_cl[:,0] = ((np.linspace(0, 180, dc + 1)[:-1] + 60)%180).astype(np.uint8)
            ch_cl = cv2.cvtColor(ch_cl[None], cv2.COLOR_HSV2BGR)[0]
        else:
            ch_cl = np.uint8(ch_cl)
        if None in ch_vn or len(ch_vn) != dc:
            ch_vn = np.zeros([dc], np.int)
        else:
            ch_vn = np.int64(ch_vn)
        if None in ch_vx or len(ch_vx) != dc:
            ch_vx = np.percentile(box, 99.5, axis=(1,2,3)).astype(np.int)
        else:
            ch_vx = np.int64(ch_vx)
        if None in ch_mx or len(ch_mx) != dc:
            ch_mx = np.amax(box, axis=(1,2,3)).astype(np.int)
        else:
            ch_mx = np.int64(ch_mx)
        if (ch_vn >= ch_vx).any():
            raise ValueError("vmin should be smaller than vmax for all channels")
        
        self._max_values = ch_mx
        self._lut = LUT(max(ch_mx), ch_vn, ch_vx)
        
        ch_cl = np.append(np.append(ch_cl, ch_vn[:,None], axis=1), ch_vx[:,None], axis=1).astype(np.int)
        self._c = ch_cl
        self._cs = [ch_cl]
        self._c_num = -1
        
        
        pt_nm, pt_cd, pt_cl = np.array(pt_nm), np.float64(pt_cd), np.uint8(pt_cl)
        if len(pt_cd) == 0:
            pt_cd = np.zeros([0,3])
        if len(pt_cl) != len(pt_cd):
            pt_cl = np.zeros([len(pt_cd), 3], np.uint8)
            pt_cl[:,0] = ((np.linspace(0, 180, len(pt_cd) + 1)[:-1] + 90)%180).astype(np.uint8)
            pt_cl[:,1] = 155
            pt_cl[:,2] = 255
            pt_cl = cv2.cvtColor(pt_cl[None], cv2.COLOR_HSV2BGR)[0]
        if len(pt_nm) != len(pt_cd):
            pt_nm = np.array(["p{0}".format(i) for i in range(len(pt_cd))])
        
        points = [[(0,0,0), (0,0,0),""]]
        points += [[tuple(pt_cd[i]), (int(pt_cl[i][0]), int(pt_cl[i][1]), int(pt_cl[i][2])), \
                   pt_nm[i]] for i in range(len(pt_cd))]
        
        self._names = pt_nm
        self._coors = pt_cd
        self._colors = pt_cl
        
        self._points = points
        self._point_sets = [[p.copy() for p in self._points]]
        self._pt_num = -1
        
        
        if None in [xy_rs, z_rs]:
            ratio = 1.
        else:
            ratio = z_rs / xy_rs
        L = (dx**2 + dy**2 + (dz*ratio)**2)**0.5
        if win_size == None:
            win_size = (600, 600)
        max_size = max(win_size)
        if exp_rate == None:
            exp_rate = max_size/L
        if xy_rs != None:
            if bar_len == None:
                bar_len = round(80*xy_rs/exp_rate, -int(np.log10(80*xy_rs/exp_rate)))
            lpx = int(bar_len/xy_rs*exp_rate)
        else:
            bar_len = None
            lpx = 0
        if max_size % 2 == 0:
            alpha = np.linspace(-max_size/exp_rate/2, max_size/exp_rate/2, max_size + 1)[None,:-1,None]
            beta = np.linspace(-max_size/exp_rate/2, max_size/exp_rate/2, max_size + 1)[:-1,None,None]
        else:
            alpha = np.linspace(-max_size/exp_rate/2, max_size/exp_rate/2, max_size)[None,:,None]
            beta = np.linspace(-max_size/exp_rate/2, max_size/exp_rate/2, max_size)[:,None,None]
        alpha = alpha[:, max_size//2 - win_size[0]//2: max_size//2 - win_size[0]//2 + win_size[0]]
        beta = beta[max_size//2 - win_size[1]//2: max_size//2 - win_size[1]//2 + win_size[1]]
        self._L = L
        self._bar_len = bar_len
        self._lpx = lpx
        self._xy_rs = xy_rs
        self._z_rs = z_rs
        self._ratio = ratio
        self._win_size = win_size
        self._exp_rate = exp_rate
        self._alpha = alpha
        self._beta = beta
        self._len_a = len(alpha[0])
        self._len_b = len(beta)
        
        
        if ips == None:
            ips = np.array([[0,0,0], [0,1,0], [0,0,1]], np.float)
        else:
            ips = np.array(ips)
            ips[2] /= np.linalg.norm(ips[2])
            ips[1] = ips[1] - ips[2]*np.inner(ips[1], ips[2])
            ips[1] /= np.linalg.norm(ips[1])
        frame = self._sectioner(ips)
        if type(frame) == type(None):
            ips = np.array([[0,0,0], [0,1,0], [0,0,1]], np.float)
        if pos == None:
            pos = ips.copy()
        else:
            pos = np.array(pos)
            pos[2] /= np.linalg.norm(pos[2])
            pos[1] = pos[1] - pos[2]*np.inner(pos[1], pos[2])
            pos[1] /= np.linalg.norm(pos[1])
        frame = self._sectioner(pos)
        if type(frame) == type(None):
            pos = ips.copy()
            self._frame = self._sectioner(pos)
        else:
            self._frame = frame
        
        self._init_pos = ips
        self._pos = pos.copy()
        self._init_navi = self._navigator(ips, init=True)
        
        self._a_on = True
        self._b_on = lpx != 0
        self._p_on = True
        
        self._inits = [ips]
        self._i_num = -1
        self._poses = [pos]
        self._p_num = -1
        self._exp_rates = [self._exp_rate]
        self._e_num = -1
        self._win_sizes = [np.array(self._win_size)]
        self._w_num = -1
        self._bar_lens = [self._bar_len]
        self._l_num = -1
        
        self._history = [self._move_pos]
        self._h_num = -1
        
        self._shift = np.array([0,0])
        self._angle = 0
        self._expand = 1
        self._trim = np.array(self._win_size)
        self._ldown = np.array([0,0])
        self._pre_event = (0,0)
        self._count = 0
        
        self._lock = False
        
        self._angs = {108:32, 76:256, 12:2, 104:-32, 72:-256, 8:-2, 105:-32, 73:-256,\
                      9:-2, 110:32, 78:256, 14:2, 106:4, 74:1, 107:-4, 75:-1}
         
    
    def viewer(self):
        
        sys.stdout.write("\rz:{0:>7.2f} px, y:{1:>7.2f} px, x:{2:>7.2f} px".format(0, 0, 0))
        
        cv2.namedWindow(winname="Section View")
        cv2.setMouseCallback("Section View", self._mouse_operation)
        cv2.namedWindow(winname="Navigator")
        cv2.setMouseCallback("Navigator", self._mouse_operation_2)
        self._move_pos()
        new_pro = True
        
        while(1):
            
            if cv2.getWindowProperty("Navigator", 0) < 0 \
            or cv2.getWindowProperty("Section View", 0) < 0:
                key = 27
            elif new_pro:
                key = cv2.waitKey(10)
            else:
                new_pro = True
            key_ = cv2.waitKey(10)
            if key_ != -1:
                key = key_
            
            if key == 102: # F
                self._new_process()
                self._inits += [self._pos]
                self._history += [self._record_init]
                self._record_init()
            
            elif key == 97: # A
                self._a_on = not self._a_on
                self._show_sec()
                
            elif key == 98 and self._lpx != 0: # B
                self._b_on = not self._b_on
                self._show_sec()
                
            elif key == 112: # P
                self._p_on = not self._p_on
                self._show_sec()
                
            elif key == 99: # C
                self._lock = True
                self._channel_color_settings()
                self._lock = False
                
            elif key == 115: # S
                self._lock = True
                self._stack_settings()
                self._lock = False
                
            elif key in [121, 122]: # Y, Z
                undo = {121:(1,1,0), 122:(0,-1,-1)}
                while key in [-1,121,122]:
                    if key != -1:
                        self._h_num = min(self._h_num + undo[key][0], -1)
                        self._history[self._h_num](undo[key][1])
                        self._h_num = max(self._h_num + undo[key][2], -len(self._history))
                    if cv2.getWindowProperty("Navigator", 0) < 0 \
                    or cv2.getWindowProperty("Section View", 0) < 0:
                        break
                    key = cv2.waitKey(10)
                    key_ = cv2.waitKey(10)
                    if key_ != -1:
                        key = key_
                new_pro = False
                
            elif key == 100: # D
                self._new_process()
                self._point_sets += [[[(0,0,0), (0,0,0),""]]]
                self._history += [self._new_points]
                self._new_points()
                
            elif key == 27: # Esc
                self._save_settings()
                break
            
            else:
                pos, change = self._set_pos(key)
                
                if change:
                    self._new_process()
                    self._poses += [pos]
                    self._history += [self._move_pos]
                    self._move_pos()

        cv2.destroyAllWindows()
    
        
    # ↓ Functions used only within the functions above
    
    # 与えられた平面位置における断面の各ピクセル値を求める関数
    def _sectioner(self, pos):
        
        alpha, beta = self._alpha, self._beta
        dc, dz, dy, dx = self._shape
        
        pos = pos.copy()[:,None,None]
        pos[:,:,:,0] /= self._ratio
        pos[0] += np.array([dz//2, dy//2, dx//2])
        s = pos[0] + pos[1]*beta + pos[2]*alpha

        section = np.prod((s > 0)*(s < np.array([dz-1, dy-1, dx-1])), axis=2, dtype=np.bool)

        if not section.any():
            return None
        else:
            grid = s[section]
            grid, decm = grid.astype(np.int), grid % 1

            g = grid[:,:,None] + np.array([[[1,0,1,1,1,0,0,0], [1,1,0,1,0,1,0,0], [1,1,1,0,0,0,1,0]]])    
            d = np.abs(np.prod(decm[:,:,None] - np.array([[[0,1,0,0,0,1,1,1], [0,0,1,0,1,0,1,1], [0,0,0,1,1,1,0,1]]]), axis=1))
            d = np.tile(d, (dc, 1, 1))

            res = np.average(self._box[:,g[:,0],g[:,1],g[:,2]], axis=2, weights=d)

            frame = np.zeros([dc, *s[:,:,0].shape], np.int)
            frame[:, section] = (res + 0.5).astype(np.int)

            return frame
            
            
    def _navigator(self, pos=None, exp_rate=None, win_size=None, init=False):
        
        if type(pos) == type(None):
            pos = self._pos.copy()
        if type(exp_rate) == type(None):
            exp_rate = self._exp_rate
        if type(win_size) == type(None):
            win_size = np.array(self._win_size)
        
        edges = np.array([[ -1, 179,  60,  -1, 120,  -1,  -1,  -1], \
                          [ -1,  -1,  -1, 150,  -1, 150,  -1,  -1], \
                          [ -1,  -1,  -1, 150,  -1,  -1, 150,  -1], \
                          [ -1,  -1,  -1,  -1,  -1,  -1,  -1, 150], \
                          [ -1,  -1,  -1,  -1,  -1, 150, 150,  -1], \
                          [ -1,  -1,  -1,  -1,  -1,  -1,  -1, 150], \
                          [ -1,  -1,  -1,  -1,  -1,  -1,  -1, 150], \
                          [ -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1]])
        
        edges2 = np.array([[ 0, 1, 1, 0, 1, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0], \
                           [ 0, 0, 0, 0, 0, 0, 0, 0]])
        
        dc, dz, dy, dx = self._shape
        op, ny, nx = pos
        nz = -np.cross(ny, nx)
        n = np.array([nz, ny, nx])
        
        points = self._coors.copy()
        points -= np.array([dz//2,dy//2,dx//2])
        points[:,0] *= self._ratio
        points -= op
        points = np.linalg.solve(n.T, points.T).T
        
        colors = self._colors.copy()
        if len(colors) > 0:
            colors = cv2.cvtColor(colors[None], cv2.COLOR_BGR2HSV)[0]
        
        names = self._names.copy()
        
        dz = dz*self._ratio
        peaks = np.array([[0,0,0],[0,0,dx],[0,dy,0],[0,dy,dx],[dz,0,0],[dz,0,dx],[dz,dy,0],[dz,dy,dx]])
        peaks -= op + np.array([dz//2,dy//2,dx//2])
        peaks = np.linalg.solve(n.T, peaks.T).T
        
        neg = peaks[:,0] <= 0
        pn = neg[None,:]*~neg[:,None]
        pn = np.array(np.where((pn + pn.T)*(edges>0)))
        sec = np.average(peaks[pn,1:], axis=0, weights=np.abs(np.tile(peaks[pn[::-1],:1], (1,2))))
        
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
        
        eye = 2.5*self._L
        points[:,1:] *= eye/(points[:,:1] + eye)
        peaks[:,1:] *= eye/(peaks[:,:1] + eye)
        
        l = 800
        e = l/self._L*3/4
        im = np.zeros([l,l,3], np.uint8)
        c = l//2
        peaks = (peaks[:,2:0:-1]*e).astype(np.int) + c
        points = (points[:,::-1]*e).astype(np.int)
        points[:,:2] += c
        self._navi_points = points//2
        sec = (sec[:,::-1]*e).astype(np.int) + c
        
        im[:,:,2] = 255
        
        try:
            im = cv2.polylines(im, sec[None,sort], True, (0,0,0), 1)
            h, w = im.shape[:2]
            mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
            within = np.where(np.prod(sec[sort]%l == sec[sort], axis=1, dtype=np.bool))[0][0]
            seed = sec[sort][[(within+1)%len(sec), (within-1)%len(sec)]]
            seed -= sec[sort][within]
            seed = 20*np.sum(seed/np.linalg.norm(seed, axis=1)[:,None], axis=0)
            seed = (sec[sort][within] + seed).astype(np.int)
            im = cv2.floodFill(im, mask, seedPoint=tuple(seed), newVal=(150,10,255))[1]
        except:
            1
        
        ld = int(init)*2
        
        where = np.array(np.where((edges>0)*~neg[None]*~neg[:,None])).T
        for w in where:
            im = cv2.line(im, tuple(peaks[w[0]]), tuple(peaks[w[1]]),\
                          (int(edges[tuple(w)]), int(80*edges2[tuple(w)]), int(220-50*edges2[tuple(w)])), 3 - ld)
        for i in range(len(sec)):
            im = cv2.line(im, tuple(sec[i]), tuple(peaks[pn[:,i][~neg[pn[:,i]]][0]]),\
                          (int(edges[tuple(pn[:,i])]), int(80*edges2[tuple(pn[:,i])]),\
                           int(220-20*edges2[tuple(pn[:,i])])), 3 - ld)
        if not init:
            
            order = np.argsort(points[:,2])
            p_order = order[points[order,2]>0][::-1]
            for p, color, n in zip(points[p_order], colors[p_order], names[p_order]):
                color[1] = color[1]//2
                color[2] = 220
                color = (int(color[0]), int(color[1]), int(color[2]))
                im = cv2.circle(im, tuple(p[:2]), int(6*eye/(p[2] + eye)), color, -1)
                im = cv2.putText(im, n, tuple(p[:2]+15), 2, 0.8, color, 1, cv2.LINE_AA)
            
            win_size = (e*win_size/exp_rate/2).astype(np.int)
            im = cv2.rectangle(im,(c - win_size[0], c - win_size[1]),\
                               (c + win_size[0], c + win_size[1]), (0,0,200), 2)
            im = cv2.line(im, (0, c), (l, c), (0,0,200), 2)
            im = cv2.line(im, (c, 0), (c, l), (0,0,200), 2)
            
        im = cv2.polylines(im, sec[None,sort], True, (150,50,230), 4 - ld)
        
        if not init:
            n_order = order[points[order,2]<=0][::-1]
            for p, color, n in zip(points[n_order], colors[n_order], names[n_order]):
                color[2] = int(color[2]//1.5)
                color = (int(color[0]), int(color[1]), int(color[2]))
                im = cv2.circle(im, tuple(p[:2]), int(6*eye/(p[2] + eye)), color, -1)
                im = cv2.putText(im, n, tuple(p[:2]+15), 2, 0.8, color, 1, cv2.LINE_AA)
        for i in range(len(sec)):
            im = cv2.line(im, tuple(sec[i]), tuple(peaks[pn[:,i][neg[pn[:,i]]][0]]),\
                          (int(edges[tuple(pn[:,i])]), int(220*edges2[tuple(pn[:,i])]),\
                           int(190-30*edges2[tuple(pn[:,i])])), 4 - ld)
        where = np.array(np.where((edges>0)*neg[None]*neg[:,None])).T
        for w in where:
            im = cv2.line(im, tuple(peaks[w[0]]), tuple(peaks[w[1]]),\
                          (int(edges[tuple(w)]), int(220*edges2[tuple(w)]), int(190-30*edges2[tuple(w)])), 4 - ld)
        
        im = cv2.cvtColor(im, cv2.COLOR_HSV2BGR)
        im = cv2.resize(cv2.GaussianBlur(im, (3,3), 0), (400,400))
        
        im[-22:,-66:] -= np.amin(np.append(255 - self._xyz[None], im[None,-22:,-66:], axis=0), axis=0)
        
        if not init:
            im = np.average(np.append(im[None], self._init_navi[None], axis=0),\
                            axis=0, weights=[6,1]).astype(np.uint8)
        
        return im
        
    
    def _set_pos(self, key):
        op, ny, nx = self._pos
        pos = self._pos.copy()
        nz = np.cross(ny, nx)
        
        angs = self._angs
        
        change = True

        if key in [108, 76, 12, 104, 72, 8]: # L, H
            theta = np.pi/angs[key]
            pos[2] = np.cos(theta)*nx + np.sin(theta)*nz
        elif key in [105 ,73, 9, 110, 78, 14]: # I, N
            phi = np.pi/angs[key]
            pos[1] = np.cos(phi)*ny + np.sin(phi)*nz
        elif key in [106, 74, 107, 75]: # J, K
            pos[0] +=  angs[key]*nz
        elif key == 118: # V
            pos = self._init_pos
        else:
            change = False
        
        return pos, change
    
    
    def _mouse_operation(self, event, x, y, flags, param):
        
        if not self._lock:
            
            v = np.array([x - self._len_a//2, y - self._len_b//2], np.float)
            op, ny, nx = self._pos
            self._kersol = x, y
            
            if event == cv2.EVENT_LBUTTONDOWN:
                self._ldown = v
                
            elif event == cv2.EVENT_LBUTTONUP: # Click or Tap
                
                change = False
                
                if self._pre_event[0] == cv2.EVENT_LBUTTONDOWN:
                    if x < 21 and y < 21 and flags == 0 and self._a_on:
                        self._lock = True
                        self._channel_color_settings()
                        self._lock = False
                    elif 22 < x < 42 and y < 21 and flags == 0 and self._a_on:
                        self._lock = True
                        self._stack_settings()
                        self._lock = False
                    elif -20-self._lpx <= x-self._len_a < -20 and -25 <= y-self._len_b < -20\
                    and flags == 0 and self._b_on:
                        im = self._im.copy()
                        if self._p_on:
                            im = self._put_points(im)
                        if self._a_on:
                            im[self._len_b//2] = 255 - im[self._len_b//2]
                            im[:,self._len_a//2] = 255 - im[:,self._len_a//2]
                            im[3:20,3:20] = self._c_button[2:-2,2:-2]
                            im[3:20,24:41] = self._s_button[2:-2,2:-2]
                        im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
                        a = cv2.getTextSize(" um",0,0.4,1)[0][0]
                        org = (self._len_a-a-20, self._len_b-28)
                        im = cv2.putText(im, " um",org,0,0.4,(0,0,0),2,cv2.LINE_AA)
                        im = cv2.putText(im, " um",org,0,0.4,(255,255,255),1,cv2.LINE_AA)
                        self._lock = True
                        org = (self._len_a-a-20, self._len_b-30)
                        l = self._type_name(im, org, "Section View", mode="r")
                        self._lock = False
                        try:
                            l = float(l)
                            im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
                            self._new_process()
                            self._bar_lens += [l]
                            self._history += [self._change_bar_length]
                            self._change_bar_length()
                            im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
                        except:
                            l = self._bar_len
                        a = cv2.getTextSize("{0} um".format(l),0,0.4,1)[0][0]
                        org = (self._len_a-a-20, self._len_b-28)
                        im = cv2.putText(im,"{0}".format(l),org,0,0.4,(0,0,0),2,cv2.LINE_AA)
                        im = cv2.putText(im,"{0}".format(l),org,0,0.4,(255,255,255),1,cv2.LINE_AA)
                        cv2.imshow("Section View", im)
                    
                    elif flags == cv2.EVENT_FLAG_CTRLKEY:
                        dc, dz, dy, dx = self._shape
                        p = op + ny*v[1]/self._exp_rate + nx*v[0]/self._exp_rate
                        p[0] /= self._ratio
                        p += np.array([dz//2, dy//2, dx//2])
                        
                        self._p_on = True
                        
                        self._new_process()
                        self._points += [[tuple(p), (255,255,100), "p{0}".format(len(self._points) - 1)]]
                        self._point_sets += [[p.copy() for p in self._points]]
                        self._history += [self._new_points]
                        self._new_points()
                        
                    elif np.linalg.norm(v*np.array([1, self._len_a/self._len_b])) > self._len_a/6:
                        v *= np.array([1, self._len_a/self._len_b])
                        key = int(np.angle(v[0] + 1j*v[1])/np.pi*12)
                        key = [12,12,0,0,14,14,14,14,0,0,8,8,8,8,0,0,9,9,9,9,0,0,12,12][key]
                        pos, change = self._set_pos(key)
                else:
                    op, ny, nx = self._pos
                    pos = self._pos.copy()
                    if (self._shift != 0).any():
                        pos[0] -= (self._shift[0]*nx + self._shift[1]*ny)/self._exp_rate
                        change = True
                    elif self._angle != 0:
                        pos[1] =  np.sin(self._angle)*nx + np.cos(self._angle)*ny
                        pos[2] =  np.cos(self._angle)*nx - np.sin(self._angle)*ny
                        change = True
                    elif self._expand != 1:
                        self._new_process()
                        self._exp_rates += [self._exp_rate*self._expand]
                        self._bar_lens += [round(80*self._xy_rs/self._exp_rate/self._expand,\
                                                -int(np.log10(80*self._xy_rs/self._exp_rate)))]
                        self._history += [self._change_exp_rate]
                        self._change_exp_rate()
                        self._expand = 1
                    elif (self._trim != np.array(self._win_size)).all():
                        self._new_process()
                        self._win_sizes += [self._trim]
                        self._history += [self._change_win_size]
                        self._change_win_size()
                        self._trim = np.array(self._win_size)
                
                if change:
                    self._new_process()
                    self._poses += [pos]
                    self._history += [self._move_pos]
                    self._move_pos()
                    self._shift = np.array([0,0])
                    self._angle = 0
                    
            elif event == cv2.EVENT_MOUSEMOVE:
                if flags % 8 == 0:
                    dc, dz, dy, dx = self._shape
                    p = op + ny*v[1]/self._exp_rate + nx*v[0]/self._exp_rate
                    p[0] /= self._ratio
                    p += np.array([dz//2, dy//2, dx//2])
                    self._point = p
                    sys.stdout.write("\rz:{0:>7.2f} px, y:{1:>7.2f} px, x:{2:>7.2f} px".format(p[0], p[1], p[2]))
                    
                    im = self._im.copy()
                    if self._p_on:
                        im = self._put_points(im)
                    if self._a_on:
                        im[self._len_b//2] = 255 - im[self._len_b//2]
                        im[:,self._len_a//2] = 255 - im[:,self._len_a//2]
                        if x < 21 and y < 21:
                            c_button = self._c_button.copy()
                            c_button = cv2.resize(c_button[2:-2,2:-2], c_button.shape[:2])
                            im[1:22,1:22] = c_button
                        else:
                            im[3:20,3:20] = self._c_button[2:-2,2:-2]
                        if 22 < x < 42 and y < 21:
                            s_button = self._s_button.copy()
                            s_button = cv2.resize(s_button[2:-2,2:-2], s_button.shape[:2])
                            im[1:22,22:43] = s_button
                        else:
                            im[3:20,24:41] = self._s_button[2:-2,2:-2]
                    if self._b_on:
                        im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
                        if -20-self._lpx <= x-self._len_a < -20 and -25 <= y-self._len_b < -20:
                            a = cv2.getTextSize("{0} um".format(self._bar_len),0,0.4,1)[0][0]
                            im = cv2.putText(im, "{0} um".format(self._bar_len), \
                                             (self._len_a-20-a, self._len_b-28),0,0.4,(0,0,0),2,cv2.LINE_AA)
                            im = cv2.putText(im, "{0} um".format(self._bar_len), \
                                             (self._len_a-20-a, self._len_b-28),0,0.4,(255,255,255),1,cv2.LINE_AA)
                        
                    cv2.imshow("Section View", im)
                elif flags % 2 == 1: # drag
                    flags = self._pre_event[1]
                    self._trim = np.array(self._win_size)
                    if flags < 32:
                        if flags == cv2.EVENT_FLAG_LBUTTON:
                            self._shift = v - self._ldown
                        elif flags == cv2.EVENT_FLAG_LBUTTON + cv2.EVENT_FLAG_CTRLKEY:
                            self._expand = np.linalg.norm(v)/np.linalg.norm(self._ldown)
                        else:
                            self._angle = np.angle((v[0] + 1j*v[1])/(self._ldown[0] + 1j*self._ldown[1]))
                            if flags == cv2.EVENT_FLAG_LBUTTON + cv2.EVENT_FLAG_CTRLKEY + cv2.EVENT_FLAG_SHIFTKEY:
                                self._angle = round(self._angle/np.pi*4)*np.pi/4
            
                        im = self._im_p.copy()
            
                        M = np.float32([[0,0,self._shift[0]],[0,0,self._shift[1]]])
                        M += cv2.getRotationMatrix2D((self._len_a//2, self._len_b//2), -self._angle/np.pi*180, self._expand)
                        im = cv2.warpAffine(im, M, (self._len_a, self._len_b))
                    
                    elif flags == cv2.EVENT_FLAG_LBUTTON + cv2.EVENT_FLAG_ALTKEY:
                        self._trim *= np.array([x,y])
                        self._trim = self._trim/(self._ldown + np.array([self._len_a//2, self._len_b//2]))
                        self._trim = self._trim.astype(np.int)
                        
                        im = np.zeros([self._trim[1], self._trim[0], 3], np.uint8)
                        a, b = max(len(im[0])//2-self._len_a//2, 0), max(len(im)//2-self._len_b//2, 0)
                        c, d = max(self._len_a//2-len(im[0])//2, 0), max(self._len_b//2-len(im)//2, 0)
                        im[b:b+self._len_b, a:a+self._len_a] = self._im_p[d:d+len(im), c:c+len(im[0])]
        
                    if self._a_on:
                        im[len(im)//2] = 255 - im[len(im)//2]
                        im[:,len(im[0])//2] = 255 - im[:,len(im[0])//2]
                        im[3:20,3:20] = self._c_button[2:-2,2:-2]
                        im[3:20,24:41] = self._s_button[2:-2,2:-2]
                    if self._b_on:
                        im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
        
                    cv2.imshow("Section View", im)
                    
                    self._count += 1
                    if self._count == 3:
                        self._count = 0
        
                        pos = self._pos.copy()
                        pos[1] =  np.sin(self._angle)*nx + np.cos(self._angle)*ny
                        pos[2] =  np.cos(self._angle)*nx - np.sin(self._angle)*ny
                        pos[0] -= (self._shift[0]*nx + self._shift[1]*ny)/self._exp_rate
                        
                        exp_rate = self._exp_rate*self._expand
        
                        navi = self._navigator(pos, exp_rate, win_size=self._trim)
                        self._navi = np.average(np.append(navi[None], self._init_navi[None], axis=0), axis=0, weights=[6,1]).astype(np.uint8)
                        cv2.imshow("Navigator", self._navi)
                
        self._pre_event = (event, flags)
        
        
    def _mouse_operation_2(self, event, x, y, flags, param):
        if not self._lock:
            points = self._navi_points.copy()
            
            if len(points) != 0:
            
                dists = np.linalg.norm(points[:,:2] - np.array([x,y]), axis=1)
                nearest = np.argmin(dists)
    
                if dists[nearest] <= 5:
                    navi = self._navi.copy()
                    color = self._colors.copy()[nearest]
                    if points[nearest, 2] <= 0:
                        color = color//1.5
                    else:
                        color = cv2.cvtColor(color[None,None], cv2.COLOR_BGR2HSV)[0,0]
                        color[1] = color[1]//2
                        color[2] = 220
                        color = cv2.cvtColor(color[None,None], cv2.COLOR_HSV2BGR)[0,0]
                    color = (int(color[0]), int(color[1]), int(color[2]))
                    navi = cv2.circle(navi, tuple(points[nearest,:2]), 5, color, -1)
                    
                    if event == cv2.EVENT_LBUTTONDOWN:
                        self._active_point = nearest
                        self._point_settings()
                    else:
                        cv2.imshow("Navigator", navi)
                    
                else:
                    navi = self._navi.copy()
                    cv2.imshow("Navigator", navi)
                
                
    def _mouse_operation_3(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP and self._pre_event[0] == cv2.EVENT_LBUTTONDOWN:
            num = self._active_point
            point = self._points[num + 1].copy()
            a, b = cv2.getTextSize(point[2], 2, 0.5, 1)
            a = (a[0] + 207, 51 - a[1])
            b += 53
            if x < 21 and y < 21 and flags == 0:
                self._points = self._points[:num + 1] + self._points[num + 2:]
                self._close_palette = True
            elif 203 <= x <= a[0] and a[1] <= y <= b:
                name = self._type_name(self._palette, (205,53), "Palette")
                if name != "":
                    self._points[num + 1][2] = name
                x, y = 400, 100
        self._mouse = (x, y)
        self._pre_event = (event, flags)
        
        
    def _type_name(self, im, org, win_name, mode="l"):

        name = ""
        line_on = True
        kersol = 0
    
        while(1):
            im_ = im.copy()
            a, b = cv2.getTextSize(name, 2, 0.5, 1)
            if mode == "l":
                st = org[0] - 1
            elif mode == "r":
                st = org[0] - a[0] - 3
            a = (a[0]+4, org[1]-a[1]-2)
            b += org[1]
            
            im_[a[1]:b, st:st+a[0]] = 0
            
            org_ = (st + 1, org[1])
            im_ = cv2.putText(im_, name, org_, 2, 0.5, (255,255,255), 1, cv2.LINE_AA)
            
            c = cv2.getTextSize(name[:kersol], 2, 0.5, 1)[0][0]
            c += st
            if line_on:
                im_[a[1]+2:org[1]+2, c:c+2] = 255
            line_on = not line_on
                
            cv2.imshow(win_name, im_)
            key = cv2.waitKeyEx(500)
            if key in [13,27]:
                break
            elif key == 8:
                name = name[:kersol-1] + name[kersol:]
                kersol = max(kersol-1, 0)
                line_on = True
            elif key == 0:
                continue
            elif key == 2424832:
                kersol = max(kersol-1, 0)
                line_on = True
            elif key == 2555904:
                kersol = min(kersol+1, len(name))
                line_on = True
            elif key == key%256:
                name = name[:kersol] + chr(key) + name[kersol:]
                kersol += 1
                line_on = True
            
        return name

    
    def _nothing(self, x):
        pass
    
    def _point_settings(self):
        num = self._active_point
        
        color = list(self._points[num + 1][1])
        pre_points = self._points[num + 1].copy()
        cv2.namedWindow("Palette")
        cv2.setMouseCallback("Palette", self._mouse_operation_3)
        
        im = np.zeros([101, 401, 3], np.uint8)
        z, y, x = self._points[num + 1][0]
        z, y, x = int(z), int(y), int(x)
        swin = self._box[:, z, max(y-50,0):y+51, max(x-200,0):x+201].copy()
        a0, c = np.arange(self._shape[0])[:,None,None], self._c[:,:3]
        swin = np.sum(self._lut[a0, swin][:,:,:,None] * c[:,None,None], axis=0)
        swin[swin>255] = 255
        swin = swin.astype(np.uint8)
        dc, dz, dy, dx = self._shape
        im[max(50-y,0):101-max(y+51-dy, 0), max(200-x,0):401-max(x+201-dx, 0)] = swin
        x_button = self._x_button.copy()
        im[3:20,3:20] = x_button[2:-2, 2:-2]
        self._palette = im
        
        cv2.namedWindow("Palette")
        cv2.imshow("Palette", im)
        
        cv2.createTrackbar("R", "Palette", color[2], 255, self._nothing)
        cv2.createTrackbar("G", "Palette", color[1], 255, self._nothing)
        cv2.createTrackbar("B", "Palette", color[0], 255, self._nothing)

        self._close_palette = False
        self._mouse = (100, 100)
        while(1):
            im_ = im.copy()
            im_[47:54, 197:204] = 0
            im_[48:53, 198:203] = color
            cv2.putText(im_, self._points[num+1][2], (205,53), 2, 0.5, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(im_, self._points[num+1][2], (205,53), 2, 0.5, tuple(color), 1, cv2.LINE_AA)
            a, b = cv2.getTextSize(self._points[num+1][2], 2, 0.5, 1)
            a = (a[0] + 207, 51 - a[1])
            b += 53
            if self._mouse[0] < 21 and self._mouse[1] < 21:
                x_button = self._x_button.copy()
                x_button = cv2.resize(x_button[2:-2,2:-2], x_button.shape[:2])
                im_[1:22,1:22] = x_button
            if 203 <= self._mouse[0] <= a[0] and a[1] <= self._mouse[1] <= b:
                im_[a[1]:b+2, 203:a[0]+1] = 255 - im_[a[1]:b+2, 203:a[0]+1]
                im_[a[1]+2:b, 205:a[0]-1] = 255 - im_[a[1]+2:b, 205:a[0]-1]
            cv2.imshow("Palette", im_)
            
            key = cv2.waitKey(1)
            if key in [13, 27] or cv2.getWindowProperty("Palette", 0) < 0 or self._close_palette:
                break
            
            r = cv2.getTrackbarPos('R','Palette')
            g = cv2.getTrackbarPos('G','Palette')
            b = cv2.getTrackbarPos('B','Palette')
            
            color = [b, g, r]
            self._points[num + 1][1] = tuple(color)
            
            if self._points[num + 1] != pre_points:
    
                coors, colors, names = np.array(self._points)[:,0], np.array(self._points)[:,1], np.array(self._points)[:,2]
                self._coors = np.array([list(c) for c in coors]).astype(np.float)[1:]
                self._colors = np.array([list(c) for c in colors]).astype(np.uint8)[1:]
                self._names = np.array(names)[1:]
    
                self._navi = self._navigator()
                self._show_nav()
                self._show_sec()
            pre_points = self._points[num + 1].copy()
        
        cv2.destroyWindow("Palette")
        
        self._show_sec()
        
        if self._points != self._point_sets[-1]:
            coors, colors, names = np.array(self._points)[:,0], np.array(self._points)[:,1], np.array(self._points)[:,2]
            self._coors = np.array([list(c) for c in coors]).astype(np.float)[1:]
            self._colors = np.array([list(c) for c in colors]).astype(np.uint8)[1:]
            self._names = np.array(names)[1:]
            
            self._new_process()
            self._point_sets += [[p.copy() for p in self._points]]
            self._history += [self._new_points]
            self._new_points()
    
    
    def _channel_color_settings(self):
        colors = self._c.copy()
        maxv = self._max_values.copy()
        
        b, g, r, vmin, vmax = colors[0]
        im_ = np.zeros([100, 400, 3], np.uint8)
        block = np.linspace(0,400,len(colors)+1).astype(np.int)
        for i in range(len(colors)):
            im_[:,block[i]:block[i+1]] = colors[i,:3]
        grade = np.linspace(0,1,100)[::-1]
        im_ = (im_*grade[:,None,None]).astype(np.uint8)
        
        cv2.namedWindow("Palette")
        cv2.imshow("Palette", im_)
        
        ch = 0
        pre_ch = 0
        pre_vmin = vmin
        
        cv2.createTrackbar("channel", "Palette", ch, len(colors) - 1, self._nothing)
        cv2.createTrackbar("R", "Palette", r, 255, self._nothing)
        cv2.createTrackbar("G", "Palette", g, 255, self._nothing)
        cv2.createTrackbar("B", "Palette", b, 255, self._nothing)
        cv2.createTrackbar("min", "Palette", vmin, maxv[ch], self._nothing)
        cv2.createTrackbar("max", "Palette", vmax, maxv[ch], self._nothing)
        
        while(1):
            for i in range(len(colors)):
                im_[:,block[i]:block[i+1]] = colors[i,:3]
            im_ = (im_*grade[:,None,None]).astype(np.uint8)
            
            cv2.imshow("Palette", im_)
            
            key = cv2.waitKey(1)
            if key in [13, 27] or cv2.getWindowProperty("Palette", 0) < 0: # Enter
                break
                
            ch = cv2.getTrackbarPos("channel", "Palette")
            if ch != pre_ch:
                b, g, r, vmin, vmax = colors[ch]
                cv2.setTrackbarPos("R", "Palette", r)
                cv2.setTrackbarPos("G", "Palette", g)
                cv2.setTrackbarPos("B", "Palette", b)   
                cv2.createTrackbar("min", "Palette", vmin, maxv[ch], self._nothing)
                cv2.createTrackbar("max", "Palette", vmax, maxv[ch], self._nothing)
            else:
                r = cv2.getTrackbarPos('R','Palette')
                g = cv2.getTrackbarPos('G','Palette')
                b = cv2.getTrackbarPos('B','Palette')
                vmin = cv2.getTrackbarPos('min', 'Palette')
                vmax = cv2.getTrackbarPos('max', 'Palette')
            
            if vmin >= vmax:
                if vmin != pre_vmin:
                    vmin = vmax - 1
                    cv2.setTrackbarPos("min", "Palette", vmin)
                else:
                    vmax = vmin + 1
                    cv2.setTrackbarPos("max", "Palette", vmax)
            
            colors[ch] = [b, g, r, vmin, vmax]
            self._c = colors.copy()
            self._lut = LUT(max(self._max_values), self._c[:,3], self._c[:,4])
            self._show_sec()
            
            pre_ch = ch
            pre_vmin = vmin
            
        cv2.destroyWindow("Palette")
        
        if (self._c != self._cs[-1]).any():
            self._new_process()
            self._cs += [self._c]
            self._history += [self._record_colors]
            self._record_colors()
    
    
    def _stack(self, start, stop):
        nz = -np.cross(self._pos[1], self._pos[2])
        stacked = np.zeros(self._frame.shape, dtype=self._frame.dtype)
        im = np.zeros([50, 500, 3], np.uint8)
        complete = True
        cv2.imshow("Stack", im)
        cv2.waitKey(1)
        for i in range(start, stop+1):
            pos = self._pos.copy()
            pos[0] += nz*i
            frame = self._sectioner(pos)
            if type(frame) != type(None):
                a = frame > stacked
                stacked[a] = frame[a]
            im[:,:int((i-start+1)/(stop-start+1)*500)] = [200,100,50]
            cv2.imshow("Stack", im)
            key = cv2.waitKey(1)
            if key == 27 \
            or cv2.getWindowProperty("Stack", 0) < 0 \
            or cv2.getWindowProperty("Section View", 0) < 0 \
            or cv2.getWindowProperty("Navigator", 0) < 0:
                complete = False
                break
        return stacked, complete
    
    def _stack_settings(self):
        im = np.zeros([50, 500, 3], np.uint8)
        cv2.namedWindow("Stack")
        cv2.imshow("Stack", im)
        
        nz = -np.cross(self._pos[1], self._pos[2])
        a0, c = np.arange(self._shape[0])[:,None,None], self._c[:,:3]
        
        op = self._pos[0].copy()
        dc, dz, dy, dx = self._shape
        op += np.array([(dz*self._ratio)//2, dy//2, dx//2])
        a = np.zeros([6]) + np.inf
        a[:3][nz!=0] = -op[nz!=0]/nz[nz!=0]
        a[3:][nz!=0] = (np.array([dz*self._ratio, dy, dx]) - op)[nz!=0]/nz[nz!=0]
        start0 = int(np.amax(a[a<=0]))
        stop = int(np.amin(a[a>0]))
        pre_stop = 0
        pre_start = 0
        im_start = True
        
        cv2.createTrackbar("start", "Stack", -start0, stop-start0, self._nothing)
        cv2.createTrackbar("stop", "Stack", -start0, stop-start0, self._nothing)
        
        while(1):
            start = cv2.getTrackbarPos("start", "Stack") + start0
            stop = cv2.getTrackbarPos("stop", "Stack") + start0
            if start > stop:
                if pre_stop == stop:
                    start = stop
                else:
                    stop = start
                cv2.setTrackbarPos("start", "Stack", start-start0)
                cv2.setTrackbarPos("stop", "Stack", stop-start0)
            if pre_start != start:
                im_start = True
            if pre_stop != stop:
                im_start = False
            pos = self._pos.copy()
            if im_start:
                pos[0] += nz*start
            else:
                pos[0] += nz*stop
            pre_start = start
            pre_stop = stop
            frame = self._sectioner(pos)
            if type(frame) != type(None):
                self._frame = frame
                self._show_sec()
                
            key = cv2.waitKey(1)
            if key in [13, 27] or cv2.getWindowProperty("Stack", 0) < 0: # Enter
                break
        cv2.destroyWindow("Stack")
        
        self._show_sec()
        
        if key == 13:
            stacked, comp = self._stack(start, stop)
            if comp:
                im = np.sum(self._lut[a0, stacked][:,:,:,None] * c[:,None,None], axis=0)
                im[im>255] = 255
                im = im.astype(np.uint8)
                if self._b_on:
                    im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
                cv2.imshow("Stack", im)
            else:
                cv2.destroyWindow("Stack")
        
        
    def _record_colors(self, undo=0):
        self._c_num += undo
        self._c_num = min(max(self._c_num, -len(self._cs)), -1)
        
        self._c = self._cs[self._c_num]
        self._lut = LUT(max(self._max_values), self._c[:,3], self._c[:,4])
        
        self._show_sec()
        
    
    def _new_process(self):
        self._cs = self._cs[self._c_num::-1][::-1]
        self._c_num = -1
        self._inits = self._inits[self._i_num::-1][::-1]
        self._i_num = -1
        self._poses = self._poses[self._p_num::-1][::-1]
        self._p_num = -1
        self._exp_rates = self._exp_rates[self._e_num::-1][::-1]
        self._e_num = -1
        self._bar_lens = self._bar_lens[self._l_num::-1][::-1]
        self._l_num = -1
        self._point_sets = self._point_sets[self._pt_num::-1][::-1]
        self._pt_num = -1
        self._history = self._history[self._h_num::-1][::-1]
        self._h_num = -1
        
        
    def _put_points(self, im):
        dc, dz, dy, dx = self._shape
        points = self._coors.copy()
        colors = self._colors
        names = self._names
        
        points -= np.array([dz//2,dy//2,dx//2])
        points[:,0] *= self._ratio
        op, ny, nx = self._pos
        nz = -np.cross(ny, nx)
        n = np.array([nz, ny, nx])
        points -= op
        points = np.linalg.solve(n.T, points.T).T
        points = points[np.abs(points[:,0]) < 50]
        points[:,1:] *= self._exp_rate
        points[:,1:] += np.array([self._len_b//2,self._len_a//2])
        points = points[np.prod(points[:,1:] >= 0, axis=1, dtype=np.bool)]
        points = points[points[:,1] < self._len_b]
        points = points[points[:,2] < self._len_a]
        points[:,0] = (np.cos(points[:,0]/50*np.pi) + 1)/2

        for point, color, name in zip(points, colors, names):
            a, b = point[1:].astype(np.int)
            square = im[a-3:a+4, b-3:b+4][None]
            im[a-3:a+4, b-3:b+4] = np.average(np.append(square, np.zeros([1,7,7,3], np.uint8), axis=0),\
                                              axis=0, weights=[1-point[0],point[0]])
            im[a-2:a+3, b-2:b+3] = np.average(np.append(square[:,1:-1,1:-1], np.zeros([1,5,5,3], np.uint8)+color, axis=0),\
                                              axis=0, weights=[1-point[0],point[0]])
            color = (int(color[0]), int(color[1]), int(color[2]))
            if point[0] > 0.5:
                im = cv2.putText(im, name, (b+5,a+3), 2, 0.5, (0,0,0), 2, cv2.LINE_AA)
                im = cv2.putText(im, name, (b+5,a+3), 2, 0.5, color, 1, cv2.LINE_AA)
            
        return im
        
    def _show_sec(self):
        a0, c = np.arange(self._shape[0])[:,None,None], self._c[:,:3]
        im = np.sum(self._lut[a0, self._frame][:,:,:,None] * c[:,None,None], axis=0)
        im[im>255] = 255
        im = im.astype(np.uint8)
        self._im = im.copy()
        
        if self._p_on:
            im = self._put_points(im)
            self._im_p = im.copy()
        else:
            self._im_p = self._im.copy()
        if self._a_on:
            im[self._len_b//2] = 255 - im[self._len_b//2]
            im[:,self._len_a//2] = 255 - im[:,self._len_a//2]
            im[3:20,3:20] = self._c_button[2:-2,2:-2]
            im[3:20,24:41] = self._s_button[2:-2,2:-2]
        if self._b_on:
            im[-25:-20, -20-self._lpx:-20] = 255 - im[-25:-20, -20-self._lpx:-20]
        cv2.imshow("Section View", im)
        
    def _show_nav(self):
        cv2.imshow("Navigator", self._navi)
        
    
    def _record_init(self, undo=0, view=True):
        self._i_num += undo
        self._i_num = min(max(self._i_num, -len(self._inits)), -1)
        
        self._init_pos = self._inits[self._i_num].copy()
        self._init_navi = self._navigator(self._init_pos, init=True)
        self._navi = self._navigator()
        
        if view:
            self._show_nav()
        
        
    def _new_points(self, undo=0, view=True):
        self._pt_num += undo
        self._pt_num = min(max(self._pt_num, -len(self._point_sets)), -1)
        self._points = [p.copy() for p in self._point_sets[self._pt_num]]
        
        coors, colors, names = np.array(self._points)[:,0], np.array(self._points)[:,1], np.array(self._points)[:,2]
        self._coors = np.array([list(c) for c in coors]).astype(np.float)[1:]
        self._colors = np.array([list(c) for c in colors]).astype(np.uint8)[1:]
        self._names = np.array(names)[1:]
        
        self._navi = self._navigator()
        
        if view:
            self._show_nav()
            self._show_sec()
    
        
    def _move_pos(self, undo=0, view=True):
        self._p_num += undo
        self._p_num = min(max(self._p_num, -len(self._poses)), -1)
        
        self._pos = self._poses[self._p_num].copy()
        
        frame = self._sectioner(self._pos)
        if type(frame) != type(None):
            self._frame = frame
            self._navi = self._navigator()
        else:
            self._move_pos(undo=-1)
            self._new_process()
        
        if view:
            self._show_nav()
            self._show_sec()
            
    def _change_exp_rate(self, undo=0, view=True):
        self._e_num += undo
        self._e_num = min(max(self._e_num, -len(self._exp_rates)), -1)
        self._l_num += undo
        self._l_num = min(max(self._l_num, -len(self._bar_lens)), -1)
        
        self._exp_rate = self._exp_rates[self._e_num]
        self._bar_len = self._bar_lens[self._l_num]
        if type(self._bar_len) != type(None):
            self._lpx = int(self._bar_len/self._xy_rs*self._exp_rate)
        
        win_size = np.array(self._win_size)
        max_size = np.amax(np.array(win_size))
        width = max_size/self._exp_rate/2
        if max_size%2 == 0:
            alpha = np.linspace(-width, width, max_size + 1)[None,:-1,None]
            beta = np.linspace(-width, width, max_size + 1)[:-1,None,None]
        else:
            alpha = np.linspace(-width, width, max_size)[None,:,None]
            beta = np.linspace(-width, width, max_size)[:,None,None]
        self._alpha = alpha[:, max_size//2 - win_size[0]//2: max_size//2 - win_size[0]//2 + win_size[0]]
        self._beta = beta[max_size//2 - win_size[1]//2: max_size//2 - win_size[1]//2 + win_size[1]]
        
        frame = self._sectioner(self._pos)
        if type(frame) != type(None):
            self._frame = frame
            self._navi = self._navigator()
        else:
            self._change_exp_rate(undo=-1)
            self._new_process()

        if view:
            self._show_nav()
            self._show_sec()
            
    def _change_win_size(self, undo=0, view=True):
        self._w_num += undo
        self._w_num = min(max(self._w_num, -len(self._win_sizes)), -1)
        
        self._win_size = tuple(self._win_sizes[self._w_num])
        
        win_size = np.array(self._win_size)
        max_size = np.amax(np.array(win_size))
        width = max_size/self._exp_rate/2
        if max_size%2 == 0:
            alpha = np.linspace(-width, width, max_size + 1)[None,:-1,None]
            beta = np.linspace(-width, width, max_size + 1)[:-1,None,None]
        else:
            alpha = np.linspace(-width, width, max_size)[None,:,None]
            beta = np.linspace(-width, width, max_size)[:,None,None]
        self._alpha = alpha[:, max_size//2 - win_size[0]//2: max_size//2 - win_size[0]//2 + win_size[0]]
        self._beta = beta[max_size//2 - win_size[1]//2: max_size//2 - win_size[1]//2 + win_size[1]]
        
        self._len_a = len(self._alpha[0])
        self._len_b = len(self._beta)
        
        frame = self._sectioner(self._pos)
        if type(frame) != type(None):
            self._frame = frame
            self._navi = self._navigator()
        else:
            self._change_win_size(undo=-1)
            self._new_process()
        
        if view:
            self._show_nav()
            self._show_sec()
            
    def _change_bar_length(self, undo=0, view=True):
        self._l_num += undo
        self._l_num = min(max(self._l_num, -len(self._bar_lens)), -1)
        
        self._bar_len = self._bar_lens[self._l_num]
        self._lpx = int(self._bar_len/self._xy_rs*self._exp_rate)
        
        if view:
            self._show_sec()
            
    def _save_settings(self):
        i = 0
        for f in self._file_name:
            f = f.rsplit(".",1)[0]
            f += ".svst"
            
            text = "# [b,g,r]\nchannels = {\n"
            c = self._c
            text += \
                "'colors': {0},\n 'vmins': {1},\n 'vmaxs': {2},\n  'maxs': {3}"\
                .format(c[i:i+self._ch_lens[i],:3].tolist(),
                        c[i:i+self._ch_lens[i], 3].tolist(),
                        c[i:i+self._ch_lens[i], 4].tolist(),
                        self._max_values[i:i+self._ch_lens[i]].tolist())
            i += self._ch_lens[i]
            text += "}\n\n"
            text += "# [z,y,x] [b,g,r]\npoints = {\n"
            text += "      'names': {0},\n'coordinates': {1},\n     'colors': {2}\n"\
                .format(self._names.tolist(),
                        self._coors.tolist(),
                        self._colors.tolist())
            text += "}\n\n"
            text += "settings = {\n"
            text += "'xy': {0},'z': {1},   # um/px\n".format(self._xy_rs, self._z_rs)
            text += "'window size': {0},   # px\n".format(self._win_size)
            text += "'expansion': {0},\n".format(self._exp_rate)
            text += "'bar length': {0}   # um\n".format(self._bar_len)
            text += "}\n\n"
            
            pos_text = str(self._pos)
            pos_text = tuple(pos_text.translate(pos_text.maketrans({"[":"", "]":"", "\n":""})).split())
            m = 0
            for p in pos_text:
                if len(p) > m:
                    m = len(p)
            pos_text = (*pos_text, m)
            pos_text = "[[{0:>{9}}, {1:>{9}}, {2:>{9}}],\n [{3:>{9}}, {4:>{9}}, {5:>{9}}],\n [{6:>{9}}, {7:>{9}}, {8:>{9}}]]".format(*pos_text)
            text += "# current position\npos = \\\n{0}\n\n".format(pos_text)
            pos_text = str(self._init_pos)
            pos_text = tuple(pos_text.translate(pos_text.maketrans({"[":"", "]":"", "\n":""})).split())
            m = 0
            for p in pos_text:
                if len(p) > m:
                    m = len(p)
            pos_text = (*pos_text, m)
            pos_text = "[[{0:>{9}}, {1:>{9}}, {2:>{9}}],\n [{3:>{9}}, {4:>{9}}, {5:>{9}}],\n [{6:>{9}}, {7:>{9}}, {8:>{9}}]]".format(*pos_text)
            text += "# initial position\ninit_pos = \\\n{0}".format(pos_text)
            
            with open(f, "w") as g:
                g.write(text)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        root = tkinter.Tk()
        root.withdraw()
        fTyp = [("OIB files", "*.oib"), ("TIFF files", ["*.tif", "*.tiff"]), ("All files", "*")]
        if os.path.isfile(".SectionViewer.txt"):
            with open(".SectionViewer.txt", "r") as f:
                iDir = f.read()
            if not os.path.isdir(iDir):
                iDir = os.path.dirname(sys.argv[0])
        else:
            iDir = os.path.dirname(sys.argv[0])
        file_name = tkinter.filedialog.askopenfilenames(filetypes=fTyp, initialdir=iDir)
    else:
        file_name = sys.argv[1:]
    if len(file_name) > 0:
        sv = SectionViewer(file_name)
        sv.viewer()
        
        with open(".SectionViewer.txt", "w") as f:
            f.write(os.path.dirname(file_name[0]))
