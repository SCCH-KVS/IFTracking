//
//  sampler.cpp
//  VFSampler
//
//  Created by Dmytro Kotsur on 24/09/2017.
//  Copyright © 2017 Dmytro Kotsur. All rights reserved.
//

#define _USE_MATH_DEFINES

#include "sampler.h"
#include <vector>
#include <cmath>
#include <iostream>


typedef std::pair<double, double> Point;
typedef std::vector<std::vector<double>> Image;

class Quadrant {
public:
    double v00, v01, v10, v11;
    
    Quadrant(double v00 = 0.0, double v01 = 0.0, double v10 = 0.0, double v11 = 0.0) {
        this->v00 = v00;
        this->v01 = v01;
        this->v10 = v10;
        this->v11 = v11;
    }
};


double bilinear_interpolation(const Quadrant &q, double x, double y) {
    return (q.v00 * (1 - x) + q.v01 * x) * (1 - y) + (q.v10 * (1 - x) + q.v11 * x) * y;
}


std::vector<Point> sample_vector_field(const Image &gvf_x, const Image &gvf_y, const std::vector<Point> &points) {
    
    // Get number of points
    size_t point_n = points.size();
    std::vector<Point> result(point_n);
    
    // Image processing
    size_t height = gvf_x.size();
    size_t width = gvf_x[0].size();
    
    Quadrant qx, qy;
    
    for (size_t i = 0; i < point_n; ++i) {
        double x = points[i].first, y = points[i].second;
        int xi = int(x), yi = int(y);
        
        // Skip point
        if (xi < 0 || yi < 0 || xi >= width || yi >= height)
            continue;
        
        // Select Quadrant
        if (xi == width - 1 && yi == height - 1) {
            qx = Quadrant(gvf_x[yi][xi], 0.0, 0.0, 0.0);
            qy = Quadrant(gvf_y[yi][xi], 0.0, 0.0, 0.0);
        } else if (xi == width - 1) {
            qx = Quadrant(gvf_x[yi][xi], 0.0, gvf_x[yi+1][xi], 0.0);
            qy = Quadrant(gvf_y[yi][xi], 0.0, gvf_y[yi+1][xi], 0.0);
        } else if (yi == height - 1) {
            qx = Quadrant(gvf_x[yi][xi], gvf_x[yi][xi+1], 0.0, 0.0);
            qy = Quadrant(gvf_y[yi][xi], 0.0, gvf_y[yi+1][xi], 0.0);
        } else {
            qx = Quadrant(gvf_x[yi][xi], gvf_x[yi][xi+1], gvf_x[yi+1][xi], gvf_x[yi+1][xi+1]);
            qy = Quadrant(gvf_y[yi][xi], gvf_y[yi][xi+1], gvf_y[yi+1][xi], gvf_y[yi+1][xi+1]);
        }
        
        // Interpolate
        double residual_x = x - xi, residual_y = y - yi;
        result[i].first = bilinear_interpolation(qx, residual_x, residual_y);
        result[i].second = bilinear_interpolation(qy, residual_x, residual_y);
    }
    
    return result;
}


inline int map_xy(int x, int y, int width) {
    return x + y * width;
}


inline double decode_x(double m, double a) {
    return m * cos((2.0 * a / 255.0 - 1.0) * M_PI) / 255.0;
}


inline double decode_y(double m, double a) {
    return m * sin((2.0 * a / 255.0 - 1.0) * M_PI) / 255.0;
}


void sample_vector_field(double *gvf_x, double *gvf_y, int width, int height, double *points, int point_n, double *result) {
    
    // Get number of points
    //double *result = (double*)malloc(sizeof(double) * point_n * 2);
    
    Quadrant qx, qy;
    
    for (size_t i = 0; i < point_n; ++i) {
        size_t px = i * 2, py = i * 2 + 1;
        
        double x = points[px], y = points[py];
        int xi = int(x), yi = int(y);
        
        // Skip point
        if (xi < 0 || yi < 0 || xi >= width || yi >= height)
            continue;
        
        int i00 = map_xy(xi, yi, width);
        int i01 = map_xy(xi, yi+1, width);
        int i10 = map_xy(xi+1, yi, width);
        int i11 = map_xy(xi+1, yi+1, width);
        
        // Select Quadrant
        if (xi == width - 1 && yi == height - 1) {
            qx = Quadrant(gvf_x[i00], 0.0, 0.0, 0.0);
            qy = Quadrant(gvf_y[i00], 0.0, 0.0, 0.0);
        } else if (xi == width - 1) {
            qx = Quadrant(gvf_x[i00], 0.0, gvf_x[i01], 0.0);
            qy = Quadrant(gvf_y[i00], 0.0, gvf_y[i01], 0.0);
        } else if (yi == height - 1) {
            qx = Quadrant(gvf_x[i00], gvf_x[i10], 0.0, 0.0);
            qy = Quadrant(gvf_y[i00], gvf_y[i10], 0.0, 0.0);
        } else {
            qx = Quadrant(gvf_x[i00], gvf_x[i10], gvf_x[i01], gvf_x[i11]);
            qy = Quadrant(gvf_y[i00], gvf_y[i10], gvf_y[i01], gvf_y[i11]);
        }
        
        // Interpolate
        double residual_x = x - xi, residual_y = y - yi;
        result[px] = bilinear_interpolation(qx, residual_x, residual_y);
        result[py] = bilinear_interpolation(qy, residual_x, residual_y);
    }
    
    //return result;
}


