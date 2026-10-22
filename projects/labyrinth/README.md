# Labyrinth

A marble maze game for Android, built in Flutter with the Flame engine and Forge2D (Box2D) physics. Built by a team of five for the Mobile Devices course at Ontario Tech.

## My part

I set up the project structure and owned the **level pipeline** and **physics**:

- **Levels are drawn, not coded.** Designers draw a maze in Inkscape. `svg2level.py` reads the SVG, keeps every `<path>` as wall geometry, and finds the start, goal, and holes from their Inkscape labels (using the `translate(...)` transform or the path's first point). It writes everything to a JSON `.level` file.
- **SVG paths become physics bodies.** In the game, `Wall` parses each path string and samples it every 2 units along its length. Each consecutive pair of points becomes a Forge2D `EdgeShape`, so walls of any shape, including curves, get accurate collisions without any hand-made hitboxes.
- **Loading.** `Level` and `Maze` parse the `.level` JSON into game objects.
- **Marble physics.** Collisions, holes, and position reading.
- **Tilt controls (prototype).** `tilt_test.dart` reads the accelerometer through `sensors_plus`. In the final build, the marble's velocity follows the phone's tilt.

My teammates, Daniel Hinbest, Jugal Patel, Ahmed Rizvi and Raje Singh, built most of the menus, settings and the SQLite scoreboard, and designed the levels.

## Stack

Dart · Flutter · Flame · Forge2D (Box2D) · SQLite · Python · Inkscape SVG
