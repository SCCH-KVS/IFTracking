//
//  ImageProcessing.cpp
//  ImProLib
//
//  Created by Roman on 12.07.17.
//  Copyright © 2017 Roman. All rights reserved.


#include "ImageProcessing.h"

#include <math.h>
#include <iostream>
#include <algorithm>
#include <queue>
#include <fstream>
#include <sstream>
#include <array>


ImageInt createIntImage(ImageInt::size_type width, ImageInt::size_type height, int def) {
    return ImageInt(height, std::vector<int>(width, def));
}

ImageDouble createDoubleImage(ImageDouble::size_type width, ImageDouble::size_type height, double def) {
    return ImageDouble(height, std::vector<double>(width, def));
}

ImageInt::size_type imWidth(const ImageInt& img) {
    return img[0].size();
}

ImageInt::size_type imHeight(const ImageInt& img) {
    return img.size();
}

ImageDouble::size_type imWidth(const ImageDouble& img) {
    return img[0].size();
}

ImageDouble::size_type imHeight(const ImageDouble& img) {
    return img.size();
}




// ------------------------- GLOBALS------------------------------------------------------------------------------------
NodesType graphNodes_sp;
EdgesType graphEdges_sp;

// 23.08.2017 Aachen : Create correspondence between my branching points and Dmytro's stable points
std::unordered_set<int> stable_branchings;


std::map<int, std::set<int>> dfs_graph;
std::map<int, PointDouble> transformed_points;

// my new approach for optimization

std::vector<std::unordered_set<int>> global_graph;
std::unordered_map<int, PointDouble> node_id_to_pt_good;
std::unordered_map<PointDouble, int, PointDoubleHash> node_pt_to_id_good;
// ToDay
//std::unordered_map<int, int> new_node_id_to_node_id_good;
//std::unordered_map<int, int> node_id_to_new_node_id_good;
std::unordered_set<int> all_nodes;

// made global on July, 19 to be able to transform point on image into node for Aachen
std::unordered_map<PointInt, int, PointIntHash> medial_nodes_indexes_sp;

// need this to get all points in the path
std::unordered_map<int, std::vector<LineStrip>> end_points_to_line_dict;


std::unordered_map<int, std::unordered_set<int>> node_to_stable_neighbs;


ReturnType construct_graphs(const ImageDouble& skeleton, const ImageDouble& stable_mask)
{
    std::unordered_map<int, LineInt> medial_nodes_points_sp;

    std::unordered_map<PointInt, int, PointIntHash> map_between_points_and_node_ids;

    auto copy_skeleton = skeleton;

    auto h = imHeight(skeleton);
    auto w = imWidth(skeleton);
    auto line_strip_image {createIntImage(w, h)};
    auto medial_nodes_image {createIntImage(w, h)};
    std::unordered_map<PointInt, LineInt, PointIntHash> edgesPoints;

    std::unordered_set<int> added_ids;

    separate_sparse_neighbours(copy_skeleton, line_strip_image, medial_nodes_image, medial_nodes_indexes_sp, medial_nodes_points_sp);

    // std::cout << "\nPrinting line strip image" << std::endl;
    //printImage(line_strip_image);

    // std::cout << "\nPrinting nodes image" << std::endl;
    //printImage(medial_nodes_image);

//    std::cout << "\nPrinting medial_nodes_indexes_sp" << std::endl;
//    for (const auto& el : medial_nodes_indexes_sp) {
//        std::cout << "(" << el.first.first << ", " << el.first.second << ") : " << el.second << std::endl;
//    }

    // std::cout << "\nPrinting medial_nodes_points_sp" << std::endl;
    for (const auto& el : medial_nodes_points_sp) {
        // std::cout << el.first << " : ";
        for (const auto& el2 : el.second) {
            // std::cout << "(" << el2.first << ", " << el2.second << "); ";

            // 23.08.2017 Aachen : Create correspondence between my branching points and Dmytro's stable points
            if (stable_mask[el2.second][el2.first] != 0) {
                stable_branchings.insert(el.first);
                // std::cout << "stable";
                //break;
            }
        }
        // std::cout << std::endl;
    }

    trace_sparse_lines(copy_skeleton, line_strip_image, medial_nodes_image, medial_nodes_indexes_sp, end_points_to_line_dict);

    // TODO: check this huge code just to fill "map_between_points_and_node_ids"
    for (const auto& el : medial_nodes_points_sp) {
        auto curr_id = el.first;
        // branching point. Skip it for now. It would be added from other normal points as neighbour
        if (el.second.size() > 1) {
            if (added_ids.count(curr_id) == 0) {
                added_ids.insert(curr_id);

                std::pair<int, int> sum_pt = std::accumulate(el.second.begin(), el.second.end(), std::make_pair(0, 0), pair_sum<int, int>());

                // MAYBE USE HERE FLOATING POINT NUMBERS
                auto n = el.second.size();
                auto avg_p = std::make_pair(static_cast<int>(sum_pt.first / n), static_cast<int>(sum_pt.second / n));

                // for sparse graph
                auto pos_pair = std::make_pair(avg_p.first, avg_p.second); //  + 0.5
                map_between_points_and_node_ids[pos_pair] = curr_id;
            }
            continue;
        }

        if (added_ids.count(curr_id) == 0) {
            added_ids.insert(curr_id);

            // for sparse graph
            auto pos_pair = std::make_pair(el.second[0].first, el.second[0].second); //  + 0.5
            map_between_points_and_node_ids[pos_pair] = curr_id;
        }

        std::vector<std::pair<int, int>> neighbours;
        calculate_neighbours(copy_skeleton, neighbours, el.second[0].first, el.second[0].second);
        for (const auto& neighbour : neighbours) {
            int neighbour_id {medial_nodes_indexes_sp[neighbour]};

            if (added_ids.count(neighbour_id) == 0) {
                added_ids.insert(neighbour_id);

                auto pts = medial_nodes_points_sp[neighbour_id];
                if (pts.size() > 1) {
                    std::pair<int, int> sum_pt = std::accumulate(pts.begin(), pts.end(), std::make_pair(0, 0), pair_sum<int, int>());

                    // MAYBE USE HERE FLOATING POINT NUMBERS
                    auto n_ = pts.size();
                    auto avg_p = std::make_pair(static_cast<int>(sum_pt.first / n_), static_cast<int>(sum_pt.second / n_));

                    // for sparse graph
                    auto pos_pair = std::make_pair(avg_p.first, avg_p.second); //  + 0.5
                    map_between_points_and_node_ids[pos_pair] = neighbour_id;
                }
                else {
                    // for sparse graph
                    auto pos_pair = std::make_pair(medial_nodes_points_sp[neighbour_id].at(0).first, medial_nodes_points_sp[neighbour_id].at(0).second); // + 0.5
                    map_between_points_and_node_ids[pos_pair] = neighbour_id;
                }
            }
        }
    }


//    std::cout << "\nPrinting map_between_points_and_node_ids" << std::endl;
//    for (const auto& el : map_between_points_and_node_ids) {
//        std::cout << "(" << el.first.first << ", " << el.first.second << ") : " << el.second << std::endl;
//    }


    build_sparse_graph(medial_nodes_points_sp, end_points_to_line_dict, graphNodes_sp, graphEdges_sp, edgesPoints, map_between_points_and_node_ids);

    // AACHEN
    fillGraph(graphEdges_sp, graphNodes_sp);
    findStableNeighbours();

    return std::make_pair(graphNodes_sp, graphEdges_sp);
}

