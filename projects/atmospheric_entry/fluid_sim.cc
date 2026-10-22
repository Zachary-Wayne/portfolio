/****
    * C++ port by Zachary Wayne
    * MODIFIED : 2D simulation to 3D simulation
    *
    * ===
    *
    * Copyright 2022 Matthias Müller - Ten Minute Physics,
    * www.youtube.com/c/TenMinutePhysics
    * www.matthiasMueller.info/tenMinutePhysics
    *
    * MIT License
    *
    * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    * documentation files(the "Software"), to deal in the Software without restriction, including without limitation
    * the rights to use, copy, modify, merge, publish, distribute, sublicense, and /or sell copies of the Software, and
    * to permit persons to whom the Software is furnished to do so, subject to the following conditions :
    *
    * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
    *
    * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    * OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    */

#include "fluid_sim.h"

#include <iostream>
#include <cmath>
#include <array>
#include <algorithm>


#ifdef WIN32
#include <Windows.h>
#endif

#include <GL/glew.h>
#include <unordered_set> // For storing which keys are pressed
#define GLFW_DLL
#define GLFW_INCLUDE_NONE
#define PI_180 3.1415926535897932384626433832795/180
#define PI 3.1415926535897932384626433832795
#include <GLFW/glfw3.h>
#define GLM_FORCE_RADIANS
#include <glm/glm.hpp>
#include <glm/gtx/string_cast.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include "tiny_obj_loader.h"
#include "shader_builder.h"
#include "mesh2voxels.h"
    // #include "atmosphere.h"
#include "fluid_sim.h"
#include "world.h"
#include "world_object.h"
#include <stdio.h>
#include <math.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <regex>



template <typename T>
T Fluid::get(T* arr, int i, int j, int k) {
    return arr[i*numY*numZ + j*numZ + k];
}

template <typename T>
void Fluid::add(T* arr, int i, int j, int k, T val) {
    arr[i*numY*numZ + j*numZ + k] += val;
}

template <typename T>
void Fluid::set(T* arr, int i, int j, int k, T val) {
    arr[i*numY*numZ + j*numZ + k] = val;
}

template <typename T>
void Fluid::clearArray(T* arr) {
    for (int i = 0; i < cell_count; i++) {
        arr[i] = 0.0;
    }
}

const int Fluid::U_FIELD = 0;
const int Fluid::V_FIELD = 1;
const int Fluid::W_FIELD = 2;
const int Fluid::S_FIELD = 3;
unsigned int Fluid::counter = 0;

Fluid::Fluid() {}

Fluid::Fluid(double density, int numX, int numY, int numZ, double h)
{
    this->density = density;

    this->numX = numX + 2; // + 2 for boundary cells.
    this->numY = numY + 2;
    this->numZ = numZ + 2;

    this->cell_count = this->numX*this->numY*this->numZ; // Total number of cells.

    this->h = h;

    this->u = new double[cell_count]; // X velocities.
    this->v = new double[cell_count]; // Y velocities.
    this->w = new double[cell_count]; // Z velocities.

    this->newU = new double[cell_count]; 
    this->newV = new double[cell_count];
    this->newW = new double[cell_count];

    this->p = new double[cell_count];  // Pressure.
    this->s = new double[cell_count];  // State of the cell, 0.0 = Solid, 1.0 = Fluid.

    this->m = new double[cell_count];  // Smoke / Dye for visualization. 1.0 = more dye.
    this->newM = new double[cell_count];
    std::fill_n(this->m, cell_count, 1.0);

    std::cout << "Dimensions: " << numX << "x" << numY << "x" << numZ << " \t(With Buffers: " << this->numX << "x" << this->numY << "x" << this->numZ << ")" << std::endl;
    std::cout << "Cell Count: " << numX*numY*numZ << " \t(With Buffers: " << this->cell_count << ")" << std::endl;
}

