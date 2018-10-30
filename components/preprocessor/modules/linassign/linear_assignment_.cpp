//
//  linear_assignment_.cpp
//  LinearAssignment
//
//  Created by Dmytro Kotsur on 31/03/2017.
//  Copyright © 2017 Dmytro Kotsur. All rights reserved.
//

#include "linear_assignment_.hpp"
#include <algorithm>


double get_distance(const std::vector<double> &v1, const std::vector<double> &v2) {
    double result = 0.0, diff;
    size_t n = std::min(v1.size(), v2.size());
    for (size_t i = 0; i < n; ++i) {
        diff = v1[i] - v2[i];
        result += diff * diff;
    }
    return result;
}



std::vector<std::vector<int>> linearAssignment(const std::vector<std::vector<double>> &points1,
                                               const std::vector<std::vector<double>> &points2,
                                               double max_distance) {

    std::vector<std::vector<int>> result;

    size_t n1 = points1.size(), n2 = points2.size();
    std::vector<double> distances(n1 * n2);
    std::vector<std::vector<int>> pairs(n1 * n2);
    std::vector<size_t> indices(n1 * n2);

    std::vector<bool> used1(n1, false), used2(n2, false);

    size_t n = 0;

    for (size_t i = 0; i < n1; ++i) {
        for (size_t j = 0; j < n2; ++j) {

            double distance = get_distance(points1[i], points2[j]);

            if (distance < max_distance) {
                indices[n] = n;
                distances[n] = distance;
                pairs[n].resize(2);
                pairs[n][0] = static_cast<int>(i);
                pairs[n][1] = static_cast<int>(j);
                n++;
            }
        }
    }

    std::sort(indices.begin(), indices.begin() + n, [&](size_t a, size_t b) {
        return distances[a] < distances[b];
    });

    for (size_t i = 0; i < n; ++i) {
        int j1 = pairs[indices[i]][0], j2 = pairs[indices[i]][1];
        if (!used1[j1] && !used2[j2] && distances[indices[i]] < max_distance) {
            used1[j1] = true;
            used2[j2] = true;
            result.push_back(pairs[indices[i]]);
        }
    }

    return result;
}