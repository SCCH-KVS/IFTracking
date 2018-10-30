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

import platform
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

import numpy

platform_name = platform.system()

print "Compiling for platform:", platform_name

link_extra_args = []
compile_extra_args = []

if platform_name == "Darwin":
    compile_extra_args = ["-std=c++11", "-mmacosx-version-min=10.9"]
    link_extra_args = ["-stdlib=libc++", "-mmacosx-version-min=10.9"]
elif platform_name == "Windows":
    compile_extra_args = ["-std=c++11"]
elif platform_name == "Linux":
    compile_extra_args = ["-std=c++11", "-w"]

ext_modules = [Extension("ImageProc", ["ImageProc.pyx", "ImageProcessing.cpp"],
                         language='c++',
                         include_dirs=[numpy.get_include()],
                         extra_compile_args=compile_extra_args,
                         extra_link_args=link_extra_args,
                         define_macros=[("NPY_NO_DEPRECATED_API", None)])]

setup(cmdclass={'build_ext': build_ext}, ext_modules=cythonize(ext_modules))
