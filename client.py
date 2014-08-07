# Copyright (c) 2014 Per Lindstrand

import logging
import logging.config
import socket
import select
import sys
import time
import os
import random

import pyglet
from pyglet.window import key
from pyglet.gl import *

import networking
import rendering
import terrain
import world

LOG = logging.getLogger(__name__)

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
VERTICAL_FOV = 45
CLIP_NEAR = 1
CLIP_FAR = 8192


class GameWindow(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(GameWindow, self).__init__(*args, **kwargs)
        self.active = False
        self.start_time = time.time()
        self.last_update = time.time()
        self.fps_display = pyglet.clock.ClockDisplay()
        # networking
        self.sock = None
        self.chan = None
        self.server_addr = None
        # XXX move to somewhere else!
        self.shader_cache = rendering.ShaderCache()
        self.world_rendering = rendering.WorldRendering(self.shader_cache)
        self.terrain_size = 32
        self.terrain_grid = terrain.generate_random_square_patch(
            self.terrain_size, [0,1])
        self.world_simulation = world.Simulation()
        self.camera = rendering.IsometricCamera(
            x=self.terrain_size * .5, y=self.terrain_size * .5, dist=1., scale=8.)
        self.player_ent = self.world_simulation.spawn_entity(
            self.terrain_size * .5, self.terrain_size * .5)
        self.player = world.Player(self.player_ent)

    def on_activate(self):
        self.active = True
        glShadeModel(GL_SMOOTH)

    def on_deactivate(self):
        self.active = False

    def on_draw(self):
        if not self.active:
            return

        # update time
        now = time.time() - self.start_time
        if now < self.last_update:
            self.last_update = now
        frame_time = now - self.last_update
        self.last_update = now

        # update game
        self.player.update(frame_time)
        self.world_simulation.update(frame_time)

        # clear screen
        #self.clear()
        glClearColor(0., 0., 0., 0.)
        glClearDepth(1.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # world drawing
        self.camera.x = self.player_ent.x
        self.camera.y = self.player_ent.y
        window_width, window_height = self.get_size()
        self.camera.setup(window_width, window_height)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(.2, 1., -.2, 0.))

        self.world_rendering.draw_terrain_patch(
            0., 0.,
            self.terrain_grid,
            self.terrain_size,
            self.terrain_size)
        self.world_rendering.draw_entities(self.world_simulation.entities)

        # hud drawing
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, window_width, 0, window_height, 0, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        # ...
        #ui_renderer.draw(window_width, window_height)

        # draw fps
        self.fps_display.draw()

    def on_key(self, symbol, modifiers, pressed):
        if symbol == key.W:
            self.player.move_up(pressed)
        elif symbol == key.S:
            self.player.move_down(pressed)
        elif symbol == key.A:
            self.player.move_left(pressed)
        elif symbol == key.D:
            self.player.move_right(pressed)

    def on_key_press(self, symbol, modifiers):
        self.on_key(symbol, modifiers, True)

    def on_key_release(self, symbol, modifiers):
        self.on_key(symbol, modifiers, False)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_enter(self, x, y):
        pass

    def on_mouse_leave(self, x, y):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)

    def connect_to_server(self, addr, port):
        self.server_addr = (addr, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.chan = networking.Channel(self.sock, self.server_addr)

    def talk_to_server(self, dt):
        if self.sock:
            try:
                # check if there's anything on the socket
                readable, _, _ = select.select([self.sock], [], [], 0)
                if readable:
                    data, addr = self.sock.recvfrom(1024)
                    if data:
                        self.chan.on_data_received(data)
                    else:
                        # server disconnected
                        LOG.info('Server disconnected')
                        self.sock.close()
                        self.sock = None
                        return

                # handle packets (echo)
                packet = self.chan.recv_packet()
                if packet:
                    self.handle_packet(packet)

                # check if the socket is writable
                _, writable, _ = select.select([], [self.sock], [], 0)
                if writable:
                    if not self.chan.send_data():
                        LOG.info('Server disconnected')
                        self.sock.close()
                        self.sock = None
                        return

            except socket.error:
                LOG.exception('Socket error')
                self.sock.close()
                self.sock = None

    def send_hello(self, dt):
        self.chan.send_packet('hello from %s' % socket.getfqdn())

    def handle_packet(self, packet):
        print 'got', packet


def main():
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

    pyglet_platform = pyglet.window.get_platform()
    pyglet_display = pyglet_platform.get_default_display()
    pyglet_screen = pyglet_display.get_default_screen()
    pyglet_gl_config_template = pyglet.gl.Config(
        alpha_size=8,
        depth_size=24,
        double_buffer=True,
        sample_buffers=True,
        samples=8)

    pyglet_window = GameWindow(
        config=pyglet_gl_config_template,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        caption='Big Battle',
        resizable=False,
        fullscreen=False,
        visible=True,
        vsync=False)

    pyglet_window.connect_to_server('127.0.0.1', 9009)
    pyglet.clock.schedule_interval(
        pyglet_window.talk_to_server, 1. / 60.)
    pyglet.clock.schedule_interval(
        pyglet_window.send_hello, 1.)

    pyglet.app.run()

if __name__ == '__main__':
    main()
