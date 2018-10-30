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

from distutils.core import setup, Extension
import numpy

setup(name='_tifffile',
      ext_modules=[Extension('_tifffile', ['tifffile.c'],
                             include_dirs=[numpy.get_include()])])