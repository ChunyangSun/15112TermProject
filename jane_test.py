import pyglet
from pyglet import gl
import math
from Box2D import (
    b2Vec2, b2PolygonDef, b2World,
    b2BodyDef, b2AABB, b2MouseJointDef,
    b2CircleDef
)


ball_tex = pyglet.image.load('textures/earthball.png').get_mipmapped_texture()

FPS = 60
TIMESTEP = 1.0/FPS
W = 100
H = 72

batch = None
objects = []
slowmo = False

SCALE = 0.1    # World units - screen units conversion factor

world = None  # let's keep world as a global for now
mouse_joint = None

def load_image_centered(filename):
    """Load an image and set its anchor point to the middle."""
    im = pyglet.image.load(filename)
    im.anchor_x = im.width // 2
    im.anchor_y = im.height // 2
    return im

def screen_to_world(pos):
    sx, sy = pos
    return b2Vec2(sx * SCALE, sy * SCALE)


def world_to_screen(pos):
    wx, wy = pos
    return (wx / SCALE, wy / SCALE)


def init_world():
    world_bounds = b2AABB()
    world_bounds.lowerBound = (-200, -1000)
    world_bounds.upperBound = (200, 200)
    world = b2World(
        world_bounds,
        b2Vec2(0, -30),  # Gravity vector
        True  # Use "sleep" optimisation
    )

    wallsdef = b2BodyDef()
    walls = world.CreateBody(wallsdef)
    walls.userData = 'Blocks'

    WALLS = [
        (W / 2, 1, (W / 2, -1), 0),  # floor
        (W / 2, 1, (W / 2, H + 1), 0),  # ceiling
        (1, 600, (-1, -500), 0),  # left wall
        (1, 600, (W + 1, -500), 0),  # right wall
    ]

    for wall in WALLS:
        shape = b2PolygonDef()
        shape.SetAsBox(*wall)
        walls.CreateShape(shape)

    return world


class PhysicalObject(object):
    # Load image here
    IMAGE = None

    def __init__(self, pos):
		self.create_body(pos)
		self.create_sprite()

    def create_sprite(self):
		self.sprite = pyglet.sprite.Sprite(self.IMAGE, batch=batch)

    def timerFired(self, dt):
    	self.sprite.position = world_to_screen(self.body.position)
    	self.sprite.rotation = -math.degrees(self.body.angle)


class ShootingBall(PhysicalObject):
    IMAGE = load_image_centered('textures/neonball.png')


    @classmethod
    def fire(self, pos, velocity):
        c = ShootingBall(pos)
        c.body.SetLinearVelocity(b2Vec2(*velocity))
        objects.append(c)
        return c

    def create_body(self, pos):
        bodydef = b2BodyDef()
        bodydef.position = b2Vec2(*pos)
        body = world.CreateBody(bodydef)
        cdef = b2CircleDef()
        cdef.radius = 1.2
        cdef.density = 0.01
        cdef.restitution = 1
        cdef.friction = 0.5

        body.CreateShape(cdef)
        self.body = body
        body.SetBullet(False)
        body.SetMassFromShapes()

def mousePressed(x, y, button, modifiers):
	pass 

count = 0
def timerFired(dt):
	global count
	count += 1
	world.Step(TIMESTEP * 0.2 if slowmo else TIMESTEP, 20, 16)
	for b in objects:
	    b.timerFired(dt)
	if count % 1000 == 0:
		v = b2Vec2(math.cos(20), math.sin(20))
		pos = b2Vec2(0, 2) + v * 3
		print v 
		ShootingBall.fire(pos, v*50)
	redrawALL()


def draw_obj(body, tex):
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex.id)
    transformed = [world_to_screen(body.GetWorldPoint(p)) for p in POINTS]
    gl.glBegin(gl.GL_QUADS)
    for p, tc in zip(transformed, TEX_COORDS):
        gl.glTexCoord2f(*tc)
        gl.glVertex2f(*p)
    gl.glEnd()


def init_scene():
    global batch
    batch = pyglet.graphics.Batch()


def redrawALL():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    batch.draw()


if __name__ == '__main__':
    world = init_world()
    scene = init_scene()
    # Warm up the wall physics
    for i in range(200):
        world.Step(0.01, 20, 16)
    # # Then freeze the wall in place
    # for o in objects:
    #     o.body.PutToSleep()

    window = pyglet.window.Window(
        width=int(W / SCALE),
        height=int(H / SCALE)
    )

    window.event(mousePressed)
    window.event(redrawALL)


    pyglet.clock.schedule(timerFired)
    pyglet.app.run()
