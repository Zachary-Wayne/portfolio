/****
* Authors: Samuel Shard, Zachary Wayne
* License: MIT
*/

#include "mesh2voxels.h"

// Moller-Trumbore intersection algorithm
// Determines if ray with given origin and direction vector intersects a face.
// Intersection point that is passed in by reference will be modified.
// Returns true if intersection, false otherwise
// From: https://stackoverflow.com/questions/46443580/opengl-intersection-between-vector-and-face
bool rayIntersectsFace(const glm::vec3& rayOrigin, const glm::vec3& rayVector,
	const glm::vec3& v0, const glm::vec3& v1, const glm::vec3& v2, glm::vec3& intersectionPoint) {
	const float EPSILON = 0.000001f;
	glm::vec3 edge1, edge2, h, s, q;
	float a, f, u, v;

	edge1 = v1 - v0;
	edge2 = v2 - v0;

	h = glm::cross(rayVector, edge2);
	a = glm::dot(edge1, h);

	if (a > -EPSILON && a < EPSILON)
		return false; // Ray is parallel to the triangle.

	f = 1.0f / a;
	s = rayOrigin - v0;
	u = f * glm::dot(s, h);

	if (u < 0.0f || u > 1.0f)
		return false;

	q = glm::cross(s, edge1);
	v = f * glm::dot(rayVector, q);

	if (v < 0.0f || u + v > 1.0f)
		return false;

	// At this stage we can compute t to find out where the intersection point is on the line.
	float t = f * glm::dot(edge2, q);
	if (t > EPSILON) // ray intersection
	{
		intersectionPoint = rayOrigin + rayVector * t;
		return true;
	}
	else // This means that there is a line intersection but not a ray intersection.
		return false;
}



/*
 Calls checkIntersection for a given point and a given ray for every face in the model.
 ODD = INSIDE
 EVEN = OUTSIDE (Example 0 intersections means point is outside 3D object)
 RETURNS true IF INSIDE, false OTHERWISE

 "A point is inside the polygon if either count of intersections is odd or point lies on an edge of polygon.
 If none of the conditions is true, then point lies outside."
 https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/
*/
bool isPointInMesh(glm::vec3& point, glm::vec3 rayVector, GLfloat* globalVertices, int globalNv, GLushort* globalIndices, int globalNi) {
	bool inside = false; //start with 0 intersections == false
	glm::vec3 intersectionPoint;

	//loop over each face in the model, for each intersection flip inside from true to false and vice versa
	//point is used as ray origin for rayIntersectsFace function
	for (int i = 0; i < globalNi; i += 3) {
		glm::vec3 v0 = glm::vec3(globalVertices[globalIndices[i] * 3], globalVertices[globalIndices[i] * 3 + 1], globalVertices[globalIndices[i] * 3 + 2]);
		glm::vec3 v1 = glm::vec3(globalVertices[globalIndices[i + 1] * 3], globalVertices[globalIndices[i + 1] * 3 + 1], globalVertices[globalIndices[i + 1] * 3 + 2]);
		glm::vec3 v2 = glm::vec3(globalVertices[globalIndices[i + 2] * 3], globalVertices[globalIndices[i + 2] * 3 + 1], globalVertices[globalIndices[i + 2] * 3 + 2]);
		if (rayIntersectsFace(point, rayVector, v0, v1, v2, intersectionPoint)) {
			//TODO: Account for edge cases
			inside = !inside;
		}
	}
	return inside;
}

std::size_t ArraySize(GLushort* arr) {
	std::size_t size = 0;
	while (arr[size] != 0) {
		++size;
	}
	return size;
}


std::size_t ArraySize(GLfloat* arr) {
	std::size_t size = 0;
	while (arr[size] != 0) {
		++size;
	}
	return size;
}


std::vector<int> getVoxelMesh(GLfloat* vertecies, GLushort* indices)
{
	std::vector<int> voxelArray(gridSize * gridSize * gridSize, 0); // Initialize with 0s
	for (int x = 0; x < gridSize; ++x) {
		for (int y = 0; y < gridSize; ++y) {
			for (int z = 0; z < gridSize; ++z) {
				glm::vec3 cubeCenter = glm::vec3(x * cubeSize - offset, y * cubeSize - offset, z * cubeSize - offset);
				if (isPointInMesh(cubeCenter, direction, vertecies, ArraySize(vertecies), indices, ArraySize(indices))) { // Mesh is present at this coordinate
					voxelArray[x * gridSize * gridSize + y * gridSize + z] = 1;
				}
			}
		}
	}
	return voxelArray;
}

/*
for (int x = 0; x < gridSize; ++x) {
	blue = 0.1;
	for (int y = 0; y < gridSize; ++y) {
		green = 0.1;
		for (int z = 0; z < gridSize; ++z) {
			cubes[x][y][z] = copyObject(&cube_model);
			cubes[x][y][z]->setPosition(x * cubeSize - offset, y * cubeSize - offset, z * cubeSize - offset);
			cubeCenter = glm::vec3(x * cubeSize - offset, y * cubeSize - offset, z * cubeSize - offset);
			isInside = isPointInMesh(cubeCenter, direction, dog_model.vertices, dog_model.vertex_count,
				dog_model.indices, dog_model.index_count);

			if (isInside) { // Square is solid, covered by model
				cubes[x][y][z]->isSolid = 1;
				cubes[x][y][z]->colour = glm::vec4(0, 0, 0, 1.0);
			}
			else { // Else square is not solid
				cubes[x][y][z]->colour = glm::vec4(red, blue, green, 0.1f);
			}
			green += 0.1;
		}
		blue += 0.1;
	}
	red += 0.1;
}
*/