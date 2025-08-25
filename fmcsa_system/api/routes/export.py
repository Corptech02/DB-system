"""
Export endpoints for FMCSA carrier data.
Handles CSV and Excel exports with chunked processing.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any
import logging

from ...services.export_service import ExportService
from ..models import ExportRequest, ExportResponse
from ..dependencies import check_rate_limit, verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize export service
export_service = ExportService()


@router.post("/export", response_model=ExportResponse)
async def create_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(check_rate_limit),
    api_key: str = Depends(verify_api_key)
) -> ExportResponse:
    """
    Create a carrier data export file.
    
    Exports carriers matching the provided filters to CSV or Excel format.
    Large exports are processed in chunks to manage memory efficiently.
    
    Args:
        request: Export configuration with filters and format
    
    Returns:
        Export metadata including download URL
    
    Note:
        - CSV exports support up to 1M rows
        - Excel exports are limited to 1,048,576 rows (Excel limit)
        - Large exports may take several minutes to complete
    """
    try:
        # Create export
        logger.info(f"Starting export: format={request.format}, filters={request.filters}")
        
        result = await export_service.export_carriers(request)
        
        # Schedule cleanup of old files
        background_tasks.add_task(export_service.cleanup_old_exports, max_age_hours=24)
        
        # Build download URL
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        download_url = f"{base_url}/api/export/download/{result['export_id']}"
        
        # Add API key to download URL if authentication is enabled
        if api_key:
            download_url += f"?api_key={api_key}"
        
        return ExportResponse(
            file_id=result["export_id"],
            filename=result["filename"],
            format=result["format"],
            size_bytes=result["file_size"],
            row_count=result["row_count"],
            download_url=download_url,
            expires_at=None  # Could add expiration logic
        )
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/download/{file_id}")
async def download_export(
    file_id: str,
    api_key: str = Depends(verify_api_key)
) -> FileResponse:
    """
    Download an exported file.
    
    Args:
        file_id: Export file ID
        api_key: Optional API key for authentication
    
    Returns:
        File download response
    
    Raises:
        404: File not found
    """
    # Find file in export directory
    export_dir = export_service.TEMP_DIR
    
    # Look for files with this ID
    import glob
    pattern = os.path.join(export_dir, f"{file_id}_*")
    files = glob.glob(pattern)
    
    if not files:
        raise HTTPException(status_code=404, detail="Export file not found")
    
    file_path = files[0]
    filename = os.path.basename(file_path)
    
    # Determine media type
    if file_path.endswith('.xlsx'):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = "text/csv"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/export/stream")
async def stream_export(
    request: ExportRequest,
    _: None = Depends(check_rate_limit),
    api_key: str = Depends(verify_api_key)
) -> StreamingResponse:
    """
    Stream export data without creating a temporary file.
    
    This endpoint streams the export directly to the client,
    which is more memory-efficient for large exports.
    
    Args:
        request: Export configuration
    
    Returns:
        Streaming response with CSV data
    
    Note:
        Currently only supports CSV format for streaming.
    """
    if request.format != "csv":
        raise HTTPException(
            status_code=400,
            detail="Streaming export only supports CSV format"
        )
    
    try:
        # Create async generator for streaming
        async def generate():
            try:
                async for chunk in export_service.stream_export(request):
                    yield chunk
            except Exception as e:
                logger.error(f"Streaming export failed: {e}")
                # Can't raise exception here, connection already started
                yield b"\n# ERROR: Export failed\n"
        
        # Determine filename
        from datetime import datetime
        filename = f"carriers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stream export failed: {str(e)}")


@router.get("/export/status/{file_id}")
async def get_export_status(
    file_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get the status of an export job.
    
    For future use with async/queued exports.
    
    Args:
        file_id: Export file ID
    
    Returns:
        Export status information
    """
    # This would check a job queue or database for status
    # For now, just check if file exists
    
    export_dir = export_service.TEMP_DIR
    import glob
    pattern = os.path.join(export_dir, f"{file_id}_*")
    files = glob.glob(pattern)
    
    if files:
        file_path = files[0]
        file_stats = os.stat(file_path)
        
        return {
            "file_id": file_id,
            "status": "completed",
            "file_size": file_stats.st_size,
            "created_at": file_stats.st_ctime,
            "ready_for_download": True
        }
    else:
        return {
            "file_id": file_id,
            "status": "not_found",
            "ready_for_download": False
        }