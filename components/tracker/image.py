#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created by: Dmytro Kotsur
#

import os
import sys
import numpy as np

# Add common scripts
sys.path.append('../common')

from skimage.external.tifffile import imread
from zip import unzip_csv

########################################################################################################################


class ImageSequence(object):

    def __init__(self):
        pass

    @staticmethod
    def load(path, filenames):
        data = dict()
        data_meta = dict()
        for filename in filenames:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                name, ext = os.path.splitext(filename)
                print " Loading:", full_path
                if ext.lower() == '.zip':
                    values = unzip_csv(full_path)
                    if values is None:
                        print " Oh no.... It's empty:", full_path
                    else:
                        data[name] = ('p', values)
                elif ext.lower() in ['.tif', '.tiff']:
                    images = np.squeeze(imread(full_path))
                    if len(images) == 0:
                        print " Oh no.... It's empty:", full_path
                    else:
                        data[name] = ('i', images)
        return data

########################################################################################################################


from skimage.morphology import medial_axis, dilation, disk
from skimage.exposure import rescale_intensity


########################################################################################################################
#
# The following functions are for image transformations/converting
#
########################################################################################################################

def rescale(image):
    return rescale_intensity(image.astype(np.double))


def transform_binary(image):
    return dilation(image > 0, disk(3)).astype(np.uint8)


def transform_distance(image):
    return medial_axis(image == 0, return_distance=True)[1].astype(np.double)
