from PIL import Image, ImageFilter
import numpy as np
from matplotlib.pyplot import imread


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
                blocks.append(self.original[
                    i:i + self.block_size,
                    j:j + self.block_size
                ].astype(np.float64))
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
            adj_window = window[start[0]:end[0], start[1]:end[1], None]
            adj_block = block[start[0]:end[0], start[1]:end[1]]
            img[coords[0]:coords[0] + incs[0], coords[1]:coords[1] + incs[1]] += adj_window * adj_block
            divisor[coords[0]:coords[0] + incs[0], coords[1]:coords[1] + incs[1]] += adj_window

        for i in range(inc // 2, img_size, inc):
            for j in range(overlap // 2, img_size, self.block_size - overlap):
                block = self.blocks[int(np.random.rand() * len(self.blocks))]

                if i > img_size - self.block_size or j > img_size - self.block_size:
                    gap = min(img_size - i, self.block_size), min(img_size - j, self.block_size)
                    start = [
                        i if i < img_size - self.block_size else 0,
                        j if j < img_size - self.block_size else 0
                    ]
                    increment = [(x if x == self.block_size else self.block_size - x) for x in gap]

                    set_pixels([i, j], gap, [0, 0], gap)
                    if start == [0, 0] and gap[0] != gap[1]:
                        set_pixels(
                            [0, j],
                            [self.block_size - gap[0], gap[1]],
                            [gap[0], 0], [self.block_size, gap[1]]
                        )
                        set_pixels(
                            [i, 0],
                            [gap[0], self.block_size - gap[1]],
                            [0, gap[1]], [gap[0], self.block_size]
                        )

                    else:
                        set_pixels(
                            start,
                            increment,
                            [x % self.block_size for x in gap],
                            [self.block_size] * 2
                        )

                else:
                    set_pixels([i, j], [self.block_size] * 2, [0, 0], [self.block_size] * 2)

        return img / divisor

    def read(self, texture):
        return Image.fromarray((texture * 255).astype('uint8'), 'RGB')


class Continent:
    def __init__(self, name, path, coordinates):
        self.name = name
        self.image = Image.open(path)
        self.coordinates = coordinates
        self.create_mask()

    def create_mask(self, edge_size=20):
        mask = np.ones([self.image.height, self.image.width])
        gradient = np.zeros([edge_size])
        for i in range(edge_size):
            gradient[i] += i / edge_size

        for i in range(self.image.height):
            mask[i, :edge_size] *= gradient
            mask[i, self.image.width - edge_size:] *= gradient[::-1]
        for i in range(self.image.width):
            mask[:edge_size, i] *= gradient
            mask[self.image.height - edge_size:, i] *= gradient[::-1]

        self.mask = Image.fromarray((mask * 255).astype('uint8'), 'L')


class World:
    def __init__(self, width):
        self.width = width
        self.height = int(self.width * 9 / 16)
        self.image = Image.new('RGB', (self.width, self.height))

    def small(self):
        return self.image.resize((800, int(800 * 9 / 16)))


def main():
    world = World(2000)

    ocean = Texture('./images/samples/ocean.png')
    storm = Texture('./images/samples/storm.png')

    for i in range(0, world.width, ocean.texture.width):
        for j in range(0, world.height, ocean.texture.height):
            world.image.paste(ocean.texture, (i, j))

    piskus = Continent(
        'Piskus',
        'images/map/piskus.png',
        [0, 500]
    )
    erebos = Continent(
        'Erebos',
        'images/map/erebos.png',
        [piskus.coordinates[0] + 350, piskus.coordinates[1] - 500]
    )
    orestes = Continent(
        'Orestes',
        'images/map/orestes.png',
        [erebos.coordinates[0] + 625, erebos.coordinates[1] + 250]
    )

    offset_x, offset_y = 50, 50
    for cont in [piskus, erebos, orestes]:
        location = (cont.coordinates[0] + offset_x, cont.coordinates[1] + offset_y)
        world.image.paste(cont.image, location, mask=cont.mask)

    world.image.show()
    # world.small().save('images/map/world_map.png')


main()