void Fluid::integrate(float dt, float gravity) {
    int m = numX;
    int n = numY;
    int o = numZ;
    for (int i = 1; i < m - 1; ++i) {
        for (int j = 1; j < n - 1; ++j) {
            for (int k = 1; k < o - 1; ++k) {
                // If this cell and the cell below are not solid, add gravity.
                if (get(this->s, i, j, k) != 1.0f && get(this->s, i, j, k + 1) != 1.0f) {
                    add(this->v, i, j, k, (double) gravity * dt);
                }
            }
        }
    }
}

void Fluid::solveIncompressibility(int numIters, double dt) {
    int m = this->numX;
    int n = this->numY;
    int o = this->numZ;

    double cp = this->density*this->h / dt;

    for (int iter = 0; iter < numIters; ++iter) {
        for (int i = 1; i < m - 1; ++i) {
            for (int j = 1; j < n - 1; ++j) {
                for (int k = 1; k < o - 1; ++k) {
                    // If this cell state is solid, then skip.
                    if (this->s[i*n*o + j*o + k] == 0.0) continue;

                    double sx0 = get(this->s, i-1, j, k);
                    double sx1 = get(this->s, i+1, j, k);
                    double sy0 = get(this->s, i, j-1, k);
                    double sy1 = get(this->s, i, j+1, k);
                    double sz0 = get(this->s, i, j, k-1);
                    double sz1 = get(this->s, i, j, k+1);
                    double s = sx0 + sx1 + sy0 + sy1 + sz0 + sz1;

                    // s will be 0.0 if cell (i, j, k) is surrounded by solid cells.
                    if (s == 0.0) continue;

                    double div = 
                    get(u, i+1, j, k) - get(u, i, j, k) + 
                    get(v, i, j+1, k) - get(v, i, j, k) + 
                    get(w, i, j, k+1) - get(w, i, j, k);
                
                    double p = -div / s;
                    p *= this->over_relaxation;
                    
                    add(this->p, i, j, k, cp * p);
                    add(this->u, i, j, k, -sx0 * p);
                    add(this->u, i+1, j, k, sx1 * p);
                    add(this->v, i, j, k, -sy0 * p);
                    add(this->v, i, j+1, k, sy1 * p);
                    add(this->w, i, j, k, -sz0 * p);
                    add(this->w, i, j, k+1, sz1 * p);
                }
            }
        }
    }
}


void Fluid::extrapolate() {
    int m = this->numX;
    int n = this->numY;
    int o = this->numZ;

    for (int i = 0; i < m; ++i) {
        this->set(this->u, i, 0, 0, get(this->u, i + 1, 0, 0));
        this->set(this->u, i, n - 1, 0, get(this->u, i, n - 2, 0));
        this->set(this->u, i, 0, o - 1, get(this->u, i + 1, 0, o - 2));
    }

    for (int j = 0; j < n; ++j) {
        this->set(this->v, 0, j, 0, get(this->v, 0, j + 1, 0));
        this->set(this->v, m - 1, j, 0, get(this->v, m - 2, j, 0));
        this->set(this->v, 0, j, o - 1, get(this->v, 0, j, o - 2));
    }

    for (int k = 0; k < o; ++k) {
        this->set(this->w, 0, 0, k, get(this->w, 0, 0, k + 1));
        this->set(this->w, m - 1, 0, k, get(this->w, m - 2, 0, k));
        this->set(this->w, 0, n - 1, k, get(this->w, 0, n - 2, k));
    }
}
        