void separate_neighbours(ImageDouble& skeleton, std::unordered_map<std::pair<int, int>, int, PointIntHash>& medial_nodes_indexes,
                         std::unordered_map<int, std::vector<std::pair<int, int>>>& medial_nodes_points)
{
    auto h = imHeight(skeleton);
    auto w = imWidth(skeleton);

    BinaryImage visited_mask = createIntImage(w, h);

    int branching_index {0};

    for (int x = 0; x < w; ++x) {
        for (int y = 0; y < h; ++y) {
            if (!visited_mask[x][y] && skeleton[x][y]) {
                visited_mask[x][y] = 1;

                std::vector<std::pair<int, int>> fake;

                switch (calculate_neighbours(skeleton, fake, x, y)) {
                    case 0:
                        skeleton[x][y] = 0;
                        break;
                    case 2:
                    {
                        medial_nodes_indexes[std::make_pair(x, y)] = branching_index;
                        medial_nodes_points[branching_index].push_back(std::make_pair(x, y));
                        branching_index += 1;
                        break;
                    }
                    default:
                    {
                        LineInt added_pts; // not used here
                        flood_fill_neighbours(skeleton, visited_mask, medial_nodes_indexes, medial_nodes_points, x, y, branching_index, added_pts);
                        branching_index += 1;
                        break;
                    }
                }
            }
        }
    }
}

void flood_fill_neighbours(const ImageDouble& skeleton, ImageInt& mask, std::unordered_map<std::pair<int, int>, int, PointIntHash>& medial_nodes_indexes,
                           std::unordered_map<int, std::vector<std::pair<int, int>>>& medial_nodes_points, int x, int y, int branching_index,
                           LineInt& added_pts)
{
    auto w = imWidth(skeleton);
    auto h = imHeight(skeleton);

    medial_nodes_indexes[std::make_pair(x, y)] = branching_index;
    medial_nodes_points[branching_index].push_back(std::make_pair(x, y));
    mask[y][x] = 1;
    added_pts.push_back(std::make_pair(x, y));

    for (auto _x = -1; _x < 2; ++_x) {
        for (auto _y = -1; _y < 2; ++_y) {
            std::vector<std::pair<int, int>> fake;

            if (_x || _y) {
                int new_x = x + _x;
                int new_y = y + _y;
                if (new_x >= 0 && new_x < w) {
                    if (new_y >= 0 && new_y < h) {
                        if (skeleton[new_y][new_x] && !mask[new_y][new_x]) {
                            auto n_c = calculate_neighbours(skeleton, fake, new_x, new_y);
                            if (n_c != 0 && n_c != 2) {
                                flood_fill_neighbours(skeleton, mask, medial_nodes_indexes, medial_nodes_points, new_x, new_y, branching_index, added_pts);
                            }
                        }
                    }
                }
            }
        }
    }
}


void separate_sparse_neighbours(const ImageDouble& skeleton, ImageInt& line_strip_image, ImageInt& medial_nodes_image,
                                std::unordered_map<PointInt, int, PointIntHash>& medial_nodes_indexes,
                                std::unordered_map<int, LineInt>& medial_nodes_points)
{
    auto h = imHeight(skeleton);
    auto w = imWidth(skeleton);

    BinaryImage visited_mask = createIntImage(w, h);

    int branching_index {0};


    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            if (!visited_mask[y][x] && skeleton[y][x]) {
                visited_mask[y][x] = 1;

                std::vector<std::pair<int, int>> fake;

                switch (calculate_neighbours(skeleton, fake, x, y)) {
                    case 0:
                        break;
                    case 2:
                    {
                        line_strip_image[y][x] = 1;
                        break;
                    }
                    default:
                    {
                        LineInt added_pts;
                        flood_fill_neighbours(skeleton, visited_mask, medial_nodes_indexes, medial_nodes_points, x, y, branching_index, added_pts);
                        for (const auto& pt : added_pts) {
                            medial_nodes_image[pt.second][pt.first] = 1;
                        }
                        branching_index += 1;
                        break;
                    }
                }
            }
        }
    }
}

void trace_sparse_lines(ImageDouble& skeleton,
                        BinaryImage& line_strip_image,
                        const BinaryImage& medial_nodes_image,
                        const std::unordered_map<PointInt, int, PointIntHash>& medial_nodes_indexes,
                        std::unordered_map<int, std::vector<LineStrip>>& end_points_to_line_dict)
{
    int line_id {0};

    auto h = imHeight(line_strip_image);
    auto w = imWidth(line_strip_image);

    auto temp_line_strip_image = line_strip_image;

    for (auto y = 0; y < h; ++y) {
        for (auto x = 0; x < w; ++x) {
            if (temp_line_strip_image[y][x]) {
                LineInt fake;
                auto neighbors_count = calculate_neighbours(temp_line_strip_image, fake, x, y);

                // search for endpoint in line strip image
                if (neighbors_count == 1) {
                    LineInt points_list;
                    auto x_n {x};
                    auto y_n {y};

                    while (calculate_neighbours(temp_line_strip_image, fake, x_n, y_n) == 1) {
                        points_list.push_back(std::make_pair(x_n, y_n));
                        auto x_t {x_n};
                        auto y_t {y_n};
                        auto neighbour = neighbor_of(temp_line_strip_image, x_n, y_n);
                        temp_line_strip_image[y_t][x_t] = 0;
                        if (neighbour.first != -1 && neighbour.second != -1) {
                            x_n = neighbour.first;
                            y_n = neighbour.second;
                        }
                        else {
                            break;
                        }
                    }

                    if (temp_line_strip_image[y_n][x_n]) {
                        if (calculate_neighbours(temp_line_strip_image, fake, x_n, y_n) == 0) { // last point! Don't forget to add
                            points_list.push_back(std::make_pair(x_n, y_n));
                        }
                        temp_line_strip_image[y_n][x_n] = 0;
                    }

                    auto s = neighbor_of(medial_nodes_image, x, y);
                    auto e = neighbor_of(medial_nodes_image, x_n, y_n);


                    if (s.first != -1 && s.second != -1) {
                        points_list.insert(points_list.cbegin(), s);
                    }

                    if (e.first != -1 && e.second != -1) {
                        points_list.push_back(e);
                    }

                    int si {-1};
                    int ei {-1};
                    auto it_s = medial_nodes_indexes.find(s);
                    if (it_s != medial_nodes_indexes.end()) {
                        si = it_s->second;
                    }
                    auto it_e = medial_nodes_indexes.find(e);
                    if (it_e != medial_nodes_indexes.end()) {
                        ei = it_e->second;
                    }

                    LineStrip ls(points_list, si, ei, line_id);

                    // fill {end_point : [lines]}
                    if (end_points_to_line_dict.find(si) != end_points_to_line_dict.end()) {
                        end_points_to_line_dict[si].push_back(ls);
                    }
                    else {
                        end_points_to_line_dict[si] = std::vector<LineStrip>{ls};
                    }

                    if (end_points_to_line_dict.find(ei) != end_points_to_line_dict.end()) {
                        end_points_to_line_dict[ei].push_back(ls);
                    }
                    else {
                        end_points_to_line_dict[ei] = std::vector<LineStrip>{ls};
                    }

                    ++line_id;
                }
                else {
                    if (neighbors_count == 0) { // point between two endpoints
                        LineInt points_list;
                        temp_line_strip_image[y][x] = 0;
                        points_list.push_back(std::make_pair(x, y));
                        LineInt neighbs;
                        auto neighbs_c = calculate_neighbours(medial_nodes_image, neighbs, x, y);
                        if (neighbs_c == 2) {
                            auto s = neighbs[0];
                            auto e = neighbs[1];

                            points_list.insert(points_list.cbegin(), s);
                            points_list.push_back(e);

                            int si {-1};
                            int ei {-1};
                            auto it_s = medial_nodes_indexes.find(s);
                            if (it_s != medial_nodes_indexes.end()) {
                                si = it_s->second;
                            }
                            auto it_e = medial_nodes_indexes.find(e);
                            if (it_e != medial_nodes_indexes.end()) {
                                ei = it_e->second;
                            }

                            LineStrip ls{points_list, si, ei, line_id};

                            // fill {end_point : [lines]}
                            if (end_points_to_line_dict.find(si) != end_points_to_line_dict.end()) {
                                end_points_to_line_dict[si].push_back(ls);
                            }
                            else {
                                end_points_to_line_dict[si] = std::vector<LineStrip>{ls};
                            }

                            if (end_points_to_line_dict.find(ei) != end_points_to_line_dict.end()) {
                                end_points_to_line_dict[ei].push_back(ls);
                            }
                            else {
                                end_points_to_line_dict[ei] = std::vector<LineStrip>{ls};
                            }
                            ++line_id;
                        }
                    }
                }
            }
        }
    }
}



