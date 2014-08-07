# Copyright (c) 2014 Per Lindstrand

import logging
import math

LOG = logging.getLogger(__name__)


class SimulationConfig(object):

    PLAYER_MOVE_SPEED = 3.
    ENTITY_FRICTION = .9
    VERY_SLOW_SPEED = .001
    VERY_FAST_SPEED = 10.


class EntityFlags(object):

    NO_MOVE         = 1 << 1
    NO_COLLIDE      = 1 << 2
    PROJECTILE      = 1 << 3
    ATTACKING       = 1 << 4


class Entity(object):

    def __init__(self):
        self.id = 0
        self.x = 0.
        self.y = 0.
        self.acc_x = 0.
        self.acc_y = 0.
        self.vel_x = 0.
        self.vel_y = 0.
        self.radius = .5
        self.rotation = 0.
        self.flags = 0
        self.draw_model = 'default'

    def update(self, dt):
        if (self.flags & EntityFlags.NO_MOVE) == 0:
            self.vel_x += self.acc_x * dt
            self.vel_y += self.acc_y * dt
            self.x += self.vel_x * dt
            self.y += self.vel_y * dt

        friction = SimulationConfig.ENTITY_FRICTION
        self.vel_x *= friction * dt
        self.vel_y *= friction * dt

        very_slow = SimulationConfig.VERY_SLOW_SPEED
        very_fast = SimulationConfig.VERY_FAST_SPEED
        if self.vel_x < very_slow:
            self.vel_x = 0.
        elif self.vel_x > very_fast:
            self.vel_x = very_fast
        if self.vel_y < very_slow:
            self.vel_y = 0.
        elif self.vel_y > very_fast:
            self.vel_y = very_fast

    def is_colliding(self, other):
        if ((self.flags & EntityFlags.NO_COLLIDE) != 0 or
            (other.flags & EntityFlags.NO_COLLIDE) != 0):
            return False
        dx = (self.x - other.x)
        dy = (self.y - other.y)
        dr = (self.radius + other.radius)
        return (dx * dx + dy * dy) < (dr * dr)


class Enemy(object):

    def __init__(self, entity):
        self.entity = entity


class PlayerActionFlags(object):

    MOVE_NORTH      = 1 << 1
    MOVE_SOUTH      = 1 << 2
    MOVE_WEST       = 1 << 3
    MOVE_EAST       = 1 << 4
    MOVE_FORWARD    = 1 << 5
    MOVE_BACK       = 1 << 6
    MOVE_LEFT       = 1 << 7
    MOVE_RIGHT      = 1 << 8
    ATTACK          = 1 << 9


class Player(object):

    def __init__(self, entity):
        self.entity = entity
        self.action_flags = 0

    def set_flag(self, flag, on):
        if on:
            self.action_flags |= flag
        else:
            self.action_flags &= ~flag

    def move_north(self, on):
        self.set_flag(PlayerActionFlags.MOVE_NORTH, on)

    def move_south(self, on):
        self.set_flag(PlayerActionFlags.MOVE_SOUTH, on)

    def move_west(self, on):
        self.set_flag(PlayerActionFlags.MOVE_WEST, on)

    def move_east(self, on):
        self.set_flag(PlayerActionFlags.MOVE_EAST, on)

    def move_forward(self, on):
        self.set_flag(PlayerActionFlags.MOVE_FORWARD, on)

    def move_back(self, on):
        self.set_flag(PlayerActionFlags.MOVE_BACK, on)

    def move_left(self, on):
        self.set_flag(PlayerActionFlags.MOVE_LEFT, on)

    def move_right(self, on):
        self.set_flag(PlayerActionFlags.MOVE_RIGHT, on)

    def attack(self, on):
        self.set_flag(PlayerActionFlags.ATTACK, on)

    def set_rotation(self, rotation):
        self.entity.rotation = rotation

    def update(self, dt):
        move_speed = SimulationConfig.PLAYER_MOVE_SPEED
        vel_x = 0.
        vel_y = 0.
        if (self.action_flags & PlayerActionFlags.MOVE_NORTH) != 0:
            vel_x -= move_speed
            vel_y -= move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_SOUTH) != 0:
            vel_x += move_speed
            vel_y += move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_WEST) != 0:
            vel_x -= move_speed
            vel_y += move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_EAST) != 0:
            vel_x += move_speed
            vel_y -= move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_FORWARD) != 0:
            vel_x += math.cos(self.entity.rotation) * move_speed
            vel_y += math.sin(self.entity.rotation) * move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_BACK) != 0:
            vel_x -= math.cos(self.entity.rotation) * move_speed
            vel_y -= math.sin(self.entity.rotation) * move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_LEFT) != 0:
            vel_x -= math.cos(self.entity.rotation + math.pi * .5) * move_speed
            vel_y -= math.sin(self.entity.rotation + math.pi * .5) * move_speed
        if (self.action_flags & PlayerActionFlags.MOVE_RIGHT) != 0:
            vel_x += math.cos(self.entity.rotation + math.pi * .5) * move_speed
            vel_y += math.sin(self.entity.rotation + math.pi * .5) * move_speed
        speed = math.sqrt(vel_x * vel_x + vel_y * vel_y)
        if speed:
            speed_fac = move_speed / math.sqrt(vel_x * vel_x + vel_y * vel_y)
        else:
            speed_fac = 0.
        self.entity.vel_x = vel_x * speed_fac
        self.entity.vel_y = vel_y * speed_fac
        #if (self.action_flags & PlayerActionFlags.ATTACK) != 0:
        #    self.entity.flags |= EntityFlags.ATTACKING
        #else:
        #    self.entity.flags &= ~EntityFlags.ATTACKING
        #self.action_flags = 0


class Simulation(object):

    def __init__(self):
        self.id_gen = 100
        self.entities = []

    def update(self, dt):
        for entity in self.entities:
            entity.update(dt)

    def spawn_entity(self, x, y, radius=.5, rotation=.0, flags=0,
                     draw_model='default'):
        ent = Entity()
        ent.id = self.id_gen
        ent.x = x
        ent.y = y
        ent.radius = radius
        ent.rotation = rotation
        ent.flags = flags
        ent.draw_model = draw_model
        self.entities.append(ent)
        self.id_gen = self.id_gen + 1
        return ent


class TileType(object):

    NONE    = 0
    WATER   = 1
    GRASS   = 2
    SAND    = 3


class TileFlags(object):

    NONE        = 0
    BLOCKING    = 1 << 1


class Tile(object):

    def __init__(self):
        self.type = 0
        self.flags = 0
        self.effect = 0


class TerrainPatch(object):

    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.tiles = []
