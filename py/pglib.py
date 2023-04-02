import pygame as pg
import pygame.gfxdraw as gfxdraw
import sys
from typing import Tuple


# Classes
class Screen:
    def __init__(self, dims: Tuple[int, int], title: str, version: str = "", alpha: bool = False):
        pg.init()
        pg.font.init()
        pg.mixer.init()

        flags = pg.DOUBLEBUF
        if len(sys.argv) > 1:
            if "f" in sys.argv[1]:
                flags = flags | pg.FULLSCREEN | pg.HWSURFACE
            else:
                if "n" in sys.argv[1]:
                    flags = flags | pg.NOFRAME
                if "r" in sys.argv[1]:
                    flags = flags | pg.RESIZABLE

        self.WIDTH, self.HEIGHT = dims
        self.canvas = pg.display.set_mode(dims, flags)
        if not alpha:
            self.canvas.set_alpha(None)
        if version != "":
            version = " v. " + version

        pg.display.set_caption(f'{title} {version}')
        pg.mouse.set_visible(False)
        self.frame = 0
        self.clock = pg.time.Clock()

    def q1_transform(self, location):
        def q1_transform_coordinate(location):
            return [int(location[0]), self.HEIGHT - int(location[1])]

        if isinstance(location[0], list):
            transformed_coordinates = []
            for x in location:
                transformed_coordinates.append(q1_transform_coordinate(x))
            return transformed_coordinates
        else:
            return q1_transform_coordinate(location)

    def q1_transform_rect(self, location, dims):  # transform rectangle (4 inputs)
        return [location[0], self.HEIGHT - location[1] - dims[1], dims[0], dims[1]]

    def text(self, text, color, font, location):
        rendered_text = font.render(text, True, color)
        location = [location[x] + (font.size(text)[x] // 2) for x in range(len(self.q1_transform(location)))]
        self.canvas.blit(rendered_text, location)

    def center_text(self, text, color, font):
        self.text(text, color, font, [self.WIDTH, self.HEIGHT])

    def hcenter_text(self, text, color, font, height):
        self.text(text, color, font, [self.WIDTH, height])

    def polygon(self, vertices, color):
        vertices = self.q1_transform(vertices)
        for v in vertices:
            if self.is_onscreen(self.q1_transform(v)):
                gfxdraw.aapolygon(self.canvas, vertices, color)
                gfxdraw.filled_polygon(self.canvas, vertices, color)

    def circle(self, location, radius, color=(0, 0, 0)):
        loc = self.q1_transform(location)
        r = int(radius)

        if self.is_onscreen(loc, radius):
            gfxdraw.aacircle(self.canvas, *loc, r, color)
            gfxdraw.filled_circle(self.canvas, *loc, r, color)

    def line(self, start, end, color=(200, 0, 0)):
        gfxdraw.line(self.canvas, *self.q1_transform(start), *self.q1_transform(end), color)

    def rect(self, location, dims, color=(0, 0, 0)):
        pg.draw.rect(self.canvas, color, self.q1_transform_rect(location, dims))

    def is_onscreen(self, location, radius=0):
        in_width = location[0] + radius > 0 and location[0] - radius < self.WIDTH
        in_height = location[1] + radius > 0 and location[1] - radius < self.HEIGHT
        return in_width and in_height

    def loop(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return False

        self.frame += 1
        self.clock.tick()
        pg.display.flip()

        return True


# Load functions
def load(file, extra_path="", scale=None):
    # path = os.path.join("./assets/image/" + extra_path, file)
    image = pg.image.load(file)
    if scale is None:
        return image
    else:
        scale = [round(x) for x in scale]
        return pg.transform.scale(image, scale)
