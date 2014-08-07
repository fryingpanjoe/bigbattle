# Copyright (c) 2014 Per Lindstrand

import logging
import random

LOG = logging.getLogger(__name__)

def generate_random_square_patch(size, tile_types=[0]):
    return [random.choice(tile_types) for i in range(size * size)]
