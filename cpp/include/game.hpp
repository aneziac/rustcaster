#include "player.hpp"
#include "world.hpp"

#ifndef GAME_HPP
#define GAME_HPP


class Game {
    private:
        const Player* player;
        const World* world;
        const bool projectionType;
        double projPlaneDist;
        uint minimapBlockSize;
        double scaleFactor;
        uint debugRayLength;
        double variance;
        double distErrTolerance;
        bool debug;

    public:
        Game(Player *player, World *world, bool debug = false, bool projection_type = false);
        double raycast(double angle, bool x);
        void draw();
};

#endif
