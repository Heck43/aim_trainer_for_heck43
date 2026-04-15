#version 150

uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;
in vec4 p3d_Color;

out vec4 v_color;
out float v_height;
out vec3 v_local_pos;

void main() {
    v_color = p3d_Color;
    v_height = p3d_Vertex.z;
    v_local_pos = p3d_Vertex.xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
