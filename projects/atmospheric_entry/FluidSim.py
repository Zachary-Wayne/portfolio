"""
Python port by Zachary Wayne
MODIFIED: 2D simulation to 3D simulation

===

Copyright 2022 Matthias Müller - Ten Minute Physics, 
www.youtube.com/c/TenMinutePhysics
www.matthiasMueller.info/tenMinutePhysics

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import numpy as np
import math
import matplotlib.pyplot as plt
import pygame


class Fluid:
    U_FIELD = 0
    V_FIELD = 1
    W_FIELD = 2
    S_FIELD = 3

    def __init__(self, density, numX, numY, numZ, h, over_relaxation = 1.9):
        self.density = density

        self.numX = numX + 2 # + 2 for boundary cells.
        self.numY = numY + 2
        self.numZ = numZ + 2

        self.cell_count = self.numX * self.numY * self.numZ # Total number of cells.

        self.h = h
        self.over_relaxation = over_relaxation

        self.u = np.zeros(self.cell_count) # X velocities.
        self.v = np.zeros(self.cell_count) # Y velocities.
        self.w = np.zeros(self.cell_count) # Z velocities.

        self.newU = np.zeros(self.cell_count) 
        self.newV = np.zeros(self.cell_count)
        self.newW = np.zeros(self.cell_count)

        self.p = np.zeros(self.cell_count)  # Pressure.
        self.s = np.zeros(self.cell_count)  # State of the cell, 0.0 = Solid, 1.0 = Fluid.

        self.m = np.zeros(self.cell_count)  # Smoke / Dye for visualization. 1.0 = more dye.
        self.newM = np.zeros(self.cell_count)
        self.m.fill(1)

        print(f"Dimensions: {numX}x{numY}x{numZ} \t(With Buffers: {self.numX}x{self.numY}x{self.numZ})")
        print(f"Cell Count: {numX * numY * numZ} \t(With Buffers: {self.cell_count})")
    
    def get(self, arr, i, j, k):
        return arr[i*self.numY*self.numZ + j*self.numZ + k]
    
    def add(self, arr, i, j, k, val):
        arr[i*self.numY*self.numZ + j*self.numZ + k] += val
    
    def set(self, arr, i, j, k, val):
        arr[i*self.numY*self.numZ + j*self.numZ + k] = val
    
    def integrate(self, dt, gravity):
        m = self.numX
        n = self.numY
        o = self.numZ
        for i in range(1, m-1):
            for j in range(1, n-1):
                for k in range(1, o-1):
                    # If this cell and the cell below are not solid, add gravity.
                    if self.get(self.s, i, j, k) != 1.0 and self.get(self.s, i, j, k+1) != 1.0:
                        pass
                        self.add(self.v, i, j, k, gravity * dt)

    def solveIncompressibility(self, numIters, dt):
        m = self.numX
        n = self.numY
        o = self.numZ

        cp = self.density * self.h / dt

        for _ in range(numIters):
            for i in range(1, m-1):
                for j in range(1, n-1):
                    for k in range(1, o-1):
                        # If this cell state is solid, then skip.
                        if self.s[i*n*o + j*o + k] == 0.0: continue

                        sx0 = self.get(self.s, i-1, j, k)
                        sx1 = self.get(self.s, i+1, j, k)
                        sy0 = self.get(self.s, i, j-1, k)
                        sy1 = self.get(self.s, i, j+1, k)
                        sz0 = self.get(self.s, i, j, k-1)
                        sz1 = self.get(self.s, i, j, k+1)
                        s = sx0 + sx1 + sy0 + sy1 + sz0 + sz1
                        
                        # s will be 0.0 if cell (i, j, k) is surrounded by solid cells.
                        if s == 0.0: continue

                        # Calculate the divergence of the velocity field.
                        div = \
                            self.get(self.u, i+1, j, k) - self.get(self.u, i, j, k) + \
                            self.get(self.v, i, j+1, k) - self.get(self.v, i, j, k) + \
                            self.get(self.w, i, j, k+1) - self.get(self.w, i, j, k)
                        
                        # Calculate the pressure.
                        p = -div / s
                        p *= self.over_relaxation
                        
                        # Apply the pressure to the velocity field.
                        self.add(self.p, i, j, k, cp * p)

                        self.add(self.u, i, j, k, -sx0 * p)
                        self.add(self.u, i+1, j, k, sx1 * p)
                        self.add(self.v, i, j, k, -sy0 * p)
                        self.add(self.v, i, j+1, k, sy1 * p)
                        self.add(self.w, i, j, k, -sz0 * p)
                        self.add(self.w, i, j, k+1, sz1 * p)

    def extrapolate(self):
        m = self.numX
        n = self.numY
        o = self.numZ
        
        for i in range(1, m-1):
            self.set(self.u, i, 0, 0, self.get(self.u, i+1, 0, 0))
            self.set(self.u, i, n-1, 0, self.get(self.u, i, n-2, 0))
            self.set(self.u, i, 0, o-1, self.get(self.u, i+1, 0, o-2))
        
        for j in range(1, n-1):
            self.set(self.v, 0, j, 0, self.get(self.v, 0, j+1, 0))
            self.set(self.v, m-1, j, 0, self.get(self.v, m-2, j, 0))
            self.set(self.v, 0, j, o-1, self.get(self.v, 0, j, o-2))
        
        for k in range(1, o-1):
            self.set(self.w, 0, 0, k, self.get(self.w, 0, 0, k+1))
            self.set(self.w, m-1, 0, k, self.get(self.w, m-2, 0, k))
            self.set(self.w, 0, n-1, k, self.get(self.w, 0, n-2, k))
				
    def sampleField(self, x, y, z, field):
        m = self.numX
        n = self.numY
        o = self.numZ
        h = self.h

        h1 = 1.0 / h
        h2 = h / 2

        x = max(min(x, m * h), h)
        y = max(min(y, n * h), h)
        z = max(min(z, o * h), h)

        dx = 0.0
        dy = 0.0
        dz = 0.0
        
        if field == Fluid.S_FIELD: f = self.m; dx = h2; dy = h2; dz = h2
        elif field == Fluid.U_FIELD: f = self.u; dy = h2; dz = h2
        elif field == Fluid.V_FIELD: f = self.v; dx = h2; dz = h2
        elif field == Fluid.W_FIELD: f = self.w; dx = h2; dy = h2

        x0 = min(max(math.floor((x-dx)*h1), 0), m-1)
        tx = ((x-dx) - x0*h) * h1
        x1 = min(x0 + 1, m-1)

        y0 = min(max(math.floor((y-dy)*h1), 0), n-1)
        ty = ((y-dy) - y0*h) * h1
        y1 = min(y0 + 1, n-1)

        z0 = min(max(math.floor((z-dz)*h1), 0), o-1)
        tz = ((z-dz) - z0*h) * h1
        z1 = min(z0 + 1, o-1)

        sx = 1.0 - tx
        sy = 1.0 - ty
        sz = 1.0 - tz

        return self.get(f, x0, y0, z0) * sx * sy * sz + self.get(f, x1, y0, z0) * tx * sy * sz + \
               self.get(f, x0, y1, z0) * sx * ty * sz + self.get(f, x1, y1, z0) * tx * ty * sz + \
               self.get(f, x0, y0, z1) * sx * sy * tz + self.get(f, x1, y0, z1) * tx * sy * tz + \
               self.get(f, x0, y1, z1) * sx * ty * tz + self.get(f, x1, y1, z1) * tx * ty * tz
    


    def avgU(self, i, j, k):
        u = (
            self.get(self.u, i,   j,   k) + \
            self.get(self.u, i+1, j,   k) + \
            self.get(self.u, i,   j-1, k) + \
            self.get(self.u, i+1, j-1, k) + \
            self.get(self.u, i,   j,   k-1) + \
            self.get(self.u, i+1, j,   k-1) + \
            self.get(self.u, i,   j-1, k-1) + \
            self.get(self.u, i+1, j-1, k-1)
        ) * 0.125
        return u

    def avgV(self, i, j, k):
        v = (
            self.get(self.v, i,   j,   k) + \
            self.get(self.v, i-1, j,   k) + \
            self.get(self.v, i,   j+1, k) + \
            self.get(self.v, i-1, j+1, k) + \
            self.get(self.v, i,   j,   k-1) + \
            self.get(self.v, i-1, j,   k-1) + \
            self.get(self.v, i,   j+1, k-1) + \
            self.get(self.v, i-1, j+1, k-1)
        ) * 0.125
        return v

    def avgW(self, i, j, k):
        w = (
            self.get(self.w, i,   j,   k) + \
            self.get(self.w, i-1, j,   k) + \
            self.get(self.w, i,   j-1, k) + \
            self.get(self.w, i-1, j-1, k) + \
            self.get(self.w, i,   j,   k+1) + \
            self.get(self.w, i-1, j,   k+1) + \
            self.get(self.w, i,   j-1, k+1) + \
            self.get(self.w, i-1, j-1, k+1)
        ) * 0.125
        return w
        
    def advectVel(self, dt):
        self.newU = self.u
        self.newV = self.v
        self.newW = self.w
    
        m = self.numX
        n = self.numY
        o = self.numZ
        
        h = self.h
        h2 = h / 2

        for i in range(1, m-1):
            for j in range(1, n-1):
                for k in range(1, o-1):


                    # u component
                    if self.get(self.s, i, j, k) != 0.0 and self.get(self.s, i-1, j, k) != 0.0 and j < n - 1:
                        x = i*h      - dt * self.get(self.u, i, j, k)
                        y = j*h + h2 - dt * self.avgV(i, j, k)
                        z = k*h + h2 - dt * self.avgW(i, j, k)
                        u = self.sampleField(x, y, z, Fluid.U_FIELD)
                        self.set(self.newU, i, j, k, u)
                        
                    # v component
                    if self.get(self.s, i, j, k) != 0.0 and self.get(self.s, i, j-1, k) != 0.0 and i < m - 1:

                        x = i*h + h2 - dt * self.avgU(i, j, k)
                        y = j*h      - dt * self.get(self.v, i, j, k)
                        z = k*h + h2 - dt * self.avgW(i, j, k)
                        v = self.sampleField(x, y, z, Fluid.V_FIELD)
                        self.set(self.newV, i, j, k, v)
                    
                    # w component
                    if self.get(self.s, i, j, k) != 0.0 and self.get(self.s, i, j, k-1) != 0.0 and k < o - 1:
                        x = i*h + h2 - dt * self.avgU(i, j, k)
                        y = j*h + h2 - dt * self.avgV(i, j, k)
                        z = k*h      - dt * self.get(self.w, i, j, k)
                        w = self.sampleField(x, y, z, Fluid.W_FIELD)
                        self.set(self.newW, i, j, k, w)

        self.u = self.newU
        self.v = self.newV
        self.w = self.newW

    def advectSmoke(self, dt):
        self.newM = self.m

        m = self.numX
        n = self.numY
        o = self.numZ
        
        h = self.h
        h2 = h / 2

        for i in range(1, m-1):
            for j in range(1, n-1):
                for k in range(1, o-1):
                    if self.s[i*n*o + j*o + k] != 0.0:
                        u = self.get(self.u, i, j, k) + self.get(self.u, i+1, j, k) * 0.5
                        v = self.get(self.v, i, j, k) + self.get(self.v, i, j+1, k) * 0.5
                        w = self.get(self.w, i, j, k) + self.get(self.w, i, j, k+1) * 0.5

                        x = i*h + h2 - dt * u
                        y = j*h + h2 - dt * v
                        z = k*h + h2 - dt * w

                        self.set(self.newM, i, j, k, self.sampleField(x, y, z, Fluid.S_FIELD))
        self.m = self.newM
    
    def getDimensions(self):
        return self.numX, self.numY, self.numZ

class Environment:
    c = 0
    class Obstacle:
        def __init__(self, x, y, z, r):
            self.x = x
            self.y = y
            self.z = z
            self.r = r

    obstacle = Obstacle(0, 0, 0, 3)

    def __init__(self, width, height, length, in_velocity, dt = 0.01, gravity = -9.81):
        print("[FluidSim.py]: With display pressure enabled, the colour gradient from red to blue represents the highest pressure to the lowest.")

        self.density = 10
        self.width = width
        self.height = height
        self.length = length
        self.h = 1/100
        
        self.f = Fluid(self.density, width, height, length, self.h)

        self.scale = 20
        self.dt = dt
        self.gravity = gravity
        
        m = self.f.numX
        n = self.f.numY
        o = self.f.numZ

        # TODO: Vortex Shedding
        for i in range(m):
            for j in range(n):
                for k in range(o):
                    s = 1.0
                    if (k == 0 or k == n-1):
                        s = 0.0 
                    if (i == 0):
                        self.f.set(self.f.u, 1, j, k, in_velocity)
                    self.f.set(self.f.s, i, j, k, s)
        # Dye stuff
        for j in range(6, 12):
            self.f.set(self.f.v, 10, 10, 0, 0)
    
    def setObstacle(self, x, y, z, reset):
        vx = 0
        vy = 0
        vz = 0

        if not reset:
            vx = (x - self.obstacle.x) / self.dt
            vy = (y - self.obstacle.y) / self.dt
            vz = (z - self.obstacle.z) / self.dt

        r = self.obstacle_radius
        f = self.f

        m = self.width
        n = self.height
        o = self.length

        for i in range(n):
            for j in range(m):
                f.s[i*n*o + j*o + z] = 1.0

                dx = (i + 0.5) * f.h - x
                dy = (j + 0.5) * f.h - y

                if dx**2 + dy**2 < r**2:
                    f.s[i*n*o + j*o + z] = 0.0
                    f.m[i*n*o + j*o + z] = 0.0
                    
                    f.u[i*n*o + j*o + z] = vx
                    f.u[(i+1)*n*o + j*o + z] = vx

                    f.v[i*n*o + j*o + z] = vy
                    f.v[i*n*o + (j+1)*o + z] = vy

                    f.w[i*n*o + j*o + z] = vz
                    f.w[i*n*o + j*o + (z+1)] = vz

    def update(self, num_iters):
        self.f.integrate(self.dt, self.gravity)
        self.f.p.fill(0.0)
        self.f.solveIncompressibility(num_iters, self.dt)
        self.f.extrapolate()
        self.f.advectVel(self.dt)
        self.f.advectSmoke(self.dt)

        if self.c == 20:    # DEBUGGING
            self.f.u = [np.random.random() for i in range(self.f.cell_count)]# DEBUGGING
            self.c = 0 # DEBUGGING
        #self.c+=1# DEBUGGING
        
    def get_sci_colour(self, val, min_val, max_val):
        val = min(max(val, min_val), max_val - 0.001)
        d = max_val - min_val
        val = d if d == 0.0 else (val - min_val) / d
        m = 0.25
        num = int(val // m)
        s = (val % m) / m
        r, g, b = (
            (0.0, s, 1.0) if num == 0 else
            (0.0, 1.0, 1.0 - s) if num == 1 else
            (s, 1.0, 0.0) if num == 2 else
            (1.0, 1.0 - s, 0.0)
        )
        return [255 * r, 255 * g, 255 * b, 255]

    def draw(self, screen, showPressure, showSmoke):
        screen.fill((0, 0, 0))
        fluid = self.f

        for i in range(fluid.numX):
            for j in range(fluid.numY):
                colour = [255, 255, 255]
                if (showPressure):
                    fe = fluid.v
                    p = fluid.get(fe, i, j, 1)
                    colour = self.get_sci_colour(p, min(fe), max(fe))
                    if showSmoke:
                        m = fluid.get(fluid.m, i, j, 1)
                        colour[0] = max(0.0, colour[0] - m*200)
                        colour[1] = max(0.0, colour[1] - m*200)
                        colour[2] = max(0.0, colour[2] - m*200)
                elif (showSmoke):
                    m = fluid.get(fluid.m, i, j, 1)
                    colour[0] = m*255
                    colour[1] = m*255
                    colour[2] = m*255
                
                if fluid.get(fluid.s, i, j, 1) == 0:
                    colour[0] = 0
                    colour[1] = 0
                    colour[2] = 0

                pygame.draw.rect(screen, colour, (i*self.scale, j*self.scale, self.scale, self.scale))
        pygame.display.flip()