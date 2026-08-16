from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import trimesh
import numpy as np
import os, uuid

app = FastAPI()

def create_building(floors, has_stairs, building_type, furniture_list):
    meshes = []
    floor_h = 3.0
    size = 12
    for f in range(floors):
        z = f * floor_h
        floor_m = trimesh.creation.box((size, size, 0.2))
        floor_m.apply_translation([0,0,z])
        meshes.append(floor_m)
        wall_positions = [[0,size/2],[0,-size/2],[size/2,0],[-size/2,0]]
        for i,pos in enumerate(wall_positions):
            is_h = i<2
            w = size if is_h else 0.2
            d = 0.2 if is_h else size
            wall = trimesh.creation.box((w,d,floor_h))
            wall.apply_translation([pos[0], pos[1], z+floor_h/2])
            meshes.append(wall)
        if has_stairs and building_type=="Building" and f < floors-1:
            for s in range(10):
                step = trimesh.creation.box((2,0.4,0.2))
                step.apply_translation([size/2-2, -4+s*0.8, z+s*0.3])
                meshes.append(step)
        if f==0:
            for item in furniture_list:
                if "Table" in item:
                    m = trimesh.creation.box((1.2,1.2,0.7))
                    m.apply_translation([0,0,z+0.35])
                    meshes.append(m)
    return trimesh.util.concatenate(meshes)

@app.post("/generate")
async def generate(floors: int = Form(1), stairs: bool = Form(False), building_type: str = Form("House"), furniture: str = Form(""), photo: UploadFile = File(None)):
    furn = furniture.split(",") if furniture else []
    mesh = create_building(floors, stairs, building_type, furn)
    path = f"/tmp/{uuid.uuid4()}.glb"
    try:
        mesh.export(path)
    except:
        path = f"building.glb"
        mesh.export(path)
    return FileResponse(path, media_type="model/gltf-binary", filename="building.glb")

@app.get("/")
def root():
    return {"status": "Tharuu 3D Cloud Running"}