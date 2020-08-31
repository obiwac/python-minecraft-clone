#version 330 // specify we are indeed using modern opengl

layout(location = 0) in vec3 vertex_position; // vertex position attribute

out vec3 local_position; // interpolated vertex position

void main(void) {
	local_position = vertex_position;
	gl_Position = vec4(vertex_position, 1.0); // set vertex position
}