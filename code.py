"""
Continuously scroll randomly generated Mario style toasters.
Designed fr an ItsyBitsy M4 Express and a 1.3" 240x240 TFT

Adafruit invests time and resources providing this open source code.
Please support Adafruit and open source hardware by purchasing
products from Adafruit!

Written by Dave Astels for Adafruit Industries
Copyright (c) 2019 Adafruit Industries
Licensed under the MIT license.

All text above must be included in any redistribution.
"""

import time
from random import seed, randint
import board
import displayio
from adafruit_st7789 import ST7789
import adafruit_imageload

NUMBER_OF_SPRITES = 3

# Sprite cell values
EMPTY = 0
CELL_1 = 1
CELL_2 = 2

# Animation support

FIRST_CELL = CELL_1
LAST_CELL = CELL_2

NUMBER_OF_CELLS = (LAST_CELL - FIRST_CELL) + 1

# A boolean array corresponding to the sprites, True if it's part of the animation sequence.
ANIMATED = [_sprite >= FIRST_CELL and _sprite <= LAST_CELL for _sprite in range(NUMBER_OF_SPRITES)]


# The chance (out of 10) that a new toaster, or toast will enter
CHANCE_OF_NEW_TOASTER = 4
CHANCE_OF_NEW_TOAST = 2

# How many sprites to styart with
INITIAL_NUMBER_OF_SPRITES= 5

# Global variables
display = None
tilegrid = None

seed(int(time.monotonic()))

def make_display():
    """Set up the display support.
    Return the Display object.
    """
    spi = board.SPI()
    while not spi.try_lock():
        pass
    spi.configure(baudrate=24000000) # Configure SPI for 24MHz
    spi.unlock()
    tft_cs = board.D10
    tft_dc = board.D7

    displayio.release_displays()
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D9)

    return ST7789(display_bus, width=240, height=240, rowstart=80, auto_refresh=False)

def make_tilegrid():
    """Construct and return the tilegrid."""
    group = displayio.Group(max_size=10)

    sprite_sheet, palette = adafruit_imageload.load("/tilesheet.bmp",
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)
    grid = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                              width=11, height=11,
                              tile_height=24, tile_width=24,
                              x=0, y=-24,
                              default_tile=EMPTY)
    group.append(grid)
    display.show(group)
    return grid

def random_cell():
    return randint(FIRST_CELL, LAST_CELL)

def evaluate_position(row, col):
    """Return whether how long of aa toaster is placable at the given location.
    :param row: the tile row (0-9)
    :param col: the tile column (0-9)
    """
    return tilegrid[col, row] == EMPTY

def seed_toasters(number_of_toasters):
    """Create the initial toasters so it doesn't start empty"""
    for _ in range(number_of_toasters):
        while True:
            row = randint(0, 9)
            col = randint(0, 9)
            if evaluate_position(row, col):
                break
        tilegrid[col, row] = random_cell()

def next_sprite(sprite):
    if ANIMATED[sprite]:
        return (((sprite - FIRST_CELL) + 1) % NUMBER_OF_CELLS) + FIRST_CELL
    return sprite

def advance_animation():
    """Cycle through animation cells each time."""
    for tile_number in range(121):
        tilegrid[tile_number] = next_sprite(tilegrid[tile_number])

def slide_tiles():
    """Move the tilegrid one pixel to the bottom-left."""
    tilegrid.x -= 1
    tilegrid.y += 1

def shift_tiles():
    """Move tiles one spot to the left, and reset the tilegrid's position"""
    for row in range(10, 0, -1):
        for col in range(10):
            tilegrid[col, row] = tilegrid[col + 1, row - 1]
        tilegrid[10, row] = EMPTY
    for col in range(11):
        tilegrid[col, 0] = EMPTY
    tilegrid.x = 0
    tilegrid.y = -24

def add_toaster():
    """Maybe add a new toaster on the right and/or top at a randon open location"""
    chance_of_entry_at_right = randint(1, 10)
    if chance_of_entry_at_right > CHANCE_OF_NEW_TOASTER:
        while True:
            row = randint(0, 9)
            if tilegrid[9, row] == EMPTY and tilegrid[10, row] == EMPTY:
                break
        tilegrid[10, row] = random_cell()
    chance_of_entry_at_top = randint(1, 10)
    if chance_of_entry_at_top > CHANCE_OF_NEW_TOASTER:
        while True:
            col = randint(0, 9)
            if tilegrid[col, 0] == EMPTY and tilegrid[col, 1] == EMPTY:
                break
        tilegrid[col, 0] = random_cell()

display = make_display()
tilegrid = make_tilegrid()
seed_toasters(INITIAL_NUMBER_OF_SPRITES)
display.refresh()

while True:
    for _ in range(24):
        advance_animation()
        slide_tiles()
        display.refresh()
    shift_tiles()
    add_toaster()
    display.refresh()
