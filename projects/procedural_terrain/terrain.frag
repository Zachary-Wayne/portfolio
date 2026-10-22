// Zachary Wayne | CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)

#ifdef GL_ES
precision mediump float;
#endif

float seed      		= 3.624;	// Default: 3.624
float cameraHeight		= 3.144;	// Recommeded: 1.5 to 5	-	High = Higher Camera position
float yScale    		= 1.; 		// Recomended: 1	 	-	High = +Artifacting, Low = +Raymarch error
float xzScale   		= 3.984; 	// Recomended: 2 to 5	-	High = smaller land masses
float yPreScale 		= 0.972;	// Recomended: .4 to 1	-	High = Flatter terrain
float yPreOffset		= 1.584;	// Recomended: 1 to 4	-	High = Higher terrain offset, less water, more snow 
float shallowWaterWaveH = 0.128;	// Recomended: .1 to .3	- 	High = Big Waves
const int raymarchMax 	= 100; 		// Default: 100, preforance heavy

const float PI = 3.1415926;

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

float noise(vec2 p) {
    return fract(sin(dot(p.xy, vec2(12.9898, 78.233))) * 43758.5453 * seed);
}

float smoothNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);

    float a = noise(i);
    float b = noise(i + vec2(1.0, 0.0));
    float c = noise(i + vec2(0.0, 1.0));
    float d = noise(i + vec2(1.0, 1.0));

    float u = f.x * f.x * (3.0 - 2.0 * f.x);
    float v = f.y * f.y * (3.0 - 2.0 * f.y);
    return mix(mix(a, b, u), mix(c, d, u), v);
}

float fractalNoise(vec2 p, float frequency, float amplitude) {
    return smoothNoise(p * frequency) * amplitude; // Octave = 1
}

float terrain(vec3 p) {
    p.xz *= xzScale;
    // Mountains
    float baseTerrain = fractalNoise(p.xz * 0.1, 0.4, 2.0);
    float mountainNoise = smoothNoise(p.xz * -0.022) * 4.0;

    // hills, valleys
    float hillNoise = fractalNoise(p.xz * 0.25, 0.15, 1.2);
    float valleyNoise = smoothNoise(p.xz * 0.15) * 2.5;

    // Surface roughness
    float detailNoise = smoothNoise(p.xz * 0.75) * smoothNoise(p.xz * 0.5) * 0.6;
    
    // Weighting Noise
    float height = baseTerrain * 0.8 + mountainNoise * 0.5 + hillNoise * 0.4 - valleyNoise * 0.3 + detailNoise * 0.2;

    // Offsets
    return p.y * yPreScale + height - yPreOffset;
}

vec3 paint(vec3 cameraPos, float height, vec3 currentPosition, inout float dist) {
    vec2 c = currentPosition.xz;
    vec2 d = vec2(-currentPosition.x, currentPosition.z) + vec2(cameraPos.x * 1.2, cameraPos.z * 0.5);
    vec3 color;

    if (height < 0.) { 
        // Water
        float waveFrequency = 3.0;
        float waveAmplitude = 0.2;
        float wave = fractalNoise(c * waveFrequency, 0.1, 0.1) * waveAmplitude;
        float j = -fractalNoise(c, 0.2, 0.2) + 1.112;
        dist = 0.0;
        height = 0.0;
        vec3 waterColor = vec3(0.019, 0.019, 1.000);
        color = mix(color, waterColor + vec3(wave, wave * 0.5, wave * 0.3), j);
    } else if (height < shallowWaterWaveH * smoothNoise(d)) {
        // Shallow Water / Foam
        color = mix(color, vec3(0.000, 0.794, 0.970), 1.);
    } else if (height < 1.160) {
        // Grass
        float j = smoothNoise(c * 0.5) * height;
        color = mix(vec3(0.6, 0.9, 0.3), vec3(0.086, 0.500, 0.081), smoothstep(1., -1., height - j));

        // Sand / Beach
        color = mix(color, vec3(0.945, 0.901, 0.305), smoothstep(0.116, 0., j));
    } else if (height - smoothNoise(c * 0.052) < 0.836 + smoothNoise(c * 0.148) - 0.5) {
        // Soil
        color = mix(vec3(0.6, 0.9, 0.3), vec3(0.5, 0.35, 0.15), smoothstep(-0.520, 0.444, height));
    } else if (height < 1.616) {
        // Stone
        color = vec3(0.5, 0.5, 0.5);
    } else {
        // Snow
        color = vec3(0.860, 0.860, 0.860);
    }

    // Fake Clouds and sunlight
    color = mix(color, vec3(0.003, 0.003, 0.005), smoothNoise(d * -0.075) - smoothNoise(d * 0.276) * 0.944);
    
    // Shadow-like effect
    return mix(color, vec3(0.001, 0.130, 0.000), smoothstep(-1.0, 1.0, -height));
}



vec3 raymarch(vec3 cameraPos, vec3 direction) {
    float totalDistance = 0.0;
    for (int i = 0; i < raymarchMax; i++) {
        vec3 currentPosition = cameraPos + totalDistance * direction;
        float dist = terrain(currentPosition);
        if (dist < 0.01) {
            float height = currentPosition.y;
            return paint(cameraPos, height, currentPosition, dist);
        }
        totalDistance += dist * yScale;;
    }
    // Sky Color
    float sty = gl_FragCoord.y / u_resolution.y;
    return mix(vec3(0.557, 0.804, 0.820), vec3(0.243, 0.720, 0.805), sty * 5.);
}

mat3 rotationMatrixY(float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat3(
        c, 0.0, s,
        0.0, 1.0, 0.0,
        -s, 0.0, c
    );
}

mat3 rotationMatrixX(float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat3(
        1.0, 0.0, 0.0,
        0.0, c, -s,
        0.0, s, c
    );
}

void main() {
    vec2 st = gl_FragCoord.xy / u_resolution.xy;
    st.x *= u_resolution.x / u_resolution.y;

    vec3 cameraPos = vec3(0.0, cameraHeight, 3.0);
    
    float yaw = (u_mouse.x / u_resolution.x - 0.5) * PI * 2.0;
    float pitch = -(u_mouse.y / u_resolution.y - 0.5) * PI * .3;

    cameraPos.x += u_time;
    cameraPos.z -= u_time; 
    
    vec3 rayDir = normalize(vec3(st - 0.5, -1.0));
    rayDir = rotationMatrixY(yaw) * rotationMatrixX(pitch) * rayDir;

    gl_FragColor = vec4(raymarch(cameraPos, rayDir), 1.0);
}


