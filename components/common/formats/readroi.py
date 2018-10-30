from __future__ import division
from __future__ import unicode_literals
# from builtins import str
# from builtins import range
# Copyright: Luis Pedro Coelho <luis@luispedro.org>, 2012
# License: MIT
#
# https://gist.github.com/luispedro/3437255
#
# Modified 2014 by Jeffrey Zaremba.

import numpy as np
from itertools import product
import zipfile


def read_imagej_roi_zip(filename):
    """Reads an ImageJ ROI zip set and parses each ROI individually
    Parameters
    ----------
    filename : string
        Path to the ImageJ ROis zip file
    Returns
    -------
    roi_list : list
        List of the parsed ImageJ ROIs
    """
    roi_list = []
    with zipfile.ZipFile(filename) as zf:
        for name in zf.namelist():
            roi = read_roi(zf.open(name))
            if roi is None:
                continue
            roi['label'] = str(name).rstrip('.roi')
            roi_list.append(roi)
        return roi_list


def read_roi(roi_obj):
    """Parses an individual ImageJ ROI
    _getX lines with no assignment are bytes within the imageJ roi file
    format that contain additional information that can be extracted if
    needed. In line comments label what they are.
    This is based on:
    http://rsbweb.nih.gov/ij/developer/source/ij/io/RoiDecoder.java.html
    http://rsbweb.nih.gov/ij/developer/source/ij/io/RoiEncoder.java.html
    Parameters
    ----------
    roi_obj : file object
        File object containing a single ImageJ ROI
    Returns
    -------
    ROI
        Returns a parsed ROI object (dictionary)
    Raises
    ------
    IOError
        If there is an error reading the roi file object
    ValueError
        If unable to parse ROI
    """

    sub_pixel_resolution = 128

    # Other options that are not currently used
    # SPLINE_FIT = 1
    # DOUBLE_HEADED = 2
    # OUTLINE = 4
    # OVERLAY_LABELS = 8
    # OVERLAY_NAMES = 16
    # OVERLAY_BACKGROUNDS = 32
    # OVERLAY_BOLD = 64
    # DRAW_OFFSET = 256

    pos = [4]

    def _get8():
        """Read 1 byte from the roi file object"""
        pos[0] += 1
        s = roi_obj.read(1)
        if not s:
            raise IOError('read_imagej_roi: Unexpected EOF')
        return ord(s)

    def _get16():
        """Read 2 bytes from the roi file object"""
        b0 = _get8()
        b1 = _get8()
        return (b0 << 8) | b1

    def _get32():
        """Read 4 bytes from the roi file object"""
        s0 = _get16()
        s1 = _get16()
        return (s0 << 16) | s1

    def _getfloat():
        """Read a float from the roi file object"""
        v = np.int32(_get32())
        return v.view(np.float32)

    def _getcoords(z=0):
        """Get the next coordinate of an roi polygon"""
        if options & sub_pixel_resolution:
            getc = _getfloat
            points = np.empty((n_coordinates, 3), dtype=np.float32)
        else:
            getc = _get16
            points = np.empty((n_coordinates, 3), dtype=np.int16)
        points[:, 0] = [getc() for _ in range(n_coordinates)]
        points[:, 1] = [getc() for _ in range(n_coordinates)]
        points[:, 0] += left
        points[:, 1] += top
        points[:, 2] = z
        return points

    magic = roi_obj.read(4)
    if magic != b'Iout':
        raise IOError('read_imagej_roi: Magic number not found')

    _get16()  # version

    roi_type = _get8()
    # Discard extra second Byte:
    _get8()

    if not (0 <= roi_type < 11):
        raise ValueError('read_imagej_roi: \
                          ROI type {} not supported'.format(roi_type))

    top = _get16()
    left = _get16()
    bottom = _get16()
    right = _get16()
    n_coordinates = _get16()

    x1 = _getfloat()  # x1
    y1 = _getfloat()  # y1
    x2 = _getfloat()  # x2
    y2 = _getfloat()  # y2
    _get16()  # stroke width
    _get32()  # shape roi size
    _get32()  # stroke color
    _get32()  # fill color
    subtype = _get16()
    if subtype != 0:
        raise ValueError('read_imagej_roi: \
                          ROI subtype {} not supported (!= 0)'.format(subtype))
    options = _get16()
    _get8()  # arrow style
    _get8()  # arrow head size
    _get16()  # rectangle arc size
    z = _get32()  # position
    if z > 0:
        z -= 1  # Multi-plane images start indexing at 1 instead of 0
    _get32()  # header 2 offset

    if roi_type == 0:
        # Polygon
        coords = _getcoords(z)
        coords = coords.astype('float')
        return {'polygons': coords}
    elif roi_type == 1:
        # Rectangle
        coords = [[left, top, z], [right, top, z], [right, bottom, z],
                  [left, bottom, z]]
        coords = np.array(coords).astype('float')
        return {'polygons': coords}
    elif roi_type == 2:
        # Oval
        width = right - left
        height = bottom - top

        # 0.5 moves the mid point to the center of the pixel
        x_mid = (right + left) / 2.0 - 0.5
        y_mid = (top + bottom) / 2.0 - 0.5
        mask = np.zeros((z + 1, bottom, right), dtype=bool)
        for y, x in product(np.arange(top, bottom), np.arange(left, right)):
            mask[z, y, x] = ((x - x_mid) ** 2 / (width / 2.0) ** 2 +
                             (y - y_mid) ** 2 / (height / 2.0) ** 2 <= 1)
        return {'mask': mask}
    elif roi_type == 3:
        # Line
        coords = [[x1, y1, z], [x2, y2, z]]
        coords = np.array(coords).astype('float')
        return {'polygons': coords}
    elif roi_type == 7:
        # Freehand
        coords = _getcoords(z)
        coords = coords.astype('float')
        return {'polygons': coords}
    else:
        try:
            coords = _getcoords(z)
            coords = coords.astype('float')
            return {'polygons': coords}
        except:
            raise ValueError(
                'read_imagej_roi: ROI type {} not supported'.format(roi_type))

