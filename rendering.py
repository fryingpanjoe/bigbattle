# Copyright (c) 2014 Per Lindstrand

import logging
import json

import pyglet
from pyglet.gl import *

import shader

LOG = logging.getLogger(__name__)

TILE_SIZE = 1.

CUBE_VERT_XYZ = [
    # front
    -.5, -.5,  .5,
     .5, -.5,  .5,
     .5,  .5,  .5,
     .5,  .5,  .5,
    -.5,  .5,  .5,
    -.5, -.5,  .5,

    # back
    -.5, -.5, -.5,
    -.5,  .5, -.5,
     .5,  .5, -.5,
     .5,  .5, -.5,
     .5, -.5, -.5,
    -.5, -.5, -.5,

    # right
     .5, -.5, -.5,
     .5,  .5, -.5,
     .5,  .5,  .5,
     .5,  .5,  .5,
     .5, -.5,  .5,
     .5, -.5, -.5,

    # left
    -.5, -.5, -.5,
    -.5, -.5,  .5,
    -.5,  .5,  .5,
    -.5,  .5,  .5,
    -.5,  .5, -.5,
    -.5, -.5, -.5,

    # top
    -.5,  .5, -.5,
    -.5,  .5,  .5,
     .5,  .5,  .5,
     .5,  .5,  .5,
     .5,  .5, -.5,
    -.5,  .5, -.5,

    # bottom
    # XXX probably no need to draw bottom
    -.5, -.5, -.5,
     .5, -.5, -.5,
     .5, -.5,  .5,
     .5, -.5,  .5,
    -.5, -.5,  .5,
    -.5, -.5, -.5,
]

CUBE_VERT_UV = [
    # front
    0., 0.,
    1., 0.,
    1., 1.,
    1., 1.,
    0., 1.,
    0., 0.,

    # back
    1., 0.,
    1., 1.,
    0., 1.,
    0., 1.,
    0., 0.,
    1., 0.,

    # right
    1., 0.,
    1., 1.,
    0., 1.,
    0., 1.,
    0., 0.,
    1., 0.,

    # left
    0., 0.,
    1., 0.,
    1., 1.,
    1., 1.,
    0., 1.,
    0., 0.,

    # top
    0., 1.,
    0., 0.,
    1., 0.,
    1., 0.,
    1., 1.,
    0., 1.,

    # bottom
    1., 1.,
    0., 1.,
    0., 0.,
    0., 0.,
    1., 0.,
    1., 1.,
]

CUBE_VERT_NORM = [
    # front
     0.,  0.,  .1,
     0.,  0.,  .1,
     0.,  0.,  .1,
     0.,  0.,  .1,
     0.,  0.,  .1,
     0.,  0.,  .1,

    # back
     0.,  0., -.1,
     0.,  0., -.1,
     0.,  0., -.1,
     0.,  0., -.1,
     0.,  0., -.1,
     0.,  0., -.1,

    # right
     1.,  0.,  0.,
     1.,  0.,  0.,
     1.,  0.,  0.,
     1.,  0.,  0.,
     1.,  0.,  0.,
     1.,  0.,  0.,

    # left
    -1.,  0.,  0.,
    -1.,  0.,  0.,
    -1.,  0.,  0.,
    -1.,  0.,  0.,
    -1.,  0.,  0.,
    -1.,  0.,  0.,

    # top
     0.,  1.,  0.,
     0.,  1.,  0.,
     0.,  1.,  0.,
     0.,  1.,  0.,
     0.,  1.,  0.,
     0.,  1.,  0.,

    # bottom
     0., -1.,  0.,
     0., -1.,  0.,
     0., -1.,  0.,
     0., -1.,  0.,
     0., -1.,  0.,
     0., -1.,  0.,
]

PYRAMID_VERT_XYZ = [
    # front
     0.,  .5,  0.,
    -.5, -.5,  .5,
     .5, -.5,  .5,

    # back
     0.,  .5,  0.,
    -.5, -.5, -.5,
     .5, -.5, -.5,

    # right
     0.,  .5,  0.,
     .5, -.5,  .5,
     .5, -.5, -.5,

    # left
     0.,  .5,  0.,
    -.5, -.5,  .5,
     .5, -.5,  .5,

    # bottom (two tris)
    -.5, -.5,  .5,
     .5, -.5,  .5,
    -.5, -.5, -.5,

    -.5, -.5, -.5,
     .5, -.5,  .5,
     .5, -.5, -.5,
]

