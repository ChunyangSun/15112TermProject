import math
import pyglet
from pyglet import gl
from pyglet.window import key
from Box2D import (
    b2Vec2, b2PolygonDef, b2World,
    b2BodyDef, b2AABB, b2CircleDef,
    b2MouseJointDef, b2RevoluteJointDef, b2ContactListener,
    b2DistanceJointDef, b2BuoyancyControllerDef
)
from xml.etree.ElementTree import parse

FPS = 60
TIMESTEP = 1.0 / FPS
W = 100
H = 72
FLOOR = 15
WATER_LEVEL = 3
world = None  # let's keep world as a global for now

earth_tex = pyglet.image.load('textures/ground.png')

def setup_world():
    global buoyancy
    world_bounds = b2AABB()
    world_bounds.lowerBound = (-200, -100)
    world_bounds.upperBound = (1000, 1000)
    world = b2World(
        world_bounds,
        b2Vec2(0, -30),  # Gravity vector
        True  # Use "sleep" optimisation
    )

    wallsdef = b2BodyDef()
    walls = world.CreateBody(wallsdef)
    walls.userData = 'Blocks'

    WALLS = [
        (W, FLOOR * 0.5, (W / 2, FLOOR * 0.5), 0),  # floor
        (W / 2, 1, (W / 2, H + 1), 0),  # ceiling
        (1, 600, (-1, -500), 0),  # left wall
        (1, 600, (W + 1, -500), 0),  # right wall
    ]

    for wall in WALLS:
        shape = b2PolygonDef()
        shape.SetAsBox(*wall)
        walls.CreateShape(shape)

    for shape in read_shapes_from_svg('shapes/ground.svg'):
        walls.CreateShape(shape)

    buoyancydef = b2BuoyancyControllerDef()
    buoyancydef.normal = b2Vec2(0, 1)
    buoyancydef.offset = WATER_LEVEL
    buoyancydef.density = 2.5
    buoyancydef.angularDrag = 0.5
    buoyancydef.linearDrag = 3
    buoyancy = world.CreateController(buoyancydef)

    return world

def setup_scene():
    global batch, heli, hook, truck, controlling, ground
    batch = pyglet.graphics.Batch()

    # Create the ground
    ground = pyglet.sprite.Sprite(earth_tex, 0, 0, batch=batch)
    group = pyglet.sprite.SpriteGroup(
       earth_tex, gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA
    )

    l, b = (0, 0)
    r, t = (W, FLOOR)
    # batch.add(4, gl.GL_QUADS, group,
    #    ('v2f', [l, b, l, t, r, t, r, b]),
    #    ('t2f', [0, 0.5, 0, 1, 10, 1, 10, 0.5]),
    # )
    ball = Ball((10,4))
    objects.append(truck)

def update(dt):
    world.Step(TIMESTEP, 20, 16)
    for b in objects:
        b.update(dt)

def on_mouse_press():
    pass

def on_mouse_release():
    pass
def on_mouse_drag():
    pass
def on_key_press():
    pass


##########def shapes##################
def circle_def(radius,
        center=(0, 0),
        density=1,
        restitution=0.1,
        friction=2,
        groupindex=0):
    s = b2CircleDef()
    s.radius = radius
    s.localPosition = b2Vec2(*center)
    s.density = density
    s.restitution = restitution
    s.friction = friction
    s.filter.groupIndex = groupindex
    return s

class GraphicalObject(object):
    # Load image here
    IMAGE = None

    def __init__(self, pos):
        self.create_sprite(pos)

    def create_sprite(self, pos):
        x, y = pos
        self.sprite = pyglet.sprite.Sprite(self.IMAGE, x, y, batch=batch)

    def update(self, dt):
        pass

    def destroy(self):
        objects.remove(self)


class PhysicalObject(GraphicalObject):
    BULLET = False
    SHAPEDEFS = []

    def __init__(self, pos):
        super(PhysicalObject, self).__init__(pos)
        self.create_body(pos)

    def create_body(self, pos):
        if not self.SHAPEDEFS:
            return

        bodydef = b2BodyDef()
        bodydef.position = b2Vec2(*pos)
        body = world.CreateBody(bodydef)
        for shape in self.SHAPEDEFS:
            body.CreateShape(shape)
        body.SetBullet(self.BULLET)
        body.SetMassFromShapes()
        self.body = body
        buoyancy.AddBody(body)
        body.userData = self

    def update(self, dt):
        self.sprite.position = self.body.position
        self.sprite.rotation = -math.degrees(self.body.angle)

    def destroy(self):
        world.DestroyBody(self.body)
        objects.remove(self)


class Ball(PhysicalObject):
    SHAPEDEFS = [
        circle_def(1.6, friction=50.0)
    ]

###########util#####################
def load_image_centered(filename):
    """Load an image and set its anchor point to the middle."""
    im = pyglet.image.load(filename)
    im.anchor_x = im.width // 2
    im.anchor_y = im.height // 2
    return im


def read_shapes_from_svg(fname):
    """Dirty way to read polygons from a subset of SVG."""
    doc = parse(fname)
    shapes = []

    h = float(doc.getroot().get('height'))
    for p in doc.findall('.//{http://www.w3.org/2000/svg}path'):
        path = p.get('d') or ''
        coords = []
        last = b2Vec2(0, h)
        for cmd in path.split():
            if ',' in cmd:
                x, y = [float(c) for c in cmd.split(',')]
                c = b2Vec2(x, -y) + last
                last = c
                coords.append(c)
        shape = b2PolygonDef()
        shape.setVertices(tuple(coords))
        shapes.append(shape)
    return shapes



if __name__ == '__main__':
    world = setup_world()
    setup_scene()

    window = pyglet.window.Window(
        width=int(W / SCALE),
        height=int(H / SCALE)
    )

    keyboard = key.KeyStateHandler()
    window.push_handlers(keyboard)

    # window.event(on_draw)
    window.event(on_mouse_press)
    window.event(on_mouse_release)
    window.event(on_mouse_drag)
    window.event(on_key_press)

    pyglet.clock.schedule(update)
    pyglet.app.run()