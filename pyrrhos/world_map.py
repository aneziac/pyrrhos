from PIL import Image, ImageColor
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

    def make_composite(self, size, overlap_factor=2):
        block_count_x = (size[0] // (self.block_size // overlap_factor)) + 1
        block_count_y = (size[1] // (self.block_size // overlap_factor)) + 1
        blocks = [[0 for _ in range(block_count_x)] for _ in range(block_count_y)]
        for i in range(block_count_y):
            for j in range(block_count_x):
                blocks[i][j] = self.random_sample()
        self.raw = stitch_textures(self.block_size, size, blocks, overlap_factor=overlap_factor)
        return read_rgb(self.raw)

    def _get_blocks(self, overlap_factor):
        blocks = []
        block_inc = int(self.block_size / overlap_factor)
        for i in range(0, self.original.shape[0] - self.block_size, block_inc):
            for j in range(0, self.original.shape[1] - self.block_size, block_inc):
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

    def random_sample(self):
        return self.blocks[int(np.random.rand() * len(self.blocks))]


class Biomes:
    def __init__(self):
        self.biomes = []
        for biome in ['desert', 'grass', 'snow', 'stone']:
            self.biomes.append(Texture('images/samples/' + biome + '.png', 10, copy_overlap=1.5))
        for biome in ['hilly', 'forest', 'ocean']:
            self.biomes.append(Texture('images/samples/' + biome + '.png', 15))


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
        self._normalize()

    def apply_mask(self, mask, weight):
        self.map = self.map * (1 - weight) + mask * weight
        self._normalize()

    def apply_circular_mask(self, weight, n=1.25):
        interpolation = lambda x: x ** n
        mask = np.outer(
            create_gradient(self.height, f=interpolation, two_dir=True),
            create_gradient(self.width, f=interpolation, two_dir=True),
        )

        self.apply_mask(mask, weight)

    def simple_colorize(self, mapping):
        colorized = Image.new('RGB', (self.width, self.height))
        for m in mapping:
            if type(mapping[m]) != tuple:
                mapping[m] = ImageColor.getrgb(mapping[m])
        for i in range(self.height):
            for j in range(self.width):
                for m in mapping:
                    if self.map[i, j] <= m:
                        colorized.putpixel((j, i), mapping[m])
                        break
        return colorized

    def _normalize(self):
        self.map -= np.min(self.map)
        self.map /= np.max(self.map)

    def resize(self, scale_factor):
        self.height = self.height * scale_factor - scale_factor
        self.width = self.width * scale_factor - scale_factor
        self.map = interpolate_array(self.map, scale_factor)


class GeneratedIsland:
    biomes = Biomes().biomes

    def __init__(self, size, flatness):
        self.size = size
        self.terrain = NoiseMap(size, flatness=flatness)
        self.moisture = NoiseMap(size)

    def get_pixelized(self):
        return self.terrain.simple_colorize(self.coloring)

    def get_textured(self, size, overlap_factor=3):
        # scaled_dims = [self.terrain.height // inpatch_size, self.terrain.width // inpatch_size]
        # scaled_map = self.terrain.map.reshape([
        #    scaled_dims[0],
        #    self.terrain.height // scaled_dims[0],
        #    scaled_dims[1],
        #    self.terrain.width // scaled_dims[1]
        # ]).mean(3).mean(1)
        # scaled_map = interpolate_array(self.terrain.map, 5)#size[0] // self.terrain.height)
        self.terrain.resize(5)
        self.get_pixelized().show()
        quit()

        for biome in GeneratedIsland.biomes:
            biome.make_composite(size).show()

        # ALGORITHM
        # 1. generate masks for each biome
        # 2. multiply masks by the composite textures
        # 3. beginning with water texture, smooth paste other textures in

        # outpatch_dims = [((int(i * overlap_factor) + 1) // outpatch_size) - 1 for i in size[::-1]]

        # outpatches = [[0 for _ in range(outpatch_dims[0])] for _ in range(outpatch_dims[1])]
        # for i in range(outpatch_dims[0]):
        #    for j in range(outpatch_dims[1]):
        #        average_pixel = scaled_map[int(i * scaled_dims[0] / outpatch_dims[0]),
        #        # \ int(j * scaled_dims[1] / outpatch_dims[1])]
        #        for t in self.texturing:
        #            if average_pixel <= t:
        #                biome_name = self.texturing[t]
        #                for biome in GeneratedIsland.textures:
        #                    if biome.name == biome_name:
        #                        outpatches[i][j] = biome.random_sample()[:outpatch_size, :outpatch_size]
        #                        break
        #                break
        # size = size[::-1]
        # outpatches = [[0 for _ in range(scaled_dims[1])] for _ in range(scaled_dims[0])]
        # outpatch_size =
        # \ min([(size[i] * overlap_factor // scaled_dims[i]) + 1 for i in range(2)] + [15])
        # for i in range(scaled_dims[0]):
        #    for j in range(scaled_dims[1]):
        #        for t in self.texturing:
        #            if scaled_map[i, j] <= t:
        #                biome_name = self.texturing[t]
        #                for biome in GeneratedIsland.textures:
        #                    if biome.name == biome_name:
        #                        outpatches[i][j] = biome.random_sample()[:outpatch_size, :outpatch_size]
        #                        break
        #                break

        # return read_rgb(
        # stitch_textures(outpatch_size, size, outpatches, overlap_factor=overlap_factor))


class BigIsland(GeneratedIsland):
    def __init__(self, size, flatness=0.5):
        super().__init__(size, flatness)
        self.shape = NoiseMap(size)

        self.shape.apply_circular_mask(0.75)
        self.shape.map = (self.shape.map > 0.3).astype(int)  # convert into boolean array

        self.terrain.apply_circular_mask(0.4)
        self.terrain.apply_mask(self.moisture.map, 0.3)
        self.terrain.map *= self.shape.map

        # TO DO: FIX THIS MESS
        self.coloring = {
            0.3: '#135AD4',  # ocean
            0.4: '#F1DA7A',  # desert
            0.5: '#CF8C36',  # hills
            0.6: '#0ADD08',  # grass
            0.8: '#228B22',  # forest
            0.9: '#516572',  # stone
            1.0: '#FFFFFF',  # snow
        }
        self.texturing = {
            0.3: 'ocean',
            0.4: 'desert',
            0.5: 'hilly',
            0.6: 'grass',
            0.8: 'forest',
            0.9: 'stone',
            1.0: 'snow',
        }


class SmallIsland(GeneratedIsland):
    def __init__(self, size, flatness=0.7):
        super().__init__(size, flatness)
        self.terrain.apply_circular_mask(0.75)
        self.moisture.apply_circular_mask(0.4)
        self.terrain.apply_mask(self.moisture.map, 0.4)

        self.coloring = {
            0.4: '#135AD4',  # ocean
            0.5: '#7BC8F6',  # coastal water
            0.6: '#F1DA7A',  # beach
            0.8: '#0ADD08',  # grass
            0.9: '#228B22',  # forest
            1.0: '#516572',  # stone
        }


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


def stitch_textures(block_size, img_size, blocks, overlap_factor=2):
    img_size = [x + 2 for x in img_size]
    block_overlap = int(block_size / overlap_factor)
    img = np.zeros((img_size[0], img_size[1], 3))
    window = np.outer(np.hanning(block_size), np.hanning(block_size))
    divisor = np.zeros_like(img) + 1e-10

    def set_pixels(coords, incs, end):
        adj_window = window[: end[0], : end[1], None]
        adj_block = block[: end[0], : end[1]]
        img[coords[0] : coords[0] + incs[0], coords[1] : coords[1] + incs[1]] += adj_window * adj_block
        divisor[coords[0] : coords[0] + incs[0], coords[1] : coords[1] + incs[1]] += adj_window

    for i in range(0, img_size[1], block_overlap):
        for j in range(0, img_size[0], block_overlap):
            try:
                block = blocks[i // block_overlap][j // block_overlap]
            except IndexError:
                pass

            # if on the bottom or right edges of the image, block must be cropped
            if i > img_size[1] - block_size or j > img_size[0] - block_size:
                gap = [min(img_size[1] - i, block_size), min(img_size[0] - j, block_size)]
                set_pixels([i, j], gap, gap)

            else:
                set_pixels([i, j], [block_size] * 2, [block_size] * 2)

    return (img / divisor)[1:-1, 1:-1]


def read_rgb(texture):
    return Image.fromarray((texture * 255).astype('uint8'), 'RGB')


def read_l(texture):
    return Image.fromarray((texture * 255).astype('uint8'), 'L')


def square_mask(image, edge_size):
    mask = np.ones([image.height, image.width])
    gradient = create_gradient(edge_size)

    for i in range(image.height):
        mask[i, :edge_size] *= gradient
        mask[i, image.width - edge_size :] *= gradient[::-1]
    for i in range(image.width):
        mask[:edge_size, i] *= gradient
        mask[image.height - edge_size :, i] *= gradient[::-1]

    return read_l(mask)


def smooth_paste(background, image, coordinates, edge_size=None):
    if edge_size is None:
        edge_size = image.width // 40
    mask = square_mask(image, edge_size=edge_size)
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


def interpolate_array(inarray, resize_factor):
    result = np.zeros([(inarray.shape[i] - 1) * resize_factor + 1 for i in range(2)])
    for i in range(inarray.shape[0]):
        row = inarray[i]
        result[i * resize_factor, ::resize_factor] = row

        interpolation = np.zeros(result.shape[1])
        for j in range(inarray.shape[1] - 1):
            delta = row[j + 1] - row[j]
            gradient = np.linspace(0, 1, num=resize_factor, endpoint=False) * delta
            interpolation[j * resize_factor : (j + 1) * resize_factor] = row[j] + gradient

        mask = np.ones(result.shape[1])
        mask[::resize_factor] = np.zeros(inarray.shape[1])

        result[i * resize_factor] += interpolation * mask

    for i in range(0, result.shape[0] - 1, resize_factor):
        for j in range(1, resize_factor + 1):
            delta = result[i + resize_factor] - result[i]
            result[i + j] = result[i] + (j * delta / resize_factor)

    return result


def stitch_world_map():
    world = World(2000)

    ocean_texture = Texture('images/samples/ocean.png', 50).make_composite(300)
    # storm = Texture('images/samples/storm.png')

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
    island = BigIsland((200, 200))
    island.get_pixelized().show()
    island.get_textured((1000, 1000)).show()

    # biomes[4].make_composite(500).show()

    # grassland.texture.show()
    # stitch_world_map()


if __name__ == '__main__':
    main()
