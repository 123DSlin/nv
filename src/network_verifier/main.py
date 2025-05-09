"""
Main FastAPI application for the Network Verifier system.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional
from .data_layer.config_loader import ConfigLoader
from .verification_layer.verification_engine import VerificationEngine
from .presentation_layer.report_generator import ReportGenerator
from .model_layer.topology_builder import TopologyBuilder
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Network Verifier")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Create necessary directories
Path("configs").mkdir(exist_ok=True)
Path("snapshots").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

class ReachabilityRequest(BaseModel):
    source: str
    target: str

class IsolationRequest(BaseModel):
    source: str
    target: str

class PathLocateRequest(BaseModel):
    source: str
    target: str

class DisjointPathRequest(BaseModel):
    source: str
    target: str
    mode: str = "node"  # 'node' or 'edge'

class LoopDetectionRequest(BaseModel):
    mode: str = "global"  # 'global' or 'node'
    node: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_config(files: List[UploadFile] = File(..., description="Multiple configuration files")):
    """Handle configuration file upload and verification."""
    try:
        logger.info("Received upload request")
        
        if not files:
            logger.error("No files were uploaded")
            raise HTTPException(status_code=400, detail="No files were uploaded")
            
        configs = {}
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Process each uploaded file
        for file in files:
            logger.info(f"Processing file: {file.filename}")
            
            if not file.filename.endswith(('.cfg', '.txt')):
                logger.error(f"Invalid file type: {file.filename}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only .cfg and .txt files are allowed."
                )
                
            # Save uploaded file
            file_path = f"configs/{timestamp}_{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            logger.info(f"Saved uploaded file to: {file_path}")
            
            saved_files.append(file_path)
            
            # Load configuration
            loader = ConfigLoader()
            file_configs = loader.load_configs(str(file_path))
            configs.update(file_configs)
            logger.info(f"Loaded configurations from: {file.filename}")
        
        if not configs:
            logger.error("No valid configurations were found")
            raise HTTPException(status_code=400, detail="No valid configurations were found in the uploaded files")
        
        # Create snapshot with saved file paths
        snapshot_path = f"snapshots/snapshot_{timestamp}.json"
        snapshot_data = {
            "timestamp": timestamp,
            "files": saved_files,
            "configs": configs
        }
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        logger.info(f"Created snapshot at: {snapshot_path}")
        
        # Build topology
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(configs)
        logger.info("Built network topology")
        
        # Format topology data for vis.js
        formatted_topology = {
            "nodes": [
                {
                    "id": node["id"],
                    "label": node["label"],
                    "title": node["title"],
                    "group": node["group"],
                    "value": node["value"]
                }
                for node in topology["nodes"]
            ],
            "edges": [
                {
                    "id": edge["id"],
                    "from": edge["from"],
                    "to": edge["to"],
                    "label": edge["label"],
                    "title": edge["title"]
                }
                for edge in topology["edges"]
            ]
        }
        
        logger.info("Sending response with topology data")
        return JSONResponse({
            "status": "success",
            "message": "Configurations uploaded successfully",
            "topology": formatted_topology
        })
        
    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{report_name}")
async def get_report(report_name: str):
    """Retrieve a verification report."""
    try:
        report_path = Path("reports") / f"{report_name}.json"
        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        with open(report_path, "r") as f:
            return json.load(f)
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving report: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.post("/verify-reachability")
async def verify_reachability(request: ReachabilityRequest):
    try:
        # Get the latest snapshot
        snapshot_dir = Path("snapshots")
        snapshots = sorted(snapshot_dir.glob("snapshot_*.json"), key=lambda x: x.stat().st_mtime)
        if not snapshots:
            raise HTTPException(status_code=404, detail="No network configuration found")
        
        latest_snapshot = snapshots[-1]
        with open(latest_snapshot, "r") as f:
            snapshot_data = json.load(f)
        
        # Get configuration files from snapshot
        config_files = snapshot_data.get("files", [])
        if not config_files:
            raise HTTPException(status_code=404, detail="No configuration files found in snapshot")
        
        # Initialize verification engine
        verification_engine = VerificationEngine(use_batfish=False)
        
        # Verify reachability
        result = verification_engine.verify_reachability(
            request.source,
            request.target,
            config_files
        )
        
        # Generate report
        report = {
            "summary": {
                "overall_status": "PASS" if result["reachable"] else "FAIL",
                "total_checks": 1,
                "passed_checks": 1 if result["reachable"] else 0,
                "failed_checks": 0 if result["reachable"] else 1,
                "error_checks": 0
            },
            "analysis": {
                "reachability": {
                    "status": "PASS" if result["reachable"] else "FAIL",
                    "description": f"Reachability check between {request.source} and {request.target}",
                    "details": {
                        "source": request.source,
                        "target": request.target,
                        "reachable": result["reachable"],
                        "path": result.get("path", []),
                        "reason": result.get("reason", "Unknown")
                    }
                }
            }
        }
        
        return {"status": "success", "report": report}
        
    except Exception as e:
        logger.error(f"Error verifying reachability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-isolation")
async def verify_isolation(request: IsolationRequest):
    try:
        # Get the latest snapshot
        snapshot_dir = Path("snapshots")
        snapshots = sorted(snapshot_dir.glob("snapshot_*.json"), key=lambda x: x.stat().st_mtime)
        if not snapshots:
            raise HTTPException(status_code=404, detail="No network configuration found")
        latest_snapshot = snapshots[-1]
        with open(latest_snapshot, "r") as f:
            snapshot_data = json.load(f)
        config_files = snapshot_data.get("files", [])
        if not config_files:
            raise HTTPException(status_code=404, detail="No configuration files found in snapshot")
        # Initialize verification engine
        verification_engine = VerificationEngine(use_batfish=False)
        # Verify reachability
        result = verification_engine.verify_reachability(
            request.source,
            request.target,
            config_files
        )
        # 逻辑反转：有路径为FAIL，无路径为PASS
        isolated = not result["reachable"]
        report = {
            "summary": {
                "overall_status": "PASS" if isolated else "FAIL",
                "total_checks": 1,
                "passed_checks": 1 if isolated else 0,
                "failed_checks": 0 if isolated else 1,
                "error_checks": 0
            },
            "analysis": {
                "isolation": {
                    "status": "PASS" if isolated else "FAIL",
                    "description": f"Isolation check between {request.source} and {request.target}",
                    "details": {
                        "source": request.source,
                        "target": request.target,
                        "isolated": isolated,
                        "path": result.get("path", []),
                        "reason": result.get("reason", "")
                    }
                }
            }
        }
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Error verifying isolation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/snapshots")
async def list_snapshots():
    snapshot_dir = Path("snapshots")
    snapshots = sorted(snapshot_dir.glob("snapshot_*.json"), key=lambda x: x.stat().st_mtime)
    snapshot_list = []
    for snap in snapshots:
        with open(snap, "r") as f:
            data = json.load(f)
        snapshot_list.append({
            "id": snap.stem,  # e.g. snapshot_20240505_123456
            "timestamp": data.get("timestamp", ""),
            "files": data.get("files", [])
        })
    return {"snapshots": snapshot_list}

@app.get("/load-snapshot/{snapshot_id}")
async def load_snapshot(snapshot_id: str):
    try:
        snapshot_path = Path("snapshots") / f"{snapshot_id}.json"
        if not snapshot_path.exists():
            raise HTTPException(status_code=404, detail="Snapshot not found")
        with open(snapshot_path, "r") as f:
            snapshot_data = json.load(f)
        configs = snapshot_data.get("configs", {})
        # Build topology
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(configs)
        formatted_topology = {
            "nodes": [
                {
                    "id": node["id"],
                    "label": node["label"],
                    "title": node["title"],
                    "group": node["group"],
                    "value": node["value"]
                }
                for node in topology["nodes"]
            ],
            "edges": [
                {
                    "id": edge["id"],
                    "from": edge["from"],
                    "to": edge["to"],
                    "label": edge["label"],
                    "title": edge["title"]
                }
                for edge in topology["edges"]
            ]
        }
        return {"status": "success", "topology": formatted_topology}
    except Exception as e:
        logger.error(f"Error loading snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/locate-path")
async def locate_path(request: PathLocateRequest):
    try:
        # Get the latest snapshot
        snapshot_dir = Path("snapshots")
        snapshots = sorted(snapshot_dir.glob("snapshot_*.json"), key=lambda x: x.stat().st_mtime)
        if not snapshots:
            raise HTTPException(status_code=404, detail="No network configuration found")
        latest_snapshot = snapshots[-1]
        with open(latest_snapshot, "r") as f:
            snapshot_data = json.load(f)
        config_files = snapshot_data.get("files", [])
        if not config_files:
            raise HTTPException(status_code=404, detail="No configuration files found in snapshot")
        # Initialize verification engine
        verification_engine = VerificationEngine(use_batfish=False)
        # 查找所有路径
        result = verification_engine.find_all_paths(
            request.source,
            request.target,
            config_files
        )
        return {
            "status": "success",
            "found": result.get("found", False),
            "paths": result.get("paths", []),
            "best_path": result.get("best_path", []),
            "reason": result.get("reason", "")
        }
    except Exception as e:
        logger.error(f"Error locating path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-disjoint-paths")
async def verify_disjoint_paths(request: DisjointPathRequest):
    try:
        # Get the latest snapshot
        snapshot_dir = Path("snapshots")
        snapshots = sorted(snapshot_dir.glob("snapshot_*.json"), key=lambda x: x.stat().st_mtime)
        if not snapshots:
            raise HTTPException(status_code=404, detail="No network configuration found")
        latest_snapshot = snapshots[-1]
        with open(latest_snapshot, "r") as f:
            snapshot_data = json.load(f)
        config_files = snapshot_data.get("files", [])
        if not config_files:
            raise HTTPException(status_code=404, detail="No configuration files found in snapshot")
        verification_engine = VerificationEngine(use_batfish=False)
        result = verification_engine.find_disjoint_paths(
            request.source,
            request.target,
            config_files,
            mode=request.mode,
            max_paths=2
        )
        return {
            "status": "success",
            "found": result.get("found", False),
            "paths": result.get("paths", []),
            "type": result.get("type", request.mode),
            "reason": result.get("reason", "")
        }
    except Exception as e:
        logger.error(f"Error verifying disjoint paths: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-forwarding-loops")
async def verify_forwarding_loops(request: LoopDetectionRequest):
    try:
        snapshot_dir = Path("snapshots")
        snapshots = sorted(snapshot_dir.glob("snapshot_*.json"), key=lambda x: x.stat().st_mtime)
        if not snapshots:
            raise HTTPException(status_code=404, detail="No network configuration found")
        latest_snapshot = snapshots[-1]
        with open(latest_snapshot, "r") as f:
            snapshot_data = json.load(f)
        configs = snapshot_data.get("configs", {})
        engine = VerificationEngine(use_batfish=False)
        params = {"mode": request.mode, "node": request.node}
        result = engine.check_forwarding_loops(params, configs)
        return result
    except Exception as e:
        logger.error(f"Error verifying forwarding loops: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying forwarding loops: {str(e)}")

@app.get("/snapshot/{snapshot_id}")
async def get_snapshot(snapshot_id: str):
    """查看单个快照内容"""
    snapshot_path = Path("snapshots") / f"{snapshot_id}.json"
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found")
    with open(snapshot_path, "r") as f:
        return json.load(f)

@app.delete("/snapshot/{snapshot_id}")
async def delete_snapshot(snapshot_id: str, file: Optional[str] = Body(default=None)):
    """删除指定快照或快照中的单个文件"""
    snapshot_path = Path("snapshots") / f"{snapshot_id}.json"
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found")
    if file:
        # 删除快照中的单个文件
        try:
            with open(snapshot_path, "r") as f:
                data = json.load(f)
            files = data.get("files", [])
            configs = data.get("configs", {})
            # 支持完整路径和短文件名
            short_file = file.split("/")[-1]
            files = [f for f in files if f != file and f.split("/")[-1] != short_file]
            configs.pop(file, None)
            configs.pop(short_file, None)
            data["files"] = files
            data["configs"] = configs
            with open(snapshot_path, "w") as f:
                json.dump(data, f, indent=2)
            return {"status": "success", "message": f"File {file} deleted from snapshot {snapshot_id}."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from snapshot: {str(e)}")
    else:
        # 删除整个快照
        try:
            snapshot_path.unlink()
            return {"status": "success", "message": f"Snapshot {snapshot_id} deleted."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete snapshot: {str(e)}")

@app.get("/snapshots/batch/{timestamp}")
async def get_snapshots_by_batch(timestamp: str):
    """查看同一批次（timestamp）下所有快照内容"""
    snapshot_dir = Path("snapshots")
    batch_files = list(snapshot_dir.glob(f"snapshot_{timestamp}*.json"))
    if not batch_files:
        raise HTTPException(status_code=404, detail="No snapshots found for this batch")
    batch_snapshots = []
    for snap in batch_files:
        with open(snap, "r") as f:
            data = json.load(f)
        batch_snapshots.append({
            "id": snap.stem,
            "timestamp": data.get("timestamp", ""),
            "files": data.get("files", []),
            "content": data
        })
    return {"snapshots": batch_snapshots}

@app.delete("/snapshots/batch/{timestamp}")
async def delete_snapshots_by_batch(timestamp: str):
    """批量删除同一批次（timestamp）下所有快照"""
    snapshot_dir = Path("snapshots")
    batch_files = list(snapshot_dir.glob(f"snapshot_{timestamp}*.json"))
    if not batch_files:
        raise HTTPException(status_code=404, detail="No snapshots found for this batch")
    deleted = []
    errors = []
    for snap in batch_files:
        try:
            snap.unlink()
            deleted.append(snap.stem)
        except Exception as e:
            errors.append({"id": snap.stem, "error": str(e)})
    return {"deleted": deleted, "errors": errors} 