void build_sparse_graph(const std::unordered_map<int, LineInt>& medial_nodes_points,
                        const std::unordered_map<int, std::vector<LineStrip>>& end_points_to_line_dict,
                        std::vector<std::pair<int, std::unordered_map<std::string, PointDouble>>>& graphNodes,
                        EdgesType& graphEdges,
                        std::unordered_map<PointInt, LineInt, PointIntHash>& edgesPoints,
                        const std::unordered_map<PointInt, int, PointIntHash>& _map_between_points_and_node_ids)
{
    std::unordered_map<PointInt, int, PointIntHash> map_between_points_and_node_ids;

    // get a branching point
    for (const auto& elem : medial_nodes_points) {
        // get all lines that start or end with this point of graph
        auto point_id = elem.first;

        std::vector<LineStrip> line_strips;
        auto it = end_points_to_line_dict.find(point_id);
        if (it != end_points_to_line_dict.end() ) {
            line_strips = it->second;
        }

        // process all lines that outcome from this cluster point
        auto sz = line_strips.size();
        for (auto i = 0; i < sz; ++i) {
            // get current line
            auto curr_line = line_strips[i];

            PointInt mean_pos1;
            PointInt mean_pos2;

            const auto it1 = medial_nodes_points.find(curr_line.beg_p);
            if (it1 != medial_nodes_points.end()) {
                auto pts1 = it1->second;
                auto num1 = pts1.size();
                std::pair<int, int> sum_pt1 = std::accumulate(pts1.begin(), pts1.end(), std::make_pair(0, 0), pair_sum<int, int>());
                mean_pos1 = std::make_pair(static_cast<int>(sum_pt1.first / num1), static_cast<int>(sum_pt1.second / num1));
            }

            const auto it2 = medial_nodes_points.find(curr_line.end_p);
            if (it2 != medial_nodes_points.end()) {
                auto pts2 = it2->second;
                auto num2 = pts2.size();
                std::pair<int, int> sum_pt2 = std::accumulate(pts2.begin(), pts2.end(), std::make_pair(0, 0), pair_sum<int, int>());
                mean_pos2 = std::make_pair(static_cast<int>(sum_pt2.first / num2), static_cast<int>(sum_pt2.second / num2));
            }

            int node1_id {0};
            int node2_id {0};
//            auto node1_x = mean_pos1.second;
//            auto node1_y = mean_pos1.first;
//            auto node2_x = mean_pos2.second;
//            auto node2_y = mean_pos2.first;
            auto node1_x = mean_pos1.first;
            auto node1_y = mean_pos1.second;
            auto node2_x = mean_pos2.first;
            auto node2_y = mean_pos2.second;

            auto node1 = std::make_pair(node1_x, node1_y);
            auto node2 = std::make_pair(node2_x, node2_y);

            auto iter = map_between_points_and_node_ids.find(node1);
            if (iter != map_between_points_and_node_ids.end()) {
                node1_id = iter->second;
            }
            else {
                std::unordered_map<std::string, PointDouble> pos_map;
                pos_map["pos"] = std::make_pair(node1_x, node1_y); // + 0.5
                const auto it = _map_between_points_and_node_ids.find(pos_map["pos"]);
                if (it != _map_between_points_and_node_ids.end()) {
                    node1_id = it->second;
                }
                else {
                    // std::cerr << "Didn't find the correspondent node" << std::endl;
                    node1_id = -1;
                }
                graphNodes.push_back(std::make_pair(node1_id, pos_map));
                map_between_points_and_node_ids[node1] = node1_id;
            }


            auto iter2 = map_between_points_and_node_ids.find(node2);
            if (iter2 != map_between_points_and_node_ids.end()) {
                node2_id = iter2->second;
            }
            else {
                std::unordered_map<std::string, PointDouble> pos_map;
                pos_map["pos"] = std::make_pair(node2_x, node2_y); // + 0.5
                const auto it = _map_between_points_and_node_ids.find(pos_map["pos"]);
                if (it != _map_between_points_and_node_ids.end()) {
                    node2_id = it->second;
                }
                else {
                    // std::cerr << "Didn't find the correspondent node" << std::endl;
                    node2_id = -1;
                }
                graphNodes.push_back(std::make_pair(node2_id, pos_map));
                map_between_points_and_node_ids[node2] = node2_id;
            }

            if (node1_id != node2_id && node1_id != -1 && node2_id != -1) {
                // add edge to a graph
                auto edge = std::make_pair(node1_id, node2_id);
                graphEdges.insert(edge);
                edgesPoints[edge] = curr_line.points_list;
            }
        }
    }
}

std::vector<double> assessPath(const std::vector<PointDouble>& path_pts, double dist, double slope_dist)
{
    std::vector<double> alpha {};

    std::vector<PointDouble> splitted_projections;
    std::map<std::pair<PointDouble, PointDouble>, std::pair<PointDouble, PointDouble>> projection_points_to_segments;
    std::vector<PointDouble> splitted_points;
    std::vector<PointDouble> path_pts_or;
    double segments = eqi_path(path_pts, dist, splitted_projections, projection_points_to_segments, splitted_points, path_pts_or);


    if (segments != -1) {

        alpha = assess(projection_points_to_segments, splitted_projections, splitted_points, slope_dist);
    }

    return alpha;
}


std::vector<PointDouble> new_origin_pts(const std::vector<PointDouble>& path_pts)
{
    std::vector<PointDouble> res_pts(path_pts.size());

    // 1. change origin point to (0,0)
    for (auto i = 0; i < path_pts.size(); ++i) {
        res_pts[i] = std::make_pair(path_pts[i].first - path_pts[0].first, path_pts[i].second - path_pts[0].second);
    }

    // 1. change origin point to (0,0)
    for (auto i = 0; i < res_pts.size(); ++i) {
        res_pts[i] = std::make_pair(res_pts[i].first, -res_pts[i].second);
    }

    // 2. calculate an angle between (0,0) axes and our shifted line. (5,0) - any point on x-axes
    auto angle = calculate_angle(res_pts[0], std::make_pair(5., 0.), res_pts[res_pts.size() - 1]);

    // 1. recalculate coordinates with respect to rotation angle
    for (auto i = 0; i < res_pts.size(); ++i) {
        res_pts[i] = std::make_pair(res_pts[i].first * cos(angle) - res_pts[i].second * sin(angle), res_pts[i].first * sin(angle) + res_pts[i].second * cos(angle));
    }

    return res_pts;
}

std::vector<PointDouble> split(const PointDouble& start, const PointDouble& end, int segments)
{
    auto x_delta = (end.first - start.first) / segments;
    auto y_delta = (end.second - start.second) / segments;

    std::vector<PointDouble> points;
    for (int i = 0; i < segments; ++i) {
        points.push_back(std::make_pair(start.first + i * x_delta, start.second + i * y_delta)); // TOdo maybe just 0 here????
    }

    points.push_back(end);
    return points;
}



