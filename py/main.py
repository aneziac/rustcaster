import pygame as pg
import pygame.key
import pglib
from pglib import Coordinate, Palette, Rectangle
import numpy as np
import sys


class World:
    def __init__(self, map_path: str, debug=False):
        if debug:
            self.GAME_MAP = [
                [1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1],
                [1, 0, 2, 0, 1],
                [1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1]
            ]
            self.COLORS = [
                Palette.BLACK,
                Palette.DARKGRAY,
                Palette.GREEN
            ]

        else:
            self.GAME_MAP, self.COLORS = self.load_map(map_path)

        self.WIDTH, self.HEIGHT = len(self.GAME_MAP[0]), len(self.GAME_MAP)
        self.block_size = 80
        self.lower_corner = (0, 0)
        self.upper_corner = (self.WIDTH * self.block_size,
                            self.HEIGHT * self.block_size)

    def load_map(self, map_path) -> tuple[list[list[int]], list[pg.Color]]:
        im = pglib.load_image(map_path)
        size = im.get_size()
        game_map, colors = [[0] * size[0] for _ in range(size[1])], [Palette.INVISIBLE]

        for i in range(size[0]):
            for j in range(size[1]):
                c = im.get_at((i, size[1] - 1 - j))
                if c not in colors:
                    colors.append(c)
                if c[3] != 0:  # alpha channel is 0, meaning it's invisible so we don't care
                    game_map[i][j] = colors.index(c)

        return game_map, colors

    def in_boundaries(self, x: float, y: float) -> bool:
        return x >= self.lower_corner[0] and x < self.upper_corner[0] and \
               y >= self.lower_corner[1] and y < self.upper_corner[1]


