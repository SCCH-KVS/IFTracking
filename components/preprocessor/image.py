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

import sys
sys.path.append('../common')

import time
import datetime

import numpy as np
import platform
import multiprocessing as mp

from skimage.external.tifffile import imread
from modules.proc_v1_0 import proc_image


def load(filename):
    """
    Read TIFF file.
    """
    return imread(filename)


class ImageData:

    def __init__(self, data=None):
        if data is None:
            self.data = dict()
        else:
            self.data = data

    def update(self, data):
        self.data.update(data)

    def __getitem__(self, item):
        return self.data[item]


class Processor:
    def __init__(self, module, config):
        self.module = module
        self.config = config

    def process(self, image):
        # rescale image
        curr_image = image.astype(np.double) / image.max()
        # process image
        return proc_image(curr_image, self.config)


ImageProc_Config = None


if platform.system() == 'Windows':
    def Init_Pool(config):
        global ImageProc_Config
        ImageProc_Config = config
        

def Process_Image(image):
    # rescale image
    curr_image = image.astype(np.double) / image.max()
    # process image
    global ImageProc_Config
    if ImageProc_Config is None:
        print "\n No configuration file.\n"
    return proc_image(curr_image, ImageProc_Config)


class ImageSequence:

    def __init__(self, filename):
        self.filename = filename

        # Load images
        self.images = load(filename)

        # Initialize image data
        self.image_data = [ImageData() for _ in xrange(len(self.images))]

        # Set frame number
        self.frame_n = len(self.images)

    def apply(self, configs):
        # Define global variables
        global ImageProc_Config
        
        ImageProc_Config = configs

        if configs["Parallel Computing"]["enabled_b"]:

            # Get maximal number of processors
            num_cores = configs["Parallel Computing"]["processors_number_i"]
            if num_cores <= 0:
                num_cores = mp.cpu_count()

            time_start = datetime.datetime.now()
            print "Starting parallel processing on {0} cores: {1}".format(num_cores, time_start)

            # Start parallel processing
            if platform.system() == "Windows":
                pool = mp.Pool(num_cores, initializer=Init_Pool, initargs=(configs, ))
            else:
                pool = mp.Pool(num_cores)
            pool_status = pool.map_async(Process_Image, self.images)
            pool.close()

            # Check job status
            while not pool_status.ready():
                time_now = datetime.datetime.now()
                sys.stdout.write('\r Remaining images: {0} | {1}'.format(pool_status._number_left, time_now - time_start))
                sys.stdout.flush()
                time.sleep(0.1)

            results = pool_status.get()

            # Update image sequence data
            for i in xrange(self.frame_n):
                self.image_data[i].update(results[i])

            time_end = datetime.datetime.now()
            print "\rProcessing is finished: {0}. Total time: {1}".format(time_end, time_end-time_start)

        else:
            time_start = datetime.datetime.now()
            print "Start processing: {0}".format(time_start)

            for image_i in xrange(self.frame_n):
                # Print current frame index
                sys.stdout.write("Processing frame {0} of {1}: {2}\n".format(image_i, self.frame_n, datetime.datetime.now() - time_start))
                # Process image and initialize data item
                self.image_data[image_i].update(Process_Image(self.images[image_i]))

            time_end = datetime.datetime.now()
            print "\rProcessing is finished: {0}. Total time: {1}".format(time_end, time_end-time_start)

    def __getitem__(self, key):
        return self.image_data[key]

    def shape(self):
        return self.images.shape

    def width(self):
        return self.images[0].shape[1]

    def height(self):
        return self.images[0].shape[0]


if __name__ == "__main__":

    import os
    import matplotlib.pyplot as plt

    IMAGE_SEQUENCE_PATH = r'/Users/dkotssur/Projects/InCeM/Data/Keratin_Tracking/'

    image_sequence = ImageSequence(os.path.join(IMAGE_SEQUENCE_PATH, "MZ_OL_0320_1", "MZ_OL_0320_1.tif"))
    image_sequence.apply("modules.proc_v1_0")

    plt.figure()
    plt.imshow(image_sequence[0].enhanced_image, cmap="gray")
    plt.show()