double Fluid::sampleField(double x, double y, double z, int field) {
    int m = numX;
    int n = numY;
    int o = numZ;
    double h = this->h;

    double h1 = 1.0 / h;
    double h2 = h / 2;

    x = std::max(std::min(x, m * h), h);
    y = std::max(std::min(y, n * h), h);
    z = std::max(std::min(z, o * h), h);

    double dx = 0.0;
    double dy = 0.0;
    double dz = 0.0;

    double* f;
    if (field == S_FIELD) f = this->m; dx = h2; dy = h2; dz = h2;
    if (field == U_FIELD) f = this->u; dy = h2; dz = h2;
    if (field == V_FIELD) f = this->v; dx = h2; dz = h2;
    if (field == W_FIELD) f = this->w; dx = h2; dy = h2;

    int x0 = std::min(std::max(static_cast<int>(std::floor((x-dx)*h1)), 0), m-1);
    double tx = ((x-dx) - x0*h) * h1;
    int x1 = std::min(x0 + 1, m-1);

    int y0 = std::min(std::max(static_cast<int>(std::floor((y-dy)*h1)), 0), n-1);
    double ty = ((y-dy) - y0*h) * h1;
    int y1 = std::min(y0 + 1, n-1);

    int z0 = std::min(std::max(static_cast<int>(std::floor((z-dz)*h1)), 0), o-1);
    double tz = ((z-dz) - z0*h) * h1;
    int z1 = std::min(z0 + 1, o-1);

    double sx = 1.0 - tx;
    double sy = 1.0 - ty;
    double sz = 1.0 - tz;

    return get(f, x0, y0, z0) * sx * sy * sz + get(f, x1, y0, z0) * tx * sy * sz + 
            get(f, x0, y1, z0) * sx * ty * sz + get(f, x1, y1, z0) * tx * ty * sz + 
            get(f, x0, y0, z1) * sx * sy * tz + get(f, x1, y0, z1) * tx * sy * tz + 
            get(f, x0, y1, z1) * sx * ty * tz + get(f, x1, y1, z1) * tx * ty * tz;
}

double Fluid::avgU(int i, int j, int k) {
return (
    get(u, i,   j,   k) +
    get(u, i+1, j,   k) +
    get(u, i,   j-1, k) +
    get(u, i+1, j-1, k) +
    get(u, i,   j,   k-1) +
    get(u, i+1, j,   k-1) +
    get(u, i,   j-1, k-1) +
    get(u, i+1, j-1, k-1)
) * 0.125;
}

double Fluid::avgV(int i, int j, int k) {
return (
    get(v, i,   j,   k) +
    get(v, i-1, j,   k) +
    get(v, i,   j+1, k) +
    get(v, i-1, j+1, k) +
    get(v, i,   j,   k-1) +
    get(v, i-1, j,   k-1) +
    get(v, i,   j+1, k-1) +
    get(v, i-1, j+1, k-1)
) * 0.125;
}

double Fluid::avgW(int i, int j, int k) {
return (
    get(w, i,   j,   k) +
    get(w, i-1, j,   k) +
    get(w, i,   j-1, k) +
    get(w, i-1, j-1, k) +
    get(w, i,   j,   k+1) +
    get(w, i-1, j,   k+1) +
    get(w, i,   j-1, k+1) +
    get(w, i-1, j-1, k+1)
) * 0.125;
}

void Fluid::advectVel(double dt) {
    newU = u;
    newV = v;
    newW = w;

    int m = numX;
    int n = numY;
    int o = numZ;

    double h = this->h;
    double h2 = h / 2.0;

    for (int i = 1; i < m-1; i++) {
        for (int j = 1; j < n-1; j++) {
            for (int k = 1; k < o-1; k++) {
                // u component
                if (get(s, i, j, k) != 0.0 && get(s, i-1, j, k) != 0.0) {
                    double x = i*h      - dt * get(u, i, j, k);
                    double y = j*h + h2 - dt * avgV(i, j, k);
                    double z = k*h + h2 - dt * avgW(i, j, k);
                    double u = sampleField(x, y, z, Fluid::U_FIELD);
                    this->set(newU, i, j, k, u);
                    
                // v component
                } if (get(s, i, j, k) != 0.0 && get(s, i, j-1, k) != 0.0) {
                    double x = i*h + h2 - dt * avgU(i, j, k);
                    double y = j*h      - dt * get(v, i, j, k);
                    double z = k*h + h2 - dt * avgW(i, j, k);
                    double v = sampleField(x, y, z, Fluid::V_FIELD);
                    this->set(newV, i, j, k, v);
                
                // w component
                } if (get(s, i, j, k) != 0.0 && get(s, i, j, k-1) != 0.0) {
                    double x = i*h + h2 - dt * avgU(i, j, k);
                    double y = j*h + h2 - dt * avgV(i, j, k);
                    double z = k*h      - dt * get(w, i, j, k);
                    double w = sampleField(x, y, z, Fluid::W_FIELD);
                    this->set(newW, i, j, k, w);
                }
            }
        }
    }
    u = newU;
    v = newV;
    w = newW;
}

