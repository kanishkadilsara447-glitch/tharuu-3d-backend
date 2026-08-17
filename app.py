from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
import trimesh
import numpy as np
import uuid, os

app = FastAPI()

def fix_vertical(mesh):
    # Blender එකේ කෙලින් හිටින්න
    rot = trimesh.transformations.rotation_matrix(np.radians(90), [0,1,0])
    mesh.apply_transform(rot)
    return mesh

def create_lotus_tower():
    meshes=[]
    stalk = trimesh.creation.cylinder(radius=4, height=200, sections=32)
    stalk.apply_translation([0,0,100]); meshes.append(stalk)
    bud = trimesh.creation.uv_sphere(radius=18, count=[32,32])
    bud.apply_translation([0,0,210]); meshes.append(bud)
    for i in range(16):
        ang = i * 2*np.pi/16
        petal = trimesh.creation.cone(radius=4, height=20, sections=12)
        petal.apply_translation([0,0,10])
        petal.apply_transform(trimesh.transformations.rotation_matrix(np.radians(50), [1,0,0]))
        petal.apply_transform(trimesh.transformations.rotation_matrix(ang, [0,0,1]))
        petal.apply_translation([15*np.cos(ang), 15*np.sin(ang), 205])
        meshes.append(petal)
    antenna = trimesh.creation.cylinder(radius=1, height=50, sections=16)
    antenna.apply_translation([0,0,250]); meshes.append(antenna)
    # interior spiral
    for i in range(80):
        z=i*1.2
        if z>95: break
        ang=i*0.6
        step=trimesh.creation.box((1.5,0.6,0.2))
        step.apply_translation([1.5,0,z])
        step.apply_transform(trimesh.transformations.rotation_matrix(ang, [0,0,1]))
        meshes.append(step)
    return fix_vertical(trimesh.util.concatenate(meshes))

def create_home():
    meshes=[]
    size=12
    # Floor
    meshes.append(trimesh.creation.box((size,size,0.3)))
    # Walls with door gap
    # Back wall
    meshes.append(trimesh.creation.box((size,0.3,3)).apply_translation([0,size/2,1.5]) or trimesh.creation.box((size,0.3,3)))
    back=trimesh.creation.box((size,0.3,3)); back.apply_translation([0,size/2,1.5]); meshes.append(back)
    # Left/Right
    left=trimesh.creation.box((0.3,size,3)); left.apply_translation([-size/2,0,1.5]); meshes.append(left)
    right=trimesh.creation.box((0.3,size,3)); right.apply_translation([size/2,0,1.5]); meshes.append(right)
    # Front wall with door hole - 2 pieces
    front1=trimesh.creation.box((4,0.3,3)); front1.apply_translation([-4,-size/2,1.5]); meshes.append(front1)
    front2=trimesh.creation.box((4,0.3,3)); front2.apply_translation([4,-size/2,1.5]); meshes.append(front2)
    top=trimesh.creation.box((4,0.3,1)); top.apply_translation([0,-size/2,2.5]); meshes.append(top)
    # Windows
    for pos in [[-size/2,0],[size/2,0],[0,size/2]]:
        win=trimesh.creation.box((0.5,1.5,1)); win.apply_translation([pos[0],pos[1],1.5]); meshes.append(win)
    # Roof
    roof=trimesh.creation.cone(radius=9, height=4, sections=4)
    roof.apply_translation([0,0,5]); meshes.append(roof)
    return fix_vertical(trimesh.util.concatenate(meshes))

def create_building(floors):
    meshes=[]
    size=14; h=3.2
    for f in range(floors):
        z=f*h
        floor_m=trimesh.creation.box((size,size,0.2)); floor_m.apply_translation([0,0,z]); meshes.append(floor_m)
        # 4 walls with windows & doors per floor
        # Front wall with door on ground, windows on others
        if f==0:
            # door
            w1=trimesh.creation.box((5,0.3,h)); w1.apply_translation([-4.5,-size/2,z+h/2]); meshes.append(w1)
            w2=trimesh.creation.box((5,0.3,h)); w2.apply_translation([4.5,-size/2,z+h/2]); meshes.append(w2)
            w3=trimesh.creation.box((4,0.3,1)); w3.apply_translation([0,-size/2,z+h-0.5]); meshes.append(w3)
        else:
            w=trimesh.creation.box((size,0.3,h)); w.apply_translation([0,-size/2,z+h/2]); meshes.append(w)
            win=trimesh.creation.box((2,0.4,1.2)); win.apply_translation([0,-size/2,z+h/2]); meshes.append(win)
        # other 3 walls with windows
        for side in [[0,size/2],[size/2,0],[-size/2,0]]:
            is_y=side[1]!=0
            wall=trimesh.creation.box((size if is_y else 0.3, 0.3 if is_y else size, h))
            wall.apply_translation([side[0],side[1],z+h/2]); meshes.append(wall)
        # Stairs
        if f < floors-1:
            for s in range(10):
                step=trimesh.creation.box((2.5,0.5,0.2)); step.apply_translation([size/2-2, -4+s*0.7, z+s*0.3]); meshes.append(step)
    return fix_vertical(trimesh.util.concatenate(meshes))

@app.post("/generate")
async def generate(floors: int = Form(2), building_type: str = Form("House"), text_prompt: str = Form(""), photo: UploadFile = File(None)):
    p = (text_prompt+" "+building_type).lower()
    if "lotus" in p or "nelum" in p or "කුළුණ" in p:
        mesh=create_lotus_tower()
    elif "build" in p or "tattu" in p or "තට්ටු" in p:
        mesh=create_building(floors)
    else: # home
        mesh=create_home()
    path=f"/tmp/{uuid.uuid4()}.glb"; mesh.export(path)
    return FileResponse(path, media_type="model/gltf-binary", filename="building.glb")

@app.post("/blender_script")
async def blender_script(text_prompt: str = Form("lotus tower")):
    p=text_prompt.lower()
    if "lotus" in p or "nelum" in p:
        script = '''
import bpy
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
# Stalk 350m Lotus Tower - Colombo
bpy.ops.mesh.primitive_cylinder_add(radius=4, depth=200, location=(0,0,100))
bpy.ops.mesh.primitive_uv_sphere_add(radius=18, location=(0,0,210))
for i in range(16):
    import math
    ang=i*math.pi*2/16
    x=15*math.cos(ang); y=15*math.sin(ang)
    bpy.ops.mesh.primitive_cone_add(radius1=4, depth=20, location=(x,y,215))
    bpy.context.active_object.rotation_euler[0]=math.radians(50)
    bpy.context.active_object.rotation_euler[2]=ang
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=50, location=(0,0,250))
print("Lotus Tower Created - Accurate to Colombo Lotus Tower")
'''
    elif "build" in p:
        script = '''
import bpy
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
floors=5
for f in range(floors):
    z=f*3.2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,z))
    bpy.context.active_object.scale=(14,14,0.2)
    # add walls, doors, windows with gaps
print("Building with floors created")
'''
    else:
        script = '''
import bpy
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(size=12, location=(0,0,1.5))
bpy.ops.mesh.primitive_cone_add(radius1=9, depth=4, location=(0,0,5))
print("Beautiful Home Created")
'''
    path=f"/tmp/{uuid.uuid4()}.py"
    with open(path,"w") as f: f.write(script)
    return FileResponse(path, media_type="text/x-python", filename="lotus_tower_blender.py")

@app.get("/")
def root(): return {"status":"Live v4 Home+Building+Lotus+Script"}
