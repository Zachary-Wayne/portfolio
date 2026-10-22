precision mediump float;
varying vec2 vTexCoord;
uniform float uTime;

void distort(inout vec2 uv, float t, float m) {
    for (float i = 1.0; i < 5.0; i++) {
        float factor = 0.6 / i;
        uv.x += factor * cos(i * 2.5 * uv.y + t * 0.95) * m;
        uv.y += factor * sin(i * 3.5 * uv.x + t) * m;
    }
}

void main() {
    vec2 uv = vTexCoord;
    float time = uTime;

    distort(uv, time, 1.0);
    distort(uv, time * 0.78, sin(time) * 0.5 + 0.2);

    vec3 color1 = vec3(0.6, 0.3, 0.9);
    vec3 color2 = vec3(0.3 * sin(time * 1.4), 0.0, 0.5 * sin(time * 1.4) + 0.2);
    vec3 finalColor = mix(color1, color2, uv.x + uv.y * sin(time * 0.34) + 0.5);

    gl_FragColor = vec4(finalColor * 0.5, 0.5);
}