PYRAMID_VERT_UV = [
     # front
     .5, 1.,
     0., 0.,
     1., 0.,

     # back
     .5, 1.,
     0., 0.,
     1., 0.,

     # right
     .5, 1.,
     0., 0.,
     1., 0.,

     # left
     .5, 1.,
     0., 0.,
     1., 0.,

     # bottom
     0., 1.,
     1., 1.,
     0., 0.,

     0., 0.,
     1., 1.,
     1., 0.,
]


def calc_pyramid_norms(xyz):
    def vec_sub(u, v):
        return (u[0] - v[0], u[1] - v[1], u[2] - v[2])

    def vec_cross(u, v):
        return (
             u[1]*v[2] - v[1]*u[2],
            -u[0]*v[2] + v[0]*u[2],
             u[0]*v[1] - v[0]*u[1])

    it = iter(xyz)
    vecs = [(x, next(it), next(it)) for x in it]

    norms = []
    it = iter(vecs)
    for u in it:
        v = next(it)
        w = next(it)
        norms.extend(vec_cross(vec_sub(u, v), vec_sub(u, w)) * 3)
    return norms


PYRAMID_VERT_NORM = calc_pyramid_norms(PYRAMID_VERT_XYZ)


class IsometricCamera(object):

    def __init__(self, x=0., y=0., dist=1., scale=10.):
        self.x = x
        self.y = y
        self.scale = scale
        self.dist = dist

    def setup(self, width, height):
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glOrtho(
            -self.scale, self.scale,
            -self.scale, self.scale,
            -1024, 1024);
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        gluLookAt(
            self.x + self.dist, self.dist, self.y + self.dist,
            self.x, 0., self.y,
            0., 1., 0.);


def read_file(filename):
    with open(filename, 'r') as file:
        return file.read()


class ShaderCache(object):

    def __init__(self):
        self.terrain_shaders = {}

    def load_shader(self, vert_fname, frag_fname):
        key = vert_fname + frag_fname
        program = self.terrain_shaders.get(key)
        if not program:
            program = shader.Shader(
                vert=[read_file(vert_fname)],
                frag=[read_file(frag_fname)])
        return program


#def draw_cube(x, y, z, width, height, depth):
#    glPushMatrix()
#    glTranslatef(x, y, z)
#    glScalef(width, height, depth)
#    pyglet.graphics.draw(
#        24, pyglet.gl.GL_QUADS,
#        ('v3f', CUBE_VERT_XYZ),
#        ('t2f', CUBE_VERT_UV),
#        ('n3f', CUBE_VERT_NORM))
#    glPopMatrix()


def create_static_interleaved_vbo(verts, uvs, norms):
    data = []
    count = len(verts) / 3
    vert_it = iter(verts)
    uv_it = iter(uvs)
    norm_it = iter(norms)
    for i in range(count):
        data.extend([
            next(vert_it), next(vert_it), next(vert_it),
            next(uv_it), next(uv_it),
            next(norm_it), next(norm_it), next(norm_it)])
    return create_static_vbo(data)


def create_static_vbo(data):
    #vbo_id = GLuint()
    #glGenBuffers(1, vbo_id)
    #glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
    #glBufferData(
    #    GL_ARRAY_BUFFER,
    #    len(data) * 4,
    #    (GLfloat * len(data))(*data),
    #    GL_STATIC_DRAW)
    #return vbo_id
    vbo = pyglet.graphics.vertexbuffer.create_buffer(
        len(data) * 4,
        target=GL_ARRAY_BUFFER,
        usage=GL_STATIC_DRAW,
        vbo=True)
    vbo.set_data((GLfloat * len(data))(*data))
    return vbo


class InterleavedStaticVBO(object):

    def __init__(self, xyz, uvs, norms):
        data = []
        count = len(xyz) / 3
        xyz_it = iter(xyz)
        uv_it = iter(uvs)
        norm_it = iter(norms)
        for i in range(count):
            data.extend([
                # xyz
                next(xyz_it), next(xyz_it), next(xyz_it),
                # uv
                next(uv_it), next(uv_it),
                # norm
                next(norm_it), next(norm_it), next(norm_it)])
        self.vbo = pyglet.graphics.vertexbuffer.create_buffer(
            len(data) * 4,
            target=GL_ARRAY_BUFFER,
            usage=GL_STATIC_DRAW,
            vbo=True)
        self.vbo.set_data((GLfloat * len(data))(*data))

    def enable_state(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    def disable_state(self):
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)

    def bind(self):
        self.vbo.bind()
        stride = (3 + 2 + 3) * 4
        glVertexPointer(3, GL_FLOAT, stride, 0)
        glTexCoordPointer(2, GL_FLOAT, stride, 3 * 4)
        glNormalPointer(GL_FLOAT, stride, (3 + 2) * 4)

    def unbind(self):
        self.vbo.unbind()


