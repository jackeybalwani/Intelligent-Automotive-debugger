"""
Main FastAPI Backend Application
Handles log parsing, analysis, and AI integration
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Import custom modules
from parsers.auto_detector import AutoDetector
from parsers.can_parser import CANParser
from parsers.dbc_parser import DBCParser
from analyzers.error_detector import ErrorDetector
from analyzers.pattern_analyzer import PatternAnalyzer
from analyzers.root_cause import RootCauseAnalyzer
from analyzers.predictive import PredictiveAnalyzer
from analyzers.timeline_builder import TimelineBuilder
from ai.ollama_manager import OllamaManager
from ai.nlp_engine import NLPEngine
from database.models import init_database, Session
from utils.file_utils import save_uploaded_file, get_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Automotive Debug Log Analyzer",
    description="AI-powered automotive log analysis and debugging",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
auto_detector = AutoDetector()
error_detector = ErrorDetector()
pattern_analyzer = PatternAnalyzer()
root_cause_analyzer = RootCauseAnalyzer()
predictive_analyzer = PredictiveAnalyzer()
timeline_builder = TimelineBuilder()
ollama_manager = OllamaManager()
nlp_engine = NLPEngine()

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

# Request/Response Models
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    format: str
    size: int
    status: str
    message: str

class AnalysisRequest(BaseModel):
    file_ids: List[str]
    analysis_types: List[str]
    dbc_file_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = {}

class NLPQueryRequest(BaseModel):
    query: str
    context_file_ids: List[str]
    session_id: Optional[str] = None

class ExportRequest(BaseModel):
    analysis_id: str
    format: str  # pdf, html, csv, json
    include_sections: List[str]

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        # Initialize database
        init_database()
        
        # Initialize Ollama
        await ollama_manager.initialize()
        
        # Load ML models
        pattern_analyzer.load_models()
        predictive_analyzer.load_models()
        
        logger.info("Backend services initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_update(message: dict):
    """Broadcast updates to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass

