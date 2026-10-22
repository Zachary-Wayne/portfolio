/// FRAGMENT_START
#version 460 core

uniform vec2 u_resolution, u_mouse;
uniform float u_time;

out vec4 FragColor;

// Helpers from the CSCI 4110U project shader.
void distort(inout vec2 uv, float t, float m){for(float i=1.0;i<10.0;i++){uv.x+=0.6/i*cos(i*2.5*uv.y+t)*m;uv.y+=0.6/i*sin(i*3.5*uv.x+t)*m;}}
vec3 checkers(vec2 uv, vec3 c1, vec3 c2, vec2 s, vec2 o){float x=floor(uv.x*s.x+o.x),y=floor(uv.y*s.y+o.y);return mix(c1,c2,mod(x+y,2.0));}
float smoothedge(float v){return smoothstep(0.0,1.0/u_resolution.x,v);}
float circle(vec2 p,float r){return length(p)-r;}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;
    vec2 mouse = (u_mouse - 0.5 * u_resolution) / u_resolution.y;

    vec2 warped = uv;
    distort(warped, u_time * 0.6, 0.12 + 0.1 * smoothstep(0.5, 0.0, length(uv - mouse)));
    vec3 color = checkers(warped, vec3(0.08, 0.10, 0.16), vec3(0.16, 0.42, 0.62), vec2(6.0), vec2(u_time * 0.4, 0.0));

    for (int i = 0; i < 5; i++) {
        float a = u_time * 0.8 + float(i) * 1.2566;
        vec2 p = mouse + 0.22 * vec2(cos(a), sin(a * 1.3));
        float ring = abs(circle(uv - p, 0.06 + 0.02 * sin(u_time * 3.0 + float(i)))) - 0.008;
        color = mix(vec3(0.98, 0.84, 0.45), color, smoothedge(ring));
    }
    color = mix(vec3(1.0), color, smoothedge(circle(uv - mouse, 0.025)));

    FragColor = vec4(color, 1.0);
}
/// FRAGMENT_END


/// VERTEX_START
#version 460 core

void main() {
    vec2 positions[6] = vec2[](vec2(-1.),vec2(1.,-1.),vec2(-1.,1.),vec2(-1.,1.),vec2(1.,-1.),vec2(1.));
    gl_Position = vec4(positions[gl_VertexID], 0., 1.);
}
/// VERTEX_END
