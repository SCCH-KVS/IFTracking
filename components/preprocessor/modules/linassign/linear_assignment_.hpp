//
//  linear_assignment_.hpp
//  LinearAssignment
//
//  Created by Dmytro Kotsur on 31/03/2017.
//  Copyright © 2017 Dmytro Kotsur. All rights reserved.
//

#ifndef linear_assignment__hpp
#define linear_assignment__hpp

#include <iostream>
#include <vector>


std::vector<std::vector<int>> linearAssignment(const std::vector<std::vector<double>> &points1,
                                               const std::vector<std::vector<double>> &points2,
                                               double max_distance);

#endif /* linear_assignment__hpp */