# File upload endpoints
@app.post("/api/upload", response_model=List[FileUploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload and process log files"""
    responses = []
    
    for file in files:
        try:
            # Save file
            file_path = await save_uploaded_file(file)
            file_hash = get_file_hash(file_path)
            
            # Auto-detect format
            detected_format = auto_detector.detect_format(file_path)
            
            # Send progress update
            await broadcast_update({
                "type": "file_upload",
                "filename": file.filename,
                "status": "processing",
                "progress": 50
            })
            
            # Initial parsing based on format
            parser = auto_detector.get_parser(detected_format)
            initial_stats = parser.get_file_stats(file_path)
            
            response = FileUploadResponse(
                file_id=file_hash,
                filename=file.filename,
                format=detected_format,
                size=initial_stats.get("size", 0),
                status="success",
                message=f"File uploaded and format detected: {detected_format}"
            )
            
            responses.append(response)
            
            # Send completion update
            await broadcast_update({
                "type": "file_upload",
                "filename": file.filename,
                "status": "completed",
                "progress": 100,
                "file_id": file_hash
            })
            
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            responses.append(FileUploadResponse(
                file_id="",
                filename=file.filename,
                format="unknown",
                size=0,
                status="error",
                message=str(e)
            ))
    
    return responses

# Analysis endpoints
@app.post("/api/analyze")
async def analyze_logs(request: AnalysisRequest):
    """Perform comprehensive analysis on uploaded logs"""
    try:
        results = {
            "analysis_id": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "files": request.file_ids,
            "results": {}
        }
        
        # Load files
        log_data = []
        for file_id in request.file_ids:
            # Load parsed data from cache/database
            data = await load_parsed_data(file_id)
            log_data.append(data)
        
        # Load DBC if provided
        dbc_data = None
        if request.dbc_file_id:
            dbc_data = await load_dbc_file(request.dbc_file_id)
        
        # Perform requested analyses
        total_steps = len(request.analysis_types)
        current_step = 0
        
        for analysis_type in request.analysis_types:
            current_step += 1
            progress = (current_step / total_steps) * 100
            
            await broadcast_update({
                "type": "analysis_progress",
                "analysis_type": analysis_type,
                "progress": progress
            })
            
            if analysis_type == "error_detection":
                results["results"]["errors"] = await error_detector.detect_errors(log_data, dbc_data)
            
            elif analysis_type == "pattern_analysis":
                results["results"]["patterns"] = await pattern_analyzer.analyze_patterns(log_data)
            
            elif analysis_type == "root_cause":
                results["results"]["root_cause"] = await root_cause_analyzer.analyze(log_data, dbc_data)
            
            elif analysis_type == "predictive":
                results["results"]["predictions"] = await predictive_analyzer.predict(log_data)
            
            elif analysis_type == "timeline":
                results["results"]["timeline"] = await timeline_builder.build_timeline(log_data)
        
        # Save analysis results
        await save_analysis_results(results)
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NLP Query endpoint
@app.post("/api/nlp/query")
async def process_nlp_query(request: NLPQueryRequest):
    """Process natural language queries about log files"""
    try:
        # Load context data
        context_data = []
        for file_id in request.context_file_ids:
            data = await load_parsed_data(file_id)
            context_data.append(data)
        
        # Process query with NLP engine
        response = await nlp_engine.process_query(
            query=request.query,
            context=context_data,
            session_id=request.session_id
        )
        
        # Use Ollama for enhanced response
        if ollama_manager.is_available():
            enhanced_response = await ollama_manager.enhance_response(
                query=request.query,
                initial_response=response,
                context=context_data
            )
            response["enhanced"] = enhanced_response
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing NLP query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export endpoints
@app.post("/api/export")
async def export_analysis(request: ExportRequest):
    """Export analysis results in various formats"""
    try:
        # Load analysis results
        analysis = await load_analysis_results(request.analysis_id)
        
        if request.format == "pdf":
            from utils.pdf_exporter import PDFExporter
            exporter = PDFExporter()
            pdf_bytes = await exporter.export(analysis, request.include_sections)
            
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=analysis_{request.analysis_id}.pdf"
                }
            )
        
        elif request.format == "html":
            from utils.html_exporter import HTMLExporter
            exporter = HTMLExporter()
            html_content = await exporter.export(analysis, request.include_sections)
            
            return StreamingResponse(
                io.BytesIO(html_content.encode()),
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename=analysis_{request.analysis_id}.html"
                }
            )
        
        elif request.format == "csv":
            from utils.csv_exporter import CSVExporter
            exporter = CSVExporter()
            csv_content = await exporter.export(analysis, request.include_sections)
            
            return StreamingResponse(
                io.BytesIO(csv_content.encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=analysis_{request.analysis_id}.csv"
                }
            )
        
        elif request.format == "json":
            return JSONResponse(
                content=analysis,
                headers={
                    "Content-Disposition": f"attachment; filename=analysis_{request.analysis_id}.json"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {request.format}")
            
    except Exception as e:
        logger.error(f"Error exporting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Check backend service health"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "ollama": ollama_manager.is_available(),
            "models_loaded": pattern_analyzer.models_loaded and predictive_analyzer.models_loaded
        }
    }

# Helper functions
async def load_parsed_data(file_id: str) -> Dict[str, Any]:
    """Load parsed data from database/cache"""
    # Implementation to load parsed data
    pass

async def load_dbc_file(file_id: str) -> Dict[str, Any]:
    """Load DBC file data"""
    # Implementation to load DBC data
    pass

async def save_analysis_results(results: Dict[str, Any]):
    """Save analysis results to database"""
    # Implementation to save results
    pass

async def load_analysis_results(analysis_id: str) -> Dict[str, Any]:
    """Load analysis results from database"""
    # Implementation to load results
    pass

# Main entry point
if __name__ == "__main__":
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False
    )
