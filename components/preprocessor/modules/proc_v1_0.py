#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created
# by: Dmytro Kotsur
#

import sys
sys.path.append("..")
sys.path.append("../..")

import mahotas as mh
import numpy as np
from scipy.misc import imresize
from skimage import exposure, measure
from skimage.feature import hessian_matrix, hessian_matrix_eigvals
from skimage.morphology import remove_small_objects, remove_small_holes, skeletonize

from tracker.modules.snakes import compute_gvf

INTENSITY_SCALE = 5.0
INTENSITY_THRESHOLD_MIN = 0.05
INTENSITY_THRESHOLD_MAX = 1.1


def branchedPoints(skel):
    # cross X
    X0 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    X1 = np.array([[1, 0, 1], [0, 1, 0], [1, 0, 1]])
    X = [X0, X1]
    # T like
    # T0 contains X0
    T0 = np.array([[2, 1, 2], [1, 1, 1], [2, 2, 2]])
    T1 = np.array([[1, 2, 1], [2, 1, 2], [1, 2, 2]])
    T2 = np.array([[2, 1, 2], [1, 1, 2], [2, 1, 2]])
    T3 = np.array([[1, 2, 2], [2, 1, 2], [1, 2, 1]])
    T4 = np.array([[2, 2, 2], [1, 1, 1], [2, 1, 2]])
    T5 = np.array([[2, 2, 1], [2, 1, 2], [1, 2, 1]])
    T6 = np.array([[2, 1, 2], [2, 1, 1], [2, 1, 2]])
    T7 = np.array([[1, 2, 1], [2, 1, 2], [2, 2, 1]])
    T = [T0, T1, T2, T3, T4, T5, T6, T7]
    # Y like
    Y0 = np.array([[1, 0, 1], [2, 1, 2], [2, 1, 2]])
    Y1 = np.array([[0, 1, 0], [1, 1, 2], [0, 2, 1]])
    Y2 = np.array([[1, 2, 2], [0, 1, 1], [1, 2, 2]])
    Y3 = np.array([[0, 2, 1], [1, 1, 2], [0, 1, 0]])
    Y4 = np.array([[2, 1, 2], [2, 1, 2], [1, 0, 1]])
    Y5 = np.rot90(Y3)
    Y6 = np.rot90(Y4)
    Y7 = np.rot90(Y5)
    Y = [Y0, Y1, Y2, Y3, Y4, Y5, Y6, Y7]
    # O like
    O1 = np.array([[2, 2, 2], [2, 1, 1], [2, 1, 1]])
    O2 = np.array([[1, 1, 2], [1, 1, 2], [2, 2, 2]])
    O3 = np.array([[2, 1, 1], [2, 1, 1], [2, 2, 2]])
    O4 = np.array([[2, 2, 2], [1, 1, 2], [1, 1, 2]])
    O = [O1, O2, O3, O4]

    bp = np.zeros(skel.shape, dtype=int)
    for x in X:
        bp = bp + mh.morph.hitmiss(skel, x)
    for y in Y:
        bp = bp + mh.morph.hitmiss(skel, y)
    for t in T:
        bp = bp + mh.morph.hitmiss(skel, t)
    for o in O:
        bp = bp + mh.morph.hitmiss(skel, o)
    return bp


def endPoints(skel):
    endpoint1 = np.array([[0, 0, 0], [0, 1, 0], [2, 1, 2]])
    endpoint2 = np.array([[0, 0, 0], [0, 1, 2], [0, 2, 1]])
    endpoint3 = np.array([[0, 0, 2], [0, 1, 1], [0, 0, 2]])
    endpoint4 = np.array([[0, 2, 1], [0, 1, 2], [0, 0, 0]])
    endpoint5 = np.array([[2, 1, 2], [0, 1, 0], [0, 0, 0]])
    endpoint6 = np.array([[1, 2, 0], [2, 1, 0], [0, 0, 0]])
    endpoint7 = np.array([[2, 0, 0], [1, 1, 0], [2, 0, 0]])
    endpoint8 = np.array([[0, 0, 0], [2, 1, 0], [1, 2, 0]])
    ep1 = mh.morph.hitmiss(skel, endpoint1)
    ep2 = mh.morph.hitmiss(skel, endpoint2)
    ep3 = mh.morph.hitmiss(skel, endpoint3)
    ep4 = mh.morph.hitmiss(skel, endpoint4)
    ep5 = mh.morph.hitmiss(skel, endpoint5)
    ep6 = mh.morph.hitmiss(skel, endpoint6)
    ep7 = mh.morph.hitmiss(skel, endpoint7)
    ep8 = mh.morph.hitmiss(skel, endpoint8)
    ep = ep1 + ep2 + ep3 + ep4 + ep5 + ep6 + ep7 + ep8
    return ep


