#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created by: Roman Yakobenchuk, Dmytro Kotsur
#

import os
import sys
import ImageProc as IP

import numpy as np
import networkx as nx
import cPickle as pickle

from skimage.external.tifffile import imread


def select_node_positions(graph, node_indices):
    a = [graph.node[n_i]["pos"] for n_i in node_indices]
    return a


def pickle_data(data, fname):
    with open(fname, 'w') as output_file:
        pickle.dump(data, output_file)


def unpickle_data(fname):
    with open(fname, 'r') as input_file:
        e = pickle.load(input_file)
        return e


def filter_filaments(filaments, image_shape, min_length=7, max_overlap=7, border_size=20):
    mask = np.zeros(image_shape, dtype=np.bool)

    border_mask = np.zeros(image_shape, dtype=np.bool)
    border_mask[:border_size, :] = True
    border_mask[-border_size::, :] = True
    border_mask[:, :border_size] = True
    border_mask[:, -border_size::] = True

    filtered_fibers = []

    for filament in filaments:
        coords = np.asarray(filament)

        if len(coords) < min_length:
            continue

        or_mask = np.zeros_like(mask)
        or_mask[coords[:, 1], coords[:, 0]] = True

        overlap = np.sum(np.logical_and(mask, or_mask))
        overlap_border = np.sum(np.logical_and(border_mask, or_mask))

        if overlap >= max_overlap or overlap_border > 0:
            continue

        mask = np.logical_or(mask, or_mask)
        filtered_fibers.append(coords)

    return filtered_fibers


def generate(input_dir, folder, generator_config):
    skel = np.squeeze(imread(os.path.join(input_dir, folder, "skeletons.tif")))[0]
    msk = np.squeeze(imread(os.path.join(input_dir, folder, "stable_branching.tif")))[0]

    skeleton = skel.astype(np.double)
    mask = msk.astype(np.double)

    print "Constructing graph..."

    (sparseGraphNodes, sparseGraphEdges) = IP.construct_graphs(skeleton, mask)

    graph = nx.Graph()
    graph.add_nodes_from(sparseGraphNodes)
    graph.add_edges_from(sparseGraphEdges)

    node_to_stable_neighbs = IP.getStable()

    filaments, filaments_count = process_stable_point(node_to_stable_neighbs, generator_config)
    filaments = sorted(filaments)

    filament_coodrinates = []
    for filament in filaments:
        filament_coodrinates.append(filament[1])

    min_length = generator_config["Filter"]["MinLength_i"]
    max_overlap = generator_config["Filter"]["MaxOverlap_i"]
    border_size = generator_config["Filter"]["Border_Size_i"]

    final_filaments = filter_filaments(filament_coodrinates, skel.shape, min_length, max_overlap, border_size)

    print "\rFilament generation finished"
    print " Filaments total:", filaments_count
    print " Filaments after filtering:", len(final_filaments)

    return filament_coodrinates, final_filaments


def process_stable_point(node_to_stable_neighbs, generator_config):
    len_thresh = int(generator_config["Search"]["LengthThresh"])
    nodes_cutoff = int(generator_config["Search"]["NodesCutoff"])
    cost_thresh = float(generator_config["Search"]["CostThresh"])
    
    final_fibers = []
    iiii = 0
    iteration_count = 0
    processed_pairs = set()

    for k in node_to_stable_neighbs.keys():
        iteration_count += 1
        sys.stdout.write("\r Processed " + str(iteration_count) + " / " + str(len(node_to_stable_neighbs.keys())) + " branching points")

        new_start_id = k
        nei = node_to_stable_neighbs[k]

        for new_end_id in nei:
            if (new_start_id, new_end_id) in processed_pairs or (new_end_id, new_start_id) in processed_pairs:
                continue

            (prunned_sparseGraphNodesAndEdges, new_start_end) = IP.preprocessGraph(new_start_id, new_end_id)
            prunned_sparseGraphNodes = prunned_sparseGraphNodesAndEdges[0]
            prunned_sparseGraphEdges = prunned_sparseGraphNodesAndEdges[1]

            prunned_graph = nx.DiGraph()
            prunned_graph.add_nodes_from(prunned_sparseGraphNodes)
            prunned_graph.add_edges_from(prunned_sparseGraphEdges)

            start_id = new_start_end[0]
            end_id = new_start_end[1]

            if end_id == -1:
                # no possible path from start to end
                continue

            paths = nx.all_simple_paths(prunned_graph, source=start_id, target=end_id, cutoff=nodes_cutoff)
            all_average_costs = []
            path_count = 0

            limit = 100
            iteration = 0
            for path in paths:
                bad_path = False
                # check if we don't cross any stable point
                for n_id_i in xrange(len(path)):
                    if n_id_i == 0 or (n_id_i == len(path) - 1):
                        continue
                    for stable_id in node_to_stable_neighbs.keys():
                        if path[n_id_i] == stable_id:
                            bad_path = True

                if bad_path:
                    continue

                path_count += 1

                pts = select_node_positions(prunned_graph, path)

                path_pts = pts[:]
                ppts = path_pts[:]

                equi_dist = 1
                slope_dist = 2 * equi_dist
                costs = IP.assessPath(ppts, equi_dist, slope_dist)

                if costs is None or len(costs) == 0:
                    continue

                cost_sum = 0.
                for i in xrange(len(costs)):
                    cost_sum += costs[i]

                all_average_costs.append((cost_sum, path))

                iteration += 1
                if iteration > limit:
                    break

            if len(all_average_costs) == 0:
                continue

            sorted_costs = sorted(all_average_costs)

            best_cost_path = sorted_costs[0][1]

            skel_path = IP.graphPathToSkeleton(best_cost_path)
            if len(skel_path) > len_thresh or sorted_costs[0][0] > cost_thresh:
                continue

            final_fibers.append((sorted_costs[0][0], skel_path))

            processed_pairs.add((new_start_id, new_end_id))

            IP.clearGlobals()

            iiii += 1
            #print "Generated", iiii, "filaments"

    return (final_fibers, iiii)


if __name__ == "__main__":
    input_dir = "../../../output/preprocessing/"
    output_dir = "../../../output/generator/"
    folder = "MZ_OL_0320_1"
    generator_config = {}
    # generator_config["Search"]["LengthThresh"] = 60
    # generator_config["Search"]["NodesCutoff"] = 5
    # generator_config["Search"]["CostThresh"] = 0.00001
    generate(input_dir, output_dir, folder, generator_config)
