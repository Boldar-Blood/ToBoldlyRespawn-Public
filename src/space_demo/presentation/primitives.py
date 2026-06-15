# Procedural Graphics Generators - To Boldly Respawn

from panda3d.core import (
    LineSegs, CardMaker, NodePath,
    GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    GeomTriangles, Geom, GeomNode
)

def create_filled_geom(vertices, color_vec):
    """Helper method to construct a solid flat-colored polygon on the native XZ screen plane."""
    format = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData('poly', format, Geom.UHStatic)
    
    vertex = GeomVertexWriter(vdata, 'vertex')
    color = GeomVertexWriter(vdata, 'color')
    
    for v in vertices:
        # Map our 2D vertex components (X, Y) to Panda3D's native (X, 0.0, Z) plane
        vertex.addData3(v[0], 0.0, v[1])
        color.addData4(color_vec[0], color_vec[1], color_vec[2], color_vec[3])
        
    tris = GeomTriangles(Geom.UHStatic)
    # Simple triangle (3 vertices)
    if len(vertices) == 3:
        tris.addVertices(0, 1, 2)
    # Arrowhead or quad (4 vertices) split into two triangles
    elif len(vertices) == 4:
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
    # 5-vertex polygon
    elif len(vertices) == 5:
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
        tris.addVertices(0, 3, 4)
    # 6-vertex polygon
    elif len(vertices) == 6:
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
        tris.addVertices(0, 3, 4)
        tris.addVertices(0, 4, 5)
        
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    return geom

def create_textured_xz_quad(x_half, z_half):
    """Creates a flat textured quad directly in the native XZ plane at Y=0."""
    format = GeomVertexFormat.getV3t2() # Position (3D) and Texture Coordinates (2D)
    vdata = GeomVertexData('quad', format, Geom.UHStatic)
    
    vertex = GeomVertexWriter(vdata, 'vertex')
    texcoord = GeomVertexWriter(vdata, 'texcoord')
    
    # 4 vertices of the quad in CCW order on the XZ plane:
    # 1. Bottom-Left: (-x_half, 0.0, -z_half) -> UV (0, 0)
    # 2. Bottom-Right: (x_half, 0.0, -z_half) -> UV (1, 0)
    # 3. Top-Right: (x_half, 0.0, z_half) -> UV (1, 1)
    # 4. Top-Left: (-x_half, 0.0, z_half) -> UV (0, 1)
    
    vertex.addData3(-x_half, 0.0, -z_half)
    texcoord.addData2(0.0, 0.0)
    
    vertex.addData3(x_half, 0.0, -z_half)
    texcoord.addData2(1.0, 0.0)
    
    vertex.addData3(x_half, 0.0, z_half)
    texcoord.addData2(1.0, 1.0)
    
    vertex.addData3(-x_half, 0.0, z_half)
    texcoord.addData2(0.0, 1.0)
    
    tris = GeomTriangles(Geom.UHStatic)
    tris.addVertices(0, 1, 2)
    tris.addVertices(0, 2, 3)
    
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    
    geom_node = GeomNode('textured_quad')
    geom_node.addGeom(geom)
    return geom_node

def create_player_ship_geom():
    """Generates a player card geometry directly in the XZ plane."""
    return create_textured_xz_quad(1.0, 1.0)

def create_chaser_drone_geom():
    """Generates a chaser drone card geometry directly in the XZ plane."""
    return create_textured_xz_quad(0.8, 0.8)

def create_boss_dreadnought_geom():
    """Generates a boss dreadnought card geometry directly in the XZ plane."""
    return create_textured_xz_quad(9.6, 7.2)

def create_laser_geom(is_player=True):
    """Generates a textured laser card geometry directly in the XZ plane."""
    return create_textured_xz_quad(0.18, 0.6)

def create_missile_geom():
    """Generates a textured missile card geometry directly in the XZ plane."""
    return create_textured_xz_quad(0.35, 0.9)

def create_pickup_geom(pickup_type="health"):
    """Generates a textured pickup quad geometry directly in the XZ plane."""
    if pickup_type == "missile":
        return create_textured_xz_quad(0.60, 0.60)
    return create_textured_xz_quad(0.70, 0.70)

def create_arrow_geom():
    """Generates a solid flat-colored downward pointing arrow/chevron geometry in the XZ plane."""
    # Vertices for sci-fi arrowhead chevron pointing downward
    # 0: top left, 1: top right, 2: bottom point, 3: inner indent
    vertices = [(-0.6, 0.5), (0.6, 0.5), (0.0, -0.8), (0.0, 0.0)]
    geom = create_filled_geom(vertices, (1.0, 0.6, 0.2, 0.85)) # Neon Amber
    geom_node = GeomNode('arrow_chevron')
    geom_node.addGeom(geom)
    return geom_node

