import os
import gzip
import pickle
from typing import Union
import numpy as np

from .tools import base_dir, desolve_secv, load_stac, load_data
from .tools import calc_section, calc_sideview
from .tools import synthesize_image, draw_points, calc_skeleton
from .components import DataArray, CUI, MetadataDict


def load(file_path):
    if file_path[-5:] == '.stac':
        cui = STAC(file_path)
    else:
        cui = SECV(file_path)
    return cui

class SECV(CUI):
    
    def __init__(self, paths: Union[str, list], 
                voxel_array: Union[DataArray, None] = None,
                metadata: Union[dict, None] = None):
        if type(paths) == str:
            paths = [paths]
            
        secv_path = None
        for path in paths:
            ext = os.path.splitext(path)[1]
            if ext == '.secv':
                if len(paths) > 1:
                    raise TypeError('One .secv file or a list of source files '
                                    '(.oir, .oib, .tif, .tiff) has to be input.')
                secv_path = path
        
        if metadata is None:
            metadata = desolve_secv(secv_path)
            if metadata['files']['paths'] is None:
                metadata['files']['paths'] = tuple(paths)
        object.__setattr__(self, 'metadata', metadata)
        
        update_funcs = [
            self._load_voxels,
            self._allocate_frames,
            self._calc_frame,
            self._calc_image,
            self._decorate_image,
            self._update_guide
            ]
        object.__setattr__(self, 'update_funcs', update_funcs)
        
        if voxel_array is None:
            self._load_voxels()
        else:
            object.__setattr__(self, 'voxels', voxel_array)
        object.__setattr__(self, 'metadata', MetadataDict(self))
        if not hasattr(self, 'meta_prev'):
            object.__setattr__(self, 'meta_prev', self.metadata.copy())
        
        key_levels = {
            'files': ({'paths': ({}, 1)}, 6),
            'geometry': ({'image_size': ({}, 2), 'scale_bar_length': ({}, 4)}, 3),
            'display': ({'thickness': ({}, 3), 'white_back': ({}, 4), 
                         'shown_channels': ({}, 4), 'points': ({}, 5), 
                         'scale_bar': ({}, 5), 'point_focus': ({}, 5)}, 6),
            'position': ({}, 3),
            'channels': ({}, 4),
            'points': ({}, 4),
            'snapshots': ({}, 6)
            }
        object.__setattr__(self, '_key_levels', key_levels)
        
        sideview_image = DataArray(np.zeros([569, 400, 4], np.uint8))
        object.__setattr__(self, 'sideview_image_raw', sideview_image)
        object.__setattr__(self, 'sideview_image', sideview_image[:,:,:3])
        
        skeleton_image = DataArray(np.zeros([400, 400, 3], np.uint8))
        object.__setattr__(self, 'skeleton_image', skeleton_image)
        
        self.update(level = 4)
    
    def __str__(self):
        text = 'SECV({0})'
        if self.files['secv_path'] is not None:
            path = os.path.basename(self.files['secv_path'])
            path = "'{0}'".format(path)
            text = text.format(path)
        else:
            paths = [os.path.basename(p) for p in self.files['paths']]
            text = text.format(paths)
        return text
    
    def save(self, file_path: str = None) -> None:
        if file_path is None:
            file_path = self.files['secv_path']
            if file_path is None:
                raise FileNotFoundError('No available path given for saving .secv file')
        if os.path.splitext(file_path)[1] != '.secv':
            file_path = file_path + '.secv'
        
        secv = self.metadata._format()
        
        secv['files']['original_secv_path'] = file_path
        with open(file_path, 'wb') as f:
            pickle.dump(secv, f, protocol=4)
        dict.__setitem__(self.files, 'secv_path', file_path)
        dict.__setitem__(self.files, 'original_secv_path', file_path)
          
            
    def reload(self, file_path: str = None) -> None:
        if file_path is None:
            file_path = self.files['secv_path']
            if file_path is None:
                raise FileNotFoundError('No available path given for reloading .secv file')
        if not os.path.isfile(file_path):
            raise FileNotFoundError('No such secv. file: {0}'.format(file_path))
        self.__init__(file_path)
        
            
    def copy(self, metadata = None):
        if metadata is None:
            metadata = self.metadata
        if hasattr(metadata, '_format'):
            metadata = metadata._format()
        return SECV([], self.voxels, metadata)
    
    
    def update(self, level: int = None, end: int = 6) -> bool:
        if not hasattr(self, 'voxels'):
            raise NoDataGivenError('No available data for 3d-image array')
        if hasattr(self, 'meta_prev') and \
            hasattr(self.metadata, '_locate_difference'):
            loc = self.metadata._locate_difference(self.meta_prev)
            if level is None:
                level = self._get_update_level(loc)
        level = min(level, end + 1)
        success = True
        for i in range(level - 1, end):
            success = self.update_funcs[i]()
            if not success:
                break
        if success:
            if hasattr(self, 'meta_prev') and \
                hasattr(self.metadata, '_locate_difference'):
                if level == self._get_update_level(loc) and end == 6:
                    object.__setattr__(self, 'meta_prev', self.metadata.copy())
        return success
    
    def getframe(self):
        self.update()
        return self.view_frame[list(self.display['shown_channels'])]
    
    def getimage(self):
        self.update()
        return self.view_image.copy()
    
    def getskeleton(self):
        self.update()
        return self.skeleton_image.copy()
    
    
    def calc_2d_to_3d(self, coor_xy: np.ndarray) -> np.ndarray:
        iw, ih = self.geometry['image_size']
        sz, sy, sx = self.files['shape']
        op, ny, nx = self.position
        v = coor_xy - np.array([iw, ih])//2
        coor_zyx = op + (ny*v[1] + nx*v[0])/self.geometry['expansion_rate']
        return coor_zyx
    
    
    def _locate_difference(self, other):
        return self.metadata._locate_difference(other.metadata)
    
    def _get_update_level(self, loc):
        level = 6
        for l in loc:
            obj, num = self._key_levels[l[0]]
            for i in range(1, len(l)):
                if l[i] not in obj:
                    break
                obj, num = obj[l[i]]
            level = min(num, level)
        return level
    
    def _load_voxels(self):
        voxels = None
        file_paths = ()
        channel_nums = ()
        if hasattr(self, 'voxels'):
            if hasattr(self.voxels, '_file_paths_vx'):
                voxels = self.voxels.base
                file_paths = self.voxels._file_paths_vx
                channel_nums = self.voxels._channel_nums_vx
        voxels, metadata_in_files = load_data(self.files['paths'], 
                                              self.files['original_secv_path'],
                                              voxels, file_paths, channel_nums)
        if len(voxels) == 0:
            raise NoDataGivenError('No available data for 3d-image array')
        
        voxel_array = voxels[0]
        for vx in voxels[1:]:
            voxel_array = np.append(voxel_array, vx, axis=0)
        voxel_array = voxel_array.view(DataArray)
        object.__setattr__(voxel_array, '_file_paths_vx', self.files['paths'])
        object.__setattr__(voxel_array, '_channel_nums_vx', metadata_in_files['channel_nums'])
        object.__setattr__(self, 'voxels', voxel_array)
        object.__setattr__(self, 'shape', voxel_array.shape)
        
        for k in metadata_in_files:
            dict.__setitem__(self.files, k, metadata_in_files[k])
        if hasattr(self.channels, '_format'):
            old_chs = list(self.channels)
            old_ch_show = list(self.display['shown_channels'])
            sep = [0] + list(np.cumsum(channel_nums))
            old_chs = [old_chs[sep[i]: sep[i+1]] for i in range(len(channel_nums))]
            old_ch_show = [old_ch_show[sep[i]: sep[i+1]] for i in range(len(channel_nums))]
            new_chs = [[None]*n for n in metadata_in_files['channel_nums']]
            new_ch_show = [[True]*n for n in metadata_in_files['channel_nums']]
            for i, f in enumerate(self.files['paths']):
                if f in file_paths:
                    j = file_paths.index(f)
                    new_chs[i] = old_chs[j]
                    new_ch_show[i] = old_ch_show[j]
            for i in range(1, len(new_chs)):
                new_chs[0] += new_chs[i]
                new_ch_show[0] += new_ch_show[i]
            new_chs = new_chs[0]
            new_ch_show = new_ch_show[0]
            self.display['shown_channels'] = new_ch_show
            self.channels.generate(new_chs)
        
        return True
    

    def _allocate_frames(self) -> bool:
        geometry = self.geometry
        
        view_frame = np.zeros([len(self.voxels), 
                               *geometry['image_size'][::-1]], np.uint16)
        view_image_buffer = np.zeros([*geometry['image_size'][::-1], 4], np.uint8)
        sideview_frame = np.zeros([len(self.voxels), 569, 400], np.uint16)
        sideview_frame1 = np.zeros([len(self.voxels), 284, 400], np.uint16)
        sideview_frame2 = np.zeros([len(self.voxels), 284, 400], np.uint16)
        
        view_frame = DataArray(view_frame)
        view_image_buffer = DataArray(view_image_buffer)
        sideview_frame = DataArray(sideview_frame)
        sideview_frame1 = DataArray(sideview_frame1)
        sideview_frame2 = DataArray(sideview_frame2)
        
        object.__setattr__(self, 'view_frame', view_frame)
        object.__setattr__(self, 'view_image_buffer', view_image_buffer)
        object.__setattr__(self, 'sideview_frame', sideview_frame)
        object.__setattr__(self, '_sideview_frame1', sideview_frame1)
        object.__setattr__(self, '_sideview_frame2', sideview_frame2)
        
        return True
    
    
    def _calc_frame(self, center = None) -> bool:
        voxels = self.voxels
        section = self.view_frame
        if section[0].shape != self.geometry['image_size'][::-1] or \
            len(section) != len(voxels):
            self._allocate_frames()
        
        success = calc_section(self.voxels, self.geometry, self.position, 
                               self.display, section, center = center)
        return success
    
    
    def _calc_image(self) -> bool:
        
        image = synthesize_image(self.view_frame, self.channels, 
                                 self.display, self.view_image_buffer)
        object.__setattr__(self, 'view_image_raw', image)
        return True
    
    
    def _decorate_image(self):
        image = self.view_image_raw.copy()
        
        if self.display['points'] and len(self.points) > 0:
            
            point_names = np.array(self.points.getnames())
            point_colors = np.array(self.points.getcolors())
            point_coors = self.points.coorsonimage()
            thickness = self.display['thickness']
            
            show = draw_points(image, point_coors, point_colors,
                               point_names, thickness)
            
            object.__setattr__(self.display, '_shown_points_ids', np.where(show)[0])
            object.__setattr__(self.display, '_shown_points_coors', point_coors[show, 1:])
            
            p_num = self.display['point_focus']
            if 0 <= p_num < len(self.points):    
                ps = slice(p_num, p_num + 1)
                draw_points(image, point_coors[ps], point_colors[ps],
                            point_names[ps], thickness, r = 6)
        else:
            object.__setattr__(self.display, '_shown_points_ids', 
                               np.zeros((0), dtype=int))
            object.__setattr__(self.display, '_shown_points_coors', 
                               np.zeros((0,3), dtype=float))
        
        if self.display['scale_bar']:
            sbp = self.geometry._scale_bar_px
            if sbp > 0:
                sb = image[-25: -20, -20 - sbp: -20]
                sb[:] = 255 if np.average(sb) < 128 else 0
            
        object.__setattr__(self, 'view_image', image)
            
        return True
    
    def _update_guide(self):
        if self.display['sideview']:
            
            sideview1 = self._sideview_frame1
            sideview2 = self._sideview_frame2
            calc_sideview(self.voxels, self.geometry, self.position, 
                          self.display, sideview1, sideview2)
            self.sideview_frame.base[:,:len(sideview1[0])] = sideview1.base
            self.sideview_frame.base[:,-len(sideview2[0]):] = sideview2.base
            
            side_image = synthesize_image(self.sideview_frame, self.channels, 
                                          self.display, self.sideview_image_raw)
            
            side_image[::5, len(side_image[0])//2] = \
                255 - side_image[::5, len(side_image[0])//2]
            side_image[len(sideview1[0])//2] = \
                255 - side_image[len(sideview1[0])//2]
            side_image[len(sideview1[0]) + len(sideview2[0])//2] = \
                255 - side_image[len(sideview1[0]) + len(sideview2[0])//2]
            
            if self.display['points'] and len(self.points) > 0:
                point_names = np.array(self.points.getnames())
                point_colors = np.array(self.points.getcolors())
                point_coors = self.points.coorsonimage()
                thickness = self.display['thickness']
                
                point_coors[:,1:] -= np.array(self.geometry['image_size'][::-1])//2
                point_coors /= 2
                point_coors1 = point_coors[:,[1,0,2]]
                point_coors1[:,1:] += np.array(self._sideview_frame1[0].shape)//2
                point_coors2 = point_coors[:,[2,0,1]]
                point_coors2[:,1:] += np.array(self._sideview_frame2[0].shape)//2
                point_coors2[:,1] += len(self._sideview_frame1[0])
                
                point_coors = np.append(point_coors1, point_coors2, axis=0)
                point_colors = np.tile(point_colors, (2,1))
                point_names = np.append(point_names, point_names)
                draw_points(side_image, point_coors, point_colors, 
                            point_names, thickness)
                
                p_num = self.display['point_focus']
                if 0 <= p_num < len(self.points):
                    ps= slice(p_num, 2*len(self.points), len(self.points))
                    draw_points(side_image, point_coors[ps], point_colors[ps], 
                                point_names[ps], thickness, r = 6)
            object.__setattr__(self, 'sideview_image', side_image)
        
        point_locations = calc_skeleton(self.files, self.geometry, 
                                        self.position, self.points,
                                        self.display, self.skeleton_image)
        object.__setattr__(self.display, '_skeleton_points', point_locations)
    
        return True
    
class STAC(CUI):
    def __init__(self, path):
        ext = os.path.splitext(path)[1]
        if ext != '.stac':
            raise TypeError('Only .stac files are supported.')
        stacks, metadata = load_stac(path)
        object.__setattr__(self, 'metadata', metadata)
        if os.path.dirname(path) == base_dir + 'temp':
            os.remove(path)
            metadata['files']['stac_path'] = None
        shape = np.array(stacks).shape
        metadata['files']['channel_nums'] = [shape[1]]
        shape = (shape[0], shape[2], shape[3])
        metadata['files']['shape'] = shape
        object.__setattr__(self, 'stacks', [np.array(s).view(DataArray) for s in stacks])
        image_buffer = np.zeros([*self.stacks[0][0].shape, 4], np.uint8)
        object.__setattr__(self, 'view_image_buffer', image_buffer.view(DataArray))
        object.__setattr__(self, 'metadata', MetadataDict(self))
        
    def __str__(self):
        text = "STAC('{0}')"
        text = text.format(os.path.basename(self.files['stac_path']))
        return text
        
    def save(self, file_path: str = None) -> None:
        if file_path is None:
            file_path = self.display['stac_path']
            if file_path is None:
                raise FileNotFoundError('No available path given for saving .secv file')
        if os.path.splitext(file_path)[1] != '.stac':
            file_path = file_path + '.stac'
            
        stacks = self.stacks.base
        channels = self.channels._format()
        geometry = self.geometry._format()
        display = self.display._format()
        
        stac = [stacks, channels, geometry, display]
        
        byt = pickle.dumps(stac, protocol=4)
        byt = gzip.compress(byt, compresslevel=1)
        with open(file_path, 'wb') as f:
            f.write(byt)
        
    def update(self, *args, **kwargs):
        index = self.display['index']
        frame = self.stacks[index]
        image = synthesize_image(frame, self.channels, 
                                 self.display, self.view_image_buffer)
        if self.display['scale_bar']:
            sbp = self.geometry._scale_bar_px
            if sbp > 0:
                sb = image[-25: -20, -20 - sbp: -20]
                sb[:] = 255 if np.average(sb) < 128 else 0
        object.__setattr__(self, 'view_image', image)
        
        return True
    
class NoDataGivenError(Exception):
    pass