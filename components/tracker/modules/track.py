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
from skimage.feature import match_template
from skimage.util import pad

import parametrize as gparam
from snakes import generate_matrix, sample_sf, constraint_forces, gen_gauss_kernel
from utils import gen_potential
from vfsampler.vfsampler import decode_vf, sample_vf

from Queue import Queue


import sys
sys.path.append("../../common")


class TrackerParams(object):
    def __init__(self):
        pass


def match_and_track(point, img_curr, img_next, skel_next, img_branch_dt, wlarge=50, wsmall=10, corr_mult=15.0, branch_cost=1.0):
    """
    Track points by optimizing compound cost function
    """
    # set padding width
    pad_size = ((wlarge, wlarge), (wlarge, wlarge))
    # set paddings
    img_curr = pad(img_curr, pad_size, 'constant')
    img_next = pad(img_next, pad_size, 'constant')
    skel_next = pad(skel_next, pad_size, 'constant')
    img_branch_dt = pad(img_branch_dt, pad_size, 'constant')
    # convert to the int type
    pnt = point.astype(np.int) + wlarge
    # get template
    template = img_curr[pnt[1]-wsmall:pnt[1]+wsmall+1, pnt[0]-wsmall:pnt[0]+wsmall+1]
    # get search region
    search_region = img_next[pnt[1]-wlarge:pnt[1]+wlarge+1, pnt[0]-wlarge:pnt[0]+wlarge+1]
    # get skeleton region
    skel_region = skel_next[pnt[1]-wlarge:pnt[1]+wlarge+1, pnt[0]-wlarge:pnt[0]+wlarge+1]
    # get branching image region
    branch_dt_region = img_branch_dt[pnt[1]-wlarge:pnt[1]+wlarge+1, pnt[0]-wlarge:pnt[0]+wlarge+1]
    # match template
    match = match_template(search_region, template, pad_input=True)
    # map to the skeleton
    skel_match = match.copy()
    skel_match[skel_region == 0] = 0.0
    # get coordinates of peeks
    peeks_r, peeks_c = np.where(skel_region)
    # calculate distance to the skeleton
    norm = np.sqrt((peeks_r - wlarge) ** 2 + (peeks_c - wlarge) ** 2)
    # calculate penalty
    penalty = norm + corr_mult * np.abs(match.max() - match[peeks_r, peeks_c]) + branch_cost * 0.0 * branch_dt_region[peeks_r, peeks_c]
    # find the point with the smallest penalty
    ii = np.argmin(penalty)
    # convert result to global coordinates
    result_pnt = np.array([peeks_c[ii], peeks_r[ii]], dtype=pnt.dtype) + pnt - 2 * wlarge
    # output cross correlation on the skeleton
    skel_match_out = np.zeros_like(img_curr, dtype=match.dtype)
    skel_match_out[pnt[1]-wlarge:pnt[1]+wlarge+1, pnt[0]-wlarge:pnt[0]+wlarge+1][skel_region > 0] = match[skel_region > 0]
    # output matching result
    match_out = np.zeros_like(img_curr, dtype=match.dtype)
    match_out[pnt[1]-wlarge:pnt[1]+wlarge+1, pnt[0]-wlarge:pnt[0]+wlarge+1][peeks_r, peeks_c] = penalty
    # return result
    return result_pnt, skel_match_out, match_out


def shortest_path_bfs(mask, row1, col1, row2, col2):
    q = Queue()
    q.put((row1, col1))

    row_n, col_n = mask.shape
    used = np.ones((row_n, col_n, 2), dtype=np.int) * -1
    used[row1, col1, 0], used[row1, col1, 1] = row1, col1

    # define neighbourhood
    neighbour_r = [-1, -1, -1, 0, 1, 1, 1, 0]
    neighbour_c = [-1, 0, 1, 1, 1, 0, -1, -1]

    found = False

    # start search
    while not q.empty():
        row, col = q.get()

        for (n_r, n_c) in zip(neighbour_r, neighbour_c):
            next_r, next_c = row + n_r, col + n_c

            if 0 <= next_r < row_n and 0 <= next_c < col_n and used[next_r, next_c, 0] < 0 and mask[next_r, next_c] > 0:
                used[next_r, next_c, 0] = row
                used[next_r, next_c, 1] = col

                if next_r == row2 and next_c == col2:
                    found = True
                    break

                q.put((next_r, next_c))

        if found:
            result_path = []
            curr_row, curr_col = row2, col2
            while not (curr_row == row1 and curr_col == col1):
                result_path.append((curr_col, curr_row))
                curr_row, curr_col = used[curr_row, curr_col, 0], used[curr_row, curr_col, 1]
            result_path.append((col1, row1))

            result_path.reverse()
            return result_path

    return []