double eqi_path(const std::vector<PointDouble>& path_pts, double dist,
                std::vector<PointDouble>& splitted_projections,
                std::map<std::pair<PointDouble, PointDouble>, std::pair<PointDouble, PointDouble>>& projection_points_to_segments,
                std::vector<PointDouble>& splitted_points,
                std::vector<PointDouble>& path_pts_or)
{
    auto total_dist = calc_line_length(path_pts[0], path_pts[path_pts.size() - 1]);
    double eps = 1e-13;

    // ALERT: NOR VERY PRECISE!!!!!!!! Todo ceiling here!!!
    auto segments = static_cast<int>(ceil(total_dist / double(dist)));

    path_pts_or = new_origin_pts(path_pts);
    std::map<int, PointDouble> projections;

    for (auto i = 0; i < path_pts_or.size(); ++i) {
        if (i == 0) {
            projections[0] = path_pts_or[0];
        }
        else {
            if (i == path_pts_or.size() - 1) {
                projections[path_pts_or.size() - 1] = path_pts_or[path_pts_or.size() - 1];
                projection_points_to_segments[std::make_pair(projections[i-1], projections[i])] = std::make_pair(path_pts_or[i-1], path_pts_or[i]);
            }
            else {
                projections[i] = orthogonal_projection(path_pts_or[0], path_pts_or[path_pts_or.size() - 1], path_pts_or[i]);

                // Check for pathes which include back directed segments. TODO: smart criteria, not dist/2
                if (projections[i].first < projections[i-1].first) {
                    if (projections[i].first - projections[i-1].first > dist/2) {
                        // std::cerr << "Error! Found back direction on itearation " << i << " projections[i].x= "
                        // << projections[i].first << " projections[i-1].x= " << projections[i-1].first << std::endl;
                        return -1; // throw here or return something not valid TODO
                    }
                    else {
                        projection_points_to_segments[std::make_pair(projections[i], projections[i-1])] = std::make_pair(path_pts_or[i-1], path_pts_or[i]);
                    }
                }
                else {
                    projection_points_to_segments[std::make_pair(projections[i-1], projections[i])] = std::make_pair(path_pts_or[i-1], path_pts_or[i]);
                }
            }
        }
    }

    splitted_points = split(path_pts_or[0], path_pts_or[path_pts_or.size() - 1], segments);

    for (const auto& splitted_pt : splitted_points) {
        auto orthogonal_line = std::make_pair(std::make_pair(-splitted_pt.second + splitted_pt.first, splitted_pt.first + splitted_pt.second),
                                              std::make_pair(splitted_pt.second + splitted_pt.first, -splitted_pt.first + splitted_pt.second));

        for (const auto& segment_pair : projection_points_to_segments) {
            auto segment = segment_pair.first;

            // MAYBE ADD HERE < because of unknown order, or just check order by comparing projection_points_to_segments [0] and [1]


            double first1 {0};
            double second1 {0};
            double first2 {0};
            double second2 {0};

            if (segment.first.first < segment.second.first) {
                first1 = splitted_pt.first;
                second1 = segment.first.first;
                first2 = splitted_pt.first;
                second2 = segment.second.first;
            }
            // shoud Never get here
            else {
                //std::cerr << "shoud Never get here!!!!" << std::endl;
                second1 = splitted_pt.first;
                first1 = segment.first.first;
                second2 = splitted_pt.first;
                first2 = segment.second.first;
            }


            if ( (first1 >= second1) || (fabs(first1 - second1) < eps) ) {
                if ( (first2 <= second2) || (fabs(first1 - second2) < eps) ) {
                    // add here iterator. Use find to check if value is inside the map before using it
                    auto curr_segment = segment_pair.second;
                    // calculate intersection point between curr_segment and orthogonal_line
                    auto x1 = curr_segment.first.first;
                    auto x2 = curr_segment.second.first;
                    auto x3 = orthogonal_line.first.first;
                    auto x4 = orthogonal_line.second.first;
                    auto y1 = curr_segment.first.second;
                    auto y2 = curr_segment.second.second;
                    auto y3 = orthogonal_line.first.second;
                    auto y4 = orthogonal_line.second.second;

                    auto bot = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
                    double px {0.};
                    double py {0.};

                    if (fabs(bot) < eps) {
                        px = splitted_pt.first;
                        py = splitted_pt.second;
                    }
                    else {
                        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / bot;
                        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / bot;
                    }

                    splitted_projections.push_back(std::make_pair(px, py));
                    break;
                }
            }
        }
    }

    return segments;
}


std::vector<double> assess(const std::map<std::pair<PointDouble, PointDouble>, std::pair<PointDouble, PointDouble>>& projection_points_to_segments,
                           const std::vector<PointDouble>& path_pts,
                           const std::vector<PointDouble>& projections,
                           int slope_step)
{
    // std::cerr << "-------------Inside c++ assess" << std::endl;
    std::vector<double> x(path_pts.size()); // TODO
    std::vector<double> h(path_pts.size()); // TODO
    std::vector<double> delta_x(path_pts.size()); // TODO
    std::vector<double> delta_h(path_pts.size()); // TODO
    std::vector<double> slope(path_pts.size()); // TODO
    std::vector<double> f(path_pts.size()); // TODO
    std::vector<double> alpha(path_pts.size()); // TODO
    std::vector<double> h_left(path_pts.size());
    std::vector<double> h_right(path_pts.size());

    auto total_dist = calc_line_length(path_pts[0], path_pts[path_pts.size() - 1]);

    for (int i = 0; i < path_pts.size(); ++i) {
        if (i == 0) {
            delta_x[i] = 1;
            delta_h[i] = 0;
            f[i] = 0;
            alpha[i] = 0;
            slope[i] = 0;
            x[i] = 0;
            h[i] = 0;
            alpha[i] = 0;
        }
        else {
            // calculate x[i]. We already can get projections[i] from equi_path.
            auto x_l = (projections[i].first - slope_step > 0) ? (projections[i].first - slope_step) : 0;
            auto x_r = (projections[i].first + slope_step < total_dist) ? (projections[i].first + slope_step) : total_dist;

            auto projection_left = std::make_pair(x_l, projections[i].second);
            auto projection_right = std::make_pair(x_r, projections[i].second);
            auto x_left = calc_line_length(path_pts[0], projection_left);
            auto x_right = calc_line_length(path_pts[0], projection_right);

            // calculate h[i] TODO!!!! (not up to date todo)
            std::vector<PointDouble> projection = { projection_left, projection_right };
            std::vector<PointDouble> calculated_projection_on_line; // always only 2 values. change it

            const double eps = 1e-13;

            for (const auto& pj : projection) {
                auto pj_ = pj;
                auto orthogonal_line = std::make_pair(std::make_pair(-pj_.second + pj.first, pj_.first + pj.second), std::make_pair(pj_.second + pj.first, -pj_.first + pj.second));

                for (const auto& segment_pair : projection_points_to_segments) {

                    auto segment = segment_pair.first;
                    auto first1 = pj.first;
                    auto second1 = segment.first.first;
                    auto first2 = pj.first;
                    auto second2 = segment.second.first;

                    if (((fabs(first1 - second1) > eps) && (first1 > second1)) || (fabs(first1 - second1) < eps)) {
                        if (((fabs(first2 - second2) > eps) && (first2 < second2)) || (fabs(first2 - second2) < eps)) {
                            auto curr_segment = segment_pair.second;
                            // calculate intersection point between curr_segment and orthogonal_line
                            auto x1 = curr_segment.first.first;
                            auto x2 = curr_segment.second.first;
                            auto x3 = orthogonal_line.first.first;
                            auto x4 = orthogonal_line.second.first;
                            auto y1 = curr_segment.first.second;
                            auto y2 = curr_segment.second.second;
                            auto y3 = orthogonal_line.first.second;
                            auto y4 = orthogonal_line.second.second;

                            auto bot = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
                            double px {0};
                            double py {0};

                            if (fabs(bot) < eps) {
                                px = pj.first;
                                py = pj.second;
                            }
                            else {
                                px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3*y4 - y3 * x4)) / bot;
                                py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / bot;
                            }

                            calculated_projection_on_line.push_back(std::make_pair(px, py));
                            break;
                        }
                    }
                }
            }

            // TODO::: CHECK WHAT WE ARE DOING WITH GET_SIGHN. Showudn't we calculate sight for h_l and h_r separately?
            h_left[i] = calc_line_length(calculated_projection_on_line[0], projection_left);
            int sign_left = get_sign(calculated_projection_on_line[0], path_pts[0], path_pts[path_pts.size() - 1]);
            h_right[i] = calc_line_length(calculated_projection_on_line[1], projection_right);
            int sign_right = get_sign(calculated_projection_on_line[1], path_pts[0], path_pts[path_pts.size() - 1]);

            h[i] = calc_line_length(projections[i], path_pts[i]);
            int sign = get_sign(path_pts[i], path_pts[0], path_pts[path_pts.size() - 1]);
            if (sign < 0) {
                h[i] = -h[i];
            }

            if (sign_left < 0) {
                h_left[i] = -h_left[i];
            }

            if (sign_right < 0) {
                h_right[i] = -h_right[i];
            }

            delta_x[i] = x_right - x_left;
            delta_h[i] = h_right[i] - h_left[i];

            if (delta_x[i] < 0) {
                return std::vector<double>{}; // TODO indicate return error or throw an exception
            }

            if (fabs(delta_x[i]) < eps) {
                return std::vector<double>{}; // TODO indicate return error or throw an exception
            }

            // TODO try block here maybe
            slope[i] = delta_h[i] / delta_x[i];
            slope[i] = (fabs(slope[i]) < eps) ? 0 : slope[i];

            if (i != 1) {
                if (same_sign(h[i], h[i-1])) {
                    if (h[i] < 0) {
                        // both are negative
                        f[i] = slope[i] - slope[i-1];
                    }
                    else {
                        // both are positive
                        f[i] = slope[i-1] - slope[i];
                    }

                    f[i] = (fabs(f[i]) < eps) ? 0 : f[i];
                    alpha[i] = (f[i] < 0) ? fabs(f[i]) : 0;
                }
                else {
                    // TODO can be incorrect here
                    alpha[i] = fabs(slope[i]);
                }
            }
            else {
                alpha[i] = 0;
            }
        }
    }

    return alpha;
}

