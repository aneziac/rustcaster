#include "../include/player.hpp"
#include <math.h>


const int Player::adjacent[4] = {0, 1, 0, -1};

Player::Player(int pos[2], World* world) : world(world) {
    x = (pos[0] + 0.5) * world->getBlockSize();
    y = (pos[1] + 0.5) * world->getBlockSize();

    dir = 0.01;
    stepSize, turnSpeed = 4.0, 0.03;
    fov = 60.0;
}

double radians(double degrees) {
    return degrees * M_PI / 180.0;
}

void Player::move() {

}

double *Player::getPos() const {
    double pos[2] = {x, y};
    return pos;
}

double *Player::getDirVec(double offset) const {
    double offsetRad = radians(offset);
    double dirVec[2] = {cos(dir + offsetRad), sin(dir + offsetRad)};
    return dirVec;
}

uint8_t Player::find_walls() {
    uint8_t wallFlags = 0;

    blockX = (int)x / world->getBlockSize();
    blockY = (int)y / world->getBlockSize();

    for (uint n = 0; n < 4; n++) {
        wallFlags |= (1 << n) * (bool)
        world->gameMapAt(
            blockX + adjacent[n],
            blockY + adjacent[(n + 2) % 4]
        );
    }

    return wallFlags;
}

void Player::collide(uint8_t wallFlags) {
    if (wallFlags & 1) {
        y = min((uint)y, (blockY + 1) * (world->getBlockSize() - 1));
    }
    if (wallFlags & 2) {
        y = min((uint)x, (blockX + 1) * (world->getBlockSize() - 1));
    }
    if (wallFlags & 4) {
        x = max((uint)y, blockY * world->getBlockSize());
    }
    if (wallFlags & 8) {
        x = max((uint)x, blockX * world->getBlockSize());
    }
}

void Player::loop() {
    uint8_t wallFlags = find_walls();
    move();
    collide(wallFlags);
}
