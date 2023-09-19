#ifndef WORLD_HPP
#define WORLD_HPP

#include <iostream>
#include <vector>
using namespace std;


class World {
    private:
        uint WIDTH, HEIGHT;
        const uint blockSize = 80;
        const uint lowerCorner[2] = {0, 0};
        uint upperCorner[2];
        vector<vector<uint>> GAME_MAP;
        // color Colors[];

    public:
        World(string mapPath, bool debug);
        vector<vector<uint>> loadMap(string mapPath);
        bool inBoundaries(double x, double y) const;

        uint getBlockSize() const { return blockSize; }
        uint gameMapAt(uint i, uint j) const { return GAME_MAP[i][j]; }
};

#endif
