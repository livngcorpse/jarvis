from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import os
import json

app = FastAPI(title="JARVIS v2 API")

# Serve static files
app.mount("/miniapp", StaticFiles(directory="miniapp", html=True), name="miniapp")

class PromptRequest(BaseModel):
    prompt: str
    user_id: int

class FileOperation(BaseModel):
    operation: str
    file_path: str
    content: str = ""

@app.get("/")
async def root():
    return {"message": "JARVIS v2 API"}

@app.post("/api/prompt")
async def process_prompt(request: PromptRequest):
    """Process AI prompt from WebApp"""
    try:
        # Initialize JARVIS engine
        from jarvis_engine import JarvisEngine
        engine = JarvisEngine()
        
        response = await engine.process_prompt(request.prompt, request.user_id)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/file-operation")
async def file_operation(request: FileOperation):
    """Handle file operations from WebApp"""
    try:
        if request.operation == "read":
            if os.path.exists(request.file_path):
                with open(request.file_path, 'r') as f:
                    content = f.read()
                return {"content": content}
            else:
                raise HTTPException(status_code=404, detail="File not found")
        
        elif request.operation == "write":
            os.makedirs(os.path.dirname(request.file_path), exist_ok=True)
            with open(request.file_path, 'w') as f:
                f.write(request.content)
            return {"message": "File written successfully"}
        
        elif request.operation == "delete":
            if os.path.exists(request.file_path):
                os.remove(request.file_path)
                return {"message": "File deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="File not found")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/file-tree")
async def get_file_tree():
    """Get file tree structure"""
    from file_manager import FileManager
    fm = FileManager()
    tree = fm.get_file_tree()
    return {"tree": tree}