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
import re
import numpy as np


def get_latest_folder(path):
    reg_exp = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}[0-9A-Fa-f_]*"
    filter_func = lambda fn: os.path.isdir(os.path.join(path, fn)) and re.match(reg_exp, fn) is not None
    return sorted(filter(filter_func, os.listdir(path)))[-1]


def tyx_to_tzcyx(data, dtype=np.uint8, scale=255):
    return np.expand_dims(np.expand_dims((data * scale).astype(dtype), axis=1), axis=1)