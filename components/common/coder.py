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
import time
import numpy as np
import multiprocessing as mp

from functools import partial
from datetime import datetime


def encode_float(image, output_type=np.uint8):
    """
    Input is float-type image with intensity values [0, 1]
    """
    t_info = np.iinfo(output_type)
    image[image > 1.0] = 1.0

    return (image * (t_info.max - t_info.min) + t_info.min).astype(output_type)


def decode_float(image):
    """
    Converts image from current type to np.float with range [0, 1]
    """
    t_info = np.iinfo(image.dtype)
    return (image.astype(np.float) - t_info.min) / float(t_info.max - t_info.min)


def encode_angle(image_x, image_y, output_type=np.uint8):
    """
    Convert vector field to image encoding the angle of the vectors
    """
    image_angle = 0.5 * (np.arctan2(image_y, image_x) / np.pi + 1.0)
    return encode_float(image_angle, output_type)


def decode_angle(image):
    """
    Converts image to vector field
    """
    image_float = np.pi * (2.0 * decode_float(image) - 1)
    vf_x = np.cos(image_float)
    vf_y = np.sin(image_float)
    return vf_x, vf_y


def encode_magnitude(image_x, image_y, output_type=np.uint8):
    """
    Encodes the magnitude of the vector field
    """
    magnitude = np.sqrt(image_x ** 2 + image_y ** 2)
    return encode_float(magnitude, output_type)


def encode_vector_field(image_vf, output_type=np.uint8):
    """
    Convert vector field (Vx, Vy) to integer representation (Magnitude, Angle)
    """
    image_x, image_y = image_vf
    e_magnitude = encode_magnitude(image_x, image_y, output_type)
    e_angle = encode_angle(image_x, image_y, output_type)
    return e_magnitude, e_angle


def decode_vector_field(image_ma):
    """
    Convert integer field of (Magnitude, Angle) to  representation (Vx, Vy)
    """
    image_magnitude, image_angle = image_ma
    magnitude = decode_float(image_magnitude)
    vf_x, vf_y = decode_angle(image_angle)
    return vf_x * magnitude, vf_y * magnitude


class ParallelVFCoder:

    def __init__(self, processor_num=None):
        if processor_num is None or processor_num == 0:
            self.processor_num = mp.cpu_count()
        else:
            self.processor_num = processor_num

    def encode(self, vf_data, out_type=np.uint8):
        time_start = datetime.now()
        # set function
        encode_func = partial(encode_vector_field, output_type=out_type)
        # make a pool of processes
        pool = mp.Pool(processes=self.processor_num)
        pool_result = pool.map_async(encode_func, vf_data)
        pool.close()
        # update status
        while not pool_result.ready():
            time_passed = datetime.now() - time_start
            sys.stdout.write('\r Remaining jobs: {0} Time: {1}'.format(pool_result._number_left, time_passed))
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write('\r Encoding is finished. Time: {0}\n'.format(datetime.now() - time_start))
        return pool_result.get()

    def decode(self, data):
        time_start = datetime.now()
        # make pool of processes
        pool = mp.Pool(processes=self.processor_num)
        pool_result = pool.map_async(decode_vector_field, data)
        pool.close()
        # update status
        while not pool_result.ready():
            time_passed = datetime.now() - time_start
            sys.stdout.write('\r Remaining jobs: {0} Time: {1}'.format(pool_result._number_left, time_passed))
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write('\r Decoding is finished. Time: {0}\n'.format(datetime.now() - time_start))
        return pool_result.get()


class ParallelMap:

    def __init__(self, processor_num=None):
        if processor_num is None or processor_num == 0:
            self.processor_num = mp.cpu_count()
        else:
            self.processor_num = processor_num

    def map(self, function, data):
        time_start = datetime.now()
        # make a pool of processes
        pool = mp.Pool(processes=self.processor_num)
        pool_result = pool.map_async(function, data)
        pool.close()
        # update status
        while not pool_result.ready():
            time_passed = datetime.now() - time_start
            sys.stdout.write('\r Remaining jobs: {0} Time: {1}'.format(pool_result._number_left, time_passed))
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write('\r Mapping is finished. Time: {0}\n'.format(datetime.now() - time_start))
        return np.asarray(pool_result.get())


global _output


def _init_output(data):
    global _output
    _output = data


class ParallelApply:

    def __init__(self, processor_num=None):
        if processor_num is None or processor_num == 0:
            self.processor_num = mp.cpu_count()
        else:
            self.processor_num = processor_num

    def map(self, input, output, func):
        time_start = datetime.now()
        # make a pool of processes
        pool = mp.Pool(processes=self.processor_num, initializer=_init_output, initargs=(output,))
        pool_result = pool.apply_async(func, input)
        pool.close()
        # update status
        while not pool_result.ready():
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write('\r Mapping is finished. Time: {0}\n'.format(datetime.now() - time_start))


if __name__ == '__main__':

    vf_x = np.asarray([
        [0.1, 0.1, 0.1, 0.1, 0.1],
        [0.1, 0.5, 1.0, 0.5, 0.1],
        [0.1,-0.5,-1.0,-0.5, 0.1],
        [0.1, 0.1, 0.1, 0.1, 0.1],
    ])

    vf_y = np.asarray([
        [0.1, 0.5, 0.1, -0.5, 0.1],
        [0.1, 1.0, 0.1, -1.0, 0.1],
        [0.1, 0.5, 0.1, -0.5, 0.1],
        [0.1, 1.0, 0.1, -1.0, 0.1],
    ])

    vf_m = np.sqrt(vf_x ** 2 + vf_y ** 2)
    vf_x /= vf_m
    vf_y /= vf_m

    encoded = encode_angle(vf_x, vf_y)
    print encoded

    d_x, d_y = decode_angle(encoded)
    print d_x
    print d_y

    print (d_x - vf_x).max(), (d_y - vf_y).max()