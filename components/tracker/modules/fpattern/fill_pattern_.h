//
//  fill_pattern.h
//  FillPattern
//
//  Created by Dmytro Kotsur on 15/03/2017.
//  Copyright © 2017 Dmytro Kotsur. All rights reserved.
//

#ifndef fill_pattern_h
#define fill_pattern_h

#include <cstddef>
#include <vector>


typedef std::vector<std::vector<double>> ImageFloat;
typedef std::vector<std::vector<bool>> ImageBool;
typedef std::vector<std::vector<int>> ImageInt;


ImageFloat fillPatternFromImage(const ImageBool &image, const ImageFloat &pattern);


std::pair<ImageFloat, ImageInt> fillPatternFromCoords(const std::vector<long long> &x,
                                                      const std::vector<long long> &y,
                                                      const std::vector<std::vector<double>> &pattern, size_t width, size_t height);

void fillPatternFromCoords(long long *x, long long *y, int point_n,
                           double *pattern, int pattern_width, int pattern_height,
                           double *out_pattern, long long *out_mask, int width, int height);

#endif /* fill_pattern_h */
