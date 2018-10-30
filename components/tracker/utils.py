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


import numpy as np
import multiprocessing as mp


class ImageSequence(object):
    def __init__(self):
        pass


def make_shared(npy_array):
    ct = np.ctypeslib.as_ctypes(npy_array.ravel())
    data_size = np.asarray(npy_array.shape).prod()
    shared_memory = mp.Array(ct._type_, long(data_size), lock=False)
    shared_memory[:] = npy_array.ravel()[:]
    return shared_memory


def to_shared_memory(data_dictionary):
    shared_dictionary = dict()
    for key, data in data_dictionary.items():
        meta, arr = data
        if meta == 'i':
            shared_dictionary[key] = (meta, make_shared(arr), arr.shape, str(arr.dtype))
        elif meta == 'p':
            data_sizes = np.asarray([len(a) for a in arr])
            data_stack = np.vstack(arr)
            shared_dictionary[key] = (meta, make_shared(data_stack), make_shared(data_sizes), str(data_stack.dtype))
    return shared_dictionary


def pack_shared_memory(dictionary):
    package = []
    for key, value in dictionary.items():
        package.append(key)
        package.append(value[0])
        package.append(value[1])
        package.append(value[2])
        package.append(value[3])
    return package


def unpack_values(package):
    keys = package[::5]
    meta = package[1::5]
    arrays = package[2::5]
    shapes = package[3::5]
    types = package[4::5]
    # Make a dictionary
    data = dict()
    for k, m, a, s, t in zip(keys, meta, arrays, shapes, types):
        buffer_ = np.frombuffer(a, t)
        if m == 'i':
            data[k] = (m, buffer_.reshape(s))
        elif m == 'p':
            shapes_ = np.frombuffer(s, dtype=np.int)
            offsets_ = np.concatenate([[0], np.cumsum(shapes_)])
            unpacked = []
            for i in xrange(len(shapes_)):
                idx_s, idx_e = 2 * offsets_[i], 2 * offsets_[i+1]
                unpacked.append(buffer_[idx_s:idx_e].reshape(shapes_[i], 2))
            data[k] = (m, np.asarray(unpacked))
    # Return data
    return data


def to_image_sequence(dictionary):
    result = ImageSequence()
    for key, attrib in dictionary.items():
        meta, data = attrib
        setattr(result, key, data)
    return result


if __name__ == '__main__':

    coords = [np.random.rand(6, 2), np.random.rand(10, 2), np.random.rand(7, 2)]

    data = {
        'coords': ('p', coords),
        'images': ('i', np.random.rand(10, 1024, 1024))
    }

    import sys
    from datetime import datetime

    # convert to shared memory
    time_start = datetime.now()
    data_shared = to_shared_memory(data)
    print "Time elapsed:", datetime.now() - time_start
    sys.stdout.flush()

    time_start = datetime.now()
    package = pack_shared_memory(data_shared)
    print "Time elapsed:", datetime.now() - time_start
    sys.stdout.flush()

    time_start = datetime.now()
    data = unpack_values(package)
    print "Time elapsed:", datetime.now() - time_start
    sys.stdout.flush()
