#include "../include/world.hpp"


World::World(string mapPath, bool debug) {
    if (debug) {
        GAME_MAP = {
            {1, 1, 1, 1, 1},
            {1, 0, 0, 0, 1},
            {1, 0, 2, 0, 1},
            {1, 0, 0, 0, 1},
            {1, 1, 1, 1, 1}
        };
    } else {
        GAME_MAP = loadMap(mapPath);
    }

    WIDTH, HEIGHT = GAME_MAP[0].size(), GAME_MAP.size();
    upperCorner[0] = WIDTH * blockSize;
    upperCorner[1] = HEIGHT * blockSize;
}

vector<vector<uint>> World::loadMap(string mapPath) {

}

bool World::inBoundaries(double x, double y) const {
    return x >= lowerCorner[0] && x < upperCorner[0] &&
           y >= lowerCorner[0] && y < upperCorner[1];
}
