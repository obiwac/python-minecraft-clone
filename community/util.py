import glm

DIRECTIONS = (glm.ivec3(1, 0, 0), 
            glm.ivec3(-1, 0, 0), 
            glm.ivec3(0, 1, 0), 
            glm.ivec3(0, -1, 0), 
            glm.ivec3(0, 0, 1), 
            glm.ivec3(0, 0, -1))

EAST = glm.ivec3(1, 0, 0)
WEST = glm.ivec3(-1, 0, 0)
UP = glm.ivec3(0, 1, 0)
DOWN = glm.ivec3(0, -1, 0)
SOUTH = glm.ivec3(0, 0, 1)
NORTH = glm.ivec3(0, 0, -1)