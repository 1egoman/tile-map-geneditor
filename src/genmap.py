#!/usr/bin/python
"""Credit goes to Ryan (1egoman) for the majority of the gen_map, 
generate_noise, smooth_noise, and turbulence function code below.
"""
import os
import random

from lib import easygui
import common



class MapGenerator(object):
    """Handles generation and regeneration of the maps."""
    # Dictionary of generator parameters
    params = {}


    def __init__(self, common_inst, map_data):
        # Reference to shared data object
        self.common = common_inst
        # Change generation values
        self.set_params(map_data)
        # Generation-specific stuff
        self.noise = []
        self.noise_width = 0
        self.noise_height = 0


    def set_params(self, params):
        # Set values
        self.params = params
        # Randomize seed if left blank
        if self.params['seed'] is None:
            self.params['seed'] = str(random.randint(1000,1000000000))
        # Set the seed for the random number generator
        random.seed(self.params['seed'])


    # TODO: Test if this will have issues with larger maps (OS thinks program crahsed, etc)
    def gen_map(self):
        """Generates a map and stores it in the common/shared class."""
        # Clear the list of tiles
        self.common.tile_map = []
        print "Generating Map..."
        # Water tile upper limit/value for both biome and tile generation
        watertable = 110
        # Biome type levels/limits
        biome_desert_level = 85
        biome_swamp_level = 100
        biome_forest_level = 125
        biome_flatland_level = 150
        biome_tiaga_level = 175
        biome_mountain_level = 255
        # Tile type threshholds/limits
        sandlevel = watertable+10
        forestlevel = 150
        mtnlevel = 180
        # Used by noise generator
        octaves = 200
        # Generate tile noise and biome noise
        noise = self.generate_noise(self.params['width'], self.params['height'], 10, octaves)
        biomenoise = self.generate_noise(self.params['width'], self.params['height'], 5, octaves/3)
        allowaquatic = True
        nbiome = None

        for x,c in enumerate(noise):
            column = []
            for y,d in enumerate(c):
                # Generate biomes #
                # Water biome
                if d <= watertable:
                    if allowaquatic:
                        biome = "aquatic"
                    else:
                        biome = nbiome
                        allowaquatic = True
                # Desert biome
                elif biomenoise[x][y] <= biome_desert_level:
                    biome = "desert"
                    allowaquatic = True
                # Swamp biome
                elif biomenoise[x][y] <= biome_swamp_level:
                    biome = "swamp"
                    allowaquatic = False
                    nbiome = "swamp"
                # Forest biome
                elif biomenoise[x][y] <= biome_forest_level:
                    biome = "forest"
                    allowaquatic = True
                # Grassland biome
                elif biomenoise[x][y] <= biome_flatland_level:
                    biome = "grassland"
                    allowaquatic = True 
                # Tiaga biome
                elif biomenoise[x][y] <= biome_tiaga_level:
                    biome = "tiaga"
                    allowaquatic = True
                # Mountain biome
                elif biomenoise[x][y] <= biome_mountain_level:
                    biome = "mountain"
                    allowaquatic = True
                # Unspecified biome type
                else:
                    biome = "unknown"
                    allowaquatic = True

                # Generate tiles #
                # Water tile
                if d <= watertable:
                    tile = "water"
                    # water
                # Sand tile
                elif (d > watertable and d <= sandlevel) or (biome == "desert" and d > sandlevel):
                    tile = "sand"
                    # sand
                # Mountain tile
                elif d > sandlevel and biome == "mountain": # biomenoise[x][y] > mtnlevel
                    tile = "mountainhigh"
                    # mountains
                # Forest/grass tile
                elif d > sandlevel and (biome == "forest" or biome == "tiaga"):
                    tile = "forest"
                    if biome == "tiaga" and random.randrange(0, 3) == 0:
                        tile = "grass"
                    # forest
                # Grass tile
                elif d > sandlevel:
                    tile = "grass"
                    # grass
                # Undefined tile type
                else:
                    tile = "none"
                    # no tile?

                # Add tile to current row/column list
                column.append(tile)
            # Add column/row to tile map
            self.common.tile_map.append(column)
        print "Map Generated"


    def generate_noise(self, width, height, frequency, octaves):
        """Generates a 2d array of random noise."""
        del self.noise[:]
        self.noise_width = width
        self.noise_height = height

        for y in range(0, self.noise_height):
            noise_row = []
            for x in range(0, self.noise_width):
                noise_row.append(random.randint(0, 1000)/1000.0)
            self.noise.append(noise_row)

        result = []

        for y in range(0, self.noise_height):
            row = []
            for x in range(0, self.noise_width):
                row.append(self.turbulence(x*frequency, y*frequency, octaves))
            result.append(row)

        return result


    def smooth_noise(self, x, y):
        """ Returns the average value of the 4 neighbors of (x, y) from the
        noise array.
        """
        fractX = x-int(x)
        fractY = y-int(y)

        x1 = (int(x)+self.noise_width) % self.noise_width
        y1 = (int(y)+self.noise_height) % self.noise_height

        x2 = (x1+self.noise_width - 1) % self.noise_width
        y2 = (y1+self.noise_height - 1) % self.noise_height

        value = 0.0
        value += fractX * fractY * self.noise[y1][x1]
        value += fractX * (1-fractY) * self.noise[y2][x1]
        value += (1-fractX) * fractY * self.noise[y1][x2]
        value += (1-fractX) * (1-fractY) * self.noise[y2][x2]

        return value


    def turbulence(self, x, y, size):
        """This function controls how far we zoom in/out of the noise array.
        The further zoomed in gives less detail and is more blurry.
        """
        value = 0.0
        size *= 1.0
        initial_size = size

        while size >= 1:
            value += self.smooth_noise(x / size, y / size) * size
            size /= 2.0

        return 128.0 * value / initial_size