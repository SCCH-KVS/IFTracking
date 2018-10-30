//
//  ImageProcessing.h
//  ImProLib
//
//  Created by Roman on 12.07.17.
//  Copyright © 2017 Roman. All rights reserved.
//

#ifndef ImageProcessing_h
#define ImageProcessing_h

#include <stdio.h>
#include <vector>
#include <string>
#include <unordered_map>
#include <map>
#include <unordered_set>
#include <set>
#include <numeric>
#include <iostream>

using PointInt = std::pair<int, int>;
using PointDouble = std::pair<double, double>;

using ImageInt = std::vector<std::vector<int>>;
using ImageDouble = std::vector<std::vector<double>>;

using LineInt = std::vector<PointInt>;
using LineDouble = std::vector<PointDouble>;
using BinaryImage = ImageInt; // redundant, but ok

using MappedPos = std::unordered_map<std::string, PointDouble>;
using EdgesType = std::set<PointInt>;
using NodesType = std::vector<std::pair<int, MappedPos>>;
using PairOfPoints = std::pair<PointDouble, PointDouble>;

using ReturnType = std::pair<NodesType, EdgesType>;

const std::string pos = "pos";
const double eps = 1e-13;


ImageInt createIntImage(ImageInt::size_type width = 0, ImageInt::size_type height = 0, int def = 0);
ImageDouble createDoubleImage(ImageDouble::size_type width = 0, ImageDouble::size_type height = 0, double def = 0);
ImageInt::size_type imWidth(const ImageInt& img);
ImageInt::size_type imHeight(const ImageInt& img);
ImageDouble::size_type imWidth(const ImageDouble& img);
ImageDouble::size_type imHeight(const ImageDouble& img);

//template <>
struct PointIntHash {
public:
    size_t operator()(std::pair<int, int> x) const throw() {
        size_t h = x.first ^ x.second;
        return h;
    }
};

//template <>
struct PointDoubleHash {
public:
    size_t operator()(std::pair<double, double> x) const throw() {
        size_t h = static_cast<int>(x.first) ^ static_cast<int>(x.second);
        return h;
    }
};

template <typename T1, typename T2>
struct pair_sum : public std::binary_function< std::pair<T1,T2>, std::pair<T1,T2>, std::pair<T1,T2> >
{
    std::pair<T1,T2> operator()(const std::pair<T1,T2>& lhs, const std::pair<T1,T2>& rhs)
    {
        return std::pair<T1,T2>(lhs.first + rhs.first, lhs.second + rhs.second);
    }
};

struct LineStrip
{
    LineStrip(const LineInt& pl, int bp, int ep, int idx)
    {
        points_list = pl;
        beg_p = bp;
        end_p = ep;
        id = idx;
    }

    LineInt points_list;
    int beg_p;
    int end_p;
    int id;
};

template<class T>
int calculate_neighbours(const T& skeleton, LineInt& neighbours, int x, int y)
{
    int neighbours_sum {0};
    auto h = imHeight(skeleton);
    auto w = imWidth(skeleton);

    for (int _x = -1; _x < 2; ++_x) {
        if ((x + _x >= 0) && (x + _x < w)) {
            for (int _y = -1; _y < 2; ++_y) {
                if (_x == 0  && _y == 0) {
                    continue;
                }
                if ((y + _y >= 0) && (y + _y < h)) {
                    if (skeleton[y + _y][x + _x]) {
                        neighbours.push_back(std::make_pair(x + _x, y + _y));
                        ++neighbours_sum;
                    }
                }
            }
        }
    }

    return neighbours_sum;
}

void flood_fill_neighbours(const ImageDouble& skeleton, ImageInt& mask, std::unordered_map<PointInt, int, PointIntHash>& medial_nodes_indexes,
                           std::unordered_map<int, LineInt>& medial_nodes_points, int x, int y, int branching_index, LineInt& added_pts);

ReturnType construct_graphs(const ImageDouble& skeleton, const ImageDouble& stable_mask);
//ImageDouble pruneSkeleton(const ImageDouble& skeleton);

// sparse graph
void separate_sparse_neighbours(const ImageDouble& skeleton, ImageInt& line_strip_image, ImageInt& medial_nodes_image,
                                std::unordered_map<PointInt, int, PointIntHash>& medial_nodes_indexes,
                                std::unordered_map<int, LineInt>& medial_nodes_points);