def pruning(skeleton, size):
    """
    remove iteratively end points "size"
    times from the skeleton
    """
    for i in range(0, size):
        endpoints = endPoints(skeleton)
        endpoints = np.logical_not(endpoints)
        skeleton = np.logical_and(skeleton, endpoints)
    return skeleton


def double_threshold(data, th1, th2):
    d1 = data > th1
    d2 = data > th2
    result = np.zeros_like(data)
    result[d1] = ((data - th1) / (th2 - th1))[d1]
    result[d2] = 1.0
    return result


def preprocess_image(image, out_skeleton=False, out_branching_image=False):
    """
    Performs preprocessing of keratin images.
    Returns:
     - normalized ridges;
     - branchings potential;
     - branchings forces;
    """

    # 1) Compute hessian matrix and find its eigen values
    hxx, hxy, hyy = hessian_matrix(image, sigma=1.5)
    eigenval_large = hessian_matrix_eigvals(hxx, hxy, hyy)[1]

    # 2) Take largest eigenvalue and detect ridges
    ridges = 1.0 - exposure.rescale_intensity(eigenval_large)

    # 3) Normalize ridges
    # 3.1) Calculate intensity histogram
    hvals, hticks = exposure.histogram(ridges)
    th0 = hticks[np.argmax(hvals)]
    # 3.2) Rescale based on the peek-internsity (assumed to be background)
    ridges_rescale = (ridges - th0) * INTENSITY_SCALE
    # 3.3) Apply double-side thresholding
    ridges_norm = double_threshold(ridges_rescale, INTENSITY_THRESHOLD_MIN, INTENSITY_THRESHOLD_MAX)

    # 4) Calculate and process binary mask
    mask = ridges_norm > 0.1  # cv2.adaptiveThreshold(255 - (255 * ridges).astype(np.uint8), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2) == 0
    mask_denoised = remove_small_objects(mask, 50)
    mask_connected = remove_small_holes(mask_denoised, 3)

    # 5) Build skeleton
    skeleton = skeletonize(mask_connected)
    # skeleton = pruning(skeleton_raw, 15) # skeleton pruning

    # 6) Find branching points
    branching_points = np.logical_or(branchedPoints(skeleton) > 0, endPoints(skeleton) > 0)

    branching_props = measure.regionprops(measure.label(branching_points), cache=False)
    branching_coords = np.array([prop.centroid for prop in branching_props])[:, [1, 0]]

    # branching_indices = np.where(branching_points)
    # branching_coords = np.hstack([branching_indices[1].reshape(-1, 1), branching_indices[0].reshape(-1, 1)])

    results = [ridges_norm, branching_coords, mask_connected]

    if out_skeleton:
        results.append(skeleton)

    if out_branching_image:
        results.append(branching_points)

    # Return results
    return tuple(results)


def proc_image(image, config):

    # get image shape
    image_rows, image_cols = image.shape

    # preprocess image
    ridge_img, br_coords, mask, skel, br_img = preprocess_image(image, out_branching_image=True, out_skeleton=True)

    # initialize gradient vector flow array
    gvf_result = np.zeros((2, 2 * image_rows, 2 * image_cols), dtype=np.double)

    # enhanced image (2x upscaled)
    enhanced_image2x = exposure.rescale_intensity(imresize(ridge_img, 2.0, interp="bilinear").astype(np.double))

    # get gradient vector flow parameters
    gvf_mu = config["Gradient Vector Flow"]["mu_f"]
    gvf_iter_n = config["Gradient Vector Flow"]["iterations_number_i"]

    # compute gradient vector flow
    curr_gvf_x, curr_gvf_y = compute_gvf(1.0 - enhanced_image2x, mu=gvf_mu, max_iter=gvf_iter_n)
    gvf_result[0] = curr_gvf_x.copy()
    gvf_result[1] = curr_gvf_y.copy()

    return {
        "enhanced_image": ridge_img,
        "branching_coords": br_coords,
        "binary_image": mask,
        "skeleton": skel,
        "branching_image": br_img,
        "gvf": gvf_result
    }