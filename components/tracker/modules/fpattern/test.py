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
from fpattern import fill_pattern_coords


pattern = np.array([
    [0.5, 1.0, 0.5],
    [1.0, 1.5, 1.0],
    [0.5, 1.0, 0.5]
])


x = np.array([0, 4, 2])
y = np.array([0, 0, 1])

image_p, image_m = fill_pattern_coords(x, y, pattern, 5, 5)

print image_p
print image_m