void trace_sparse_lines(ImageDouble& skeleton,
                        BinaryImage& line_strip_image,
                       const BinaryImage& medial_nodes_image,
                       const std::unordered_map<PointInt, int, PointIntHash>& medial_nodes_indexes,
                       std::unordered_map<int, std::vector<LineStrip>>& end_points_to_line_dict);
PointInt neighbor_of(const BinaryImage& image, int x, int y);
void build_sparse_graph(const std::unordered_map<int, LineInt>& medial_nodes_points,
                        const std::unordered_map<int, std::vector<LineStrip>>& end_points_to_line_dict,
                        std::vector<std::pair<int, std::unordered_map<std::string, PointDouble>>>& graphNodes,
                        EdgesType& graphEdges, std::unordered_map<PointInt, LineInt, PointIntHash>& edgesPoints,
                        const std::unordered_map<PointInt, int, PointIntHash>& _map_between_points_and_node_ids);
std::vector<double> getCurvature(const std::vector<PointInt>& vecContourPoints, int step = 1);
double calcDist(const PointDouble& p1, const PointDouble& p2);


template <class T>
void printImage(const T& image) {
    // 1.5 Print the skeleton
    for (int j = 0; j < imHeight(image); ++j) {
        for (int i = 0; i < imWidth(image); ++i) {
            std::cout << image[j][i];
        }
        std::cout << std::endl;
    }
}

double angle(const PointInt& p1, const PointInt& p2, const PointInt& p3);
double dist(const PointInt& p1, const PointInt& p2, const PointInt& p);

// --------- assessment----------
std::vector<double> assessPath(const std::vector<PointDouble>& path_pts, double dist, double slope_dist);
double vector_dot(const PointDouble& a,const PointDouble& b);
double calc_line_length(const PointDouble& p1, const PointDouble& p2);
double calculate_angle(const PointDouble& central_p1, const PointDouble& p2, const PointDouble& p3);
std::vector<PointDouble> new_origin_pts(const std::vector<PointDouble>& path_pts);
PointDouble orthogonal_projection(PointDouble P0, PointDouble P1, PointDouble P);
std::vector<PointDouble> split(const PointDouble& start, const PointDouble& end, int segments);

double eqi_path(const std::vector<PointDouble>& path_pts, double dist, std::vector<PointDouble>& splitted_projections,
                std::map<std::pair<PointDouble, PointDouble>, std::pair<PointDouble, PointDouble>>& projection_points_to_segments,
                std::vector<PointDouble>& splitted_points, std::vector<PointDouble>& path_pts_or);

int get_sign(const PointDouble& A, const PointDouble& p1, const PointDouble& p2);

template<typename T>
bool same_sign(T l1, T l2) {
    if (((l1 >= 0) && (l2 >= 0)) || ((l1 <= 0) && (l2 <= 0))) {
        return true;
    }
    else {
        return false;
    }
}

std::vector<double> assess(const std::map<std::pair<PointDouble, PointDouble>, std::pair<PointDouble, PointDouble>>& projection_points_to_segments,
                           const std::vector<PointDouble>& path_pts, const std::vector<PointDouble>& projections, int slope_step);
//-------------------------------




class BadKeyException : public std::runtime_error {
public:
    BadKeyException(const std::string& msg) : std::runtime_error(std::string("Not existing key used") + msg) { }
};


std::pair<std::pair<NodesType, EdgesType>, std::pair<int, int>> preprocessGraph(int start_id, int end_id);
void fillGraph(const EdgesType& graphEdges, const NodesType& nds);
void printGraph(const std::vector<std::unordered_set<int>>& graph);
std::map<int, PointDouble> recalculateCoordinates(const NodesType& nds, int origin_id, int end_id, PointDouble& or5);
std::pair<std::map<int, std::set<int>>, bool> DFS(const std::map<int, PointDouble>& id_to_pt,
                                 int start_node_id,
                                 int end_node_id);
void removeDeadNodes(std::set<int>& dead_nodes,
                     std::map<int, std::set<int>>& graph_i,
                     std::map<int, std::set<int>>& graph_o,
                     std::map<int, std::set<int>>& came_backwards,
                     std::map<int, std::set<int>>& went_backwards,
                     int start_node,
                     int end_node);

void save_graph(const std::pair<EdgesType, NodesType>& edges_nodes, const std::string& filename);

// special for Aachen
std::pair<int, int> get_ids(const PointInt& origin_p, const PointInt& end_p);
std::vector<PointInt> graphPathToSkeleton(const std::vector<int>& path);

void findStableNeighbours();
std::unordered_map<int, std::unordered_set<int>> getStable();
void clearGlobals();
#endif /* ImageProcessing_h */
