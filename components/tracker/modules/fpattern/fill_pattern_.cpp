//
//  main.cpp
//  FillPattern
//
//  Created by Dmytro Kotsur on 15/03/2017.
//  Copyright © 2017 Dmytro Kotsur. All rights reserved.
//

#include "fill_pattern_.h"
#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>

const double EPSILON = 1.0e-7;


std::vector<std::vector<double>> fillPatternFromImage(const std::vector<std::vector<bool>> &image,
                                                      const std::vector<std::vector<double>> &pattern) {


    size_t width = image[0].size(), height = image.size();
    size_t pattern_width = pattern[0].size(), pattern_height = pattern.size();

    if (pattern_width % 2 != 1 || pattern_height % 2 != 1) {
        return std::vector<std::vector<double>>();
    }

    std::vector<std::vector<double>> result(height, std::vector<double>(width, 0));

    for (size_t y = 0; y < height; ++y) {
        for (size_t x = 0; x < width; ++x) {
            if (image[y][x]) {
                for (size_t _y = 0; _y < pattern_height; ++_y) {
                    for (size_t _x = 0; _x < pattern_width; ++_x) {
                        long long ry = (long long) (y + _y) - (long long) pattern_height / 2;
                        long long rx = (long long) (x + _x) - (long long) pattern_width / 2;
                        if (rx < 0 || ry < 0 || rx >= width || ry >= height)
                            continue;
                        result[ry][rx] = std::max(result[ry][rx], pattern[_y][_x]);
                    }
                }
            }
        }
    }

    return result;
}



std::pair<ImageFloat, ImageInt> fillPatternFromCoords(const std::vector<long long> &x,
                                                      const std::vector<long long> &y,
                                                      const std::vector<std::vector<double>> &pattern,
                                                      size_t width, size_t height) {

    std::pair<ImageFloat, ImageInt> result;

    size_t pattern_width = pattern[0].size(), pattern_height = pattern.size();

    if (pattern_width % 2 != 1 || pattern_height % 2 != 1) {
        return result;
    }

    ImageFloat &weights = result.first;
    ImageInt &mask = result.second;

    weights.resize(height, std::vector<double>(width, 0.0));
    mask.resize(height, std::vector<int>(width, 0));

    size_t point_n = static_cast<int>(x.size());

    for (int point_i = 0; point_i < point_n; ++point_i) {
        for (size_t _y = 0; _y < pattern_height; ++_y) {
            for (size_t _x = 0; _x < pattern_width; ++_x) {
                long long ry = (long long) (y[point_i] + _y) - (long long) pattern_height / 2;
                long long rx = (long long) (x[point_i] + _x) - (long long) pattern_width / 2;
                if (rx < 0 || ry < 0 || rx >= width || ry >= height)
                    continue;

                if (fabs(pattern[_y][_x]) > EPSILON && weights[ry][rx] < pattern[_y][_x]) {
                    weights[ry][rx] = pattern[_y][_x];
                    mask[ry][rx] = point_i + 1;
                }
            }
        }

    }

    return result;
}


inline long long map_coords(long long x, int y, int width) {
    return x + y * width;
}


void fillPatternFromCoords(long long *x, long long *y, int point_n,
                           double *pattern, int pattern_width, int pattern_height,
                           double *out_pattern, long long *out_mask, int width, int height) {
    
    if (pattern_width % 2 != 1 || pattern_height % 2 != 1) {
        return;
    }
    
    for (int point_i = 0; point_i < point_n; ++point_i) {
        for (size_t _y = 0; _y < pattern_height; ++_y) {
            for (size_t _x = 0; _x < pattern_width; ++_x) {
                long long ry = (long long) (y[point_i] + _y) - (long long) pattern_height / 2;
                long long rx = (long long) (x[point_i] + _x) - (long long) pattern_width / 2;
                if (rx < 0 || ry < 0 || rx >= width || ry >= height)
                    continue;
                
                long long pi = map_coords(_x, _y, pattern_width), ri = map_coords(rx, ry, width);

                if (fabs(pattern[pi]) > EPSILON && out_pattern[ri] < pattern[pi]) {
                    out_pattern[ri] = pattern[pi];
                    out_mask[ri] = point_i + 1;
                }
            }
        }
    }
}

