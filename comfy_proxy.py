from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests, os, time, tempfile, shutil

COMFY_HOST = "http://127.0.0.1:8188"
AUTH_TOKEN = os.getenv("COMFY_TOKEN", "my-secret-token")

app = FastAPI(title="ComfyUI Proxy")

class RunRequest(BaseModel):
    token: str
    workflow: dict

@app.post("/run_workflow")
def run_workflow(req: RunRequest):
    if req.token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Bad token")

    # 1) send prompt
    rsp = requests.post(f"{COMFY_HOST}/prompt", json=req.workflow).json()
    prompt_id = rsp["prompt_id"]

    # 2) poll history
    while True:
        hist = requests.get(f"{COMFY_HOST}/history/{prompt_id}").json()
        if hist["status"] == "completed":
            break
        time.sleep(1)

    # 3) pull first image path
    output_path = list(hist["outputs"].values())[0][0]["filename"]
    tmp = tempfile.mkdtemp()
    new_path = shutil.copy(output_path, tmp)

    return {"file_path": new_path}