class Tracker:

    def __init__(self, image_sequence, params=None, lock=None):

        if params is None:
            params = TrackerParams()
            params.kernel_size = 11
            params.kernel_sigma = 2.5
            params.alpha = 1.0
            params.beta = 1.0
            params.max_iter_n = 600
            params.dt = 0.01
            params.min_shift = 1.0e-7

        # Initialize image sequence
        self.image_sequence = image_sequence

        # Generate gaussian kernel
        self.gauss_kernel = gen_gauss_kernel(params.kernel_sigma, params.kernel_size)

        # Snake matrix
        self.U = 0

        # Set lock for parallel computing
        self.lock = lock

        # Maximum iterations
        self.max_iter_n = params.max_iter_n

        # Alpha-Beta
        self.alpha = params.alpha
        self.beta = params.beta

        # Delta time
        self.dt = params.dt

        # GVF offset
        self.gvf_offset = 40

        # Motion threshold
        self.motion_threshold = params.min_shift

    def track(self, initial_positions, log):
        """
        Track
        """
        # Get image sequence shape
        frame_n, im_r, im_c = self.image_sequence.enhanced.shape
        log += "  [Tracker] : number of images: " + str(frame_n)

        # Get number of points in snake
        N = len(initial_positions)

        # Generate stiffness matrix
        A = generate_matrix(N, self.alpha, self.beta)

        # Generate snake matrix
        self.U = np.linalg.inv(np.eye(N, N) - self.dt * A)

        # Get number of iterations
        iter_n = self.max_iter_n

        # Trajectories of the snakes during tracking and evolution
        snake_traj = np.zeros((frame_n, iter_n + 1, N, 2), dtype=np.double)
        snake_traj[0][0] = initial_positions

        # Trajectories of branching points at the ends
        ends_traj = np.zeros((frame_n, 2, 2), dtype=np.double)

        # Sampled intensities
        snake_intensities = np.zeros((frame_n, N), dtype=np.int)

        # Branching points
        branching_potentials = np.zeros((frame_n, 2, im_r, im_c), dtype=np.double)  # branching potential

        # Endpoints initialized
        endpoint_initialized = [False, False]

        # Track snake and branching points at the ends
        for image_i in xrange(frame_n):

            # Print current frame index
            log += "  [Tracker] : current frame: " + str(image_i)

            # Get enhanced image
            enhanced_image = self.image_sequence.enhanced[image_i]

            # Get binary image
            binary_image = self.image_sequence.binaries[image_i]

            # Get gradient vector flow
            gvf = self.image_sequence.gvf_magnitude[image_i], self.image_sequence.gvf_angle[image_i]

            if not endpoint_initialized[0] or not endpoint_initialized[1]:
                br_coords = self.image_sequence.branching_coords[image_i]
                br_potential, br_force, br_mask = gen_potential(br_coords, enhanced_image.shape, self.gauss_kernel)

            if endpoint_initialized[0]:
                br_p0, br_f0, br_m0 = gen_potential(ends_traj[image_i][0].reshape(1, 2), enhanced_image.shape, self.gauss_kernel)
            else:
                br_p0, br_f0, br_m0 = br_potential, br_force, br_mask

            if endpoint_initialized[1]:
                br_p1, br_f1, br_m1 = gen_potential(ends_traj[image_i][1].reshape(1, 2), enhanced_image.shape,
                                                    self.gauss_kernel)
            else:
                br_p1, br_f1, br_m1 = br_potential, br_force, br_mask

            branching_potentials[image_i, 0] = br_p0
            branching_potentials[image_i, 1] = br_p1

            log += "  [Tracker] Snake evolution."

            # evolve snake
            snake_traj[image_i] = self.evolve_snake(snake_traj[image_i], gvf, enhanced_image, br_f0, br_f1, iter_n,
                                                    self.dt, N)

            # sample intensities
            snake_intensities[image_i] = sample_sf(binary_image, snake_traj[image_i][iter_n], interp=False).ravel()

            # set trajectory of the endpoints
            if not endpoint_initialized[0]:
                endpoint_initialized[0] = True
                indices = sample_sf(br_m0.astype(np.int), snake_traj[image_i][iter_n][0, :].reshape(1, 2),
                                    interp=False).ravel()

                ends_traj[image_i][0] = self.image_sequence.branching_coords[image_i][indices[0] - 1]

            if not endpoint_initialized[1]:
                endpoint_initialized[1] = True
                indices = sample_sf(br_m1.astype(np.int), snake_traj[image_i][iter_n][-1, :].reshape(1, 2),
                                    interp=False).ravel()

                ends_traj[image_i][1] = self.image_sequence.branching_coords[image_i][indices[0] - 1]

            # Use optical flow to translate contour to the next frame
            if image_i + 1 < frame_n:

                # Set next snake trajectory
                snake_traj[image_i + 1][0][:, 0] = snake_traj[image_i][iter_n][:, 0]  # result_x.copy()#next_x#result_x.copy()
                snake_traj[image_i + 1][0][:, 1] = snake_traj[image_i][iter_n][:, 1]  # result_y.copy()#next_y#result_y.copy()

                # Get enhanced image on the next frame
                enhanced_image_next = self.image_sequence.enhanced[image_i+1]

                # Get skeleton image
                skeleton_next = self.image_sequence.skeletons[image_i+1]

                # Get branching image
                branch_img_next = self.image_sequence.branching[image_i+1]

                for end_i in xrange(2):
                    ends_traj[image_i + 1][end_i] = match_and_track(ends_traj[image_i][end_i],
                                                                    enhanced_image,
                                                                    enhanced_image_next,
                                                                    skeleton_next,
                                                                    branch_img_next)[0]

        return {
            "snake_trajectory": snake_traj,
            "branching_potential": branching_potentials,
            "ends_trajectories": ends_traj,
            "snake_intensities": snake_intensities
        }

    def evolve_snake(self, snake_traj, gvf_result, enhanced_image, br_f0, br_f1, iter_n, dt, point_n):
        # evolve snake
        for iter_i in xrange(1, iter_n + 1):
            curr_points = snake_traj[iter_i - 1]

            # sample vector field
            gvf_vecs = decode_vf(gvf_result[0], gvf_result[1], (2.0 * curr_points))

            # compute constraint forces
            constraint_force = constraint_forces(enhanced_image, br_f0, br_f1, curr_points)

            result_x = self.U.dot(curr_points[:, 0] + dt * (gvf_vecs[:, 0] + constraint_force[:, 0]))
            result_y = self.U.dot(curr_points[:, 1] + dt * (gvf_vecs[:, 1] + constraint_force[:, 1]))
            # track results
            snake_traj[iter_i][:, 0] = result_x
            snake_traj[iter_i][:, 1] = result_y

            snake_traj[iter_i][:, 0], snake_traj[iter_i][:, 1], step = gparam.uniform_contour_reparametrization_n(
                snake_traj[iter_i][:, 0], snake_traj[iter_i][:, 1], point_n)

            # quantify the motion of the snake
            dx = snake_traj[iter_i][:, 0] - snake_traj[iter_i-1][:, 0]
            dy = snake_traj[iter_i][:, 1] - snake_traj[iter_i-1][:, 1]
            ds = np.sqrt(dx ** 2 + dy ** 2).mean()

            if ds < self.motion_threshold:
                snake_traj[iter_i+1::][..., 0] = snake_traj[iter_i][:, 0]
                snake_traj[iter_i+1::][..., 1] = snake_traj[iter_i][:, 1]
                return snake_traj

        return snake_traj