class Player:
    def __init__(self, pos: tuple[int, int], world: World):
        x, y = pos
        self.x = world.block_size * x + (world.block_size // 2)
        self.y = world.block_size * y + (world.block_size // 2)
        self.world = world
        self.dir = np.float64(0.01)  # prevent division by zero by giving small intial value
        self.step_size = 2.0
        self.turn_speed = 0.015
        self.fov = np.float64(60)

    def move(self) -> None:
        keys = pygame.key.get_pressed()

        if keys[pg.K_w]:
            self.x += self.step_size * np.cos(self.dir)
            self.y += self.step_size * np.sin(self.dir)

        if keys[pg.K_s]:
            self.x -= self.step_size * np.cos(self.dir)
            self.y -= self.step_size * np.sin(self.dir)

        if keys[pg.K_a]:
            self.dir += self.turn_speed

        if keys[pg.K_d]:
            self.dir -= self.turn_speed

    @property
    def pos(self) -> pg.Vector2:
        return pg.Vector2(self.x, self.y)

    def dirvec(self, offset: float = 0) -> pg.Vector2:
        offset_rad = np.radians(offset)
        return pg.Vector2(np.cos(self.dir + offset_rad), np.sin(self.dir + offset_rad))

    def find_walls(self) -> int:
        # store walls near player location as a bitmask in order N E S W
        wall_flags = 0

        # store these in the object because they'll be useful later
        self.block_x = int(self.x) // self.world.block_size
        self.block_y = int(self.y) // self.world.block_size

        # this bit is unnecessarily fancy but it's clever so I'm keeping it
        for n in range(4):
            wall_flags |= (1 << n) * bool(
                self.world.GAME_MAP[self.block_x + int(np.sin(np.pi / 2 * n))] \
                                   [self.block_y + int(np.cos(np.pi / 2 * n))]
            )

        return wall_flags

    def collide(self, wall_flags: int) -> None:
        # collision resolution based on bitmask flags set by find_walls
        if wall_flags & 1:
            self.y = min(self.y, (self.block_y + 1) * self.world.block_size - 1)
        if wall_flags & 2:
            self.x = min(self.x, (self.block_x + 1) * self.world.block_size - 1)
        if wall_flags & 4:
            self.y = max(self.y, self.block_y * self.world.block_size)
        if wall_flags & 8:
            self.x = max(self.x, self.block_x * self.world.block_size)

    def loop(self) -> None:
        wall_flags = self.find_walls()
        self.move()
        self.collide(wall_flags)


class Game:
    def __init__(self, screen: pglib.Screen, player: Player, world: World, debug=False, projection_type=False):
        self.screen = screen
        self.player = player
        self.world = world
        self.projection_type = projection_type  # True = gaussian, False = linear
        self.PROJ_PLANE_DIST: float = self.screen.WIDTH / 2 / np.tan(np.radians(self.player.fov / 2))
        self.MINIMAP_BLOCK_SIZE: int = np.ceil(self.screen.HEIGHT / 3 / self.world.HEIGHT)
        self.SCALE_FACTOR = self.MINIMAP_BLOCK_SIZE / self.world.block_size
        self.SHADE = Palette.DARKGRAY
        self.DEBUG_RAY_LENGTH = max(8, self.MINIMAP_BLOCK_SIZE / 2)

        # when using gaussian projection, blocks are all 10% of screen when more than _ blocks away
        falloff_distance = 6
        self.VARIANCE = (falloff_distance * self.world.block_size / 3) ** 2
        self.DIST_ERR_TOLERANCE = 0.03

        self.DEBUG = debug

    def raycast(self, angle: np.float64, horizontal: bool) -> tuple[np.float64, int]:
        """from angle and position, we find intersections on grid lines and test
        for whether there's a wall there. If there is, we return the square of the
        distance to the wall and the wall's color. If not, we continue searching
        until the ray goes out of bounds.

        discrete variable is on the gridlines, but cont variable can go in between"""

        if horizontal:
            # raycast with y as discrete variable and x as continuous, so we are finding
            # intersections on lines parallel to x axis
            player_discrete, player_cont = self.player.y, self.player.x
            side_sign = int(np.sign(np.sin(angle)))
            slope = 1 / np.tan(angle)

        else:
            # raycast with x as discrete variable and y as continuous, so we are finding
            # intersections on lines parallel to y axis
            player_discrete, player_cont = self.player.x, self.player.y
            side_sign = int(np.sign(np.cos(angle)))
            slope = np.tan(angle)

        # offset to account for discrete point not initially on gridline
        block_offset = player_discrete % self.world.block_size

        # fixes to correct for differences in each semicircle
        if side_sign == -1:
            slope *= -1
        else:
            block_offset = self.world.block_size - block_offset

        # amount continuous variable should change each block
        delta_cont = slope * self.world.block_size

        # initial value of continuous variable
        cont = player_cont + slope * block_offset

        # discrete block - current block plus minus 1 for behind vs in front
        # then since we may be on the left / bottom of that block, discrete variable
        discrete_block = int(player_discrete // self.world.block_size) + side_sign
        discrete = discrete_block * self.world.block_size
        discrete += (self.world.block_size if side_sign == -1 else 0)

        while self.world.in_boundaries(discrete, cont):
            cont_block = int(cont // self.world.block_size)

            # intersection visualization helpful for debugging
            if self.DEBUG:
                if horizontal:
                    self.screen.circle((cont * self.SCALE_FACTOR, discrete * self.SCALE_FACTOR), 2, Palette.LIGHTBLUE)
                else:
                    self.screen.circle((discrete * self.SCALE_FACTOR, cont * self.SCALE_FACTOR), 2, Palette.LIGHTBLUE)

            # if a wall is detected, return distance squared and color
            if     horizontal and (c := self.world.GAME_MAP[cont_block][discrete_block]) or \
               not horizontal and (c := self.world.GAME_MAP[discrete_block][cont_block]):
                return ((discrete - player_discrete) ** 2 + (cont - player_cont) ** 2, c)

            # wall not detected, so we make another step to find the next intersection
            cont += delta_cont
            discrete_block += side_sign
            discrete += self.world.block_size * side_sign

        # return a large value to indicate intersection out of bounds
        # we do this instead of returning -1 etc because we want to take the
        # minimum of distance on both axes
        return (1e+8, 0)

    def draw(self) -> None:
        # initial raycast angle and corresponding angle increment
        angle_inc = np.radians(self.player.fov / self.screen.WIDTH)
        angle: np.float64 = self.player.dir + np.radians(self.player.fov / 2)

        for x in range(self.screen.WIDTH):
            # find the minimum of the x and y axis rays distance and the corresponding color
            rays = (self.raycast(angle, True), self.raycast(angle, False))
            horizontal, (dist_squared, color_index) = min(enumerate(rays), key=lambda x: x[1][0])
            color = self.world.COLORS[color_index]

            if horizontal:
                color += self.SHADE

            # correct for fisheye effect
            corrected_dist_squared = dist_squared * np.cos(angle - self.player.dir)

            if self.projection_type:
                # gaussian projection based on sampling normal distribution
                h = 0.9 * self.screen.HEIGHT * np.exp(-0.5 * corrected_dist_squared / self.VARIANCE) \
                        + self.screen.HEIGHT * 0.1
            else:
                # standard linear projection
                h = min(self.screen.HEIGHT,
                        self.world.block_size * self.PROJ_PLANE_DIST / np.sqrt(corrected_dist_squared))

            start_y = (self.screen.HEIGHT - h) // 2

            # draw the wall
            self.screen.line((x, start_y), (x, start_y + h), color)
            angle -= angle_inc

        if not self.DEBUG:
            minimap_background = Rectangle((0, 0), (
                self.MINIMAP_BLOCK_SIZE * (self.world.WIDTH - 1),
                self.MINIMAP_BLOCK_SIZE * (self.world.HEIGHT  - 1)
            ))
            self.screen.rect(minimap_background, Palette.GRAY)

        # draw the walls on the minimap
        for i in range(self.world.HEIGHT):
            for j in range(self.world.WIDTH):
                if self.world.GAME_MAP[i][j]:
                    minimap_block = Rectangle((i * self.MINIMAP_BLOCK_SIZE, j * self.MINIMAP_BLOCK_SIZE),
                                                  (self.MINIMAP_BLOCK_SIZE,     self.MINIMAP_BLOCK_SIZE))
                    block_color = self.world.COLORS[self.world.GAME_MAP[i][j]] - self.SHADE

                    self.screen.rect(minimap_block, block_color)

        # draw the player on the minimap
        minimap_pos = self.player.pos * self.SCALE_FACTOR
        radius = max(2, np.floor(self.MINIMAP_BLOCK_SIZE / 15))
        self.screen.circle(minimap_pos, radius, Palette.PURPLE)

        # fov and direction indicators
        if self.DEBUG:
            self.screen.line(minimap_pos, minimap_pos +
                            self.player.dirvec() * self.DEBUG_RAY_LENGTH)
            self.screen.line(minimap_pos, minimap_pos +
                            self.player.dirvec(-self.player.fov / 2) * self.DEBUG_RAY_LENGTH)
            self.screen.line(minimap_pos, minimap_pos +
                            self.player.dirvec( self.player.fov / 2) * self.DEBUG_RAY_LENGTH)


def main():
    debug = (len(sys.argv) > 1 and 'd' in sys.argv[1])
    screen = pglib.Screen("Rustcaster python prototype", "v. 0.0.1")
    world = World('../default_map.png', debug=debug)
    player = Player((1, 1), world)
    game = Game(screen, player, world, debug=debug)

    while screen.loop():
        screen.clear()
        player.loop()
        game.draw()


if __name__ == '__main__':
    main()
