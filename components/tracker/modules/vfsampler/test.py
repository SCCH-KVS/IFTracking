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
sys.path.append("..")

import timeit
import functools
import numpy as np
from vfsampler import sample_vf as cpp_sample_vf
from skimage.filters import gaussian
from skimage.exposure import rescale_intensity

import matplotlib.pyplot as plt

from snakes import sample_vf as python_sample_vf

vf_x = np.array([
    [0.0, 1.0, 1.0, 0.0],
    [0.0, 2.0, 2.0, 0.0],
    [0.0, 2.0, 2.0, 0.0],
    [0.0, 1.0, 1.0, 0.0]
])

vf_y = np.array([
    [0.0, 0.0, 0.0, 0.0],
    [1.0, 2.0, 2.0, 1.0],
    [1.0, 2.0, 2.0, 1.0],
    [0.0, 0.0, 0.0, 0.0]
])

points = np.array([[0.5, 0.0], [0.5, 0.5], [1.5, 1.5], [0.5, 1.0]])

cpp_result = cpp_sample_vf(vf_x, vf_y, points)
print "C++ result:"
print cpp_result, "\n"

python_result = python_sample_vf(vf_x, vf_y, points)
print "Python result:"
print python_result, "\n"

print "Error (L-infinity): ", np.abs((cpp_result - python_result)).max()

image_w, image_h, points_n = 1024, 1024, 1000

vf_x = rescale_intensity(gaussian(np.random.rand(image_h, image_w) * 65535, 10.0))
vf_y = rescale_intensity(gaussian(np.random.rand(image_h, image_w) * 65535, 10.0))
points = np.hstack([np.random.rand(points_n, 1) * (image_w - 1), np.random.rand(points_n, 1) * (image_h - 1)])

vf_vis = plt.figure()
ax1 = vf_vis.add_subplot(121)
ax1.plot(points[:,0], points[:,1], 'ko')
ax1.imshow(vf_x)

ax2 = vf_vis.add_subplot(122)
ax2.plot(points[:,0], points[:,1], 'ko')
ax2.imshow(vf_y)


points_nn = 2 ** np.arange(2, 10)
python_time = np.zeros_like(points_nn, dtype=np.float)
cpp_time = np.zeros_like(points_nn, dtype=np.float)

for i, points_n in enumerate(points_nn):
    points = np.hstack([np.random.rand(points_n, 1) * (image_w - 1), np.random.rand(points_n, 1) * (image_h - 1)])

    error = np.abs(python_sample_vf(vf_x, vf_y, points) - cpp_sample_vf(vf_x, vf_y, points)).max()

    t_python = timeit.Timer(functools.partial(python_sample_vf, vf_x, vf_y, points))
    python_time[i] = t_python.timeit(5)

    t_cpp = timeit.Timer(functools.partial(cpp_sample_vf, vf_x, vf_y, points))
    cpp_time[i] = t_cpp.timeit(5)

    print "Points_N: {0}, Python_Time: {1}, Cpp_Time: {2}, Error: {3}".format(points_n, python_time[i], cpp_time[i], error)


plt.figure()
plt.plot(points_nn, python_time, 'o-', label="Python")
plt.plot(points_nn, cpp_time, 'o-', label="C++")
plt.legend()

plt.show()
