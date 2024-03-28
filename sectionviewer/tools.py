import gzip
import os
import pickle
import platform
import subprocess
from typing import Union
import numpy as np
try:
    from aicsimageio.readers.bioformats_reader import BioformatsReader
except ModuleNotFoundError:
    pass
import cv2
from PIL import Image, ImageTk
import oiffile as oif
import tifffile as tif
from tkinter import filedialog

from .components import FileDict, DataArray, GeometryDict, PositionArray
from .components import ChannelList, PointList, DisplayDict
from . import utils as ut

base_dir = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/') + '/'

def init_dir():
    if os.path.isfile(base_dir + 'init_dir.txt'):
        with open(base_dir + 'init_dir.txt', 'r') as f:
            initialdir = f.read()
        if not os.path.isdir(initialdir):
            initialdir = os.path.expanduser('~/Desktop')
    else:
        initialdir = os.path.expanduser('~/Desktop')
        with open(base_dir + 'init_dir.txt', 'w') as f:
            f.write(initialdir)
    return initialdir
def save_init(path):
    if path is not None:
        with open(base_dir + 'init_dir.txt', 'w') as f:
            f.write(os.path.dirname(path))
            
def ask_file_path(master):
    master.deiconify()
    filetypes = [('Supported files', ['*.secv', '*.stac', '*.oir', 
                                      '*.oib', '*.tif', '*.tiff']),
                 ('All files', '*')]
    initialdir = init_dir()
    file_path = filedialog.askopenfilename(parent = master, 
                                           filetypes = filetypes, 
                                           initialdir = initialdir, 
                                           title = 'Open')
    return file_path

def launch(file_path = None):
    launch_code = 'from {0}.main import main\nmain()'
    launch_code = launch_code.format(os.path.basename(os.path.dirname(base_dir)))
    with open(base_dir + 'launch.py', 'w') as f:
        f.write(launch_code)
    if file_path == None:
        file_path = ''
    command = 'python ' + base_dir + 'launch.py ' + file_path
    subprocess.Popen(command, shell = True)
    return

resources = cv2.imread(base_dir + 'img/resources.png')
pf = platform.system()

geometry_key_patterns = [
    ['res_xy', 'X_px_size'],
    ['res_xy', 'Y_px_size'],
    ['res_z', 'Z_px_size'],
    ['exp_rate', 'expansion_rate'],
    ['im_size', 'image_size'],
    ['bar_len', 'scale_bar_length']
    ]

def desolve_secv(secv_path: Union[str, None]) -> dict:
    
    file_keys = ['original_secv_path', 'secv_path', 'paths']
    if secv_path is None:
        metadata = {'files': {},
                    'geometry': {},
                    'display': {}, 
                    'position': None, 
                    'channels': None,
                    'points': [],
                    'snapshots': []}
        metadata['files'] = dict([(fk, None) for fk in file_keys])
    else:
        with open(secv_path, 'rb') as f:
            metadata = pickle.load(f)
        if 'files' not in metadata:
            metadata['files'] = metadata['data']
            del metadata['data']
        mf = metadata['files']
        if type(mf) != dict:
            metadata['files'] = dict([(fk, None) for fk in file_keys])
            metadata['files']['paths'] = [d[0] for d in mf]
        else:
            for k in list(mf.keys()):
                if k not in file_keys:
                    del mf[k]
        metadata['files']['secv_path'] = secv_path
    mg = metadata['geometry']
    for gkps in geometry_key_patterns:
        if gkps[-1] in mg:
            continue
        mg[gkps[-1]] = None
        for gkp in gkps[:-1]:
            if gkp not in mg:
                continue
            mg[gkps[-1]] = mg[gkp]
    for k in list(mg.keys()):
        if k not in [gkps[-1] for gkps in geometry_key_patterns]:
            del mg[k]
        
    return metadata


def load_stac(stac_path: str):
    with open(stac_path, 'rb') as f:
        byt = f.read()
    byt = gzip.decompress(byt)
    stacks, channels, geometry, display = pickle.loads(byt)
    for gkps in geometry_key_patterns:
        if gkps[-1] in geometry:
            continue
        geometry[gkps[-1]] = None
        for gkp in gkps[:-1]:
            if gkp not in geometry:
                continue
            geometry[gkps[-1]] = geometry[gkp]
    for k in list(geometry.keys()):
        if k not in [gkps[-1] for gkps in geometry_key_patterns]:
            del geometry[k]
    metadata = {}
    metadata['files'] = {'stac_path': stac_path}
    metadata['geometry'] = geometry
    metadata['display'] = display
    metadata['channels'] = channels
    return stacks, metadata


