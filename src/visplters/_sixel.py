# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Contains class to display DEC SIXEL graphics in terminal.
'''

import io
import os
import sys
import struct
import matplotlib.pyplot

from ..glogger import getGLogger
from ..utils import find_available_module, which_cmds, run_child_cmd

__all__ = ['get_imgwh', 'DisplaySIXEL']
vlog = getGLogger('V')


def get_imgwh(data):
    '''
    Read the (width, height) from a PNG/JPEG/GIF header.

    Notes
    -----
    1. Adapted from :mod:`IPython.core.display`
    2. https://en.wikipedia.org/wiki/Portable_Network_Graphics
    3. http://giflib.sourceforge.net/whatsinagif/bits_and_bytes.html

    Parameters
    ----------
    data: bytes
        entire image bytes
    '''
    assert type(data) == bytes
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        ihdr = data.index(b'IHDR')
        # next 8 bytes are width/height
        return struct.unpack('>ii', data[ihdr+4:ihdr+12])
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
        return w, h
    elif data[:6] in (b'GIF87a', b'GIF89a'):
        return struct.unpack('<HH', data[6:10])
    else:
        raise ValueError('unexpected image bytes!')


class DisplaySIXEL(object):
    '''
    Use libsixel, PySixel or imgcat to display DEC SIXEL graphics
    in terminal which support sixel graphics.

    Projects
    --------
    1. https://github.com/saitoha/libsixel
    2. https://github.com/saitoha/PySixel
    3. https://github.com/elsteveogrande/PySixel
    4. https://www.iterm2.com/documentation-images.html

    Attributes
    ----------
    sixel_bin: str or sequence of program arguments
        program can be imgcat or img2sixel
    sixel_mod: module
        SIXEL module object, libsixel or sixel
    output: output file object
        sys.stdout(default), sys.stderr or file-like object
    attty: bool
        True if the output is connected to a terminal.
    max_width: int
        max display width in pixels, default 1366
    '''
    __slots__ = ['_sixel_bin', '_sixel_mod', '_output', 'max_width']

    def __init__(self, output=sys.stdout, max_width=1366):
        self.sixel_bin = ('imgcat', 'img2sixel')
        self.sixel_mod = ('libsixel', 'sixel')
        self.output = output
        self.max_width = max_width

    def _get_sixel_bin(self):
        return self._sixel_bin

    def _set_sixel_bin(self, candidates):
        self._sixel_bin = which_cmds(*candidates)

    sixel_bin = property(_get_sixel_bin, _set_sixel_bin)

    def _get_sixel_mod(self):
        return self._sixel_mod

    def _set_sixel_mod(self, candidates):
        self._sixel_mod = find_available_module(*candidates)

    sixel_mod = property(_get_sixel_mod, _set_sixel_mod)

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

    def display(self, in_put, width=None, height=None, mod=False):
        '''
        Use :attr:`sixel_bin` command or :attr:`sixel_mod` to display.

        Parameters
        ----------
        in_put: str, bytes or Figure object
            image path, entire image bytes
            or matplotlib.figure.Figure instance
        width: int
            width of image, not for :meth:`bin_display` imgcat
        height: int
            height of image, not for :meth:`bin_display` imgcat
        mod: bool
            Use :meth:`mod_display` or :meth:`bin_display`. default False
        '''
        if isinstance(in_put, str) and os.path.isfile(in_put):
            intype = 'path'
        elif isinstance(in_put, bytes):
            intype = 'byte'
        elif isinstance(in_put, matplotlib.pyplot.Figure):
            intype = 'mplf'
        else:
            vlog.error("Invalid input, not a path, bytes, "
                       "or matplotlib.figure.Figure instance!")
            return
        try:
            if mod:
                if self.sixel_mod:
                    self._mod_display(in_put, width, height, intype)
                    self.output.flush()
                else:
                    vlog.error("Attr sixel_mod is not available! "
                               "See https://github.com/saitoha/libsixel "
                               "or https://github.com/saitoha/PySixel")
                    return
            else:
                if self.sixel_bin:
                    self._bin_display(in_put, width, height, intype)
                    self.output.flush()
                else:
                    vlog.error("Attr sixel_bin is not set! "
                               "See https://github.com/saitoha/libsixel "
                               "or https://www.iterm2.com")
                    return
        except Exception:
            vlog.error("Failed to display image!", exc_info=1)

    def _bin_display(self, in_put, width, height, intype):
        '''Use :attr:`sixel_bin` command to display.'''
        if intype == 'mplf':
            # in_put: mplf --> bytes
            ib = io.BytesIO()
            in_put.savefig(ib, format='png')
            in_put = ib.getvalue()
            intype = 'byte'
        if isinstance(self.sixel_bin, list):
            cmd = self.sixel_bin
        else:
            cmd = [self.sixel_bin]
        if cmd[0].endswith('img2sixel'):
            w = str(width) if isinstance(width, int) else 'auto'
            h = str(height) if isinstance(height, int) else 'auto'
            if isinstance(width, int) and width > self.max_width:
                vlog.debug("Resize image max width: %d -> %d"
                           % (width, self.max_width))
                w, h = str(self.max_width), 'auto'
            cmd += ['-w', w, '-h', h]
        cmdline = ' '.join(cmd)
        if intype == 'path':
            cmd += [in_put]
            vlog.info('Running command: %s' % cmdline)
            code, out, err = run_child_cmd(cmd)
        else:
            vlog.info('Running command: %s, with bytes input.' % cmdline)
            code, out, err = run_child_cmd(cmd, input=in_put)
            out = out.decode('ascii')
            err = err.decode()
        if out:
            self.output.write(out)
        else:
            vlog.error('Failed to display: (%d) %s' % (code, err))

    def _mod_display(self, in_put, width, height, intype):
        '''Use module :attr:`sixel_mod` to display.'''
        if self.sixel_mod.__name__ == 'libsixel':
            vlog.info("Use libsixel to display.")
            libsixel = self.sixel_mod
            if intype == 'mplf':
                fig = in_put
                mode = 'RGBA'
                oldsize = tuple(map(int, fig.bbox.size))
                width, height = self._resize_imgwh(oldsize, width, height)
                if (width, height) != oldsize:
                    fig.set_size_inches(width/fig.dpi, height/fig.dpi)
                    fig.canvas.draw()
                if not hasattr(fig.canvas, 'renderer'):
                    fig.canvas.draw()
                # issue, https://github.com/fastai/fastai/issues/2170
                # assert isinstance(data) == bytes
                data = fig.canvas.buffer_rgba().tobytes()
            else:
                Image = find_available_module('PIL.Image')
                if not Image:
                    vlog.error("Display in Terminal requires Pillow.")
                    return
                if intype == 'path':
                    im = Image.open(in_put)
                elif intype == 'byte':
                    im = Image.open(io.BytesIO(in_put))
                mode = im.mode
                oldsize = im.size
                if im.format == 'EPS' and im.width < self.max_width//2:
                    scale = self.max_width // im.width
                    im.load(scale=scale)
                    vlog.debug("Load vector image with enough resolution. "
                               "scale: %d, size: %s -> %s"
                               % (scale, oldsize, im.size))
                    oldsize = im.size
                width, height = self._resize_imgwh(oldsize, width, height)
                if (width, height) != oldsize:
                    im = im.resize((width, height))
                try:
                    data = im.tobytes()
                except NotImplementedError:
                    data = im.tostring()
            self._libsixel_convert(
                libsixel, data, width, height, self.output, mode=mode)
        else:
            vlog.info("Use PySixel to display.")
            sixel = self.sixel_mod
            ib = io.BytesIO()
            if intype == 'path':
                with open(in_put, 'rb') as f:
                    ib.write(f.read())
            elif intype == 'byte':
                ib.write(in_put)
            elif intype == 'mplf':
                in_put.savefig(ib, format='png')
            if bool(width) ^ bool(height):
                oldsize = get_imgwh(ib.getvalue())
                width, height = self._resize_imgwh(oldsize, width, height)
            writer = sixel.SixelWriter()
            writer.draw(ib, w=width, h=height, output=self.output)

    def _resize_imgwh(self, oldsize, width=None, height=None):
        if width and width > self.max_width:
            vlog.debug("Resize image max width: %d -> %d"
                       % (width, self.max_width))
            new_h = int(oldsize[1] * self.max_width / oldsize[0])
            return self.max_width, new_h
        if width and height:
            return width, height
        else:
            if width:
                return width, int(oldsize[1] * width / oldsize[0])
            elif height:
                return int(oldsize[0] * height / oldsize[1]), height
            else:
                return oldsize

    @staticmethod
    def _libsixel_convert(libsixel, data, w, h, output, mode):
        '''
        Convert image bytes *data* into SIXEL using libsixel python interface.

        Ref: https://github.com/saitoha/libsixel/blob/v1.8.6/examples/python/converter.py
        The *w*, *h* and *data* must match.
        Guess: *data* is not entire images, it's pixel data only,
        such as a width*height long array of RGBA values.
        '''
        ncolors = 256
        if mode == 'RGBA':
            pixelformat = libsixel.SIXEL_PIXELFORMAT_RGBA8888
        elif mode == 'RGB':
            pixelformat = libsixel.SIXEL_PIXELFORMAT_RGB888
        else:
            raise RuntimeError("unexpected image mode, not in 'RGBA', 'RGB'.")
        s = io.BytesIO()
        out = libsixel.sixel_output_new(lambda data, s: s.write(data), s)
        dither = libsixel.sixel_dither_new(ncolors)
        try:
            libsixel.sixel_dither_initialize(dither, data, w, h, pixelformat)
            libsixel.sixel_encode(data, w, h, 1, dither, out)
            output.write(s.getvalue().decode('ascii'))
        finally:
            libsixel.sixel_output_unref(out)
            libsixel.sixel_dither_unref(dither)
