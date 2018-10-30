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
import csv
import numpy as np
import pandas as pd

from zipfile import ZipFile
from cStringIO import StringIO
from formats.readroi import read_roi


def zip_csv(filename, data):

    with ZipFile(filename, 'w') as zipfile:
        for _i, points in enumerate(data):
            string_buffer = StringIO()
            writer = csv.writer(string_buffer)
            writer.writerows(points.tolist())
            string_buffer.flush()
            zipfile.writestr("{0:05d}.csv".format(_i+1), string_buffer.getvalue())


def unzip_csv(filename):
    try:
        with ZipFile(filename, 'r') as zipfile:
            result = []
            for filename in zipfile.namelist():
                data = zipfile.read(filename)
                data_frame = pd.read_csv(StringIO(data), header=None)
                result.append(data_frame.as_matrix())
            return result
    except:
        return None


def unzip_trajectories(filename):
    result = dict()
    try:
        with ZipFile(filename, 'r') as zipfile:
            for filename in zipfile.namelist():
                name, ext = os.path.splitext(filename)
                if ext.lower() == '.csv':
                    data = zipfile.read(filename)
                    result[name] = pd.read_csv(StringIO(data), header=None).as_matrix()
                elif ext.lower() == '.roi':
                    result[name] = read_roi(zipfile.open(filename, 'rb'))[u'polygons'][:, :2]
    finally:
        return result


def to_csv(filename, matrix):
    try:
        with open(filename, "w") as fout:
            writer = csv.writer(fout)
            writer.writerows(matrix.tolist())
    except:
        return False
    return True


def from_csv(filename):
    import pandas as pd
    df = pd.read_csv(filename)
    return df.as_matrix()


def colors_to_csv(filename, names, colors):
    try:
        with open(filename, "w") as fout:
            writer = csv.writer(fout)
            for name, color in zip(names, colors):
                writer.writerow([name] + color.tolist())
    except:
        return False
    return True


def colors_from_csv(filename):
    try:
        filenames = []
        colors = []
        with open(filename, "r") as fin:
            reader = csv.reader(fin)
            for row in reader:
                filenames.append(row[0])
                colors.append([float(row[1]), float(row[2]), float(row[3])])
        return filenames, np.asarray(colors)
    except:
        return None


# if __name__ == "__main__":
#     import numpy as np
#     data = np.random.rand(15).reshape(5, 3)
#
#     to_csv("tmp.csv", data)
#     print from_csv("tmp.csv")
#
#     # zip_csv("tmp.zip", data)
#     # unzip_csv("tmp.zip")