def load_data(
        paths: list, 
        original_secv_path: Union[str, None] = None,
        voxels: np.ndarray = None, 
        file_paths_vx: tuple = (), 
        channel_nums_vx: tuple = ()
        ):
    
    for path in paths:
        if not os.path.exists(path):
            # TODO relative path calculation
            raise FileNotFoundError('[Errno 2] No such file or directory: {0}'.format(path))
        ext = os.path.splitext(path)[1]
        if ext not in ('.oir', '.oib', '.tif', '.tiff'):
            raise TypeError('File type {0} is not supported.'.format(ext))
    
    X_px_size_in_files = None
    Y_px_size_in_files = None
    Z_px_size_in_files = None
    
    data = []
    for i, path in enumerate(paths):
        if path in file_paths_vx:
            fid = file_paths_vx.index(path)
            num = np.sum(channel_nums_vx[:fid]) if fid != 0 else 0
            data += [voxels[num: num + channel_nums_vx[fid]]]
            continue
        ext = os.path.splitext(path)[1]
        if ext == '.oir':
            oir = BioformatsReader(path)
            img = oir.data
            try:
                axes = oir.dims.order.upper()
                if 'C' in axes:
                    axes = [axes.index('C'), axes.index('Z'), 
                            axes.index('Y'), axes.index('X')]
                else:
                    axes = [axes.index('Z'), 
                            axes.index('Y'), axes.index('X')]
                img = img.transpose(*([i for i in range(len(img.shape)) if i not in axes] + axes))
                img = img[tuple([0]*(len(img.shape) - len(axes)))]
            except Exception:
                pass
            if img.dtype != np.uint16:
                img = img.astype(np.uint16)
            if img.ndim == 3:
                img = img[None]
            assert img.ndim == 4
            data += [img]
            
            try:
                pxs = oir.physical_pixel_sizes
                X_px_size_in_files = pxs.X
                Y_px_size_in_files = pxs.Y
                Z_px_size_in_files = pxs.Z
            except Exception:
                pass
            
        elif ext == '.oib':
            img = oif.imread(path)
            
            try:
                with oif.OifFile(path) as oib:
                    axes = oib.axes.upper()
                    shape = oib.shape
                    info = oib.mainfile
                bshape = np.array(img.shape)
                oshape = np.array(shape)
                if len(bshape) == len(oshape):
                    ixs = np.zeros(len(bshape), dtype=int)
                    for n in range(len(bshape)):
                        w = np.where(bshape == oshape[n])[0]
                        ixs[oshape==oshape[n]] = w
                    trans = []
                    if 'C' in axes:
                        trans += [ixs[axes.index('C')]]
                    for a in ['Z', 'Y', 'X']:
                        trans += [ixs[axes.index(a)]]
                    img = img.transpose(*([i for i in range(len(bshape)) if i not in trans] + trans))
                    img = img[tuple([0]*(len(bshape) - len(trans)))]
                    
                shape = dict(np.append(np.array(list(axes))[:,None], np.array(shape)[:,None], axis=1))
                axes = dict(np.append(np.array(list(axes))[::-1][:,None], np.arange(len(axes))[:,None], axis=1))
    
                pxs = axes.copy()
                for ax in ['Z', 'Y', 'X']:
                    ax_info = info['Axis {0} Parameters Common'.format(axes[ax])]
                    px = abs((ax_info['EndPosition'] - ax_info['StartPosition'])/float(shape[ax]))
                    pxs[ax] = px
                    if ax_info['UnitName'] == 'nm':
                        pxs[ax] /= 1000
                X_px_size_in_files = pxs['X']
                Y_px_size_in_files = pxs['Y']
                Z_px_size_in_files = pxs['Z']
                
            except Exception:
                pass
            if img.dtype != np.uint16:
                img = img.astype(np.uint16)
            if img.ndim == 3:
                img = img[None]
            assert img.ndim == 4
            data += [img]

        else:
            img = tif.imread(path)
            if img.dtype != np.uint16:
                img = img.astype(np.uint16)
            if img.ndim == 3:
                img = img[None]
            assert img.ndim == 4
            a = np.argmin(img.shape)
            b = [0,1,2,3]
            b.remove(a)
            img = img.transpose(a, *b)
            data += [img]
            
    shape = data[0][0].shape
    for d in data[1:]:
        if d[0].shape != shape:
            raise DataShapeMismatchError('all the spatial dimensions in the'
                                         ' input data must match exactly')
    
    metadata = {}
    metadata['X_px_size_in_files'] = X_px_size_in_files
    metadata['Y_px_size_in_files'] = Y_px_size_in_files
    metadata['Z_px_size_in_files'] = Z_px_size_in_files
    metadata['channel_nums'] = [len(d) for d in data]
    metadata['shape'] = shape
    return data, metadata


