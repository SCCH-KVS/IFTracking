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

if platform_name == "Windows":
    extra_args = ["/std:c++latest", "/EHsc"]
elif platform_name == "Darwin":
    extra_args = ["-std=c++11", "-mmacosx-version-min=10.9"]
elif platform_name == "Linux":
    extra_args = ["-std=c++11", "-w"]
else:
    extra_args = []


ext_modules = [Extension("fpattern", ["fpattern.pyx", "fill_pattern_.cpp"],
                         language='c++',
                         include_dirs=[numpy.get_include()],
                         extra_compile_args=extra_args,
                         define_macros=[("NPY_NO_DEPRECATED_API", None)])]

setup(cmdclass={'build_ext': build_ext}, ext_modules=cythonize(ext_modules))