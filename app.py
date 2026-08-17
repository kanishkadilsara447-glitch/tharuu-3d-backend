from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse
import trimesh
import numpy as np
import uuid

app = FastAPI()

def create_lotus_tower():
    # Nelum Kuluna - Accurate Shape
    meshes = []
    # 1. Bottom Stalk
    stalk = trimesh.creation.cylinder(radius=3, height=40, sections=32)
    stalk.apply_translation([0,0,20])
    meshes.append(stalk)
    # 2. Green base
    base = trimesh.creation.cylinder(radius=3.5, height=5, sections=32)
    base.apply_translation([0,0,40])
    meshes.append(base)
    # 3. Lotus Bulb - Main
    bulb = trimesh.creation.icosphere(subdivisions=2, radius=8)
    bulb.apply_scale([1,1,1.2])
    bulb.apply_translation([0,0,50])
    meshes.append(bulb)
    # 4. Petals - 8 petals around
    for i in range(8):
        angle = i * (2*np.pi/8)
        petal = trimesh.creation.icosphere(subdivisions=1, radius=3)
        petal.apply_scale([1,0.4,1.5])
        x = 6*np.cos(angle)
        y = 6*np.sin(angle)
        petal.apply_translation([x,y,52])
        meshes.append(petal)
    # 5. Upper white part
    upper = trimesh.creation.cylinder(radius=3, height=8, sections=32)
    upper.apply_translation([0,0,62])
    meshes.append(upper)
    # 6. Antenna
    antenna = trimesh.creation.cylinder(radius=0.5, height=20, sections=16)
    antenna.apply_translation([0,0,75])
    meshes.append(antenna)

    # Add spiral stairs inside stalk - walkable
    for i in range(60):
        z = i * 0.6
        angle = i * 0.5
        r = 2.0
        x = r*np.cos(angle)
        y = r*np.sin(angle)
        step = trimesh.creation.box((0.8,0.4,0.1))
        step.apply_translation([x,y,z])
        meshes.append(step)

    return trimesh.util.concatenate(meshes)

def create_building(floors, b_type):
    if "lotus" in b_type.lower() or "nelum" in b_type.lower() or "කුළුණ" in b_type.lower():
        return create_lotus_tower()

    meshes = []
    h=3.0
    size=10
    if b_type=="Other":
        return create_lotus_tower()
    for f in range(floors):
        z=f*h
        floor_m = trimesh.creation.box((size,size,0.2))
        floor_m.apply_translation([0,0,z])
        meshes.append(floor_m)
        for pos in [[0,size/2],[0,-size/2],[size/2,0],[-size/2,0]]:
            is_h = pos[1]!=0
            w = size if is_h else 0.2
            d = 0.2 if is_h else size
            wall = trimesh.creation.box((w,d,h))
            wall.apply_translation([pos[0],pos[1],z+h/2])
            meshes.append(wall)
        if b_type=="Building" and f < floors-1:
            for s in range(10):
                step = trimesh.creation.box((2,0.4,0.2))
                step.apply_translation([size/2-2, -3+s*0.6, z+s*0.3])
                meshes.append(step)
    return trimesh.util.concatenate(meshes)

@app.post("/generate")
async def generate(
    floors: int = Form(2),
    building_type: str = Form("House"),
    text_prompt: str = Form(""),
    photo: UploadFile = File(None)
):
    # Text prompt එකෙන් search වගේ හදනවා
    final_type = text_prompt if text_prompt!="" else building_type
    mesh = create_building(floors, final_type)
    path = f"/tmp/{uuid.uuid4()}.glb"
    try:
        mesh.export(path)
    except:
        path="building.glb"
        mesh.export(path)
    return FileResponse(path, media_type="model/gltf-binary", filename="building.glb")

@app.get("/")
def root(): return {"status":"Live"}
