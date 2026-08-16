from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse
import trimesh, uuid, os

app = FastAPI()

def create_building(floors, has_stairs, b_type, furn):
    meshes = []
    h = 3.0
    if b_type == "Other": # කුළුණ / Tower
        # Cylinder Tower
        tower = trimesh.creation.cylinder(radius=2.5, height=floors*h)
        tower.apply_translation([0,0,floors*h/2])
        meshes.append(tower)
        # Top
        top = trimesh.creation.cylinder(radius=3, height=0.5)
        top.apply_translation([0,0,floors*h])
        meshes.append(top)
    else:
        size = 12
        for f in range(floors):
            z = f*h
            floor_m = trimesh.creation.box((size, size, 0.2))
            floor_m.apply_translation([0,0,z])
            meshes.append(floor_m)
            for pos in [[0,size/2],[0,-size/2],[size/2,0],[-size/2,0]]:
                is_h = pos[1]!=0
                w = size if is_h else 0.2
                d = 0.2 if is_h else size
                wall = trimesh.creation.box((w,d,h))
                wall.apply_translation([pos[0],pos[1],z+h/2])
                meshes.append(wall)
            if has_stairs and b_type=="Building" and f < floors-1:
                for s in range(10):
                    step = trimesh.creation.box((2,0.4,0.2))
                    step.apply_translation([size/2-2, -4+s*0.8, z+s*0.3])
                    meshes.append(step)
    # Furniture
    for item in furn:
        if "Table" in item:
            m = trimesh.creation.box((1.2,1.2,0.7))
            m.apply_translation([0,0,0.35])
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
        path = "building.glb"
        mesh.export(path)
    return FileResponse(path, media_type="model/gltf-binary", filename="building.glb")

@app.get("/")
def root(): return {"status": "Tharuu Cloud Live", "url": "https://tharuu-3d-backend.onrender.com"}
