//
//  sampler.h
//  VFSampler
//
//  Created by Dmytro Kotsur on 24/09/2017.
//  Copyright © 2017 Dmytro Kotsur. All rights reserved.
//

#ifndef sampler_h
#define sampler_h


void sample_vector_field_xy(double *gvf_x, double *gvf_y, int width, int height, double *points, int point_n, double *result);
void sample_vector_field_ra(unsigned char *gvf_m, unsigned char *gvf_a, int width, int height, double *points, int point_n, double *result);

#endif /* sampler_h */