# import os
# import struct
# import zipfile
#
# __all__ = ['read_roi_file', 'read_roi_zip']
#
#
# OFFSET = dict(VERSION_OFFSET=4,
#               TYPE=6,
#               TOP=8,
#               LEFT=10,
#               BOTTOM=12,
#               RIGHT=14,
#               N_COORDINATES=16,
#               X1=18,
#               Y1=22,
#               X2=26,
#               Y2=30,
#               XD=18,
#               YD=22,
#               WIDTHD=26,
#               HEIGHTD=30,
#               STROKE_WIDTH=34,
#               SHAPE_ROI_SIZE=36,
#               STROKE_COLOR=40,
#               FILL_COLOR=44,
#               SUBTYPE=48,
#               OPTIONS=50,
#               ARROW_STYLE=52,
#               ELLIPSE_ASPECT_RATIO=52,
#               ARROW_HEAD_SIZE=53,
#               ROUNDED_RECT_ARC_SIZE=54,
#               POSITION=56,
#               HEADER2_OFFSET=60,
#               COORDINATES=64)
#
# ROI_TYPE = dict(polygon=0,
#                 rect=1,
#                 oval=2,
#                 line=3,
#                 freeline=4,
#                 polyline=5,
#                 noRoi=6,
#                 freehand=7,
#                 traced=8,
#                 angle=9,
#                 point=10)
#
# OPTIONS = dict(SPLINE_FIT=1,
#                DOUBLE_HEADED=2,
#                OUTLINE=4,
#                OVERLAY_LABELS=8,
#                OVERLAY_NAMES=16,
#                OVERLAY_BACKGROUNDS=32,
#                OVERLAY_BOLD=64,
#                SUB_PIXEL_RESOLUTION=128,
#                DRAW_OFFSET=256)
#
# HEADER_OFFSET = dict(C_POSITION=4,
#                      Z_POSITION=8,
#                      T_POSITION=12,
#                      NAME_OFFSET=16,
#                      NAME_LENGTH=20,
#                      OVERLAY_LABEL_COLOR=24,
#                      OVERLAY_FONT_SIZE=28,
#                      AVAILABLE_BYTE1=30,
#                      IMAGE_OPACITY=31,
#                      IMAGE_SIZE=32,
#                      FLOAT_STROKE_WIDTH=36)
#
# SUBTYPES = dict(TEXT=1,
#                 ARROW=2,
#                 ELLIPSE=3,
#                 IMAGE=4)
#
#
# def get_byte(data, base):
#     if isinstance(base, int):
#         return data[base]
#     elif isinstance(base, list):
#         return [data[b] for b in base]
#
#
# def get_short(data, base):
#     b0 = data[base]
#     b1 = data[base + 1]
#     n = (b0 << 8) + b1
#     return n
#
#
# def get_int(data, base):
#     b0 = data[base]
#     b1 = data[base + 1]
#     b2 = data[base + 2]
#     b3 = data[base + 3]
#     n = ((b0 << 24) + (b1 << 16) + (b2 << 8) + b3)
#     return n
#
#
# def get_float(data, base):
#     return float(get_int(data, base))
#
#
# def read_roi(data):
#     """
#     """
#
#     # if isinstance(fpath, zipfile.ZipExtFile):
#     #     data = fpath.read()
#     #     name = os.path.splitext(os.path.basename(fpath.name))[0]
#     # elif isinstance(fpath, str):
#     #     fp = open(fpath, 'rb')
#     #     data = fp.read()
#     #     fp.close()
#     #     name = os.path.splitext(os.path.basename(fpath))[0]
#     # el:
#     #     # raise an error
#     #     return None
#
#     size = len(data)
#     code = '>'
#
#     roi = {}
#
#     magic = get_byte(data, list(range(4)))
#     magic = "".join([chr(c) for c in magic])
#
#     # TODO: raise error if magic != 'Iout'
#
#     version = get_short(data, OFFSET['VERSION_OFFSET'])
#     type = get_byte(data, OFFSET['TYPE'])
#     subtype = get_short(data, OFFSET['SUBTYPE'])
#     top = get_short(data, OFFSET['TOP'])
#     left = get_short(data, OFFSET['LEFT'])
#
#     if top > 6000:
#         top -= 2**16
#     if left > 6000:
#         left -= 2**16
#
#     bottom = get_short(data, OFFSET['BOTTOM'])
#     right = get_short(data, OFFSET['RIGHT'])
#     width = right - left
#     height = bottom - top
#     n = get_short(data, OFFSET['N_COORDINATES'])
#     options = get_short(data, OFFSET['OPTIONS'])
#     position = get_int(data, OFFSET['POSITION'])
#     hdr2Offset = get_int(data, OFFSET['HEADER2_OFFSET'])
#
#     sub_pixel_resolution = (options == OPTIONS['SUB_PIXEL_RESOLUTION']) and version >= 222
#     draw_offset = sub_pixel_resolution and (options == OPTIONS['DRAW_OFFSET'])
#     # sub_pixel_rect = version >= 223 and sub_pixel_resolution and (type == ROI_TYPE['rect'] or type == ROI_TYPE['oval'])
#     #
#     # # Untested
#     # if sub_pixel_rect:
#     #     packed_data = fp.read(16)
#     #     s = struct.Struct(code + '4f')
#     #     xd, yd, widthd, heightd = s.unpack(packed_data)
#
#     # # Untested
#     # if hdr2Offset > 0 and hdr2Offset + HEADER_OFFSET['IMAGE_SIZE'] + 4 <= size:
#     #     channel = get_int(data, hdr2Offset + HEADER_OFFSET['C_POSITION'])
#     #     slice = get_int(data, hdr2Offset + HEADER_OFFSET['Z_POSITION'])
#     #     frame = get_int(data, hdr2Offset + HEADER_OFFSET['T_POSITION'])
#     #     overlayLabelColor = get_int(data, hdr2Offset + HEADER_OFFSET['OVERLAY_LABEL_COLOR'])
#     #     overlayFontSize = get_short(data, hdr2Offset + HEADER_OFFSET['OVERLAY_FONT_SIZE'])
#     #     imageOpacity = get_byte(data, hdr2Offset + HEADER_OFFSET['IMAGE_OPACITY'])
#     #     imageSize = get_int(data, hdr2Offset + HEADER_OFFSET['IMAGE_SIZE'])
#
#     # is_composite = get_int(data, OFFSET['SHAPE_ROI_SIZE']) > 0
#     #
#     # # Not implemented
#     # if is_composite:
#     #     if version >= 218:
#     #         # Not implemented
#     #         pass
#     #     if channel > 0 or slice > 0 or frame > 0:
#     #         pass
#
#     # if type == ROI_TYPE['rect']:
#     #     roi = {'type': 'rectangle'}
#     #
#     #     if sub_pixel_rect:
#     #         roi.update(dict(left=xd, top=yd, width=widthd, height=heightd))
#     #     else:
#     #         roi.update(dict(left=left, top=top, width=width, height=height))
#     #
#     #     roi['arc_size'] = get_short(data, OFFSET['ROUNDED_RECT_ARC_SIZE'])
#     #
#     # elif type == ROI_TYPE['oval']:
#     #     roi = {'type': 'oval'}
#     #
#     #     if sub_pixel_rect:
#     #         roi.update(dict(left=xd, top=yd, width=widthd, height=heightd))
#     #     else:
#     #         roi.update(dict(left=left, top=top, width=width, height=height))
#
#     if type == ROI_TYPE['line']:
#         roi = {'type': 'line'}
#
#         x1 = get_float(data, OFFSET['X1'])
#         y1 = get_float(data, OFFSET['Y1'])
#         x2 = get_float(data, OFFSET['X2'])
#         y2 = get_float(data, OFFSET['Y2'])
#
#         if subtype == SUBTYPES['ARROW']:
#             # Not implemented
#             pass
#         else:
#             roi.update(dict(x1=x1, x2=x2, y1=y1, y2=y2))
#             roi['draw_offset'] = draw_offset
#
#     elif type in [ROI_TYPE[t] for t in ["polygon", "freehand", "traced", "polyline", "freeline", "angle", "point"]]:
#         x = []
#         y = []
#         base1 = OFFSET['COORDINATES']
#         base2 = base1 + 2 * n
#         for i in range(n):
#             xtmp = get_short(data, base1 + i * 2)
#             if xtmp < 0:
#                 xtmp = 0
#             ytmp = get_short(data, base2 + i * 2)
#             if ytmp < 0:
#                 ytmp = 0
#             x.append(left + xtmp)
#             y.append(top + ytmp)
#
#         if sub_pixel_resolution:
#             xf = []
#             yf = []
#             base1 = OFFSET['COORDINATES'] + 4 * n
#             base2 = base1 + 4 * n
#             for i in range(n):
#                 xf.append(get_float(data, base1 + i * 4))
#                 yf.append(get_float(data, base2 + i * 4))
#
#         if type == ROI_TYPE['point']:
#             roi = {'type': 'point'}
#
#             if sub_pixel_resolution:
#                 roi.update(dict(x=xf, y=yf, n=n))
#             else:
#                 roi.update(dict(x=x, y=y, n=n))
#
#         if type == ROI_TYPE['polygon']:
#             roi = {'type': 'polygon'}
#         elif type == ROI_TYPE['freehand']:
#             roi = {'type': 'freehand'}
#             if subtype == SUBTYPES['ELLIPSE']:
#                 ex1 = get_float(data, OFFSET['X1'])
#                 ey1 = get_float(data, OFFSET['Y1'])
#                 ex2 = get_float(data, OFFSET['X2'])
#                 ey2 = get_float(data, OFFSET['Y2'])
#                 roi['aspect_ratio'] = get_float(data, OFFSET['ELLIPSE_ASPECT_RATIO'])
#                 roi.update(dict(ex1=ex1, ey1=ey1, ex2=ex2, ey2=ey2))
#
#         elif type == ROI_TYPE['traced']:
#             roi = {'type': 'traced'}
#         elif type == ROI_TYPE['polyline']:
#             roi = {'type': 'polyline'}
#         elif type == ROI_TYPE['freeline']:
#             roi = {'type': 'freeline'}
#         elif type == ROI_TYPE['angle']:
#             roi = {'type': 'angle'}
#         else:
#             roi = {'type': 'freeroi'}
#
#         if sub_pixel_resolution:
#             roi.update(dict(x=xf, y=yf, n=n))
#         else:
#             roi.update(dict(x=x, y=y, n=n))
#     else:
#         # TODO: raise an error for 'Unrecognized ROI type'
#         pass
#
#     if version >= 218:
#         # Not implemented
#         # Read stroke width, stroke color and fill color
#         pass
#
#     if version >= 218 and subtype == SUBTYPES['TEXT']:
#         # Not implemented
#         # Read test ROI
#         pass
#
#     if version >= 218 and subtype == SUBTYPES['IMAGE']:
#         # Not implemented
#         # Get image ROI
#         pass
#
#     roi['position'] = position
#     # if channel > 0 or slice > 0 or frame > 0:
#     #     roi['position'] = dict(channel=channel, slice=slice, frame=frame)
#
#     return roi