def load_texture_image(fname):
    image = pyglet.image.load(fname)
    tex = image.get_texture()
    glBindTexture(tex.target, tex.id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glBindTexture(tex.target, 0)
    return image


class WorldRendering(object):

    def __init__(self, shader_cache):
        self.cube_vlist = vertex_list = pyglet.graphics.vertex_list(
            36,
            ('v3f', CUBE_VERT_XYZ),
            ('t2f', CUBE_VERT_UV),
            ('n3f', CUBE_VERT_NORM))
        self.pyramid_vlist = vertex_list = pyglet.graphics.vertex_list(
            18,
            ('v3f', PYRAMID_VERT_XYZ),
            ('t2f', PYRAMID_VERT_UV),
            ('n3f', PYRAMID_VERT_NORM))
        #self.cube_vbo = create_static_interleaved_vbo(
        #    CUBE_VERT_XYZ, CUBE_VERT_UV, CUBE_VERT_NORM)
        #self.pyramid_vbo = create_static_interleaved_vbo(
        #    PYRAMID_VERT_XYZ, PYRAMID_VERT_UV, PYRAMID_VERT_NORM)
        self.cube_vbo = InterleavedStaticVBO(
            CUBE_VERT_XYZ, CUBE_VERT_UV, CUBE_VERT_NORM)
        self.pyramid_vbo = InterleavedStaticVBO(
            PYRAMID_VERT_XYZ, PYRAMID_VERT_UV, PYRAMID_VERT_NORM)

        self.entity_shader = shader_cache.load_shader(
            'entity.vp', 'entity.fp')
        self.entity_models = json.loads(read_file('entity_models.json'))
        for model in self.entity_models.itervalues():
            model['texture'] = load_texture_image(model['texture'])

        self.terrain_shader = shader_cache.load_shader(
            'terrain.vp', 'terrain.fp')
        self.terrain_textures = [
            load_texture_image(fname)
            for fname in json.loads(read_file('terrain_textures.json'))]

    def draw_entities(self, ents):
        glEnable(GL_TEXTURE_2D)
        self.cube_vbo.enable_state()
        self.cube_vbo.bind()
        self.entity_shader.bind()
        for ent in ents:
            model = self.entity_models.get(ent.draw_model)
            if model:
                size = model['size']
                glBindTexture(
                    GL_TEXTURE_2D, model['texture'].get_texture().id)
                glPushMatrix()
                glTranslatef(ent.x, .5 * size[1], ent.y)
                glScalef(*size)
                glDrawArrays(GL_TRIANGLES, 0, 36)
                glPopMatrix()
        self.entity_shader.unbind()
        self.cube_vbo.unbind()
        self.cube_vbo.disable_state()
        glDisable(GL_TEXTURE_2D)

    def draw_terrain_patch(self, wx, wy, tiles, width, height):
        x = 0
        y = 0
        glEnable(GL_TEXTURE_2D)
        self.cube_vbo.enable_state()
        self.cube_vbo.bind()
        self.terrain_shader.bind()
        for tile in tiles:
            glBindTexture(
                GL_TEXTURE_2D, self.terrain_textures[tile].get_texture().id)
            self._draw_cube(wx + x, -.5, wy + y)
            x += 1
            if x >= width:
                x = 0
                y += 1
        self.pyramid_vbo.bind()
        glBindTexture(
            GL_TEXTURE_2D, self.terrain_textures[0].get_texture().id)
        self._draw_pyramid(wx + width / 3., .5, wy + height / 3., .5, 1., .5)
        self._draw_pyramid(wx + width / 3., 1., wy + height / 3., .25, .5, .25)
        self._draw_pyramid(wx + width / 3., 1.25, wy + height / 3., .125, .25, .125)
        self._draw_pyramid(2 + wx + width / 3., .5, wy + height / 3., .5, 1., .5)
        self._draw_pyramid(2 + wx + width / 3., 1., wy + height / 3., .25, .5, .25)
        self._draw_pyramid(2 + wx + width / 3., 1.25, wy + height / 3., .125, .25, .125)
        self.terrain_shader.unbind()
        self.cube_vbo.disable_state()
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glDisable(GL_TEXTURE_2D)

    def _draw_pyramid(self, x, y, z, sx, sy, sz):
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(sx, sy, sz)
        glDrawArrays(GL_TRIANGLES, 0, 18)
        #self.pyramid_vlist.draw(GL_TRIANGLES)
        glPopMatrix()

    def _draw_cube(self, x, y, z):
        glPushMatrix()
        glTranslatef(x, y, z)
        glDrawArrays(GL_TRIANGLES, 0, 36)
        #self.cube_vlist.draw(GL_QUADS)
        glPopMatrix()