def calc_section(
        voxels: DataArray, 
        geometry: GeometryDict, 
        position: PositionArray,
        display: DisplayDict,
        section: DataArray,
        center: np.ndarray = None
        ) -> bool:
    if center is None:
        center = np.array(section[0].shape)//2
    
    axes = position.copy()
    nz = position.basis[0].copy()
    axes[1:] /= geometry['expansion_rate']
    nz /= geometry['expansion_rate']
    
    shown_ch = display.getshown()
    thickness = display['thickness']
    
    if thickness == 1:
        if not ut.calc_section(voxels.base, axes, 
                               section.base, center,
                               shown_ch):
            return False
    else:
        start = -(thickness//2)
        stop = start + thickness
        stack_func = ut.stack_section if thickness <= 10 else ut.fast_stack
        if not stack_func(voxels.base, axes, nz, start, stop,
                          section.base, center,
                          shown_ch):
            return False
    return True


def calc_sideview(
        voxels: DataArray, 
        geometry: GeometryDict, 
        position: PositionArray, 
        display: DisplayDict,
        sideview1: DataArray, 
        sideview2: DataArray
        ) -> None:
    
    axes = position.copy()
    nz = position.basis[0].copy()
    axes[1:] /= geometry['expansion_rate']
    nz /= geometry['expansion_rate']
    
    op, ny, nx = axes
    nz, ny, nx = nz*2, ny*2, nx*2
    axes1 = np.array([op, nz, nx])
    axes2 = np.array([op, nz, ny])
    
    shown_ch = display.getshown()
    thickness = display['thickness']
    
    if thickness == 1:
        ut.fast_section(voxels.base, axes1, 
                        sideview1.base, np.array(sideview1[0].shape)//2,
                        shown_ch)
        ut.fast_section(voxels.base, axes2, 
                        sideview2.base, np.array(sideview2[0].shape)//2,
                        shown_ch)
    else:
        start = -(thickness//2)
        stop = start + thickness
        ut.fast_stack(voxels.base, axes1, ny, start, stop,
                      sideview1.base, np.array(sideview1[0].shape)//2,
                      shown_ch)
        ut.fast_stack(voxels.base, axes2, nx, start, stop,
                      sideview2.base, np.array(sideview2[0].shape)//2,
                      shown_ch)
        

def calc_projection(
        voxels: DataArray, 
        geometry: GeometryDict, 
        position: PositionArray,
        stack: DataArray,
        start: int, stop: int
        ) -> bool:
    axes = position.copy()
    nz = position.basis[0].copy()
    exp_rate = geometry['expansion_rate']
    axes[1:] /= exp_rate
    from_, to = position.depth_range
    start = (to - from_) * (start / 100) + from_
    stop = (to - from_) * (stop / 100) + from_
    if exp_rate < 1:
        nz /= exp_rate
        start = int(start * exp_rate)
        stop = int(stop * exp_rate)
    else:
        start = int(start)
        stop = int(stop)
    voxels = voxels.base
    ut.stack_section(voxels, axes, nz, start, stop, stack, 
                     np.array(stack[0].shape)//2,
                     np.arange(len(stack)))
    return True
        

def synthesize_image(
        section: DataArray, 
        channels: ChannelList, 
        display: DisplayDict, 
        image: DataArray
        ) -> np.ndarray:
    colors = np.array(channels.getcolors('bgr'), np.uint8)
    lut = channels.getlut()
    shown_ch = display.getshown()
    
    if display['white_back']:
        ut.calc_bgr_w(section.base, lut, colors, shown_ch, image.base)
        image = image[:,:,:3]*(image[:,:,3:]/255) + (255 - image[:,:,3:])
    else:
        ut.calc_bgr(section.base, lut, colors, shown_ch, image.base)
        image = image[:,:,:3]*(image[:,:,3:]/255)
    
    return image.astype(np.uint8)


def draw_points(image: np.ndarray, 
                 coors: np.ndarray, 
                 colors: np.ndarray,
                 names: Union[np.ndarray, None] = None, 
                 thickness: int = 1, 
                 r: int = 3
                 ) -> np.ndarray:
    
    if names is None:
        names = np.full(len(coors), '')
        
    threshold = 10 + thickness//2
    show = np.abs(coors[:,0]) < threshold
    ly, lx = image[:,:,0].shape
    show *= np.prod(coors[:,1:3]//np.array([ly, lx]) == 0, axis=1, dtype=bool)
    
    start = -(thickness//2)
    stop = start + thickness
    shallow, deep = coors[:,0] < start, coors[:,0] > stop - 1
    alphas = np.ones(len(coors), dtype=float)
    alphas[shallow] = (np.cos((coors[:,0][shallow]-start)/10*np.pi) + 1)/2
    alphas[deep] = (np.cos((coors[:,0][deep]-(stop-1))/10*np.pi) + 1)/2
    
    coors, colors, names, alphas = coors[show], colors[show], names[show], alphas[show]
    sort = np.argsort(coors[:,0])[::-1]
    coors, colors, names, alphas = coors[sort], colors[sort], names[sort], alphas[sort]
    
    l = np.arange(-2*r, 2*r + 1)
    l = (l[None]**2 + l[:,None]**2)**0.5
    s = l - r + 1
    s[s<0] = 0
    s[s>1] = 1
    l -= r + 0.2
    l[l<0] = 0
    l[l>1] = 1
    s = 1 - s
    r *= 2
    
    for coor, color, name, alpha in zip(coors, colors, names, alphas):
        cy, cx = coor[1:3].astype(int)
        square = image[max(cy - r, 0): max(cy + r + 1, 0),
                       max(cx - r, 0): max(cx + r + 1, 0)]
        cy0, cx0 = cy - max(cy - r, 0), cx - max(cx - r, 0)
        l1 = l[max(r - cy0, 0):, max(r - cx0, 0):]
        s1 = s[max(r - cy0, 0):, max(r - cx0, 0):]
        l1, s1 = l1[:len(square), :len(square[0])], s1[:len(square), :len(square[0])]
        
        square1 = color[None,None]*s1[:,:,None]
        square1 = square*l1[:,:,None] + square1*(1 - l1[:,:,None])
        square[:] = (square*(1 - alpha) + square1*alpha).astype(np.uint8)
        
        cy += 7
        cx += 6
        (w, h), baseline = cv2.getTextSize(name, 2, 0.5, 2)
        square = image[max(cy - h, 0): max(cy + baseline, 0),
                       max(cx, 0): max(cx + w, 0)]
        square1 = square.copy()
        cv2.putText(image, name, (cx, cy), 2, 0.5, (0,0,0), 2, cv2.LINE_AA)
        color = (int(color[0]), int(color[1]), int(color[2]))
        cv2.putText(image, name, (cx, cy), 2, 0.5, color, 1, cv2.LINE_AA)
        square[:] = (square1*(1 - alpha) + square*alpha).astype(np.uint8)
        
    return show


skeleton_settings = {
    'edge_connections': np.array([[-1, 1, 2,-1, 3,-1,-1,-1],
                                  [-1,-1,-1, 0,-1, 0,-1,-1],
                                  [-1,-1,-1, 0,-1,-1, 0,-1],
                                  [-1,-1,-1,-1,-1,-1,-1, 0],
                                  [-1,-1,-1,-1,-1, 0, 0,-1],
                                  [-1,-1,-1,-1,-1,-1,-1, 0],
                                  [-1,-1,-1,-1,-1,-1,-1, 0],
                                  [-1,-1,-1,-1,-1,-1,-1,-1]]),
    'edge_colors': [(160,130,110), ( 23, 23,170), ( 23,170, 23), (170, 23, 23)],
    'edge_thickness': [1, 1, 1, 1],
    'section_color': (255, 195, 255),
    'section_alpha': 0.5
    }
xyz_image = resources[:22,108:174]

def calc_skeleton(
        files: FileDict,
        geometry: GeometryDict,
        position: PositionArray,
        points: PointList,
        display: DisplayDict,
        image: DataArray,
        shift: int = 4,
        ) -> np.ndarray:
    
    shape = np.array(files['shape'])
    skeleton_shape = np.array(image.shape[:2])
    
    op = (position[0] - shape//2)*position._anisotropy
    n = position.basis*position._anisotropy
    sz, sy, sx = shape*position._anisotropy
    
    point_coors = np.array(points.getcoordinates())
    if len(point_coors) == 0:
        point_coors = np.empty([0, 3])
    within = np.prod(point_coors >= 0, axis=1, dtype=bool)* \
             np.prod(point_coors <= np.array([sz, sy, sx]), axis=1, dtype=bool)
    
    point_coors *= position._anisotropy
    point_coors -= op + np.array([sz, sy, sx])//2
    point_coors = np.linalg.solve(n.T, point_coors.T).T
    
    point_colors = np.array(points.getcolors(), dtype=np.uint8)
    if len(point_colors) > 0:
        point_colors[:] = point_colors//1.5
        
    sort = np.argsort(point_coors[:,0])[::-1]
    point_coors = point_coors[sort]
    point_colors = point_colors[sort]
    
    peaks = np.array([[ 0,  0,  0], [ 0,  0, sx],
                      [ 0, sy,  0], [ 0, sy, sx],
                      [sz,  0,  0], [sz,  0, sx],
                      [sz, sy,  0], [sz, sy, sx]])
    peaks -= op + np.array([sz, sy, sx])//2
    peaks = np.linalg.solve(n.T, peaks.T).T
    
    edges = skeleton_settings['edge_connections']
    neg = peaks[:, 0] <= 0
    pn = neg[None, :] * ~neg[:, None]
    separated = np.array(np.where((pn + pn.T)*(edges >= 0)))
    for i in range(len(separated[0])):
        if peaks[separated[0,i], 0] <= 0:
            separated[:,i] = separated[::-1,i]
            a, b = separated[:,i]
            edges[a, b] = edges[b, a]
            edges[b, a] = -1
    if len(separated) != 0:
        cross = np.average(peaks[separated, 1:], axis = 0,
                           weights = np.tile(np.abs(peaks[separated[::-1], :1]), (1,2)))
    else:
        cross = []
    if len(cross) > 1:
        sort = [0]
        remains = list(range(1,len(cross)))
        v0 = cross[1] - cross[0]
        v0 /= np.linalg.norm(v0)
        for _ in range(len(cross)-1):
            v1 = cross[remains] - cross[sort[-1]][None]
            v1 /= np.linalg.norm(v1, axis=1)[:,None]
            n = remains[np.argmin(np.inner(v1, v0))]
            sort += [n]
            remains.remove(n)
            v0 = cross[sort[-2]] - cross[sort[-1]]
            v0 /= np.linalg.norm(v0)
        cross = cross[sort]
        separated = separated[:,sort]
    
    exp_rate = geometry['expansion_rate']
    im_size = np.array(geometry['image_size'])
    scale = (sz**2 + sy**2 + sx**2)**0.5
    scale = max(scale, im_size[0] / exp_rate, 
                im_size[1] / exp_rate * skeleton_shape[0] / skeleton_shape[1])
    
    eye = 2.5 * scale
    peaks[:,1:] *= eye/(peaks[:,:1] + eye)
    point_coors[:,1:] *= eye/(point_coors[:,:1] + eye)
    
    center = np.average(peaks[:,1:], axis=0)
    cross -= center
    peaks[:,1:] -= center
    point_coors[:,1:] -= center
    
    cross = cross[:,::-1]
    peaks = peaks[:,2:0:-1]
    point_coors = point_coors[:,::-1]
    
    e = 0.8 * skeleton_shape[0] / scale
    peaks = ((peaks * e + skeleton_shape//2) * 2**shift).astype(int)
    point_coors = point_coors * e 
    point_coors[:,:2] += skeleton_shape//2
    point_locations = point_coors.astype(int)
    point_coors = (point_coors* 2**shift).astype(int)
    c = (skeleton_shape//2 - center[::-1]*e).astype(int)
    
    im_size = (e * im_size / exp_rate / 2).astype(int)
    im_ul = np.array([c[0] - im_size[0], c[1] - im_size[1]])
    im_br = np.array([c[0] + im_size[0], c[1] + im_size[1]])
    
    if display['window_size'] is not None:
        im_size = np.array(geometry['image_size']) * display['zoom']
        wn_size = np.array(display['window_size'])
        
        wn_ul = im_size // 2 - np.array(display['center'])
        wn_br = wn_ul + wn_size
        
        wn_ul = (im_ul + (im_br - im_ul) * wn_ul / im_size).astype(int)
        wn_br = (im_ul + (im_br - im_ul) * wn_br / im_size).astype(int)
    
    else:
        wn_ul, wn_br = im_ul, im_br
    
    im_ul, im_br = np.fmax(0, im_ul), np.fmax(0, im_br)
    wn_ul, wn_br = np.fmax(0, wn_ul), np.fmax(0, wn_br)
    wn_ul = np.fmax(wn_ul, im_ul)
    wn_br = np.fmin(wn_br, im_br)
    
    im_rect = slice(im_ul[1], im_br[1]), slice(im_ul[0], im_br[0])
    wn_rect = slice(wn_ul[1], wn_br[1]), slice(wn_ul[0], wn_br[0])
    
    image = image.base
    image[:] = 240
    image[im_rect] = 255
    
    if len(cross) > 1:
        section_color = np.array(skeleton_settings['section_color'])
        alpha = skeleton_settings['section_alpha']
        
        cross = cross * e + skeleton_shape//2
        
        sc_ul = (np.amin(cross, axis=0)).astype(int) - 1
        sc_br = (np.amax(cross, axis=0)).astype(int) + 1
        sc_ul, sc_br = np.fmax(0, sc_ul), np.fmax(0, sc_br)
        sc_ul = np.fmax(im_ul, np.fmin(wn_ul, sc_ul))
        sc_br = np.fmin(im_br, np.fmax(wn_br, sc_br))
        
        sc_rect = slice(sc_ul[1], sc_br[1]), slice(sc_ul[0], sc_br[0])
        
        cross1 = ((cross - sc_ul) * 2**shift).astype(int)
        cross = (cross * 2**shift).astype(int)
        
        mask = np.zeros_like(image[sc_rect][:,:,0])
        cv2.fillConvexPoly(mask, cross1, 255, lineType=cv2.LINE_AA, shift=shift)
        mask = mask[:,:,None] * (alpha/255)
        
        cv2.fillConvexPoly(image, cross, (220, 220, 220),
                           lineType=cv2.LINE_AA, shift=shift)
        image[im_rect] = 200
        image[wn_rect] = section_color
        image[sc_rect] = (image[sc_rect]*mask + 255*(1 - mask)).astype(np.uint8)
        image0 = image[sc_rect].copy()
        image[im_rect] = 255
        image[wn_rect] = section_color
        image[sc_rect] = (image[sc_rect]*mask + 255*(1 - mask)).astype(np.uint8)
    
    radius = int(2.5 * 2**shift)
    
    use = (point_coors[:,2] > 0) * ~within
    for coor, color in zip(point_coors[use], point_colors[use]):
        color = (int(color[0]), int(color[1]), int(color[2]))
        cv2.circle(image, (coor[0], coor[1]), radius, color, 
                   thickness=-1, lineType=cv2.LINE_AA, shift=shift)
    
    pairs = np.array(np.where((edges >= 0) * ~neg[None] * ~neg[:,None])).T
    for pair in pairs:
        n = edges[tuple(pair)]
        cv2.line(image, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),
                 (240, 240, 240), 
                 skeleton_settings['edge_thickness'][n] + 1, 
                 cv2.LINE_AA, shift=shift)
    for pair in pairs:
        n = edges[tuple(pair)]
        cv2.line(image, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),
                 skeleton_settings['edge_colors'][n], 
                 skeleton_settings['edge_thickness'][n], 
                 cv2.LINE_AA, shift=shift)
        
    for i in range(len(cross)):
        n = edges[tuple(separated[:,i])]
        cv2.line(image, tuple(peaks[separated[1,i]]), tuple(peaks[separated[0,i]]),
                 (240, 240, 240), 
                 skeleton_settings['edge_thickness'][n] + 1, 
                 cv2.LINE_AA, shift=shift)
        cv2.line(image, tuple(cross[i]), tuple(peaks[separated[0,i]]),\
                 skeleton_settings['edge_colors'][n], 
                 skeleton_settings['edge_thickness'][n], 
                 cv2.LINE_AA, shift=shift)
    
    use = (point_coors[:,2] > 0) * within
    for coor, color in zip(point_coors[use], point_colors[use]):
        color = (int(color[0]), int(color[1]), int(color[2]))
        cv2.circle(image, (coor[0], coor[1]), radius, color, 
                   thickness=-1, lineType=cv2.LINE_AA, shift=shift)
    
    if len(cross) > 1:
        image[sc_rect] = (image[sc_rect]*(1 - mask) + image0*mask).astype(np.uint8)
    if 0 <= c[1] < len(image):
        image[c[1], :] = 255
    if 0 <= c[0] < len(image[0]):
        image[:, c[0]] = 255
    
    use = (point_coors[:,2] <= 0) * within
    for coor, color in zip(point_coors[use], point_colors[use]):
        color = (int(color[0]), int(color[1]), int(color[2]))
        cv2.circle(image, (coor[0], coor[1]), radius, color, 
                   thickness=-1, lineType=cv2.LINE_AA, shift=shift)
    
    for i in range(len(cross)):
        n = edges[tuple(separated[:,i])]
        cv2.line(image, tuple(cross[i]), tuple(peaks[separated[1,i]]),\
                 skeleton_settings['edge_colors'][n], 
                 skeleton_settings['edge_thickness'][n], 
                 cv2.LINE_AA, shift=shift)
    
    pairs = np.array(np.where((edges >= 0) * neg[None] * neg[:,None])).T
    for pair in pairs:
        n = edges[tuple(pair)]
        cv2.line(image, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),
                 (240, 240, 240), 
                 skeleton_settings['edge_thickness'][n] + 1, 
                 cv2.LINE_AA, shift=shift)
    for pair in pairs:
        n = edges[tuple(pair)]
        cv2.line(image, tuple(peaks[pair[0]]), tuple(peaks[pair[1]]),
                 skeleton_settings['edge_colors'][n], 
                 skeleton_settings['edge_thickness'][n], 
                 cv2.LINE_AA, shift=shift)
        
    use = (point_coors[:,2] <= 0) * ~within
    for coor, color in zip(point_coors[use], point_colors[use]):
        color = (int(color[0]), int(color[1]), int(color[2]))
        cv2.circle(image, (coor[0], coor[1]), radius, color, 
                   thickness=-1, lineType=cv2.LINE_AA, shift=shift)
        
    p_num = display['point_focus']
    if 0 <= p_num < len(points):
        radius = int(radius * 1.5)
        name = points.getnames()[p_num]
        coor = point_coors[p_num]
        color = point_colors[p_num]
        color = (int(color[0]), int(color[1]), int(color[2]))
        cv2.circle(image, (coor[0], coor[1]), radius + int(2**shift), (255, 255, 255), 
                   thickness=-1, lineType=cv2.LINE_AA, shift=shift)
        cv2.circle(image, (coor[0], coor[1]), radius, color, 
                   thickness=-1, lineType=cv2.LINE_AA, shift=shift)
        
        coor = (coor * 2**(-shift)).astype(int)
        cv2.putText(image, name, (coor[0] + 12, coor[1] + 12), 
                    2, 0.5, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(image, name, (coor[0] + 12, coor[1] + 12), 
                    2, 0.5, color, 1, cv2.LINE_AA)
        
    image[:22, -66:] -= np.fmin(255 - xyz_image, image[:22, -66:])
    
    return point_locations

def tk_from_array(array: np.ndarray):
    return ImageTk.PhotoImage(Image.fromarray(array[:,:,::-1]))

if pf == 'Windows':
    flags = [1, 4, np.inf, 131072, 256]
elif pf == 'Darwin':
    flags = [1, 4, 8, 16, 256]
elif pf == 'Linux':
    flags = [1, 4, np.inf, 8, 256]

def desolve_state(state):
    res = {}
    keys = ['Shift', 'Ctrl', 'Command', 'Alt', 'Click']
    for k, fl in zip(keys, flags):
        res[k] = bool((state // fl) % 2)
    res['Control'] = res['Command'] if pf == 'Darwin' else res['Ctrl']
    return res
def make_key_text(key, state):
    key = key.upper()
    state = desolve_state(state)
    if state['Click']:
        key = 'Click+' + key
    if state['Alt']:
        key = 'Alt+' + key
    if state['Command']:
        key = 'Command+' + key
    if state['Ctrl']:
        key = 'Ctrl+' + key
    if state['Shift']:
        key = 'Shift+' + key
    return key

class DataShapeMismatchError(Exception):
    pass