std::pair<std::pair<NodesType, EdgesType>, std::pair<int, int>> preprocessGraph(int start_id, int end_id) {
    try {
    // ToDay
//        start_id = old_id(start_id);
//        end_id = old_id(end_id);
        // TODO: add here check if start and end are in graph
        // std::cerr << "From node " << start_id << " to node " << end_id << std::endl;

        // save_graph(std::make_pair(graphEdges_sp, graphNodes_sp), "seeds_graph070617.txt");

        // // ACHTUNG !! AAAchen 24.08.2017 Need this during construct_graph to be able to map with stable points from Dmytro
        // fillGraph(graphEdges_sp, graphNodes_sp);

        PointDouble fake;
        transformed_points = recalculateCoordinates(graphNodes_sp, start_id, end_id, fake);

        auto dfs_res = DFS(transformed_points, start_id, end_id);
        dfs_graph = dfs_res.first;

        if (!dfs_res.second) {
            end_id = -1;
        }


        NodesType retNodes;
        EdgesType retEdges;

        for (const auto& el : dfs_graph) {
            for (auto to : el.second) {
                retEdges.insert(std::make_pair(el.first, to));
            }
        }

        for (auto id : all_nodes) {
            retNodes.push_back(std::make_pair(id, MappedPos{std::make_pair(pos, node_id_to_pt_good[id])}));
        }

        return std::make_pair(std::make_pair(retNodes, retEdges), std::make_pair(start_id, end_id)); // ToDay new_id(start_id), new_id(end_id))
    }
    catch(BadKeyException& error) {
        // std::cerr << error.what() << std::endl;
        throw;
    }
}

std::map<int, PointDouble> recalculateCoordinates(const NodesType& nds, int origin_id, int end_id, PointDouble& or5) {

    // Remove useless data (for e.g. "pos") from nds and store only {id:pt} pairs
    std::map<int, PointDouble> nodes;
    for (auto i = 0; i < nds.size(); ++i) {
        auto pt_it = nds[i].second.find(pos);
        if (pt_it != nds[i].second.end()) {
            nodes[nds[i].first] = pt_it->second; // ToDay new_id(nds[i].first)
        }
    }

    // 1. change origin point to (0,0). Origin point should be constant durin the whole loop
    for (auto& node : nodes) {
    // ToDay new_id(origin_id)
        node.second = std::make_pair(node.second.first - node_id_to_pt_good[origin_id].first,
                                     node.second.second - node_id_to_pt_good[origin_id].second);
    }

    //or5 = (5,0)
    or5 = std::make_pair(5.,0);
    //    // 2. change the sign of y coordinate
    //    for (auto& node : nodes) {
    //        node.second = std::make_pair(node.second.first, -node.second.second);
    //    }

    // 3. calculate an angle between (0,0) axes and our shifted line. (5,0) - any point on x-axes
    // TODO: add safe check for existing nodes

    // ToDay new_id(origin_id)
    auto angle = calculate_angle(nodes[origin_id], std::make_pair(5., 0.), nodes[end_id]);

    // 4. recalculate coordinates with respect to rotation angle
    for (auto& node : nodes) {
        auto x = node.second.first * cos(angle) - node.second.second * sin(angle);
        auto y = node.second.first * sin(angle) + node.second.second * cos(angle);
        node.second.first = (std::fabs(x) > eps) ? x : 0;
        node.second.second = (std::fabs(y) > eps) ? y : 0;
    }

    auto x5 = or5.first * cos(angle) - or5.second * sin(angle);
    auto y5 = or5.first * sin(angle) + or5.second * cos(angle);
    or5.first = (std::fabs(x5) > eps) ? x5 : 0;
    or5.second = (std::fabs(y5) > eps) ? y5 : 0;

//#ifdef CPPDEBUG
//    std::cout << "\nMapping after angle rotation:" << std::endl;
//    for (const auto& el : nodes) {
//        std::cout << el.first << " -> " << "(" << el.second.first << ", " << el.second.second << ")" << std::endl;
//    }
//#endif // CPPDEBUG

    return nodes;
}

void fillGraph(const EdgesType& graphEdges, const NodesType& nds) {

#ifdef CPPDEBUG
#include <fstream>

#endif // CPPDEBUG

    for (auto i = 0; i < nds.size(); ++i) {
        auto pt_it = nds[i].second.find(pos);
        if (pt_it != nds[i].second.end()) {
            // Map indeces of nodes to new indeces to be able to use them as index of vector [0..nds.size()]
            // ToDay
//            new_node_id_to_node_id_good[i] = nds[i].first;
//            node_id_to_new_node_id_good[nds[i].first] = i;

            // Map each node's new id to its coordinates

            // ToDay i -> nds[i].first ??? Maybe we should remove this at all, wif we have another id->coord map
            node_id_to_pt_good[nds[i].first] = pt_it->second;
            node_pt_to_id_good[pt_it->second] = nds[i].first;
        }
    }

//#ifdef CPPDEBUG
//    std::cout << "Mapping old_id -> new_id:" << std::endl;
//    for (const auto& el : node_id_to_new_node_id_good) {
//        std::cout << el.first << " -> " << el.second << std::endl;
//    }
//
//    std::cout << "Mapping new_id -> coordinates:" << std::endl;
//    for (const auto& el : node_id_to_pt_good) {
//        std::cout << el.first << " -> (" << el.second.first << ", " << el.second.second << ")" << std::endl;
//    }
//#endif // CPPDEBUG

    global_graph.resize(nds.size());

    for (const auto& edge : graphEdges) {
        try {
            // Convert nodes' ids from old to new ids and add them into graph
            // ToDay new_id(edge.first) new_id(edge.second)
            auto node1_id = edge.first;
            auto node2_id = edge.second;

            global_graph[node1_id].insert(node2_id);
            global_graph[node2_id].insert(node1_id);
        }
        catch(BadKeyException& error) {
            // std::cerr << error.what() << std::endl;
        }
    }

#ifdef CPPDEBUG
    printGraph(global_graph);
#endif // CPPDEBUG
}