void Fluid::advectSmoke(double dt){
    newM = m;

    int m = numX;
    int n = numY;
    int o = numZ;

    double h = this->h;
    double h2 = h / 2;

    for (int i = 1; i < m-1; ++i) {
        for (int j = 1; j < n-1; ++j) {
            for (int k = 1; k < o-1; ++k) {
                if (s[i*n*o + j*o + k] != 0.0) {
                    double u = get(this->u, i, j, k) + get(this->u, i+1, j, k) * 0.5;
                    double v = get(this->v, i, j, k) + get(this->v, i, j+1, k) * 0.5;
                    double w = get(this->w, i, j, k) + get(this->w, i, j, k+1) * 0.5;

                    double x = i*h + h2 - dt * u;
                    double y = j*h + h2 - dt * v;
                    double z = k*h + h2 - dt * w;

                    this->set(newM, i, j, k, sampleField(x, y, z, Fluid::S_FIELD));
                }
            }
        }
    }
    this->m = newM;
}

void Fluid::getDimensions(int& numX, int& numY, int& numZ){
    numX = this->numX;
    numY = this->numY;
    numZ = this->numZ;
}

Environment::Environment(int width, int height, int length, double in_velocity, double dt, double gravity):
    width(width), height(height), length(length), dt(dt), gravity(gravity) {
    std::cout << "[FluidSim.cpp]: With display pressure enabled, the colour gradient from red to blue represents the highest pressure to the lowest." << std::endl;

    this->h = 1.0 / 100;

    f = Fluid(1000, width, height, length, h);

    scale = 20;

    int m = f.numX;
    int n = f.numY;
    int o = f.numZ;

    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) {
            for (int k = 0; k < o; ++k) {
                double s = 1.0;
                if (k == 0 || k == n - 1) {
                    s = 0.0;
                }
                if (i == 0) {
                    f.set(f.u, 1, j, k, in_velocity);
                }
                f.set(f.s, i, j, k, s);
            }
        }
    }

    for (int j = 6; j < 12; ++j) {
        f.set(f.v, 10, 10, 0, 0.0);
    }
}

void Environment::update(int num_iters) {
    f.integrate(dt, gravity);
    f.clearArray(f.p);
    f.solveIncompressibility(num_iters, dt);
    f.extrapolate();
    f.advectVel(dt);
    f.advectSmoke(dt);
}

void Environment::setBoundaryVelocities(double u, double v, double w) {
    for (int i = 0; i < f.numX; ++i) {
        for (int j = 0; j < f.numY; ++j) {
            for (int k = 0; k < f.numZ; ++k) {
                if (i == 0 || j == 0 || k == 0 || i == f.numX - 1 || j == f.numY - 1 || k == f.numZ - 1) {
                    f.set(f.u, i, j, k, u);
                    f.set(f.v, i, j, k, v);
                    f.set(f.w, i, j, k, w);
                }
            }
        }
    }
}

glm::vec4 Environment::getSciColour(double val, double min_val, double max_val) {
    val = std::min(std::max(val, min_val), max_val - 0.0001);
    float d = max_val - min_val;
    val = d == 0.0 ? d : (val - min_val) / d;
    float m = 0.25;
    int num = static_cast<int>(val / m);
    float s = fmod(val, m) / m;
    float r, g, b;
    if (num == 0) {
        r = 0.0; g = s; b = 1.0;
    } else if (num == 1) {
        r = 0.0; g = 1.0; b = 1.0 - s;
    } else if (num == 2) {
        r = s; g = 1.0; b = 0.0;
    } else {
        r = 1.0; g = 1.0 - s; b = 0.0;
    }
    return glm::vec4(r, g, b, 0.25);
}