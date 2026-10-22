# Simulating Atmospheric Entry

A study in simulating objects entering a planet's atmosphere: a grid-based (Eulerian) fluid solver, an atmosphere model, and a way to turn any `.obj` model into solid cells for the air to flow around. The maths is written up in full in the **Project Report** tab.

The 2D Python prototype runs, and its output is in the report's figures. The 3D C++ version voxelizes models and runs the solver, but it stayed an early, slow prototype without a finished visualization.

Built with Samuel Shard for the Simulation and Modeling course at Ontario Tech.

## What's in it

- **3D Eulerian fluid solver (C++).** Matthias Müller's 2D *Ten Minute Physics* solver (MIT-licensed), ported to C++ and extended to three dimensions. The air is a grid of cells. Each step:
  - applies external forces
  - enforces incompressibility by solving for pressure with Gauss–Seidel iterations and over-relaxation
  - advects velocity with a semi-Lagrangian scheme
- **Atmosphere model.** `atmosphere.cc` computes temperature, pressure and density at any altitude from the planet's gravity and the gas mix's molar mass, using the barometric formula. One model covers Earth-like or Venus-like atmospheres.
- **Mesh → voxels.** `mesh2voxels.cc` turns an arbitrary triangle mesh into solid cells, so the fluid flows around the object's real shape.
- **Python prototype first.** The method was validated in 2D with `FluidSim.py` (pygame) before the C++/OpenGL version was written.

## Stack

C++ · OpenGL (GLFW, GLEW, GLM) · GLSL · tinyobjloader · Python · NumPy · pygame
