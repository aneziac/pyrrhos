from PIL import Image
import numpy as np
from matplotlib.pyplot import imread
from opensimplex import OpenSimplex


class Texture:
    def __init__(self, name, block_size=50, block_num=30):
        self.name = name
        self.original = imread(self.name)[:, :, :3]  # RGBA -> RGB
        self.block_size = block_size
        self.blocks = self.get_blocks(1)
        self.raw = self.create(block_num, 2)
        self.texture = self.read(self.raw)

    def get_blocks(self, inc_factor):
        blocks = []
        for i in range(0, self.original.shape[0] - self.block_size, self.block_size // inc_factor):
            for j in range(0, self.original.shape[1] - self.block_size, self.block_size // inc_factor):
                blocks.append(
                    self.original[i : i + self.block_size, j : j + self.block_size].astype(np.float64)
                )
        return blocks

    def create(self, block_num, overlap_factor):
        overlap = self.block_size // overlap_factor
        inc = self.block_size - overlap
        img_size = block_num * inc
        img = np.zeros((img_size, img_size, 3))
        window = np.outer(np.hanning(self.block_size), np.hanning(self.block_size))
        divisor = np.zeros_like(img) + 1e-10

        def set_pixels(coords, incs, start, end):
            for x in range(len(incs)):
                if end[x] - start[x] != incs[x]:
                    raise ValueError("Dissimilar shapes: ", incs, end, start)
            adj_window = window[start[0] : end[0], start[1] : end[1], None]
            adj_block = block[start[0] : end[0], start[1] : end[1]]
            img[coords[0] : coords[0] + incs[0], coords[1] : coords[1] + incs[1]] += (
                adj_window * adj_block
            )
            divisor[coords[0] : coords[0] + incs[0], coords[1] : coords[1] + incs[1]] += adj_window

        for i in range(inc // 2, img_size, inc):
            for j in range(overlap // 2, img_size, self.block_size - overlap):
                block = self.blocks[int(np.random.rand() * len(self.blocks))]

                if i > img_size - self.block_size or j > img_size - self.block_size:
                    gap = min(img_size - i, self.block_size), min(img_size - j, self.block_size)
                    start = [
                        i if i < img_size - self.block_size else 0,
                        j if j < img_size - self.block_size else 0,
                    ]
                    increment = [(x if x == self.block_size else self.block_size - x) for x in gap]

                    set_pixels([i, j], gap, [0, 0], gap)
                    if start == [0, 0] and gap[0] != gap[1]:
                        set_pixels(
                            [0, j],
                            [self.block_size - gap[0], gap[1]],
                            [gap[0], 0],
                            [self.block_size, gap[1]],
                        )
                        set_pixels(
                            [i, 0],
                            [gap[0], self.block_size - gap[1]],
                            [0, gap[1]],
                            [gap[0], self.block_size],
                        )

                    else:
                        set_pixels(
                            start, increment, [x % self.block_size for x in gap], [self.block_size] * 2
                        )

                else:
                    set_pixels([i, j], [self.block_size] * 2, [0, 0], [self.block_size] * 2)

        return img / divisor

    def read(self, texture):
        return Image.fromarray((texture * 255).astype('uint8'), 'RGB')


class NoiseMap:
    """
    Useful resources
    https://www.youtube.com/watch?v=eaXk97ujbPQ
    https://medium.com/@travall/procedural-2d-island-generation-noise-functions-13976bddeaf9
    https://www.redblobgames.com/maps/terrain-from-noise/
    """

    def __init__(self, dimensions, flatness=1, octaves=None, show_components=False):
        self.width = dimensions[0]
        self.height = dimensions[1]

        if octaves is None:
            self.octaves = int(np.log2(self.width))
        else:
            self.octaves = octaves

        self.show_components = show_components
        if self.show_components:
            self.images = [Image.new('L', (self.width, self.height)) for _ in range(self.octaves)]

        self.generate_noise_map(flatness)

    def generate_noise_map(self, flatness):
        self.map = np.zeros([self.height, self.width])
        divisor = 0

        for n in range(self.octaves):
            simplex = OpenSimplex(int(np.random.rand() * 1e5))
            frequency = 2 ** n / 1e2
            amplitude = 1 / frequency
            divisor += amplitude

            for i in range(self.height):
                for j in range(self.width):
                    rand = simplex.noise2d(x=frequency * i, y=frequency * j)
                    self.map[i, j] += ((rand + 1) / 2) * amplitude
                    if self.show_components:
                        self.images[n].putpixel((j, i), int(255 * ((rand + 1) / 2)))

        if self.show_components:
            for x in self.images:
                x.show()
            quit()

        self.map /= divisor
        self.map = self.map ** flatness
        self.normalize()

    def apply_mask(self, mask, weight):
        self.map = self.map * (1 - weight) + mask * weight
        self.normalize()

    def apply_circular_mask(self, weight, n=1.25):
        interpolation = lambda x: x ** n
        mask = np.outer(
            create_gradient(self.height, f=interpolation, two_dir=True),
            create_gradient(self.width, f=interpolation, two_dir=True),
        )

        self.apply_mask(mask, weight)

    def generate_image(self):
        return Image.fromarray((self.map * 255).astype('uint8'), 'L')

    def simple_colorize(self, mapping):
        colorized = Image.new('RGB', (self.width, self.height))
        for i in range(self.height):
            for j in range(self.width):
                for m in mapping:
                    if self.map[i, j] <= m:
                        colorized.putpixel((j, i), mapping[m])
                        break
        return colorized

    def normalize(self):
        self.map -= np.min(self.map)
        self.map /= np.max(self.map)


class Continent:
    def __init__(self, name, path, coordinates):
        self.name = name
        self.image = Image.open(path)
        self.coordinates = coordinates
        self.create_mask()

    def create_mask(self, edge_size=20):
        mask = np.ones([self.image.height, self.image.width])
        gradient = create_gradient(edge_size)

        for i in range(self.image.height):
            mask[i, :edge_size] *= gradient
            mask[i, self.image.width - edge_size :] *= gradient[::-1]
        for i in range(self.image.width):
            mask[:edge_size, i] *= gradient
            mask[self.image.height - edge_size :, i] *= gradient[::-1]

        self.mask = Image.fromarray((mask * 255).astype('uint8'), 'L')


class World:
    def __init__(self, width):
        self.width = width
        self.height = int(self.width * 9 / 16)
        self.image = Image.new('RGB', (self.width, self.height))

    def small(self):
        return self.image.resize((800, int(800 * 9 / 16)))


def create_gradient(size, f=lambda x: x, two_dir=False):
    """
    f : [0, 1] -> [0, 1]
    """
    gradient = np.zeros([size])
    if two_dir:
        size = size // 2
    for i in range(size):
        gradient[i] = f(i / size)
        if two_dir:
            gradient[-i - 1] = f(i / size)
    return gradient


def stitch_world_map():
    world = World(2000)

    ocean = Texture('./images/samples/ocean.png')
    # storm = Texture('./images/samples/storm.png')

    for i in range(0, world.width, ocean.texture.width):
        for j in range(0, world.height, ocean.texture.height):
            world.image.paste(ocean.texture, (i, j))

    piskus = Continent('Piskus', 'images/map/piskus.png', [0, 500])
    erebos = Continent(
        'Erebos', 'images/map/erebos.png', [piskus.coordinates[0] + 350, piskus.coordinates[1] - 500]
    )
    orestes = Continent(
        'Orestes', 'images/map/orestes.png', [erebos.coordinates[0] + 625, erebos.coordinates[1] + 250]
    )

    offset_x, offset_y = 50, 50
    for cont in [piskus, erebos, orestes]:
        location = (cont.coordinates[0] + offset_x, cont.coordinates[1] + offset_y)
        world.image.paste(cont.image, location, mask=cont.mask)

    world.image.show()
    # world.small().save('images/map/world_map.png')


def generate_island():
    terrain = NoiseMap((200, 200), flatness=0.5)
    moisture = NoiseMap((200, 200))
    shape = NoiseMap((200, 200))

    shape.apply_circular_mask(0.75)
    shape.map = (shape.map > 0.3).astype(int)  # convert into boolean array

    terrain.apply_circular_mask(0.4)
    terrain.apply_mask(moisture.map, 0.3)
    terrain.map *= shape.map

    island = terrain.simple_colorize(
        {
            0.3: (19, 90, 212),  # ocean
            0.4: 0x02CCFE,  # desert
            0.5: (207, 140, 54),  # hills
            0.6: 0x0ADD08,  # grass
            0.8: 0x228B22,  # forest
            0.9: 0x516572,  # stone
            1.0: (255, 255, 255),  # snow
        }
    )
    island.show()


def main():
    generate_island()
    # stitch_world_map()


if __name__ == '__main__':
    main()
