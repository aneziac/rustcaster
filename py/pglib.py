from pygame import font, gfxdraw, mixer, display, mouse, transform, draw
import pygame.time, pygame.event, pygame.image
import sys
from typing import NamedTuple, Union


# Type not enforced for brevity - treated as equivalent to a 2 int tuple
# This class exists more to keep track of which tuples are coordinates
class Coordinate(NamedTuple):
    x: int
    y: int


class Rectangle(NamedTuple):
    origin: Coordinate
    dims: Coordinate


class Palette:
    INVISIBLE = pygame.Color(0, 0, 0, 0)
    BLACK = pygame.Color(0, 0, 0)
    DARKGRAY = pygame.Color(20, 20, 20)
    GRAY = pygame.Color(120, 120, 120)
    LIGHTBLUE = pygame.Color(0, 255, 255)
    ORANGE = pygame.Color(255, 102, 0)
    GREEN = pygame.Color(20, 200, 20)
    RED = pygame.Color(200, 0, 0)
    WHITE = pygame.Color(255, 255, 255)
    YELLOW = pygame.Color(255, 255, 0)


class Screen:
    def __init__(self, title: str, version: str = "",
                 width: int = 1080, aspect_ratio: float = 16 / 9,
                 alpha: bool = False, fonts: dict[str, font.Font] = {}):
        pygame.init()
        font.init()
        mixer.init()

        self.fonts = fonts
        self.fonts['default'] = font.Font(None, 30)

        flags = pygame.DOUBLEBUF
        if len(sys.argv) > 1:
            if "f" in sys.argv[1]:
                flags |= pygame.FULLSCREEN | pygame.HWSURFACE
            else:
                if "n" in sys.argv[1]:
                    flags |= pygame.NOFRAME
                if "r" in sys.argv[1]:
                    flags |= pygame.RESIZABLE

        self.WIDTH, self.HEIGHT = width, int(width / aspect_ratio)
        self._canvas = display.set_mode((self.WIDTH, self.HEIGHT), flags)
        if not alpha:
            self._canvas.set_alpha(None)

        display.set_caption(f'{title} {version}')
        mouse.set_visible(False)
        self.frame = 0
        self.clock = pygame.time.Clock()

    def clear(self) -> None:
        self._canvas.fill(Palette.WHITE)

    def _q1_transform(self, coords: Union[Coordinate, list[Coordinate]]
                               ) -> Union[Coordinate, list[Coordinate]]:

        def q1_transform_coordinate(coord: Coordinate):
            return Coordinate(int(coord[0]), int(self.HEIGHT - coord[1]))

        if isinstance(coords, list):
            transformed_coordinates: list[Coordinate] = []
            for coord in coords:
                transformed_coordinates.append(q1_transform_coordinate(coord))
            return transformed_coordinates

        else:
            return q1_transform_coordinate(coords)

    def _q1_transform_rect(self, rect: Rectangle) -> Rectangle:
        return Rectangle(
            Coordinate(rect.origin[0], self.HEIGHT - rect.origin[1] - rect.dims[1]), rect.dims
        )

    def text(self, text: str, coord: Coordinate,
                    color: pygame.Color = Palette.BLACK, font: str = 'default') -> None:
        font_obj = self.fonts[font]
        rendered_text = font_obj.render(text, True, color)
        self._canvas.blit(rendered_text, self._q1_transform(coord))

    def center_text(self, text: str, coord: Coordinate,
                    color: pygame.Color = Palette.BLACK, font: str = 'default') -> None:
        text_size = self.fonts[font].size(text)
        location = Coordinate(*[c + (text_size[i] // 2) * (i * 2 - 1) for i, c in enumerate(coord)])
        self.text(text, location, color, font)

    def hcenter_text(self, text: str, height: int = 0,
                    color: pygame.Color = Palette.BLACK, font: str = 'default') -> None:
        if not height:
            height = self.HEIGHT
        self.center_text(text, color, font, Coordinate(self.WIDTH, height))

    def polygon(self, vertices: list[Coordinate], color: pygame.Color) -> None:
        tvertices = self._q1_transform(vertices)

        gfxdraw.aapolygon(self._canvas, tvertices, color)
        gfxdraw.filled_polygon(self._canvas, tvertices, color)

    def circle(self, center: Coordinate, radius: int, color: pygame.Color) -> None:
        tcenter = self._q1_transform(center)

        gfxdraw.aacircle(self._canvas, *tcenter, radius, color)
        gfxdraw.filled_circle(self._canvas, *tcenter, radius, color)

    def line(self, start: Coordinate, end: Coordinate, color: pygame.Color = Palette.RED) -> None:
        gfxdraw.line(self._canvas, *self._q1_transform(start), *self._q1_transform(end), color)

    def rect(self, rect: Rectangle, color: pygame.Color = Palette.BLACK) -> None:
        draw.rect(self._canvas, color, self._q1_transform_rect(rect))

    def pixel(self, location: Coordinate, color: pygame.Color) -> None:
        self._canvas.set_at(self._q1_transform(location), color)

    def loop(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
               event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        self.frame += 1
        self.clock.tick()
        display.flip()

        return True


# Load functions
def load_image(file, scale=None) -> pygame.Surface:
    image = pygame.image.load(file)
    if scale is None:
        return image
    else:
        scale = [round(x) for x in scale]
        return transform.scale(image, scale)