void sample_vector_field_xy(double *gvf_x, double *gvf_y, int width, int height, double *points, int point_n, double *result) {

    Quadrant qx, qy;

    for (size_t i = 0; i < point_n; ++i) {
        size_t px = i * 2, py = i * 2 + 1;

        double x = points[px], y = points[py];
        int xi = int(x), yi = int(y);

        // Skip point
        if (xi < 0 || yi < 0 || xi >= width || yi >= height)
            continue;

        int i00 = map_xy(xi, yi, width);
        int i01 = map_xy(xi, yi+1, width);
        int i10 = map_xy(xi+1, yi, width);
        int i11 = map_xy(xi+1, yi+1, width);

        // Select Quadrant
        if (xi == width - 1 && yi == height - 1) {
            qx = Quadrant(gvf_x[i00], 0.0, 0.0, 0.0);
            qy = Quadrant(gvf_y[i00], 0.0, 0.0, 0.0);
        } else if (xi == width - 1) {
            qx = Quadrant(gvf_x[i00], 0.0, gvf_x[i01], 0.0);
            qy = Quadrant(gvf_y[i00], 0.0, gvf_y[i01], 0.0);
        } else if (yi == height - 1) {
            qx = Quadrant(gvf_x[i00], gvf_x[i10], 0.0, 0.0);
            qy = Quadrant(gvf_y[i00], gvf_y[i10], 0.0, 0.0);
        } else {
            qx = Quadrant(gvf_x[i00], gvf_x[i10], gvf_x[i01], gvf_x[i11]);
            qy = Quadrant(gvf_y[i00], gvf_y[i10], gvf_y[i01], gvf_y[i11]);
        }

        // Interpolate
        double residual_x = x - xi, residual_y = y - yi;
        result[px] = bilinear_interpolation(qx, residual_x, residual_y);
        result[py] = bilinear_interpolation(qy, residual_x, residual_y);
    }

    //return result;
}


void sample_vector_field_ra(unsigned char *gvf_m, unsigned char *gvf_a, int width, int height, double *points, int point_n, double *result) {

    Quadrant qm, qa;

    for (size_t i = 0; i < point_n; ++i) {
        size_t px = i * 2, py = i * 2 + 1;

        double x = points[px], y = points[py];
        int xi = int(x), yi = int(y);

        // Skip point
        if (xi < 0 || yi < 0 || xi >= width || yi >= height)
            continue;

        int i00 = map_xy(xi, yi, width);
        int i01 = map_xy(xi, yi+1, width);
        int i10 = map_xy(xi+1, yi, width);
        int i11 = map_xy(xi+1, yi+1, width);

        // Select Quadrant
        if (xi == width - 1 && yi == height - 1) {
            qm = Quadrant(gvf_m[i00], 0.0, 0.0, 0.0);
            qa = Quadrant(gvf_a[i00], 0.0, 0.0, 0.0);
        } else if (xi == width - 1) {
            qm = Quadrant(gvf_m[i00], 0.0, gvf_m[i01], 0.0);
            qa = Quadrant(gvf_a[i00], 0.0, gvf_a[i01], 0.0);
        } else if (yi == height - 1) {
            qm = Quadrant(gvf_m[i00], gvf_m[i10], 0.0, 0.0);
            qa = Quadrant(gvf_a[i00], gvf_a[i10], 0.0, 0.0);
        } else {
            qm = Quadrant(gvf_m[i00], gvf_m[i10], gvf_m[i01], gvf_m[i11]);
            qa = Quadrant(gvf_a[i00], gvf_a[i10], gvf_a[i01], gvf_a[i11]);
        }

        // Interpolate
        double residual_x = x - xi, residual_y = y - yi;
        double m = bilinear_interpolation(qm, residual_x, residual_y);
        double a = bilinear_interpolation(qa, residual_x, residual_y);

        // Decode x, y values
        result[px] = decode_x(m, a);
        result[py] = decode_y(m, a);
    }

}


