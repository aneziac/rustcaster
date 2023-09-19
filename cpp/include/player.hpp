#ifndef PLAYER_HPP
#define PLAYER_HPP

#include "world.hpp"


class Player {
    private:
        double x, y, dir;
        uint blockX, blockY;
        const World* world;
        double stepSize, turnSpeed;
        double fov;
        const static int adjacent[4];

    public:
        Player(int pos[2], World* world);
        void move();
        double* getPos() const;
        double* getDirVec(double offset = 0) const;
        uint8_t find_walls();
        void collide(uint8_t wallFlags);
        void loop();
};

#endif
