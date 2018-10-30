#!/usr/bin/env python
#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
# 
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created on: 19/09/16 12:59
# by:  Dmytro Kotsur
#

import struct
import numpy as np
import tifffile as tiff


LSM_TAG_MAPPING = {item[0] : index for index, item in enumerate(tiff.CZ_LSM_INFO)}


def lsm_getinfo(tiff_file):
    for page in tiff_file:
        if "cz_lsm_info" in page.tags:
            return page.tags["cz_lsm_info"]
    return None


def lsm_gettag(info, tag_name):
    return info.value[LSM_TAG_MAPPING[tag_name]]


def lsm_getparameters(info):
    channels = lsm_gettag(info, 'dimension_channels')
    frame_n = lsm_gettag(info, 'dimension_time')
    width = lsm_gettag(info, 'dimension_x')
    height = lsm_gettag(info, 'dimension_y')
    return width, height, frame_n, channels


def lsm_read_rect(filename, data):
    """
    @param filename - Name of the file
    @param data - Offset in bytes from file beginning

    For reference:
       https://searchcode.com/codesearch/view/15643779/
    """
    with open(filename, "rb") as f:
        f.seek(data, 0)
        nde = struct.unpack('i', f.read(4))[0]
        if nde == 0:
            return None
        size = struct.unpack('i', f.read(4))[0]
        f.seek(20, 1)
        is_valid = struct.unpack('i', f.read(4))[0]
        if is_valid == 0:
            return None
        f.seek(164, 1)
        struct_type = struct.unpack('i', f.read(4))[0]
        if struct_type != 18: # Is the structure rectangle ?
            return None
        f.seek(204, 1)
        # read top left corner
        x1 = struct.unpack('d', f.read(8))[0]
        y1 = struct.unpack('d', f.read(8))[0]
        # read bottom right corner
        x2 = struct.unpack('d', f.read(8))[0]
        y2 = struct.unpack('d', f.read(8))[0]
        return min(x1, x2), min(y1, y2), abs( x1 -x2), abs( y1 -y2)


def lsm_read_timestamps(filename, data):
    with open(filename, "rb") as f:
        f.seek(data, 0)
        size = struct.unpack('i', f.read(4))[0]
        number = struct.unpack('i', f.read(4))[0]
        time_stamps = np.zeros(number, dtype=np.float64)
        for i in xrange(number):
            time_stamps[i] = struct.unpack('d', f.read(8))[0]
    return time_stamps - time_stamps[0]