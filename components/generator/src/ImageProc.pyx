from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.set cimport set
from libcpp.unordered_set cimport unordered_set
from libcpp.unordered_map cimport unordered_map
from libcpp.string cimport string
from libcpp cimport bool
from cpython cimport bool

import numpy as np
cimport numpy as np

from cpython cimport array

cdef extern from "ImageProcessing.h":

        ctypedef pair[int, int] PointInt;
        ctypedef pair[double, double] PointDouble;
        ctypedef vector[vector[int]] ImageInt;
        ctypedef vector[vector[double]] ImageDouble;
        ctypedef vector[PointInt] LineInt;
        ctypedef vector[PointDouble] LineDouble;
        ctypedef ImageInt BinaryImage;
        ctypedef vector[pair[int, unordered_map[string, PointDouble]]] NodesType;
        ctypedef set[pair[int, int]] EdgesType;

        ctypedef pair[NodesType, EdgesType] ReturnType;

        ReturnType __construct_graphs "construct_graphs" (const ImageDouble& skeleton, const ImageDouble& stable_mask);
        ImageDouble __pruneSkeleton "pruneSkeleton" (const ImageDouble& skeleton);

        vector[double] __assessPath "assessPath" (const vector[PointDouble]& path_pts, double dist, double slope_dist);

        pair[pair[NodesType, EdgesType], pair[int, int]] __preprocessGraph "preprocessGraph" (int start_id, int end_id);

        pair[int, int] __get_ids "get_ids" (const PointInt& origin_p, const PointInt& end_p);
        vector[PointInt] __graphPathToSkeleton "graphPathToSkeleton" (const vector[int]& path);

        unordered_map[int, unordered_set[int]] __getStable "getStable" ();

        void __clearGlobals "clearGlobals" ();

cpdef construct_graphs(np.ndarray[np.double_t, ndim=2] skeleton, np.ndarray[np.double_t, ndim=2] mask):
    return __construct_graphs(skeleton, mask)

cpdef assessPath(path_pts,
                 double dist,
                 double slope_dist):
    return __assessPath(path_pts, dist, slope_dist)

cpdef preprocessGraph(int start_id, int end_id):
    return __preprocessGraph(start_id, end_id)

cpdef get_ids(start_id, end_id):
    return __get_ids(start_id, end_id)

cpdef graphPathToSkeleton(path):
    return __graphPathToSkeleton(path)

cpdef getStable():
    return __getStable()

cpdef clearGlobals():
    return __clearGlobals()