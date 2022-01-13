# -*- coding: utf-8 -*-
"""
Created on Sun Jan  2 07:58:14 2022

@author: kazuu
"""
import ctypes
import os

dllname = os.path.dirname(os.path.abspath(__file__))
dllname = os.path.join(dllname, "cfuncs.dll")
cf = ctypes.cdll.LoadLibrary(dllname)

calc_sec = cf.calc_section
calc_sec.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                      ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_int), 
                      ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, 
                      ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
calc_sec.restype = ctypes.c_bool

def calc_section(box, pos, res, c, ch_show):
    dc, dz, dy, dx = box.shape
    m, n = res.shape[1:]
    chs = len(ch_show)
    dc = ctypes.c_int(dc)
    dz = ctypes.c_int(dz)
    dy = ctypes.c_int(dy)
    dx = ctypes.c_int(dx)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    chs = ctypes.c_int(chs)
    
    return calc_sec(box.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                    pos.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                    c.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                    ch_show.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                    dc, dz, dy, dx, m, n, chs)

fill_b = cf.fill_box
fill_b.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                   ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                   ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_int), 
                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                   ctypes.c_int, ctypes.c_int, ctypes.c_int)
fill_b.restype = None

def fill_box(box, pos, v, start, stop, res, c):
    dc, dz, dy, dx = box.shape
    dc1, d, m, n = res.shape
    assert dc == dc1
    start = ctypes.c_int(start)
    stop = ctypes.c_int(stop)
    dc = ctypes.c_int(dc)
    dz = ctypes.c_int(dz)
    dy = ctypes.c_int(dy)
    dx = ctypes.c_int(dx)
    d = ctypes.c_int(d)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    
    return fill_b(box.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                  pos.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                  v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                  start, stop,
                  res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                  c.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                  dc, dz, dy, dx, d, m, n)

fast_sec = cf.fast_section
fast_sec.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                      ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_int), 
                      ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, 
                      ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
fast_sec.restype = ctypes.c_bool

def fast_section(box, pos, res, c, ch_show):
    dc, dz, dy, dx = box.shape
    m, n = res.shape[1:]
    chs = len(ch_show)
    dc = ctypes.c_int(dc)
    dz = ctypes.c_int(dz)
    dy = ctypes.c_int(dy)
    dx = ctypes.c_int(dx)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    chs = ctypes.c_int(chs)
    
    return fast_sec(box.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                    pos.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                    c.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                    ch_show.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                    dc, dz, dy, dx, m, n, chs)

stack_sec = cf.stack_section
stack_sec.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                      ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                      ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_int), 
                      ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, 
                      ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
stack_sec.restype = ctypes.c_bool

def stack_section(box, pos, v, start, stop, res, c, ch_show):
    dc, dz, dy, dx = box.shape
    m, n = res.shape[1:]
    chs = len(ch_show)
    dc = ctypes.c_int(dc)
    dz = ctypes.c_int(dz)
    dy = ctypes.c_int(dy)
    dx = ctypes.c_int(dx)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    chs = ctypes.c_int(chs)
    start = ctypes.c_int(start)
    stop = ctypes.c_int(stop)
    
    return stack_sec(box.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                     pos.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                     v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), start, stop,
                     res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                     c.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                     ch_show.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                     dc, dz, dy, dx, m, n, chs)

stack_sec2 = cf.stack_section2
stack_sec2.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                       ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                       ctypes.POINTER(ctypes.c_uint16), ctypes.c_int, ctypes.c_int, 
                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
stack_sec2.restype = ctypes.c_bool

def stack_section2(box, pos, v, start, stop, res):
    dc, dz, dy, dx = box.shape
    m, n = res.shape[1:]
    dc = ctypes.c_int(dc)
    dz = ctypes.c_int(dz)
    dy = ctypes.c_int(dy)
    dx = ctypes.c_int(dx)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    start = ctypes.c_int(start)
    stop = ctypes.c_int(stop)
    
    return stack_sec2(box.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                     pos.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                     v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), start, stop,
                     res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                     dc, dz, dy, dx, m, n)

fast_st = cf.fast_stack
fast_st.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                    ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_int), 
                    ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, 
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
fast_st.restype = ctypes.c_bool

def fast_stack(box, pos, v, start, stop, res, c, ch_show):
    dc, dz, dy, dx = box.shape
    m, n = res.shape[1:]
    chs = len(ch_show)
    dc = ctypes.c_int(dc)
    dz = ctypes.c_int(dz)
    dy = ctypes.c_int(dy)
    dx = ctypes.c_int(dx)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    chs = ctypes.c_int(chs)
    start = ctypes.c_int(start)
    stop = ctypes.c_int(stop)
    
    return fast_st(box.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                   pos.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                   v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), start, stop,
                   res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                   c.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                   ch_show.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                   dc, dz, dy, dx, m, n, chs)

calc_c = cf.calc_bgr
calc_c.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int),
                    ctypes.POINTER(ctypes.c_uint8), ctypes.c_int, ctypes.c_int, ctypes.c_int)
calc_c.restype = None

def calc_bgr(frame, alpha, colors, ch_show, res):
    m, n = res.shape[:2]
    chs = len(ch_show)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    chs = ctypes.c_int(chs)
    clr = colors/255
    
    calc_c(frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
           alpha.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
           clr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
           ch_show.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
           res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
           m, n, chs)
    
calc_cw = cf.calc_bgr_w
calc_cw.argtypes = (ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int),
                    ctypes.POINTER(ctypes.c_uint8), ctypes.c_int, ctypes.c_int, ctypes.c_int)
calc_cw.restype = None

def calc_bgr_w(frame, alpha, colors, ch_show, res):
    m, n = res.shape[:2]
    chs = len(ch_show)
    m = ctypes.c_int(m)
    n = ctypes.c_int(n)
    chs = ctypes.c_int(chs)
    clr = 1 - colors/255
    
    calc_cw(frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
            alpha.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            clr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            ch_show.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            res.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            m, n, chs)