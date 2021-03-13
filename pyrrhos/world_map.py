from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from opensimplex import OpenSimplex


class Texture:
    def __init__(self, path, block_size, copy_overlap=1):
        self.name = path.split('/')[-1].replace('.png', '')
        self.path = path
        self.original = plt.imread(self.path)[:, :, :3]  # RGBA -> RGB
        self.block_size = block_size
        self.blocks = self._get_blocks(copy_overlap)

    def make_composite(self, size, paste_overlap=2):
        self.raw = self._create(size + 2, paste_overlap)[1:-1, 1:-1]
        return self.read(self.raw)

    def _get_blocks(self, overlap_factor):
        blocks = []
        for i in range(
            0, self.original.shape[0] - self.block_size, int(self.block_size / overlap_factor)
        ):
            for j in range(
                0, self.original.shape[1] - self.block_size, int(self.block_size / overlap_factor)
            ):
                blocks.append(
                    self.original[i : i + self.block_size, j : j + self.block_size].astype(np.float64)
                )
        return blocks

    def get_samples(self, sample_count):
        assert len(self.blocks) > sample_count

        samples = []
        temp_blocks = self.blocks
        for i in range(sample_count):
            block = temp_blocks.pop(int(np.random.rand() * len(temp_blocks)))
            samples.append(self.read(block))
        return samples

    def _create(self, img_size, overlap_factor):
        block_overlap = int(self.block_size / overlap_factor)
        img = np.zeros((img_size, img_size, 3))
        window = np.outer(np.hanning(self.block_size), np.hanning(self.block_size))
        divisor = np.zeros_like(img) + 1e-10

        def set_pixels(coords, incs, end):
            adj_window = window[: end[0], : end[1], None]
            adj_block = block[: end[0], : end[1]]
            img[coords[0] : coords[0] + incs[0], coords[1] : coords[1] + incs[1]] += (
                adj_window * adj_block
            )
            divisor[coords[0] : coords[0] + incs[0], coords[1] : coords[1] + incs[1]] += adj_window

        for i in range(0, img_size, block_overlap):
            for j in range(0, img_size, block_overlap):
                block = self.blocks[int(np.random.rand() * len(self.blocks))]

                # if on the bottom or right edges of the image, block must be cropped
                if i > img_size - self.block_size or j > img_size - self.block_size:
                    gap = [min(img_size - i, self.block_size), min(img_size - j, self.block_size)]
                    set_pixels([i, j], gap, gap)

                else:
                    set_pixels([i, j], [self.block_size] * 2, [self.block_size] * 2)

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


class GeneratedIsland:
    def __init__(self, size, flatness=0.5):
        self.terrain = NoiseMap(size, flatness=flatness)
        self.moisture = NoiseMap(size)
        self.shape = NoiseMap(size)

        self.shape.apply_circular_mask(0.75)
        self.shape.map = (self.shape.map > 0.3).astype(int)  # convert into boolean array

        self.terrain.apply_circular_mask(0.4)
        self.terrain.apply_mask(self.moisture.map, 0.3)
        self.terrain.map *= self.shape.map

    def get_pixel(self):
        return self.terrain.simple_colorize(
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

    def get_textured():
        pass


class Continent:
    def __init__(self, name, path, coordinates):
        self.name = name
        self.image = Image.open(path)
        self.coordinates = coordinates


class World:
    def __init__(self, width):
        self.width = width
        self.height = int(self.width * 9 / 16)
        self.image = Image.new('RGB', (self.width, self.height))

    def small(self):
        return self.image.resize((800, int(800 * 9 / 16)))


def create_mask(image, edge_size):
    mask = np.ones([image.height, image.width])
    gradient = create_gradient(edge_size)

    for i in range(image.height):
        mask[i, :edge_size] *= gradient
        mask[i, image.width - edge_size :] *= gradient[::-1]
    for i in range(image.width):
        mask[:edge_size, i] *= gradient
        mask[image.height - edge_size :, i] *= gradient[::-1]

    return Image.fromarray((mask * 255).astype('uint8'), 'L')


def smooth_paste(background, image, coordinates):
    mask = create_mask(image, edge_size=image.width // 40)
    background.paste(image, coordinates, mask=mask)


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

    ocean_texture = Texture('./images/samples/ocean.png', 50).make_composite(300)
    # storm = Texture('./images/samples/storm.png')

    for i in range(-20, world.width, ocean_texture.width - 20):
        for j in range(-20, world.height, ocean_texture.height - 20):
            smooth_paste(world.image, ocean_texture, (i, j))

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
        smooth_paste(world.image, cont.image, location)

    world.image.show()
    # world.small().save('images/map/world_map.png')


def main():
    # nardone = GeneratedIsland((200, 200))
    # nardone.get_pixel().show()
    biomes = []
    for biome in ['desert', 'grassland', 'snow', 'stone']:
        biomes.append(Texture('images/samples/' + biome + '.png', 10, copy_overlap=1.5))
    for biome in ['hilly', 'forest']:
        biomes.append(Texture('images/samples/' + biome + '.png', 15))

    # biomes[4].make_composite(500).show()

    # grassland.texture.show()
    stitch_world_map()


if __name__ == '__main__':
    main()
