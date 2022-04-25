# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Contains class to display graphics in terminal.
'''

import io
import os
import sys
import struct
import tempfile
import numpy as np

from ..glogger import getGLogger
from ..utils import which_cmds, run_child_cmd, find_available_module

__all__ = ['get_imgfwh', 'resize_imgwh', 'convert_img', 'Display']
vlog = getGLogger('V')
TEMPPREFIX = 'gdpy3-imgcat-temp-%s-' % tempfile.mktemp(prefix='', dir='')
Image = find_available_module('PIL.Image')


def get_imgfwh(img):
    '''
    Read the (format, (width, height)) from a PNG/JPEG/GIF/EPS header.

    Notes
    -----
    1. Adapted from :mod:`IPython.core.display`
    2. https://en.wikipedia.org/wiki/Portable_Network_Graphics
    3. http://giflib.sourceforge.net/whatsinagif/bits_and_bytes.html
    4. https://www.adobe.com/content/dam/acom/en/devnet/actionscript/articles/5002.EPSF_Spec.pdf

    Parameters
    ----------
    img: path or bytes
        image path or entire image bytes
    '''
    if type(img) == str:
        if os.path.isfile(img):
            with open(img, 'rb') as im:
                data = im.read()
        else:
            vlog.error('ValueError: unexpected image path %s!' % img)
            return None, (None,)*2
    elif type(img) == bytes:
        data = img
    else:
        vlog.error("ValueError: Unexpected image type %s!" % type(img))
        return None, (None,)*2
    if data and len(data) >= 30:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            ihdr = data.index(b'IHDR')
            # next 8 bytes are width/height
            return 'PNG', struct.unpack('>ii', data[ihdr+4:ihdr+12])
        elif data[:2] == b'\xff\xd8':
            # adapted from http://www.64lines.com/jpeg-width-height
            idx = 4
            while True:
                block_size = struct.unpack('>H', data[idx:idx+2])[0]
                idx = idx + block_size
                if data[idx:idx+2] == b'\xFF\xC0':
                    # found Start of Frame
                    iSOF = idx
                    break
                else:
                    # read another block
                    idx += 2
            h, w = struct.unpack('>HH', data[iSOF+5:iSOF+9])
            return 'JPEG', (w, h)
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            return 'GIF', struct.unpack('<HH', data[6:10])
        elif (data[:12], data[15:21]) == (b'%!PS-Adobe-3', b'EPSF-3'):
            idx = data.index(b'%%BoundingBox:')
            end = data[idx:].index(b'\n')
            box = data[idx+14:idx+end].decode().split()
            llx, lly, urx, ury = list(map(float, box))
            return 'EPS', (int(urx-llx), int(ury-lly))
        else:
            vlog.error('ValueError: unexpected image format!')
            return None, (None,)*2
    else:
        vlog.error("ValueError: broken image!")
        return None, (None,)*2


def resize_imgwh(oldsize, w=None, h=None, max_width=1366):
    '''Resize image width, height and keep aspect ratio.'''
    if not oldsize[0] or not oldsize[1]:
        return oldsize
    if w and h:
        if w / oldsize[0] <= h / oldsize[1]:
            h = None  # ignore height
        else:
            w = None
    if w:
        if w > max_width:
            vlog.debug("Resize image width: %d -> %d(max)" % (w, max_width))
            w = max_width
        return w, int(oldsize[1] * w / oldsize[0])
    elif h:
        w = int(oldsize[0] * h / oldsize[1])
        if w > max_width:
            vlog.debug("Resize image width: %d -> %d(max)" % (w, max_width))
            return max_width, int(oldsize[1] * max_width / oldsize[0])
        else:
            return w, h
    else:
        w = oldsize[0]
        if w > max_width:
            vlog.debug("Resize image width: %d -> %d(max)" % (w, max_width))
            return max_width, int(oldsize[1] * max_width / oldsize[0])
        else:
            return oldsize


def _load_eps(img, intype, max_width, savefp=None, savefmt='PNG'):
    '''Open EPS, resize it if needed. intype: path, data, Image.'''
    if not Image:
        vlog.error("Display EPS in Terminal requires Pillow.")
        return None, None
    if intype == 'path':
        im = Image.open(img)
    elif intype == 'data':
        im = Image.open(io.BytesIO(img))
    elif intype == 'Image':
        assert isinstance(img, Image.Image)
        im = img
    else:
        vlog.error("Invalid EPS intype: %s!" % intype)
        return None, None
    oldsize = im.size
    if im.width < max_width//2:
        scale = max_width // im.width
        im.load(scale=scale)
        vlog.debug("Load vector image with enough resolution. "
                   "scale: %d, size: %s -> %s" % (scale, oldsize, im.size))
    if savefp:
        im.save(savefp, format=savefmt)
    return im, savefp


def convert_img(img, typecandidates, width=None, height=None, max_width=1366):
    '''
    Convert image *img* to outype and resize image if needed.

    Parameters
    ----------
    img: path, bytes or Figure objec
        1. image path
        2. entire image bytes
        3. matplotlib.figure.Figure instance
    typecandidates: tuple of valid out types
        1. 'path', return (path, fmt, width, height, None)
        2. 'data', return (entire image bytes, fmt, width, height, None)
        3. 'rawdata', return (raw image data, fmt, width, height, mode)
        4. 'BytesIO', return (io.BytesIO object, fmt, width, height, None)
    width: int
        width of out image, resize if needed.
    height: int
        height of out image, resize if needed.
    max_width: int
        max width of out image, default 1366
    '''
    if isinstance(img, str) and os.path.isfile(img):
        intype = 'path'
    elif isinstance(img, bytes):
        intype = 'data'
    else:
        import matplotlib.figure
        if isinstance(img, matplotlib.figure.Figure):
            intype = 'mplf'
        else:
            vlog.error("Invalid input, not a image path, entire image bytes "
                       "or matplotlib.figure.Figure instance!")
            return (None,)*5

    validcandidates = ('path', 'data', 'rawdata', 'BytesIO')
    typecandidates = tuple(c for c in typecandidates if c in validcandidates)
    if intype in typecandidates:
        outype = intype
    else:
        outype = typecandidates[0]

    if outype == 'path':
        if intype in ('path', 'data'):
            fmt, oldsize = get_imgfwh(img)
            path = None
            if fmt == 'EPS':
                path = tempfile.mktemp(suffix='.PNG', prefix=TEMPPREFIX)
                im, path = _load_eps(img, intype, max_width, savefp=path)
                if im:
                    fmt, oldsize = 'PNG', im.size
            if not path and intype == 'path':
                path = img
            elif not path and intype == 'data':
                path = tempfile.mktemp(suffix='.%s' % fmt, prefix=TEMPPREFIX)
                with open(path, 'wb') as im:
                    im.write(img)
        elif intype == 'mplf':
            fmt, oldsize = 'PNG', tuple(map(int, img.bbox.size))
            path = tempfile.mktemp(suffix='.PNG', prefix=TEMPPREFIX)
            img.savefig(path, format='png')
        else:
            pass  # new intype
        w, h = resize_imgwh(oldsize, w=width, h=height, max_width=max_width)
        return path, fmt, w, h, None
    elif outype == 'data':
        if intype in ('path', 'data'):
            if intype == 'path':
                with open(img, 'rb') as im:
                    data = im.read()
                fmt, oldsize = get_imgfwh(data)
            elif intype == 'data':
                data = img
                fmt, oldsize = get_imgfwh(img)
            if fmt == 'EPS':
                ib = io.BytesIO()
                im, ib = _load_eps(img, intype, max_width, savefp=ib)
                if im:
                    fmt, oldsize = 'PNG', im.size
                    data = ib.getvalue()
        elif intype == 'mplf':
            ib = io.BytesIO()
            img.savefig(ib, format='png')
            data = ib.getvalue()
            fmt, oldsize = 'PNG', tuple(map(int, img.bbox.size))
        else:
            pass  # new intype
        w, h = resize_imgwh(oldsize, w=width, h=height, max_width=max_width)
        return data, fmt, w, h, None
    elif outype == 'rawdata':
        if intype in ('path', 'data'):
            if not Image:
                vlog.error("Display rawdata in Terminal requires Pillow.")
                return (None,)*5
            if intype == 'path':
                im = Image.open(img)
            elif intype == 'data':
                im = Image.open(io.BytesIO(img))
            fmt, oldsize, mode = im.format, im.size, im.mode
            if im.format == 'EPS':
                im, _ = _load_eps(im, 'Image', max_width, savefp=None)
                oldsize = im.size
            wh = resize_imgwh(oldsize, w=width, h=height, max_width=max_width)
            if wh != oldsize:
                im = im.resize(wh)
            try:
                rawdata = im.tobytes()
            except NotImplementedError:
                rawdata = im.tostring()
        elif intype == 'mplf':
            fig, mode = img, 'RGBA'
            fmt, oldsize = 'PNG', tuple(map(int, fig.bbox.size))
            wh = resize_imgwh(oldsize, w=width, h=height, max_width=max_width)
            if wh != oldsize:
                fig.set_size_inches(wh[0]/fig.dpi, wh[1]/fig.dpi)
                fig.canvas.draw()
            if not hasattr(fig.canvas, 'renderer'):
                fig.canvas.draw()
            buffer_ = fig.canvas.buffer_rgba()
            # issue, https://github.com/fastai/fastai/issues/2170
            # assert isinstance(data) == bytes
            if type(buffer_) == memoryview:
                rawdata = buffer_.tobytes()  # mpl >= 3.1.0, memoryview
            else:
                rawdata = buffer_  # mpl <= 3.0.3, bytes
        else:
            pass  # new intype
        return (rawdata, fmt, *wh, mode)
    elif outype == 'BytesIO':
        ib = io.BytesIO()
        if intype in ('path', 'data'):
            if intype == 'path':
                with open(img, 'rb') as im:
                    data = im.read()
            elif intype == 'data':
                data = img
            fmt, oldsize = get_imgfwh(data)
            if fmt == 'EPS':
                im, _ = _load_eps(data, 'data', max_width, savefp=ib)
                if im:
                    fmt, oldsize = 'PNG', im.size
                else:
                    ib.write(data)
            else:
                ib.write(data)
        elif intype == 'mplf':
            fmt, oldsize = 'PNG', tuple(map(int, img.bbox.size))
            img.savefig(ib, format='png')
        else:
            pass  # new intype
        w, h = resize_imgwh(oldsize, w=width, h=height, max_width=max_width)
        return ib, fmt, w, h, None
    else:
        raise ValueError('unexpected image outype!')


class Display(object):
    '''
    Use programs or modules from *Projects* to display graphics in terminal.

    Projects
    --------
    1. https://github.com/saitoha/libsixel
    2. https://github.com/saitoha/PySixel
    3. https://github.com/elsteveogrande/PySixel
    4. https://www.enlightenment.org/docs/apps/terminology.md#tycat
    5. https://www.iterm2.com/documentation-images.html
    6. https://sw.kovidgoyal.net/kitty/graphics-protocol.html

    Attributes
    ----------
    cmd: str or list
        :attr:`cmd` can be program name or sequence of program arguments.
        Program can be tycat, kitty, imgcat or img2sixel.
        1. tycat only works in terminal terminology,
           and geometry <width>x<height> is cell count.
        2. kitty only works in terminal kitty and ignores geometry set.
        3. imgcat only works in iterm2 and ignores geometry set.
        4. img2sixel works in terminals which support DEC SIXEL graphics.
    mod: module
        SIXEL module object, libsixel or sixel
    output: output file object
        sys.stdout(default), sys.stderr or file-like object
    attty: bool
        True if the output is connected to a terminal.
    max_width: int
        max display width in pixels, default 1366
    '''
    __slots__ = ['_cmd', '_mod', '_output', 'max_width', '_cache']

    def __init__(self, output=None, max_width=1366):
        self._cmd, self._mod = None, None
        if os.getenv('TERMINOLOGY') == '1':
            self.cmd = 'tycat'
        elif os.getenv('TERM') == 'xterm-kitty':
            self.cmd = 'kitty'
        elif os.getenv('TERM_PROGRAM') == 'iTerm.app':  # ITERM_SESSION_ID
            self.cmd = 'imgcat'
        else:
            # terminals which support SIXEL
            self.cmd = 'img2sixel'
            self.mod = 'libsixel'
            if not self.mod:
                self.mod = 'sixel'
        self.output = output or sys.stdout
        self.max_width = max_width
        self._cache = set()

    def _get_cmd(self):
        return self._cmd

    def _set_cmd(self, candidate):
        self._cmd = which_cmds(candidate)

    cmd = property(_get_cmd, _set_cmd)

    def _get_mod(self):
        return self._mod

    def _set_mod(self, candidate):
        self._mod = find_available_module(candidate)

    mod = property(_get_mod, _set_mod)

    def _get_output(self):
        return self._output

    def _set_output(self, out):
        if hasattr(out, 'fileno'):
            self._output = out
        else:
            vlog.warning("Method fileno not found in %s!" % out)
            self._output = None

    output = property(_get_output, _set_output)

    @property
    def attty(self):
        return os.isatty(self.output.fileno())

    def show_attr_info(self):
        for attr in ('cmd', 'mod', 'output', 'attty', 'max_width'):
            self.output.write(' -> %s: %s\n' % (attr, getattr(self, attr)))

    def __del__(self):
        for fname in self._cache:
            try:
                os.remove(fname)
            except Exception:
                pass

    def _cache_add(self, path):
        if not path:
            return
        if not isinstance(path, str):
            return
        if os.path.basename(path).startswith(TEMPPREFIX):
            self._cache.add(path)

    def display(self, img, width=None, height=None, usemod=False):
        '''
        Use command :attr:`cmd` or :attr:`mod` to display.

        Parameters
        ----------
        img: path, bytes or Figure object
            1. image path
            2. entire image bytes
            3. matplotlib.figure.Figure instance
        width: int
            width of out image, resize if needed.
        height: int
            height of out image, resize if needed.
        usemod: bool
            When both module libsixel(or sixel) and program img2sixel are
            available, use module first or not. default False
        '''
        whkwargs = dict(width=width, height=height, max_width=self.max_width)
        if self.cmd and self.cmd.endswith('tycat'):
            vlog.debug("Use tycat to display.")
            path, _, w, h, _ = convert_img(img, ('path',), **whkwargs)
            self._cache_add(path)
            args = ['-g', '%dx%d' % (w, h)] if w and h else []
            # :attr:`output` is useless. Set stdout None to avoid blocking.
            self._cmd_display(args, path, {'stdout': None})
        elif self.cmd and self.cmd.endswith('kitty'):
            vlog.debug("Use kitty to display.")
            put, _, w, h, _ = convert_img(img, ('data', 'path'), **whkwargs)
            self._cache_add(put)
            self._cmd_display(['+kitten', 'icat'], put, {})
        elif self.cmd and self.cmd.endswith('imgcat'):
            vlog.debug("Use imgcat to display.")
            put, _, w, h, _ = convert_img(img, ('data', 'path'), **whkwargs)
            self._cache_add(put)
            self._cmd_display([], put, {})
        elif (self.cmd and self.cmd.endswith('img2sixel')
                or self.mod and self.mod.__name__ in ('libsixel', 'sixel')):
            # for SIXEL
            c, m = False, False
            if self.cmd and self.cmd.endswith('img2sixel'):
                c = True
            if self.mod and self.mod.__name__ in ('libsixel', 'sixel'):
                m = True
            use = 0  # 0: cmd, 1: libsixel, 2: sixel
            if c and m:
                use = 12 if usemod else 0
            elif c and not m:
                if usemod:
                    vlog.warning("No module for sixel found!")
                use = 0
            elif not c and m:
                use = 12
            else:
                pass
            if use == 12:
                use = 1 if self.mod.__name__ == 'libsixel' else 2
            # start
            if use == 1:
                vlog.info("Use libsixel to display.")
                rawdata, fmt, w, h, mode = convert_img(
                    img, ('rawdata',), **whkwargs)
                if fmt == 'GIF':
                    vlog.error("libsixel cannot display GIF for now!")
                    return
                self._libsixel_display(rawdata, w, h, mode)
            elif use == 2:
                vlog.info("Use PySixel to display.")
                put, _, w, h, _ = convert_img(
                    img, ('BytesIO', 'path'), **whkwargs)
                self._cache_add(put)
                self._sixel_display(put, w, h)
            else:
                vlog.debug("Use img2sixel to display.")
                put, fmt, w, h, _ = convert_img(
                    img, ('data', 'path'), **whkwargs)
                self._cache_add(put)
                args = ['-w', str(w), '-h', str(h)] if w and h else []
                kwargs = {}
                if fmt == 'GIF':
                    args += ['-l', 'disable']
                    kwargs['stdout'] = None
                self._cmd_display(args, put, kwargs)
        else:
            if self.cmd:
                # default run cmd
                vlog.debug("Use %s to display." % self.cmd)
                path, _, w, h, _ = convert_img(img, ('path',), **whkwargs)
                self._cache_add(path)
                self._cmd_display([], path, {})
            else:
                vlog.error("No display method found!")

    def _cmd_display(self, args, put, kwargs):
        '''Use command with *args* to display *put*.'''
        if not put:
            return
        if isinstance(self.cmd, list):
            cmd = self.cmd.copy()
        else:
            cmd = [self.cmd]
        cmd += args
        if isinstance(put, str):
            cmd += [put]
            vlog.info('Running command: %s' % ' '.join(cmd))
            code, out, err = run_child_cmd(cmd, **kwargs)
        else:
            assert type(put) == bytes, "Unexpected put type %s!" % type(put)
            cmdline = ' '.join(cmd)
            vlog.info('Running command: %s, with bytes input.' % cmdline)
            code, out, err = run_child_cmd(cmd, input=put, **kwargs)
            if out:
                out = out.decode('ascii')
            err = err.decode()
        if code == 0:
            if out:
                self.output.write(out)
        else:
            vlog.error('Failed to display: (%d) %s' % (code, err))

    def _libsixel_display(self, rawdata, w, h, mode):
        '''
        Convert raw image data into SIXEL using libsixel python interface.

        Ref: https://github.com/saitoha/libsixel/blob/v1.8.6/examples/python/converter.py
        The *w*, *h* and *rawdata* must match.
        Guess: *rawdata* is not entire images, it's pixel data only,
        such as a width*height long array of RGBA values.
        '''
        assert self.mod.__name__ == 'libsixel'
        if not rawdata:
            return
        lib = self.mod
        ncolors = 256
        if mode == 'RGBA':
            pixelfmt = lib.SIXEL_PIXELFORMAT_RGBA8888
        elif mode == 'RGB':
            pixelfmt = lib.SIXEL_PIXELFORMAT_RGB888
        else:
            raise RuntimeError("unexpected image mode, not in 'RGBA', 'RGB'.")
        s = io.BytesIO()
        out = lib.sixel_output_new(lambda rawdata, s: s.write(rawdata), s)
        dither = lib.sixel_dither_new(ncolors)
        try:
            lib.sixel_dither_initialize(dither, rawdata, w, h, pixelfmt)
            lib.sixel_encode(rawdata, w, h, 1, dither, out)
            self.output.write(s.getvalue().decode('ascii'))
        finally:
            lib.sixel_output_unref(out)
            lib.sixel_dither_unref(dither)

    def _sixel_display(self, put, w, h):
        assert self.mod.__name__ == 'sixel'
        if not put:
            return
        writer = self.mod.SixelWriter()
        writer.draw(put, w=w, h=h, output=self.output)


def overlay_alpha_png(bg, png, xy_offset=None):
    '''
    Overlay alpha png on bg image.

    Parameters
    ----------
    bg: str, background image path, jpg or png
        OR numpy.ndarray
    png: str, alpha png image path OR np.ndarray
    xy_offset: x,y offset coordinates in pixels, default center
    '''
    if Image:
        vlog.debug("Overlay_alpha_png uses Pillow.")
        ibg = bg if type(bg) == np.ndarray else np.array(Image.open(bg))
        ipng = png if type(png) == np.ndarray else np.array(Image.open(png))
    else:
        import matplotlib.image as mpimg
        vlog.debug("Overlay_alpha_png uses matplotlib.")
        ibg = bg if type(bg) == np.ndarray else mpimg.imread(bg)
        ipng = png if type(png) == np.ndarray else mpimg.imread(png)
    if ibg.dtype == np.float32:  # [0,1] --> [0,255]
        ibg = np.uint8(ibg*255)
    if ipng.dtype == np.float32:
        ipng = np.uint8(ipng*255)
    # offset
    if xy_offset:
        x_offset, y_offset = xy_offset
    else:
        # default center offset
        x_offset = int((ibg.shape[1] - ipng.shape[1])/2)
        y_offset = int((ibg.shape[0] - ipng.shape[0])/2)
    y1, y2 = y_offset, y_offset + ipng.shape[0]
    x1, x2 = x_offset, x_offset + ipng.shape[1]
    # alpha
    assert ipng.shape[2] == 4
    a0 = ipng[:, :, 3] / 255.0
    a1 = 1.0 - a0
    # overlay
    Nc = ibg.shape[2]  # bg jpg: 3; png: 4
    for c in range(0, Nc):
        ibg[y1:y2, x1:x2, c] = a0*ipng[:, :, c] + a1*ibg[y1:y2, x1:x2, c]
    return ibg
