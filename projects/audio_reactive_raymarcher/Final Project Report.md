By Zachary Wayne

CSCI 4110 - Advanced Computer Graphics

`Zachary Wayne | CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)`

# Table of Contents 
```table-of-contents
```
# Introduction

The goal of this final project is to create a music visualization using Python and OpenGL. In this report, there will be a section explaining each part of the program.

In the OpenGL Application (`src`) section, I will be explaining the code of my framework made specifically for this course, meant to be a [Processing](https://processing.org/)-like interface between python and OpenGL bindings. 

This code features many things, here are the most notable features:
- Frequency Analysis
- HSV to RGB conversion
- Signed Distance Functions (SDFs)
- Raymarching
- Menger Sponge SDF
- Mandelbrot Rendering
- Efficient $\mathbf{uv}$ distortion
- Levenshtein Distance
- Rotation Matrices
- Python GLFW Bindings and mappings

The program creates the music visualization with a combination of these features.
The song used for this project can be found in the Conclusion.
# Files
There are many files in this project, so I have created a tree to show what files are found where:
```
"Final Project"
├── ShaderArt\
│   ├── .venv\ (generated)
│   ├── models\ (unused)
│   ├── shaders\
│   │   └── project_shader.glsl
│   ├── src\
│   │   ├── camera.py (unused)
│   │   ├── drawable.py (unused)
│   │   ├── mappings.py
│   │   ├── model.py (unused)
│   │   ├── opengl_app.py
│   │   ├── shader.py
│   │   └── utils.py
│   ├── audio-3.mp3
│   ├── audio-3-beat_times.npy (generated)
│   ├── audio-3-onset_times.npy (generated)
│   └── main.py
├── "CC BY-NC-SA LICENSE.md"
├── "Final Project Report.md"
└── "Final Project Report.pdf"
```
# The Python Code

## main.py
This program is written in python, purely because it is easier to run, and debug.
### Parameters, Variables and Audio Preprocessing
Before the program begins, variables and parameters are created, and audio is loaded.

Feature extraction and audio loading fall under the Preprocessing phase, as they happen before the application starts, and are generally time consuming.
#### Variables and Parameters

| Variable/Parameter Name(s)            | Description                                                                                                                                                                                                                        |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `num_frequencies`                     | The number of frequencies being analyzed. Each audio chunk is 1136 samples, so its FFT has 568 usable frequency bins; this many of them are picked out by linearly spacing indices from bin 20 up to the last bin. The shader only draws the first `BAR_COUNT` (50) of them.                |
| `previous_frequencies`                | This holds the processed frequencies of the latest frame, and is ultimately what is passed on to the shader for processing.                                                                                                        |
| `audio_file_name`                     | A simple string to locate the file.                                                                                                                                                                                                |
| `audio_file_path`                     | Using `os.path`, the audio file can be loaded regardless of where the root of the project folder is located.                                                                                                                       |
| `data`, `sample_rate`                 | Using the `soundfile` library, the data and sample rate of the audio file is read.                                                                                                                                                 |
| `beat_times_path`, `onset_times_path` | The path of generated files to speed up load times, may not exist. More information under Audio Loading.                                                                                                                           |
| `beat_times`, `onset_times`           | Arrays of times, in seconds, at which major (beat) and minor (onset) features occur.                                                                                                                                                 |
| `audio_index`                         | The current frame of audio being processed.                                                                                                                                                                                        |
| `beat_index`, `onset_index`           | Counters for major and minor features to loop through their respective times array.                                                                                                                                                |
| `pulse1`, `pulse2`                    | Vec3 variables used to pass major and minor events to the shader, only one channel is ever meaningfully used by the shader. Every time an event occurs, the respective pulse is set to 1 and then linearly interpolated back to 0. |
| `time_offset`                         | The audio stream's clock time at the first callback. Subtracting it from later clock times gives `audio_time`, the time since playback started.                                                                                                            |
| `audio_time`                          | The current time in seconds elapsed through the audio, rather than the current sample index `audio_index`.                                                                                                                                |
| `song_keyframes`                      | An array of manually made indices that represent on which major features will animation keyframes occur.                                                                                                                           |
| `keyframe_idx`                        | The current animation keyframe.                                                                                                                                                                                                    |
#### Audio Loading
The `sf.read()` function loads the audio file, splitting it into `data` and sample rate `sample_rate`.
#### Feature Extraction
`librosa` is used to extract `beat_times` (from the left channel) and `onset_times` (from the right channel) from the audio. These are also referred to as major feature times and minor feature times.

If beat and onset data already exist as `.npy` files, they are loaded; otherwise, they are computed and saved. This is to save time instead of recalculating the times.
### Audio Processing Functions
These functions are called while the program is running, all these functions get called many times every second. 
#### `process_frequencies(time_domain)`
- Performs a Fast Fourier Transform (FFT) with `numpy` to analyze the frequency spectrum of the audio. The FFT algorithm converts the time domain into a frequency domain. The `time_domain` arrives from the `callback(...)` explained below as an audio chunk, and the FFT is taken of the difference between the magnitudes of its right and left channels.
- Normalizes the selected magnitudes so the loudest is 0.5.
- Smooths the frequency data and updates `previous_frequencies` for a gradual transition in visuals, using linear interpolation and `np.convolve`. 
- Originally this was going to be used to extract the major and minor features of the audio, but this quickly went out of scope and was abandoned, leading to the use of `librosa` instead.
#### `process_features(time)`
- Manages audio synchronization with visual elements by comparing `audio_time` to the precomputed beat and onset times. At most one beat and one onset can be counted per audio chunk.
- Raises the matching pulse to 1 when a beat or onset passes, then uses `lerp` (linear interpolation) to ease the pulse values back towards 0.
- This is where most global variables are updated.
#### `callback(out_data, frames, time, status):`
- A function called by `sounddevice` on its own audio thread each time it needs the next chunk of audio, which lets this code play and analyze the audio at the same time without managing threads myself. 
- Copies the next chunk into the output buffer, then calls `process_frequencies(time_domain)` and `process_features(time)`. When the song runs out, it stops the stream.
- This was one of the most difficult parts of the project despite being relatively shorter code-wise.
### `MyApp(OpenGLApp)`
This class extends my own application framework that allows me to easily create OpenGL applications. The inner workings of how this is done are explained in the OpenGL Application (`src`) section.

This class can be explained in steps:
1. **Define the window** - Using `OpenGLApp.set_window` I can set the height, width and title of the window for the application.
2. **Define class variables** - `shader_1`, `audio_data`, and `audio_stream` are first initialized and set to temporary values (`audio_data` ended up unused).
3. **Init** - Local keyframe and index helper variables are initialized here within the `__init__(...)` method.
4. **Define the event handler and lifecycle methods**
	1. `on_key_event(...)` - This was used for helping find keyframes; I would tap the spacebar to mark out where I want keyframes to occur, and it would print the current major audio feature/beat index.
	2. `setup(...)` - The class variables are defined here, rather than in the `__init__(...)` method, because OpenGL calls need a window and its context to exist, and those are only created once `run()` starts (explained in the OpenGL Application section). Here the shader program is initialized and audio is started with `sounddevice`. 
	3. `update(...)` - This is where all the variables are passed into the shader program, and where the keyframe index is updated. Some debugging code has been purposely left in by design to show how timing works. The current beat index, keyframe index, and real audio time are printed.
	4. `exit(...)` - This cleans up the audio when the application is closed by stopping and closing the audio stream.

The whole idea of the `OpenGLApp` class is to remove the need for interaction with glfw directly. Notice that `main.py` only calls a few OpenGL functions directly: `glDrawArrays` to draw the full-screen quad, and `glProgramUniform1fv` with `glGetUniformLocation` to upload the frequency and beat time arrays.

The only other remaining code is the following:

```python
if __name__ == "__main__":  
    app = MyApp()  
    app.run()
```

This code is just the access point. The code instantiates and runs the application.
## OpenGL Application (`src`)
OpenGLApp acts as an interface between the OpenGL python bindings and higher level python code. I was inspired to make an easy to use framework based off of the Java Processing graphics library, which has a very beginner friendly coding environment. A small note: this class doesn't have any features for directly adding shapes like Processing's `rect(x,y,w,h)`, there are also other libraries out there that do exactly this, with python for OpenGL, but doing this myself is so much more fulfilling than trying to understand and use pre-made code.

Some features aren't used so they won't be explained. (Those being `model.py`, `drawable.py`, and `camera.py`)
### `opengl_app.py`
Following the ideas of Java Processing, OpenGLApp will automatically do the following:
- Create windows with set height, width and title
- Register key and mouse callbacks
- Handle animation and update events using `setup`, `update`, and `exit`
- Localized loading of assets like shader programs (and the unused model objects)
#### Events
The `run` function is the most important, it handles what order events will happen in:
1. The glfw window is defined and initialized using the values set by the user.
2. Key and Mouse callbacks are registered.
3. `self.setup` is called. This is called after the window is defined because compiling the shader program needs the OpenGL context that comes with the glfw window.
4. The window is brought into focus. This isn't really needed, but for programs with long setup times, it is quite helpful just to have the window be focused when it is done loading.
5. Entering the update loop, the key and mouse events are polled from glfw, and the screen is cleared. `update(glfw.get_time())` is called, passing through the glfw time to the update function. The `glfw.get_time()` isn't used in this project because of how timing the audio works, but it was used in previous labs and assignments. Finally, `glfw.swap_buffers(self.window)` is called to display the frame that was just drawn.
6. If the update loop stops, the `exit()` method is called.

It is important to note that the three events, `setup`, `update` and `exit` have to be defined manually.
### shader.py
The `Shader` class in `shader.py` is responsible for managing OpenGL shader programs, providing an interface for loading, compiling, and using GLSL shader files in an OpenGL application. It streamlines the often complex process of interacting with OpenGL shaders, ensuring better readability and error handling.
#### Features
- Shader Loading and Validation
    The `Shader` class validates that the provided shader file has a `.glsl` extension and loads the file content. The source is then parsed into vertex and fragment shader sections, identified by markers (`/// VERTEX_START`, `/// VERTEX_END`, etc.). Errors in parsing or missing sections are handled explicitly.
- Shader Compilation and Linking
    The `use` method compiles the vertex and fragment shaders and links them into a single shader program. It includes error handling for shader compilation and validation, with formatted error logging (`_print_shader_error`) to help debug issues in shader source code.
- Uniform Management
    Uniforms (variables shared between the shader and the application) are managed dynamically. The shader introspects its uniforms, printing their details upon successful compilation. Users can set uniforms via the `set_uniform` method, which maps Python values to GLSL types using predefined mappings (`GL_UNIFORM_MAP`).
- Error Handling and Debugging
    The shader class contains built in error checking:
    - Compiles shaders and prints detailed error messages with line numbers and shader source context.
    - Suggests corrections for uniform names using Levenshtein distance if a requested uniform is not found.
    - Shows type compatibility for uniforms and provides warnings for mismatches, including expected and provided types and values.
#### Usage
1. Initialization:
	A `Shader` object is created by passing the path to a `.glsl` file. The file must contain properly marked vertex and fragment shader sections.
2. Compilation:
	The `use` method is called to compile and activate the shader program in the OpenGL context. `OpenGLApp.load_shader` does this automatically.
3. Uniform Updates:
	The `set_uniform` method allows for dynamic updating of uniform values. This is usually done within the `update` function of the OpenGLApp class.
### utils.py
The `Utils` class in `utils.py` contains a collection of static utility methods. These utilities are designed to simplify repetitive tasks in the program, such as debugging and some math operations.

Features:
- Levenshtein Distance
    The `levenshtein_distance(s1, s2)` method calculates the Levenshtein distance between two strings. This algorithm determines the minimum number of single-character edits (insertions, deletions, or substitutions) required to transform one string into another. It is particularly useful in the shader system for suggesting corrections to uniform names when a typo is detected.
    
- Task Timing
    The `time_task(func)` decorator measures the execution time of a function. It prints detailed timing information for performance profiling, including the class and method name if called within an object instance.
    
- Linear Interpolation (LERP)
    The `lerp(a, b, t)` method performs linear interpolation between two values `a` and `b`, based on a parameter `t` in the range `[0, 1]`. It is commonly used in animation calculations.
    
- Mapping a Value Range  
    The `map(n, i1, i2, o1, o2)` method maps a number `n` from one range `[i1, i2]` to another range `[o1, o2]`. This is helpful for converting values between different scales, such as normalizing input values or adapting to screen dimensions. Values outside `[i1, i2]` are clamped to `o1` or `o2`. This is derived from the function of the same name and signature in Processing.
### mappings.py

Used by `shader.py`, `mappings.py` contains two dictionaries: `GL_TYPE_MAP` converts OpenGL type constants to readable type names (used when printing uniforms and type warnings), and `GL_UNIFORM_MAP` converts those type names to the matching uniform binding functions:

```python
GL_TYPE_MAP = {  
    GL_BYTE: 'byte',  
    GL_UNSIGNED_BYTE: 'ubyte',  
    GL_SHORT: 'short',  
    GL_UNSIGNED_SHORT: 'ushort',  
    GL_DOUBLE: 'double',  
    GL_FLOAT: 'float',
    ...
}
```

```python
GL_UNIFORM_MAP = {  
    'byte': lambda sp, loc, v: glProgramUniform1i(sp, loc, int(v)),  
    'byte[]': lambda sp, loc, v: glProgramUniform1iv(sp, loc, len(v), v),  
    'ubyte': lambda sp, loc, v: glProgramUniform1i(sp, loc, int(v)),  
    'short': lambda sp, loc, v: glProgramUniform1i(sp, loc, int(v)),
    ...
}
```

Putting all of these functions into one place, it makes other code much more readable. This method is not the most efficient, but it works for the requirements of this project and other coursework.
# The GLSL Shader

All of this code can be found within the `project_shader.glsl` file. The biggest component of the shader code comes from the fragment shader, which will be described below.

The vertex shader only exists to act as a backdrop to draw on: it outputs two triangles that cover the whole screen, a canvas for the fragment shader to draw everything else on:
```c
/// VERTEX_START  
#version 460 core  
  
void main() {  
    // Hardcode the vertices for a full-screen quad  
    vec2 positions[6] = vec2[](vec2(-1.),vec2(1.,-1.),vec2(-1.,1.),vec2(-1.,1.),vec2(1.,-1.),vec2(1.));  
  
    // Use the gl_VertexID to access the correct vertex from the array  
    vec2 position = positions[gl_VertexID];  
    gl_Position = vec4(position,0.,1.);  
}  
/// VERTEX_END
```

In this code, you can also see the `/// VERTEX_START` and `/// VERTEX_END` tags to denote shader sections used by `shader.py` for compiling.
## Shader Functions
### Math Functions
#### `random(int v)`
$$\text{random}(v) = \text{fract}(\sin(v) \cdot 43758.5453)$$
This is a standard low complexity pseudo-random function that uses a high frequency sinusoidal function to return a random value between 0 and 1 based off of the input value. This function is deterministic, which is good for making repeatable results needed here. The large multiplier (43758.5453) spreads small changes in the input across the whole 0 to 1 range.
#### `random(vec2 v)`
$$ \text{random}(\mathbf{v}) = \text{fract}\left(\sin\left(\mathbf{v} \cdot \mathbf{c}\right) \cdot 48732.4334\right)
$$
Same as `random(...)`, but in two dimensions, where $\mathbf{c}$ is an arbitrary 2D constant vector (fancy way of saying I mashed in 2 numbers and didn't change them). This version ended up unused.
#### `hsvToRgb(vec3 hsv)`
Used by `allHues(float t)`, this function converts HSV to RGB:
$$
\begin{aligned}
h & = \text{hue (0 to 1)} \\
s & = \text{saturation (0 to 1)} \\
v & = \text{value (0 to 1)}
\end{aligned}
$$
Intermediate steps:
$$c = v \cdot s, \quad x = c \cdot \left(1 - | \text{mod}(h \cdot 6, 2) - 1 | \right), \quad m = v - c$$
The RGB values are computed based on the following hue range:
$$\mathbf{rgb} = 
\begin{cases} 
(c, x, 0) & \text{if } 0 \leq h < \frac{1}{6} \\
(x, c, 0) & \text{if } \frac{1}{6} \leq h < \frac{2}{6} \\
(0, c, x) & \text{if } \frac{2}{6} \leq h < \frac{3}{6} \\
(0, x, c) & \text{if } \frac{3}{6} \leq h < \frac{4}{6} \\
(x, 0, c) & \text{if } \frac{4}{6} \leq h < \frac{5}{6} \\
(c, 0, x) & \text{otherwise}
\end{cases}
+ m
$$
Note that the shader code does not quite match this formula: the thresholds `1/6`, `2/6`, `4/6` and `5/6` are integer divisions that evaluate to 0, and `+ m` is only added in the last case. Since `allHues` always uses full saturation and value ($m = 0$), the missing `+ m` has no effect, but every hue below $\frac{3}{6}$ takes the $(0, c, x)$ case and every hue above it takes the $(c, 0, x)$ case, so the rainbow effects only cycle through two of the six colour segments.
#### `allHues(float t)`
This returns the fully saturated RGB colour for the hue $t$ (wrapped to the range 0 to 1), cycling through the whole colour wheel. This provides a nice way to convert a single number (hue) to a 3D vector (RGB) for the animations below.
#### `smoothedge(float v)`
Turns a 2D signed distance into a colour with an anti-aliased edge:
$$\text{smoothedge}(v) = \text{smoothstep}\left(0, \frac{1}{\text{resolution}_x}, v\right)$$
Points inside the shape ($v \leq 0$) become 0 (black), points more than one pixel outside become 1 (white), and the pixel in between is blended.
#### `oscillate(float a, float f, float t)`
A sine wave with amplitude $a$ and frequency $f$, used to make the 2D shapes gently grow and shrink over time:
$$\text{oscillate}(a, f, t) = a \cdot \sin(f \cdot t)$$
#### `mapping(float x, float a, float b, float c, float d)`
Normalizes $x$ from the range $[a, b]$ and clamps the result to $[c, d]$. This function ended up unused.
$$\text{mapping}(x, a, b, c, d) = \text{clamp}\left(\frac{x - a}{b - a}, c, d\right)$$
### Rotation Matrices
#### `rotateX(a)`, `rotateY(a)`, `rotateZ(a)`
Rotation matrices $R_A(a)$ are used to rotate the scene around a given axis ($A$) by a given angle ($a$):
$$
R_x(a) = 
\begin{bmatrix}
1 & 0 & 0 \\
0 & \cos(a) & -\sin(a) \\
0 & \sin(a) & \cos(a)
\end{bmatrix}
$$
$$
R_y(a) = 
\begin{bmatrix}
\cos(a) & 0 & \sin(a) \\
0 & 1 & 0 \\
-\sin(a) & 0 & \cos(a) \\
\end{bmatrix}
$$
$$
R_z(a) = 
\begin{bmatrix}
\cos(a) & -\sin(a) & 0 \\
\sin(a) & \cos(a) & 0 \\
0 & 0 & 1 \\
\end{bmatrix}
$$

GLSL's `mat3(...)` constructor fills the matrix column by column, so the matrices in the shader are the transposes of the ones above, which rotate by $-a$. This only changes the direction of each spin.
#### `rotateXYZ(float rx, float ry, float rz)`
This is a helper function that returns the three rotation matrices combined, $R_x(r_x) \cdot R_y(r_y) \cdot R_z(r_z)$, rotating around each of the three main axes.
### 2D Shaders and UV Effects
These shaders create patterns and also can directly transform the $\mathbf{uv}$. The $\mathbf{uv}$, simply put, is the position of the pixel currently being drawn. In this shader it is centred on the screen, with $y$ running from $-0.5$ to $0.5$.
#### `distort(inout vec2 uv, float t, float m)`
This function creates a wave effect with very high efficiency. Nine waves are layered for $i = 1$ to $9$; each step offsets $x$ first and then offsets $y$ using the updated $x$, so the sum below is a simplified view:
$$\mathbf{uv} =
\mathbf{uv} + \sum_{i=1}^{9} \frac{0.6}{i}
\begin{bmatrix}
\cos\left(i \cdot 2.5 \cdot \mathbf{uv}_y + t\right) \cdot m \\
\sin\left(i \cdot 3.5 \cdot \mathbf{uv}_x + t\right) \cdot m
\end{bmatrix}
$$
#### `ripple(inout vec2 uv, float t)`
This function was unused, but creates a ripple effect on the $\mathbf{uv}$, with rings spreading out from the point $(0.5, 0.5)$.
#### `bounce(inout vec2 uv, float t)`
This will cause the UV to zoom in and out. By first subtracting 0.5 from $\mathbf{uv}$, applying the transformation, then adding 0.5 back again, the zooming happens around the point $(0.5, 0.5)$. This would be the center of the screen for $\mathbf{uv}$ in the range 0 to 1, but since this shader's $\mathbf{uv}$ is centred on the screen, it zooms around the top-right corner instead. It is used for the checkered backgrounds of the 3D scenes.
$$\mathbf{uv} = (\mathbf{uv} - 0.5) \cdot (1 + 0.1 \cdot |\sin(2\pi t)|) + 0.5$$
#### `rotate(inout vec2 uv, float a)`
This rotates the $\mathbf{uv}$ around the point $(0.5, 0.5)$, the top-right corner of the screen, using a 2D version of the rotation matrices. It is used to tilt the checkered backgrounds of the 3D scenes by a different angle for each keyframe.

#### `checkers(vec2 uv, vec3 c1, vec3 c2, vec2 s, vec2 o)`
Used to make a background for some scenes, the function takes in $\mathbf{uv}$, two colours, a scale $\mathbf{s}$ (squares per unit) and an offset $\mathbf{o}$, which is animated to scroll the pattern.
$$x = \lfloor \mathbf{uv}_x \cdot s_x + o_x \rfloor, \quad y = \lfloor \mathbf{uv}_y \cdot s_y + o_y \rfloor$$
$$\text{color} = \text{mix}(\mathbf{c}_1, \mathbf{c}_2, \text{mod}(x + y, 2))$$
### Implicit Shape Signed Distance Functions (SDFs)
Signed Distance Functions (SDFs), as pointed out in previous work, are an efficient way to represent implicit geometries in computer graphics. Each SDF encodes a 3D surface by returning the shortest distance from a given point in space ($\mathbf{p}$) to the surface of the shape. Negative distances indicate points inside the shape, while positive distances correspond to points outside. These functions eliminate the need for loading complex meshes in the scope of this project.

Below is a list of SDFs used in this project. The parameter $\mathbf{s}$ (or $r$ for spheres) defines the size of the shape, while additional parameters such as $\mathbf{n}$ and $o$ are used for planes. For the Menger Sponge, $i$ denotes the recursion depth.

For the simple SDFs (those being `sdBox`, `sdCylinder`, `sdTorus`, `sdSphere`, and `sdPlane`), only mathematical representations have been shown.
#### `sdBox(vec3 p, vec3 s)`
The signed distance to an axis-aligned box of size $\mathbf{s}$ is:
$$\text{sdBox}(\mathbf{p}, \mathbf{s}) = \min\left(\max(d_x, \max(d_y, d_z)), 0\right) + \|\max(d, 0)\|
$$
Where: $$d = |\mathbf{p}| - \mathbf{s}$$
#### `sdCylinder(vec3 p, vec2 s)`
The signed distance to a capped cylinder aligned along the $y$-axis, with radius $s_x$​ and height $2 \cdot s_y$, is:
$$\text{sdCylinder}(\mathbf{p}, \mathbf{s}) = \min\left(\max(d_x, d_y), 0\right) + \|\max(d, 0)\|
$$
Where:  $$d = |\begin{bmatrix} \|\mathbf{p}_{xz}\| \\ \mathbf{p}_y \end{bmatrix}| - \mathbf{s}$$
#### `sdTorus(vec3 p, vec2 s)`
The signed distance to a torus centered at the origin, with major radius $s_x$ and minor radius $s_y$​, is:
$$\text{sdTorus}(\mathbf{p}, \mathbf{s}) = \left\|\begin{bmatrix} \|\mathbf{p}_{xz}\| - s_x \\ \mathbf{p}_y \end{bmatrix}\right\| - s_y
$$
#### `sdSphere(vec3 p, float r)`
The signed distance to a sphere of radius $r$ centered at the origin is:
$$ \text{sdSphere}(\mathbf{p}, r) = \|\mathbf{p}\| - r $$
#### `sdPlane(vec3 p, vec3 n, float o)`
The signed distance to a plane with normal vector $\mathbf{n}$ and offset $o$ is:
$$ \text{sdPlane}(\mathbf{p}, \mathbf{n}, o) = \mathbf{p} \cdot \mathbf{n} + o$$
#### `sdCross(vec3 p)`
This function computes the signed distance to a 3D cross: three infinitely long square bars of half-width 1, one along each axis. The Menger Sponge subtracts this shape from its cube. This function and `sdMengerSponge` are modified from the Connor Haskins article listed in the References.

Unminified `sdCross` code: 
```c
float sdCross(vec3 p) {
    const float half_width = 1.0;       // Half-width of the cross arms
    vec3 arm_center = vec3(half_width); // Center of the cross arms

    // Compute distances from the center
    vec3 d = abs(p) - arm_center;
    float smallest_overlap = min(min(d.x, d.y), d.z);
    float middle_overlap = d.x + d.y + d.z 
                          - smallest_overlap 
                          - max(max(d.x, d.y), d.z);
    float largest_overlap = max(max(d.x, d.y), d.z);

    // Compute signed distances for cross geometry
    vec2 max_overlap = max(vec2(smallest_overlap, middle_overlap), 0.0);
    vec2 min_overlap = min(vec2(middle_overlap, largest_overlap), 0.0);
    return length(max_overlap) - length(min_overlap);
}
```

And mathematically this function is defined by:
$$\text{sdCross}(\mathbf{p}) = \|\mathbf{o}\| - \|\mathbf{i}\|$$
Where:
- $\mathbf{o} = \max\left(\begin{bmatrix} o_s \\ o_m \end{bmatrix}, 0\right)$
- $\mathbf{i} = \min\left(\begin{bmatrix} o_m \\ o_l \end{bmatrix}, 0\right)$

And:
- $\mathbf{d} = |\mathbf{p}| - \begin{bmatrix} 1 \\ 1 \\ 1 \end{bmatrix}$
- $o_s = \min(d_x, \min(d_y, d_z))$
- $o_m = d_x + d_y + d_z - o_s - \max(d_x, \max(d_y, d_z))$
- $o_l = \max(d_x, \max(d_y, d_z))$
#### `sdMengerSponge(vec3 p, float s, int i)`
This function computes the signed distance to a Menger Sponge fractal, generated by recursively subdividing a cube into smaller cubes and removing cross-shaped sections defined by `sdCross`. 

This algorithm is recursive:

1. Start with a box of size `size` (`s` in the shader).
2. At each recursion level, subdivide the cube into smaller cubes.
3. Use the `sdCross` function to remove cross-shaped sections of each cube.
4. Combine signed distances at each iteration.

Unminified `sdMengerSponge` code: 
```c
float sdMengerSponge(vec3 p, float size, int iterations) {
    const float width = 2.0;

    // Initial signed distance to an sdBox
    float d = sdBox(p, vec3(size));
    float min_dist = d; // Initialize the minimum distance
    float scale = 1.;   // Initialize scaling factor for fractal recursion

    // Fractal recursion loop
    for (int j = 0; j < iterations; ++j) {
        // Width of the current subdivision
        float box_width = width / scale;

        // Translate position to fractal space
        float translation = -box_width / 2.;
        vec3 rep_pos = p - translation;
        vec3 mod_pos = mod(rep_pos, box_width) + translation;

        // Scale for cross subtraction
        mod_pos *= scale;

        // Signed distance to a cross scaled to one-third the size
        float cross_dist = sdCross(mod_pos / (1./3.)) * (1./3.);

        // Divide by scale for correct distance metrics
        cross_dist /= scale;

        // Combine with the current minimum distance
        min_dist = max(min_dist, -cross_dist);

        // Increase scale for the next iteration
        scale *= 3.0;
    }
    return min_dist;
}
```
Let:
- $\mathbf{p}$ = position vector in 3D space.
- $s$ = initial scale.
- $i$ = number of fractal iterations.
- $\text{sdBox}(\mathbf{p}, s)$ = signed distance to a box of size $s$.
- $\text{sdCross}(\mathbf{p})$ = signed distance to a cross shape.

The signed distance function for the Menger Sponge can be expressed as:
$$\text{sdMengerSponge}(\mathbf{p}, s, i) = \max\left(\text{sdBox}(\mathbf{p}, s), \max_{j=0}^{i-1} -\frac{1}{3 k_j} \cdot \text{sdCross}\left(3 k_j \cdot \left(\left(\mathbf{p} - \mathbf{t}_j\right) \bmod w_j + \mathbf{t}_j\right)\right)\right)$$
Where:
- $k_j = 3^j$ is the scale factor at iteration $j$.
- $w_j = \frac{2}{k_j}$ is the width of the subdivided cube at iteration $j$.
- $\mathbf{t}_j = -\frac{w_j}{2}$ is the translation of the position to fractal space.
### 2D Geometry
These functions return the signed distance from a 2D point to a mathematically defined shape: negative inside, positive outside. `smoothedge` turns these distances into the drawn shapes.
#### `circle(vec2 p, float r)`

The intersection of a 2D point $\mathbf{p}$ and a circle of radius $r$ centered at the origin is defined by
$$\text{circle}(\mathbf{p}, r) = \|\mathbf{p}\| - r$$
#### `rect(vec2 p, vec2 s)`

The intersection of a 2D point $\mathbf{p}$ and a rectangle of size $\mathbf{s}$ centered at the origin is defined by:
$$\text{rect}(\mathbf{p}, \mathbf{s}) = \min\left(\max(d_x, d_y), 0\right) + \|\max(\mathbf{d}, 0)\|$$
Where: $$\mathbf{d} = |\mathbf{p}| - \mathbf{s}$$
#### `hexagon(vec2 p, float r)`

The intersection of a 2D point $\mathbf{p}$ and a regular hexagon of radius $r$ is defined by:

$$\text{hexagon}(\mathbf{p}, r) = \max\left(|q_y|, q_x \cdot \frac{\sqrt{3}}{2} + q_y \cdot 0.5\right) - r$$
Where:$$\mathbf{q} = |\mathbf{p}|$$
#### `mandelbrot(vec2 c)`
The Mandelbrot set is a fractal defined as the set of complex numbers $\mathbf{c}$ for which the sequence $z_{n+1} = z_n^2 + \mathbf{c}$, starting from $z_0 = 0$, does not diverge. The function approximates whether $\mathbf{c}$ is in the set by iterating up to a maximum number of iterations defined by the constant $\text{MAX\_MBr\_ITR}$ (1024).

The formula for normalized iteration count is:
$$\text{mandelbrot}(\mathbf{c}) = \frac{i}{\text{MAX\_MBr\_ITR}}$$
Where:
- $i$ is the number of iterations before $|\mathbf{z}| \geq 2$
- $\mathbf{z} = \mathbf{c}$ is the initial value of the iterative process (the same as starting from $z_0 = 0$, one step ahead).

Unminified `mandelbrot` code:
```c
float mandelbrot(vec2 c) {
    vec2 z = c;
    int i = 0;
    while (length(z) < 2.0 && i < MAX_MBr_ITR) {
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        i++;
    }
    return float(i) / float(MAX_MBr_ITR);
}
```

The `mandelbrot` function doesn't return a true in-or-out Boolean but rather the normalized iteration count, which gives the smooth bands of shading around the set.
### Scene Management and Rendering Functions

The following functions are identical to those used in my work done for Assignment 2, with the addition of a new simple function called `collides`:
#### `add(inout float d, vec3 p, int s, vec4 sp, mat3 r)`
Adds SDFs to the scene by selecting the minimum distance from each object and the current $d$ value. `s` picks the shape, `sp` holds its size parameters, and `r` rotates it; translation is done by offsetting `p` before calling.
#### `map(vec3 pos)`
Contains all the scene information, choosing which shapes exist based on the current keyframe, and returns the distance to the nearest surface.
#### `raymarch(vec3 o, vec3 r)`
 Used to trace rays through the scene by moving in steps along the ray's direction until it either hits a surface or exceeds a maximum distance.
#### `shadow(vec3 p, vec3 l)`
To determine shadows, the shader checks if the point is in shadow by performing a raymarch in the direction of the light. If the distance to the surface is smaller than a threshold, it is in shadow. This type of shadow generation creates hard shadows.
#### `occlusion(vec3 p, vec3 n)`
Darkens crevices based on how much light exposure the surface point is receiving by checking for nearby surfaces.
#### `normal(vec3 p)`
Returns the normal of a point in the scene by calculating the change in depth over all 3 dimensions via finite differencing.
#### `specular(vec3 n, vec3 l, vec3 v)`
Specular highlights are calculated using the Phong reflection model.
#### `collides(vec3 p)`
This function is just used to see if there is an object in the path of the vector at all. Used to know which pixels can be backgrounds (such as the checkers pattern).
### Animation Functions
#### `invert(inout vec3 color, float t)`
This function just inverts the colour of the screen relative to `t`, like mix.
#### `audioBar(inout vec3 color, vec2 uv, float length_mult)`
The `audioBar` function is used to visualize audio data as frequency bars on the sides of the screen. The function is broken into the following steps:

1. Calculate Bar Thickness
    The height of each bar (`bar_thickness`) is calculated by dividing the screen height (`800`) by the total number of bars (`BAR_COUNT`).
2. Determine the Current Bar
    Using the Y-coordinate of the fragment (`gl_FragCoord.y`), the function calculates which bar (`bar_index`) the current fragment belongs to. This is done by dividing the Y-coordinate by the `bar_thickness` and casting it to an integer.
3. Ensure Valid Bar Index
    The function checks if `bar_index` is within the valid range (0 to `BAR_COUNT - 1`). This ensures fragments outside the defined bars are ignored.
4. Calculate Bar Size
    The size of the bar (`bar_size`) is determined by multiplying the corresponding audio data (`u_audio_data[bar_index]`) by a scaling factor (`800.`) and the `length_mult` parameter. The `length_mult` parameter scales every bar, which lets the bars grow in at the start of keyframe 18 and shrink away during keyframe 24.
5. Invert Colors Inside the Bars
    If the X-coordinate of the fragment (`gl_FragCoord.x`) falls within the range defined by `bar_size` on either side of the screen (`<= bar_size` or `>= (800 - bar_size)`), the `invert` function is applied to the color with a strength of `0.8`. This makes the bars stand out from whatever is behind them.
6. Blend Colors Near the Screen Edges
    For fragments within the outer 70% of each bar's length (`bar_size * 0.7`, measured from the screen edge), the color is also mixed with a pulse-based color (`vec3(u_pulse1.x)`), so that part of the bar flashes white on each beat. The blend factor (`0.4`) controls the intensity of the mix.

### Lighting Calculations
#### `calculateLighting(vec3 world_pos, vec3 normal, vec3 viewDir, vec3 lightDir, vec3 lightColor)`
Used by `processRaymarchKeyframe`, `calculateLighting` is called once per light source in the current 3D scene (three coloured lights for keyframes 4 to 8, one white light otherwise). It combines the hard shadow, diffuse lighting and Phong specular highlight for that light; ambient occlusion is applied afterwards, to the total.
### Keyframe Functions
#### `processRaymarchKeyframe(vec2 uv, int keyframeIdx, out vec3 color)`
This function puts the repeated 3D rendering code in one place, used to draw the 3D scenes during their respective keyframes. It sets up the camera, raymarches the scene from `map`, adds up the lighting and ambient occlusion, and darkens the result on each beat (except in keyframe 12). Pixels that don't hit an object get a background instead: a gradient for the Menger Sponge scenes, or a checkered pattern moved by `bounce`, `rotate` and (from keyframe 19) `distort`.
#### `main()`
The fragment shader's `main` picks what to draw from `u_keyframe_index`. `main.py` moves to the next keyframe when the beat count reaches the next entry in `song_keyframes`, and closes the program after the last one.

| Keyframe | Starts at beat | Time | Scene |
| -------- | -------------- | ---- | ----- |
| 0 | 0 | 0:00 | A black circle that gently grows and shrinks |
| 1 | 10 | 0:05 | The circle also pulses with each onset |
| 2 | 26 | 0:12 | The shape morphs between a circle and a square on each beat, flashing red |
| 3 | 42 | 0:19 | A square that wobbles with `distort` as the colours slowly invert |
| 4 | 47 | 0:22 | 3D: a cube lit by red, green and blue lights, with a checkered background fading in |
| 5 | 55 | 0:25 | 3D: a cube surrounded by six small cubes that pulse with each onset |
| 6 | 63 | 0:29 | 3D: a cube inside a spinning torus |
| 7 | 71 | 0:33 | 3D: a row of seven bobbing cylinders |
| 8 | 79 | 0:36 | 3D: a cube, torus and orbiting sphere; the audio bars appear |
| 9 | 87 | 0:40 | 3D: five cubes moving in a wave |
| 10 | 95 | 0:44 | 3D: five nested spinning rings |
| 11 | 103 | 0:47 | 3D: a sphere with five orbiting spheres and a ring |
| 12 | 111 | 0:51 | 3D: the Menger Sponge |
| 13 | 127 | 0:58 | Fluid colours from `distort`, with the audio bars |
| 14 | 143 | 1:06 | The Mandelbrot zoom, fading to white at the end |
| 15 | 211 | 1:37 | Back to the circle and square morph, flashing rainbow colours |
| 16 | 243 | 1:52 | A circle and hexagon morph, inverting over time |
| 17 | 259 | 1:59 | The shape shrinks to a point on black |
| 18 | 275 | 2:07 | 3D: the Menger Sponge flies away and shrinks as the audio bars grow in |
| 19 to 24 | 306 | 2:21 | 3D: a spinning cylinder and box over distorted rainbow checkers; the audio bars shrink away in keyframe 24 |

The program closes at beat 409 (3:09).
# Conclusion
While I had initially intended to have a complete visualization for the full duration of the music, I ran into challenges during the process, particularly with testing features that occur later in the song, past the one-minute mark. Keyframes 19 to 24 all show the same scene for this reason. Repeatedly listening to the song without a reliable way to test those later features made debugging and testing increasingly difficult. Despite these challenges, I enjoyed working with raymarching and the wide range of effects that can be created through it. This project is a good example of what I can do with basic raymarching and simple 2D shader effects.

The later portion of the song was meant to incorporate volumetric clouds and atmospheric rendering, using sections from a shader I used in the previous year. However, due to the significant differences in code structure and the length of the advanced shaders, I was unable to convert, implement, and test it within a reasonable time (on top of being difficult to debug past the one-minute mark). Plus, implementing these features would have introduced substantial mathematical complexity, which would have required additional explanation and conversion into LaTeX. Given the content already included in this report (such as the Mandelbrot set, raymarching, and the Menger Sponge SDF), I opted to leave these out and settle with what remained.

Overall, I am satisfied with the work I have put into this project.

And lastly, here is the music used: [Safri Duo - Played A Live [Viktor Newman Bootleg]](https://soundcloud.com/djviktornewman/safri-duo-played-a-live-viktor-newman-bootleg-free-download)
# References
- CSCI 4110 - Assignment 1 - Zachary Wayne
- CSCI 4110 - Assignment 2 - Zachary Wayne
- CSCI 4110 - Lab 3 - Zachary Wayne
- CSCI 4110 - Lab 5 - Zachary Wayne
- https://media.contentapi.ea.com/content/dam/eacom/frostbite/files/s2016-pbs-frostbite-sky-clouds-new.pdf
- https://books.google.ca/books?id=dh7rCAAAQBAJ&pg=PA7&redir_esc=y#v=onepage&q&f=false
- https://mathworld.wolfram.com/DiscreteFourierTransform.html
- https://connorahaskins.substack.com/p/ray-marching-menger-sponge-breakdown
- https://processing.org/
- https://processing.org/reference/map_.html
- https://www.geeksforgeeks.org/introduction-to-levenshtein-distance/
- http://www.thebookofshaders.com/
- https://easyguet.ch/temp/thebookofshaders.pdf
- https://thebookofshaders.com/edit.php?log=160414040957
- https://math.bu.edu/DYSYS/explorer/def.html
- https://marksmath.org/classes/DiscourseArchive/FractalLACFall2016/t/post-a-groovy-image-of-the-mandelbrot-set/73/
- http://www.jakebakermaths.org.uk/maths/mandelbrot/canvasmandelbrotv12.html