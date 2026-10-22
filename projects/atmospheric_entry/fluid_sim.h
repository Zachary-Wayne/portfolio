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

#ifndef FLUID_SIM_H
#define FLUID_SIM_H

#include <iostream>
#include <cmath>
#include <array>
#include <algorithm>
#include <glm/glm.hpp>

class Fluid {
public:
    static const int U_FIELD;
    static const int V_FIELD;
    static const int W_FIELD;
    static const int S_FIELD;
    static unsigned int counter;

    double density;
    int numX, numY, numZ;
    int cell_count;
    float over_relaxation = 1.9;

    double h;

    double *u, *v, *w;
    double *newU, *newV, *newW;
    double *p, *s;
    double *m, *newM;

    template <typename T> T get(T* arr, int i, int j, int k);
    template <typename T> void add(T* arr, int i, int j, int k, T val);
    template <typename T> void set(T* arr, int i, int j, int k, T val);
    template <typename T> void clearArray(T* arr);

    Fluid();

    Fluid(double density, int numX, int numY, int numZ, double h);

    void integrate(float dt, float gravity);

    void solveIncompressibility(int numIters, double dt);

    void extrapolate();

    double sampleField(double x, double y, double z, int field);

    double avgU(int i, int j, int k);

    double avgV(int i, int j, int k);

    double avgW(int i, int j, int k);

    void advectVel(double dt);

    void advectSmoke(double dt);

    void getDimensions(int& numX, int& numY, int& numZ);
};

class Environment {
public:
    class Obstacle {
    public:
        Obstacle(double x, double y, double z, double r) : x(x), y(y), z(z), r(r) {}
        double x, y, z, r;
    };

    Environment(int width, int height, int length, double in_velocity, double dt = 0.01, double gravity = -9.81);

    void update(int num_iters);

    void setBoundaryVelocities(double u, double v, double w);

    glm::vec4 getSciColour(double val, double min_val, double max_val);

    void Environment::draw(bool showPressure, bool showSmoke);

    // Private

    double density;
    int width, height, length;
    double h;
    Fluid f;
    int scale;
    double dt, gravity;
    Obstacle obstacle = Obstacle(0, 0, 0, 3);
};

#endif /* FLUID_SIM_H */