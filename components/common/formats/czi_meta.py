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


import numpy as np

def czi_get_rects(czi_file):
    rect_els = czi_file.metadata.findall(".//Rectangle")
    if len(rect_els) == 0:
        return None
    rectangles = []
    try:
        for el in rect_els:
            left = float(el.find(".//Left").text)
            top = float(el.find(".//Top").text)
            width = float(el.find(".//Width").text)
            height = float(el.find(".//Height").text)
            rectangles.append((left, top, width, height))
    except:
        print "Error while parsing CZI metadata... Cannot find rectangles!"
    return rectangles


def czi_get_timestamps(czi_file):
    for a in czi_file.attachments():
        if a.attachment_entry.content_file_type == "CZTIMS":
            data = a.data()
            if data is not None:
                ndata = np.array(data)
                return ndata - ndata[0]
    return None


def czi_get_scaling(czi_file):
    s_x = czi_get_scaling_x(czi_file)
    s_y = czi_get_scaling_y(czi_file)
    if s_x is None:
        return s_y
    if s_y is None:
        return s_x
    if s_x is not None and s_y is not None and abs(s_x - s_y) < 1.0e-8:
        return s_x
    return None


def czi_get_scaling_x(czi_file):
    scaling = czi_file.metadata.findall(".//ScalingX")
    if len(scaling) > 0:
        return float(scaling[0].text)
    return None


def czi_get_scaling_y(czi_file):
    scaling = czi_file.metadata.findall(".//ScalingY")
    if len(scaling) > 0:
        return float(scaling[0].text)
    return None


def czi_get_parameters(czi_file):
    Size_X = int(czi_file.metadata.find(".//SizeX").text)
    Size_Y = int(czi_file.metadata.find(".//SizeY").text)
    Size_T = int(czi_file.metadata.find(".//SizeT").text)
    Size_C = int(czi_file.metadata.find(".//SizeC").text)
    return Size_X, Size_Y, Size_T, Size_C