void printGraph(const std::vector<std::unordered_set<int>>& graph) {
//    std::cout << "Printing graph:" << std::endl;
//    for (auto i = 0; i < graph.size(); ++i) {
//        for (auto to : graph[i]) {
//            std::cout << "From " << i << " to " << to << std::endl;
//        }
//    }
//
//    std::cout << "Back to the original:" << std::endl;
//    for (auto i = 0; i < graph.size(); ++i) {
//        for (auto to : graph[i]) {
//            try {
//            // ToDay old_id(i) old_id(to)
//                std::cout << "From " << i << " to " << to << std::endl;
//            }
//            catch(BadKeyException& error) {
//                std::cerr << error.what() << std::endl;
//            }
//        }
//    }
}

void printOrderedGraph(const std::unordered_map<int, std::unordered_set<int>>& graph) {
//    std::cout << "Printing ordered graph:" << std::endl;
//    for (const auto& node : graph) {
//        for (int to : node.second) {
//            std::cout << "From " << node.first << " to " << to << std::endl;
//        }
//    }
}

std::pair<std::map<int, std::set<int>>, bool> DFS(const std::map<int, PointDouble>& id_to_pt, int start_node_id, int end_node_id) {

    bool reachable_end = false;
    bool reachable_start = false;
    // change node id from input graph to processed new id
    // ToDay
//    start_node_id = start_node_id;
//    end_node_id = end_node_id;

    auto find_start = id_to_pt.find(start_node_id);
    auto find_end = id_to_pt.find(end_node_id);

    // should be in map
    if (find_start == id_to_pt.end() || find_end == id_to_pt.end()) {
        throw BadKeyException(" DFS ");
    }

    auto x_start = find_start->second.first;
    auto x_end = find_end->second.first;


    const int back_thresh = 3;

    // for each node we have a set of points from which we came to this point
    std::map<int, std::set<int>> came_backwards;
    std::map<int, std::set<int>> went_backwards;

    // Add all nodes to dead set
    std::set<int> dead_nodes;

    std::map<int, std::set<int>> result_graph_o;
    std::map<int, std::set<int>> result_graph_i;

    std::queue<int> q;
    q.push(start_node_id);

    std::map<int, bool> used;
    used[start_node_id] = true;

    while (!q.empty()) {
        int v = q.front();
        q.pop();

        for (int to : global_graph[v]) {

            auto find_v = id_to_pt.find(v);
            auto find_to = id_to_pt.find(to);

            // should be in map
            if (find_v == id_to_pt.end() || find_to == id_to_pt.end()) {
                throw BadKeyException(" DFS ");
            }

            auto v_x = find_v->second.first;
            auto to_x = find_to->second.first;

            if (to_x < (x_start - back_thresh) || to_x > (x_end + back_thresh)) {
                continue;
            }


            // Allow small step backwards
            if (v_x >= to_x) {
                auto p_diff = v_x - to_x;
                if (p_diff >= back_thresh) {
                    continue;
                }
                else {
                    // add to a map a parent point for each node we reached moving backwards
                    came_backwards[to].insert(v);
                    went_backwards[v].insert(to);
                }
            }


            auto in_used = used.find(to);
            if (in_used == used.end()) {
                used[to] = true;
                q.push(to);
            }

            result_graph_o[v].insert(to);
            result_graph_i[to].insert(v);
            all_nodes.insert(to);
            all_nodes.insert(v);
        }
    }

//#ifdef CPPDEBUG
//    std::cout << "\nResult graph_o after DFS" << std::endl;
//    for (const auto& s : result_graph_o) {
//        std::cout << s.first << " : ";
//        for (const auto& el : s.second) {
//            std::cout << el << " ";
//        }
//        std::cout << std::endl;
//    }
//#endif // CPPDEBUG

//#ifdef CPPDEBUG
//    std::cout << "\nResult graph_i after DFS" << std::endl;
//    for (const auto& s : result_graph_i) {
//        std::cout << s.first << " : ";
//        for (const auto& el : s.second) {
//            std::cout << el << " ";
//        }
//        std::cout << std::endl;
//    }
//#endif // CPPDEBUG


    // Add nodes without outgoing edges to a set of dead_nodes
    for (auto el : all_nodes) {
        if (el != start_node_id && el != end_node_id) {
            // first outgoing edges
            auto found_it = result_graph_o.find(el);
            if (found_it == result_graph_o.end()) {
                // Add nodes without outgoing edges to a set of dead_nodes
                dead_nodes.insert(el);
                continue;
            }
            else {
                // we have outgoing edges
                auto in_neighbs = result_graph_i.find(el);
                if (in_neighbs != result_graph_i.end()) {
                    // we have incoming edge
                    auto came_from = came_backwards.find(el);
                    if (came_from != came_backwards.end()) {
                        auto b_in = came_from->second.size();

                        auto in_neigbs_c = in_neighbs->second.size();
                        if (in_neigbs_c == b_in && b_in == found_it->second.size() && b_in == 1) {
                            dead_nodes.insert(el);
                            continue;
                        }
                    }

                    auto went_to = went_backwards.find(el);
                    if (went_to != went_backwards.end()) {
                        auto b_out = went_to->second.size();

                        auto out_neigbs_c = found_it->second.size();
                        if (out_neigbs_c == b_out && b_out == in_neighbs->second.size() && b_out == 1) {
                            dead_nodes.insert(el);
                            continue;
                        }
                    }
                }
                else {
                    // Add nodes without incoming edges to a set of dead_nodes
                    dead_nodes.insert(el);
                    continue;
                }
            }
        }
    }


    removeDeadNodes(dead_nodes, result_graph_o, result_graph_i, came_backwards, went_backwards, start_node_id, end_node_id);

    // std::cout << "\nResult graph_o after REMOVE_DEAD" << std::endl;
    for (const auto& s : result_graph_o) {
        // std::cout << s.first << " : ";
        for (const auto& el : s.second) {
            if (el == end_node_id) {
                // Everything is ok, the end is reachable from start (seems to be so)
                reachable_end = true;
            }
            // std::cout << el << " ";
        }
        // std::cout << std::endl;
    }

    // std::cout << "\nResult graph_i after REMOVE_DEAD" << std::endl;
    for (const auto& s : result_graph_i) {
        // std::cout << s.first << " : ";
        for (const auto& el : s.second) {
            if (el == start_node_id) {
                // Everything is ok, the start is reachable (seems to be so)...seems to be a stupid fix
                reachable_start = true;
            }
            // std::cout << el << " ";
        }
        // std::cout << std::endl;
    }


    return std::make_pair(result_graph_o, reachable_start && reachable_end);
}

