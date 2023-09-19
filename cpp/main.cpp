#include "include/world.hpp"
#include "include/player.hpp"


int main() {
    auto world = World("../default_map.png", false);

    int pos[2] = {1, 1};
    auto player = Player(pos, &world);
    return 0;
}
