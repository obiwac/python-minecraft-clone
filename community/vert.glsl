#version 330

layout(location = 0) in vec3 a_Position;
layout(location = 1) in vec2 a_TextureFetcher;
layout(location = 2) in float a_Shading;
layout(location = 3) in float a_BlockLight;
layout(location = 4) in float a_SkyLight;


out vec3 v_Position;
out vec3 v_TexCoords;
out float v_Shading;
out float v_Light;

uniform mat4 u_ModelViewProjMatrix;
uniform float u_Daylight;

const vec2 texture_UV[4] = vec2[4](
	vec2(0.0, 1.0),
	vec2(0.0, 0.0),
	vec2(1.0, 0.0),
	vec2(1.0, 1.0)
);

void main(void) {
	v_Position = a_Position;
	v_TexCoords = vec3(texture_UV[int(a_TextureFetcher[0])], a_TextureFetcher[1]);
	v_Shading = a_Shading;
	v_Light = max(a_BlockLight, a_SkyLight * u_Daylight);
	gl_Position = u_ModelViewProjMatrix * vec4(a_Position, 1.0);
}