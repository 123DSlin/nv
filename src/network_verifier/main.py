"""
Main FastAPI application for the Network Verifier system.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_config(files: List[UploadFile] = File(..., description="Multiple configuration files")):
    """Handle configuration file upload and verification."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files were uploaded")
            
        configs = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Process each uploaded file
        for file in files:
            if not file.filename.endswith(('.cfg', '.txt')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only .cfg and .txt files are allowed."
                )
                
            # Save uploaded file
            file_path = f"configs/{timestamp}_{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            logger.info(f"Received file upload request: {file.filename}")
            logger.info(f"Saved uploaded file to: {file_path}")
            
            # Load configuration
            loader = ConfigLoader()
            file_configs = loader.load_configs(str(file_path))
            configs.update(file_configs)
        
        if not configs:
            raise HTTPException(status_code=400, detail="No valid configurations were found in the uploaded files")
        
        # Create snapshot
        snapshot_path = loader.create_snapshot(configs, f"snapshot_{timestamp}")
        logger.info(f"Created snapshot at: {snapshot_path}")
        
        # Try to run verification with Batfish, fallback to local verification if failed
        engine = VerificationEngine()
        try:
            verification_results = engine.verify_network_properties(f"snapshot_{timestamp}", {
                "reachability": {"source": "any", "destination": "any"},
                "isolation": {"source": "any", "destination": "any"},
                "forwarding_loops": {},
                "bgp_peering": {},
                "acl_consistency": {},
                "route_table": {}
            })
            logger.info("Completed network verification with Batfish")
        except Exception as e:
            logger.warning(f"Batfish verification failed: {str(e)}")
            logger.info("Falling back to local verification")
            verification_results = engine.verify_network_properties_local(configs)
            logger.info("Completed local network verification")
        
        # Build topology
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(configs)
        logger.info("Built network topology")
        
        # Generate report
        generator = ReportGenerator()
        report_path = generator.generate_report(verification_results, f"snapshot_{timestamp}")
        logger.info(f"Generated report at: {report_path}")
        
        # Prepare response
        with open(report_path, "r") as f:
            report_content = json.load(f)
        
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
        
        return JSONResponse({
            "status": "success",
            "message": "Configurations uploaded and verified successfully",
            "report_path": str(report_path),
            "report": report_content,
            "topology": formatted_topology
        })
        
    except HTTPException as e:
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