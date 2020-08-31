#version 330 // specify we are indeed using modern opengl

out vec4 fragment_colour; // output of our shader

in vec3 local_position;  // interpolated vertex position

void main(void) {
	fragment_colour = vec4(local_position / 2.0 + 0.5, 1.0); // set the output colour based on the vertex position
}