void removeDeadNodes(std::set<int>& dead_nodes,
                     std::map<int, std::set<int>>& graph_o,
                     std::map<int, std::set<int>>& graph_i,
                     std::map<int, std::set<int>>& came_backwards,
                     std::map<int, std::set<int>>& went_backwards,
                     int start_node,
                     int end_node) {


    while (!dead_nodes.empty()) {
        int dead_node = *(dead_nodes.begin());

        auto in_neighbs = graph_i.find(dead_node);
        if (in_neighbs != graph_i.end()) {
            // there are edges (edge_id -> dead_node)
            for (auto in_n : in_neighbs->second) {

                auto found_o = graph_o.find(in_n);
                if (found_o != graph_o.end()) {
                    // we can now remove dead node from list of outneighbours of his neighbour
                    found_o->second.erase(dead_node);

                    // now check if neighbour has become a dead_node
                    if (found_o->second.empty()) {
                        if (in_n == end_node) {
                            // do not remove start-end                            graph_o.erase(in_n);
                            went_backwards.erase(in_n);
                        }
                        else {
                            // no more outgoing neighbours, just add to dead_nodes
                            dead_nodes.insert(in_n);
                        }
                    }
                    else {
                        // ---------------------

                        // we have outgoing edges

                        // -- today
                        auto in_neighbs = graph_i.find(in_n);
                        if (in_neighbs != graph_i.end()) {

                            // we can now remove dead node from list of inneighbours of his neighbour
                            in_neighbs->second.erase(dead_node);

                            // now check if neighbour has become a dead_node
                            if (in_neighbs->second.empty()) {
                                if (in_n == start_node) {
                                    came_backwards.erase(in_n);
                                    // do not remove start-end                                    graph_i.erase(in_n);
                                }
                                else {
                                    // no more outgoing neighbours, just add to dead_nodes
                                    dead_nodes.insert(in_n);
                                }
                            }
                            else {

                                // we have incoming edge
                                auto came_from = came_backwards.find(in_n);
                                if (came_from != came_backwards.end()) {

                                    // remove dead node from a set of nodes from which we came using back
                                    came_from->second.erase(dead_node);
                                    if (came_from->second.empty()) {
                                        // no more other back comings, so remove neighbour from came_backwards
                                        came_backwards.erase(came_from);
                                    }

                                    auto came_from2 = came_backwards.find(in_n);
                                    if (came_from2 != came_backwards.end()) {
                                        auto b_in = came_from2->second.size();

                                        auto in_neigbs_c = in_neighbs->second.size();
                                        if (in_neigbs_c == b_in && b_in == found_o->second.size() && b_in == 1) {
                                            if (in_n != start_node && in_n != end_node) {
                                                dead_nodes.insert(in_n);
                                                // continue; commented it today
                                            }
                                        }
                                    }
                                }

                                auto went_to = went_backwards.find(in_n);
                                if (went_to != went_backwards.end()) {

                                    // remove dead node from a set of nodes from which we go using back
                                    went_to->second.erase(dead_node);
                                    if (went_to->second.empty()) {
                                        // no more other back comings, so remove neighbour from came_backwards
                                        went_backwards.erase(went_to);
                                    }

                                    auto went_to2 = went_backwards.find(in_n);
                                    if (went_to2 != went_backwards.end()) {
                                        auto b_out = went_to2->second.size();

                                        auto out_neighbs = graph_o.find(in_n);
                                        if (out_neighbs != graph_o.end()) {
                                            auto out_neigbs_c = out_neighbs->second.size();
                                            if (out_neigbs_c == b_out && b_out == in_neighbs->second.size() && b_out == 1) {
                                                if (in_n != start_node && in_n != end_node) {
                                                    dead_nodes.insert(in_n);
                                                    //continue; commented today
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // The same for outgoing neighbours
        auto out_neighbs = graph_o.find(dead_node);
        if (out_neighbs != graph_o.end()) {
            // there are edges (dead_node -> edge_id)
            for (auto out_n : out_neighbs->second) {
                auto found_i = graph_i.find(out_n);
                if (found_i != graph_i.end()) {
                    // we can now remove dead node from list of inneighbours of his neighbour
                    found_i->second.erase(dead_node);

                    // now check if neighbour has become a dead_node
                    if (found_i->second.empty()) {
                        if (out_n == start_node) {
                            // do not remove start-end                            graph_i.erase(out_n);
                            came_backwards.erase(out_n);
                        }
                        else {
                            // no more incoming neighbours, just add to dead_nodes
                            dead_nodes.insert(out_n);
                        }
                    }
                    else {
                        // ---------------------
                        // we have incoming edges


                        auto found_o = graph_o.find(out_n);
                        if (found_o != graph_o.end()) {
                            // we have outgoing edges

                            // we can now remove dead node from list of outneighbours of his neighbour
                            found_o->second.erase(dead_node);

                            // now check if neighbour has become a dead_node
                            if (found_o->second.empty()) {
                                if (out_n == end_node) {
                                    // do not remove start-end                                    graph_o.erase(out_n);
                                    went_backwards.erase(out_n);
                                }
                                else {
                                    // no more incoming neighbours, just add to dead_nodes
                                    dead_nodes.insert(out_n);
                                }
                            }
                            else {

                                // -- today
                                auto came_from = came_backwards.find(out_n);
                                if (came_from != came_backwards.end()) {

                                    // remove dead node from a set of nodes from which we came using back
                                    came_from->second.erase(dead_node);
                                    if (came_from->second.empty()) {
                                        // no more other back comings, so remove neighbour from came_backwards
                                        came_backwards.erase(came_from);
                                    }

                                    auto came_from2 = came_backwards.find(out_n);
                                    if (came_from2 != came_backwards.end()) {
                                        auto b_in = came_from2->second.size();

                                        auto found_o_c = found_o->second.size();
                                        if (found_o_c == b_in && b_in == found_i->second.size() && b_in == 1) { // TODO::: AAAAA
                                            if (out_n != start_node && out_n != end_node) {
                                                dead_nodes.insert(out_n);
                                                // continue; commented it today
                                            }
                                        }
                                    }
                                }

                                auto went_to = went_backwards.find(out_n);
                                if (went_to != went_backwards.end()) {

                                    // remove dead node from a set of nodes from which we go using back
                                    went_to->second.erase(dead_node);
                                    if (went_to->second.empty()) {
                                        // no more other back comings, so remove neighbour from came_backwards
                                        went_backwards.erase(went_to);
                                    }

                                    auto went_to2 = went_backwards.find(out_n);
                                    if (went_to2 != went_backwards.end()) {
                                        auto b_out = went_to2->second.size();

                                        auto out_neighbs_in = graph_o.find(out_n);
                                        if (out_neighbs_in != graph_o.end()) {
                                            auto out_neigbs_c = out_neighbs_in->second.size();
                                            if (out_neigbs_c == b_out && b_out == found_o->second.size() && b_out == 1) {
                                                if (out_n != start_node && out_n != end_node) {
                                                    dead_nodes.insert(out_n);
                                                }
                                                //continue; commented today
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        graph_i.erase(dead_node);
        graph_o.erase(dead_node);
        dead_nodes.erase(dead_node);
        all_nodes.erase(dead_node);
        came_backwards.erase(dead_node);
        went_backwards.erase(dead_node);
    }
}


PointInt neighbor_of(const BinaryImage& image, int x, int y) {
    auto h = imHeight(image);
    auto w = imWidth(image);

    for (int _x = -1; _x < 2; ++_x) {
        if ((x + _x >= 0) && (x + _x < w)) {
            for (int _y = -1; _y < 2; ++_y) {
                if (_x == 0  && _y == 0) {
                    continue;
                }
                if ((y + _y >= 0) && (y + _y < h)) {
                    if (image[y + _y][x + _x]) {
                        return std::make_pair(x + _x, y + _y);
                    }
                }
            }
        }
    }
    return std::make_pair(-1,-1);
}


double angle(const PointInt& p1, const PointInt& p2, const PointInt& p3) {
    return (atan2(p2.second - p1.second, p2.first - p1.first) - atan2(p3.second - p1.second, p3.first - p1.first));
}

double dist(const PointInt& p1, const PointInt& p2, const PointInt& p) {
    auto top = std::abs((p2.second - p1.second)*p.first -(p2.first - p1.first)*p.second + p2.first*p1.second - p2.second*p1.first);
    auto bot = sqrt((p2.second - p1.second)*(p2.second - p1.second) + (p2.first - p1.first)*(p2.first - p1.first));
    return top / bot;
}

double calcDist(const PointDouble& p1, const PointDouble& p2)
{
    auto x1 = p2.first - p1.first;
    auto x2 = p2.second - p1.second;
    return sqrt(x1 * x1 + x2 * x2);
}


double vector_dot(const PointDouble& a,const PointDouble& b)
{
    return (a.first * b.first) + (a.second * b.second); //  + (a->z * b->z)
}

double calc_line_length(const PointDouble& p1, const PointDouble& p2)
{
    PointDouble res = std::make_pair(0, 0);
    res.first = p1.first - p2.first;
    res.second = p1.second - p2.second;


    return sqrt(vector_dot(res, res)); // NOT SURE IF THIS IS CORRECT
}

double calculate_angle(const PointDouble& central_p1, const PointDouble& p2, const PointDouble& p3)
{
    return atan2(p2.second - central_p1.second, p2.first - central_p1.first)
    - atan2(p3.second - central_p1.second, p3.first - central_p1.first);
}

PointDouble orthogonal_projection(PointDouble P0, PointDouble P1, PointDouble P)
{
    double center_diff = P0.second;
    P1.second -= center_diff;
    P.second -= center_diff;

    P1.first -= P0.first;
    P.first -= P0.first;

    auto top = vector_dot(P, P1);
    auto bot = vector_dot(P1, P1);

    auto coeff = top / bot;
    PointDouble proj = std::make_pair(coeff * P1.first + P0.first, coeff * P1.second + center_diff);

    return proj;
}

int get_sign(const PointDouble& A, const PointDouble& p1, const PointDouble& p2)
{
    auto xA = A.first;
    auto yA = A.second;
    auto x1 = p1.first;
    auto y1 = p1.second;
    auto x2 = p2.first;
    auto y2 = p2.second;

    auto v1 = std::make_pair(x2-x1, y2-y1);   // Vector 1
    auto v2 = std::make_pair(x2-xA, y2-yA);  // Vector 2

    auto xp = v1.first*v2.second - v1.second*v2.first;  // Cross product
    double eps = 1e-13;
    if ((xp > 0) && (xp > eps)) {
        // on same side
        return 1;
    }
    else {
        if ((xp < 0) && (fabs(xp) > eps)) {
            // on different sides
            return -1;
        }
        else {
            // on the line
            return 0;
        }
    }
}

//int new_id(int old_index) {
//    auto it = node_id_to_new_node_id_good.find(old_index);
//
//    if (it != new_node_id_to_node_id_good.end()) {
//        return it->second;
//    }
//    else {
//        throw BadKeyException(" new_id ");
//    }
//}
//
//int old_id(int new_index) {
//    auto it = new_node_id_to_node_id_good.find(new_index);
//    if (it != new_node_id_to_node_id_good.end()) {
//        return it->second;
//    }
//    else {
//        throw BadKeyException(" old_id ");
//    }
//}

void save_graph(const std::pair<EdgesType, NodesType>& edges_nodes, const std::string& filename) {
    std::ofstream ofile(filename);
    auto edges = edges_nodes.first;
    auto nodes = edges_nodes.second;
    for (const auto& pr : edges) {
        ofile << pr.first << " " << pr.second << std::endl;
    }

    ofile << "Nodes" << std::endl;

    for (const auto& pr : nodes) {
        ofile << pr.first << " ";
        auto point_it = pr.second.find(pos);
        if (point_it != pr.second.end()) {
            auto point = point_it->second;
            ofile << point.first << " " << point.second << std::endl;
        }
    }
}

// Todo: add here safe check with find
bool point_in_segment(double x, const PointInt& edge, std::map<int, PointDouble>& coords) {
    if (coords[edge.first].first < x) {
        if (x < coords[edge.second].first) {
            return true;
        }
    }
    return false;
}

struct less_than_vecpairs
{
    //std::vector<std::pair<const double, PointDouble>>
    inline bool operator() (const std::pair<double, PointDouble>& struct1, const std::pair<double, PointDouble>& struct2)
    {
        return (struct1.first < struct2.first);
    }
};

PointDouble originalCoordinates(const PointDouble& recalced,
                                const PointDouble& origin,
                                const PointDouble& end_,
                                const PointDouble& or5) {

    auto angle = calculate_angle(std::make_pair(0, 0), std::make_pair(5, 0), or5);

    auto x = recalced.first * cos(angle) - recalced.second * sin(angle);
    auto y = recalced.first * sin(angle) + recalced.second * cos(angle);
    PointDouble rec = std::make_pair(x + origin.first, y + origin.second);
    rec.first = (std::fabs(rec.first) > eps) ? rec.first : 0;
    rec.second = (std::fabs(rec.second) > eps) ? rec.second : 0;

    return rec;
}

std::pair<int, int> get_ids(const PointInt& origin_p, const PointInt& end_p) {
    int start_id {-1};
    int end_id {-1};

    for (const auto& node : medial_nodes_indexes_sp) {
        if (node.first.first == origin_p.second && node.first.second == origin_p.first) {
            start_id = node.second;
            continue;
        }
        if (node.first.first == end_p.second && node.first.second == end_p.first) {
            end_id = node.second;
        }
    }

    return std::make_pair(start_id, end_id);
}

std::vector<PointInt> graphPathToSkeleton(const std::vector<int>& path) {

    std::vector<PointInt> total_path;

    // std::cerr << "Path: " << std::endl;
    //    for (const auto& p : path) {
    //        std::cerr << p << std::endl;
    //    }

    for (int i = 0; i < path.size() - 1; ++i) {
        auto id = path[i];
        // std::cerr << "id: " << id << std::endl;

        // ToDay old_id(id)
        auto it = end_points_to_line_dict.find(id);
        if (it != end_points_to_line_dict.end()) {

            // std::cerr << "I'm here!" << std::endl;

            auto next_id = path[i+1];
            for (const auto& strip : it->second) {

                // std::cerr << "I'm here inside! " << strip.beg_p << " " << strip.end_p << std::endl;

                // ToDay old_id(id) old_id(next_id)
                if (strip.beg_p == id && strip.end_p == next_id) {

                    // std::cerr << "Never in first!" << std::endl;

                    total_path.insert(total_path.end(), strip.points_list.begin(), strip.points_list.end());
                }

                // TODO: Check, do we really need to append here with reverse
                // ToDay old_id(id) old_id(next_id)
                if (strip.beg_p == next_id && strip.end_p == id) {

                    // std::cerr << "Never in second!" << std::endl;

                    total_path.insert(total_path.end(), strip.points_list.rbegin(), strip.points_list.rend());
                }
            }
        }
    }

    return total_path;
}


// for Aachen find neighbours for stablepoints
void findStableNeighbours() {

    // TODO: just go through all nodes and check which are stable

    for (const auto& st_id : stable_branchings) {

        // ToDay new_id(st_id)
        //std::cerr << "Not Happy Day! id = " << id << std::endl;
        std::queue<int> q;
        q.push(st_id);

        std::map<int, bool> used;
        used[st_id] = true;

        while (!q.empty()) {

            int v = q.front();
            //std::cerr << "Not Happy Day! v = " << v << std::endl;
            q.pop();

            for (int to : global_graph[v]) {
                //std::cerr << "Not Happy Day! to = " << to << std::endl;
                auto in_used = used.find(to);
                if (in_used == used.end()) {
                    used[to] = true;

                    // ToDay old_id(to)
                    auto found_stable = stable_branchings.find(to);

                    if (found_stable == stable_branchings.end()) {
                        //std::cerr << "Not Happy Day!  didn't find stable to " << to << std::endl;
                        q.push(to);
                    }
                    else {
                        node_to_stable_neighbs[st_id].insert(to);
                        //std::cerr << "Not Happy Day! found stable to " << to << std::endl;
                    }
                }
            }
        }
    }
}


std::unordered_map<int, std::unordered_set<int>> getStable() {
    return node_to_stable_neighbs;
}

void clearGlobals() {

    dfs_graph.clear();
    transformed_points.clear();

//    // no need to clear. Just in case of any problems try this.
//    global_graph.clear();
//    node_id_to_pt_good.clear();
//    node_pt_to_id_good.clear();
//    new_node_id_to_node_id_good.clear();
//    node_id_to_new_node_id_good.clear();

    all_nodes.clear();
}