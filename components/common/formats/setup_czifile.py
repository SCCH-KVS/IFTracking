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
import os
import numpy as np
from distutils.core import setup, Extension
from Cython.Distutils import build_ext

jxrlib_dir = 'jxrlib'  # directory where jxrlib was built
jpeg_dir = 'jpeg-9'
win32 = sys.platform == 'win32'
include_dirs = [jpeg_dir, np.get_include()]
include_dirs += [os.path.join(jxrlib_dir, *d.split('/')) for d in ('jxrgluelib', 'common/include', 'image/sys')]

define_macros = [('WIN32', None)] if win32 else [('INITGUID', None)]
ext = Extension('_czifile', sources=['czifile.pyx'],
                include_dirs=include_dirs, define_macros=define_macros,
                library_dirs=[jxrlib_dir, jpeg_dir],
                libraries=['jxrlib' if win32 else 'libjpegxr','jpeg'])

setup(name='_czifile', cmdclass={'build_ext': build_ext}, ext_modules=[ext])