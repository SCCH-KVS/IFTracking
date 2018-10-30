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

import math
import networkx as nx
import numpy as np
from scipy import interpolate


def get_graph_position(g):
    return {node_id: data["pos"] for node_id, data in g.nodes_iter(data=True)}


def uniform_contour_reparametrization(x, y, step=1.0, curve_kind="cubic"):
    """
    Input: x, y - ndarrays for x and y coordinates of polyline, step is desired approximate step. 
    For curve_kind see kind parameter of scipy.interpolate.interp1d
    Returns new_x, new_y, new_step
    """
    l = np.hstack([[0.0], np.cumsum(np.sqrt((x[1:] - x[:-1]) ** 2 + (y[1:] - y[:-1]) ** 2))]).ravel()
    # 
    fx = interpolate.interp1d(l, x, kind=curve_kind)
    fy = interpolate.interp1d(l, y, kind=curve_kind)
    #
    length = l[-1]
    point_n = int(length / step)
    
    new_step = length / point_n
    reparam_t = np.linspace(0.0, length, point_n)
    
    return fx(reparam_t), fy(reparam_t), new_step


def uniform_contour_reparametrization_n(x, y, point_n):
    l = np.hstack([[0.0], np.cumsum(np.sqrt((x[1:] - x[:-1]) ** 2 + (y[1:] - y[:-1]) ** 2))]).ravel()
    # 
    fx = interpolate.interp1d(l, x, kind="linear")
    fy = interpolate.interp1d(l, y, kind="linear")
    #
    length = l[-1]
    reparam_t = np.linspace(0.0, length, point_n)
    
    return fx(reparam_t), fy(reparam_t), reparam_t[1]


def next_contour_node(graph, prev_node_id, curr_node_id):
    if graph.degree(curr_node_id) != 2:
        return None
    neighbors = graph.neighbors(curr_node_id)
    if neighbors[0] == prev_node_id:
        return neighbors[1]
    return neighbors[0]


def uniform_graph_reparametrization_stepwise(g, step=1.0):
    branching_points = []
    used = set()
    
    max_node_id = 1
    for node_id, node_data in g.nodes_iter(data=True):
        if g.degree(node_id) != 2 or "is_adhesion" in node_data:
            branching_points.append((node_id, node_data))
            max_node_id = max(max_node_id, node_id) + 1
    
    result_graph = nx.Graph()
    result_graph.add_nodes_from(branching_points)

    paths_seq = {}
    paths_step = {}

    path_id = 0
    for node_id, node_data in branching_points:	
        for neighbor_id in g.neighbors_iter(node_id):
            if neighbor_id not in used:
                
                # trace contour path            
                prev_node_id = node_id
                curr_node_id = neighbor_id
                path = [prev_node_id, curr_node_id]
                while curr_node_id is not None and curr_node_id not in branching_points:
                    tmp_node_id = next_contour_node(g, prev_node_id, curr_node_id)
                    prev_node_id = curr_node_id
                    curr_node_id = tmp_node_id
                    if curr_node_id is not None:
                        path.append(curr_node_id)
                        used.add(curr_node_id)
                
                # build path
                path_x = np.array([g.node[n_i]["pos"][0] for n_i in path]).ravel()
                path_y = np.array([g.node[n_i]["pos"][1] for n_i in path]).ravel()
                
                # reparametrize path
                new_path_x, new_path_y, new_step = uniform_contour_reparametrization(path_x, path_y, step)
                new_points_n = len(new_path_x)
                
                # add path to new graph
                prev_node_id = path[0]
                new_path = [prev_node_id]
                for i in xrange(1, new_points_n-1):
                    result_graph.add_node(max_node_id, {
                        	"pos": (new_path_x[i], new_path_y[i]), 
                    		"path_ids": set([path_id])
                    	})
                    result_graph.add_edge(prev_node_id, max_node_id)
                    new_path.append(max_node_id)
                    prev_node_id = max_node_id
                    max_node_id += 1
                new_path.append(path[-1])
                result_graph.add_edge(prev_node_id, path[-1])
                
                # add path id to start branching node
                if "path_ids" not in result_graph.node[path[0]]:
                    result_graph.node[path[0]]["path_ids"] = set([path_id])
                else:
                    result_graph.node[path[0]]["path_ids"].add(path_id)
                
                # add path id to end branching node
                if "path_ids" not in result_graph.node[path[-1]]:
                    result_graph.node[path[-1]]["path_ids"] = set([path_id])
                else:
                    result_graph.node[path[-1]]["path_ids"].add(path_id)

                paths_seq[path_id] = new_path
                paths_step[path_id] = new_step

                # increase path counter
                path_id += 1
    
    return result_graph, paths_seq, paths_step


def get_length(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def get_average_edge_length(graph):
    avg_length = 0.0
    for n0, n1 in graph.edges_iter():
        p0 = graph.node[n0]["pos"]
        p1 = graph.node[n1]["pos"]
        avg_length += get_length(p0, p1)
    return avg_length / graph.number_of_edges()