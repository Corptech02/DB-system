"""
Export service for generating CSV and Excel files with chunked processing.
Handles large datasets efficiently with memory optimization.
"""

import os
import io
import tempfile
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
from pathlib import Path
import uuid

import pandas as pd
import aiofiles
from dotenv import load_dotenv

from ..database import db_pool
from ..api.models import SearchFilters, ExportRequest

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting carrier data to CSV and Excel formats.
    Uses chunked processing to handle millions of records efficiently.
    """
    
    # Configuration from environment
    MAX_ROWS_CSV = int(os.getenv("EXPORT_MAX_ROWS_CSV", 1000000))
    MAX_ROWS_EXCEL = int(os.getenv("EXPORT_MAX_ROWS_EXCEL", 1048576))
    CHUNK_SIZE = int(os.getenv("EXPORT_CHUNK_SIZE", 50000))
    TEMP_DIR = os.getenv("EXPORT_TEMP_DIR", "/tmp/fmcsa_exports")
    
    # Default columns for export
    DEFAULT_COLUMNS = [
        "usdot_number",
        "legal_name",
        "dba_name",
        "physical_address",
        "physical_city",
        "physical_state",
        "physical_zip",
        "telephone",
        "email",
        "entity_type",
        "operating_status",
        "power_units",
        "drivers",
        "liability_insurance_date",
        "liability_insurance_amount",
        "safety_rating"
    ]
    
    def __init__(self):
        """Initialize export service."""
        # Ensure temp directory exists
        Path(self.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    async def export_carriers(
        self,
        request: ExportRequest,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Export carriers based on filters to CSV or Excel.
        
        Args:
            request: Export request with filters and format
            progress_callback: Optional callback for progress updates
        
        Returns:
            Export metadata including file path and statistics
        """
        start_time = datetime.utcnow()
        export_id = str(uuid.uuid4())
        
        # Determine columns to export
        columns = request.columns or self.DEFAULT_COLUMNS
        if request.include_raw_data:
            columns.append("raw_data")
        
        # Create temporary file
        file_extension = "xlsx" if request.format == "xlsx" else "csv"
        filename = f"carriers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        file_path = os.path.join(self.TEMP_DIR, f"{export_id}_{filename}")
        
        try:
            # Get total count for progress tracking
            total_count = await self._get_filtered_count(request.filters)
            
            if total_count == 0:
                # No data to export
                return {
                    "export_id": export_id,
                    "filename": filename,
                    "format": request.format,
                    "row_count": 0,
                    "file_size": 0,
                    "file_path": file_path,
                    "duration_seconds": 0,
                    "status": "completed",
                    "message": "No data matching filters"
                }
            
            # Check limits
            max_rows = self.MAX_ROWS_EXCEL if request.format == "xlsx" else self.MAX_ROWS_CSV
            if total_count > max_rows:
                logger.warning(f"Export limited to {max_rows} rows (total: {total_count})")
                total_count = max_rows
            
            # Export based on format
            if request.format == "xlsx":
                row_count = await self._export_to_excel(
                    file_path, 
                    request.filters, 
                    columns,
                    total_count,
                    progress_callback
                )
            else:
                row_count = await self._export_to_csv(
                    file_path,
                    request.filters,
                    columns,
                    total_count,
                    progress_callback
                )
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Export completed: {row_count} rows, "
                f"{file_size/1024/1024:.1f}MB, {duration:.1f}s"
            )
            
            return {
                "export_id": export_id,
                "filename": filename,
                "format": request.format,
                "row_count": row_count,
                "file_size": file_size,
                "file_path": file_path,
                "duration_seconds": duration,
                "status": "completed",
                "download_url": f"/exports/{export_id}_{filename}"
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            
            # Clean up partial file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            raise Exception(f"Export failed: {str(e)}")
    
    async def _export_to_csv(
        self,
        file_path: str,
        filters: SearchFilters,
        columns: List[str],
        total_count: int,
        progress_callback: Optional[callable] = None
    ) -> int:
        """
        Export data to CSV with chunked processing.
        
        Args:
            file_path: Output file path
            filters: Search filters
            columns: Columns to export
            total_count: Total expected rows
            progress_callback: Progress callback
        
        Returns:
            Number of rows exported
        """
        rows_exported = 0
        first_chunk = True
        
        async with aiofiles.open(file_path, mode='w') as file:
            # Process in chunks
            async for chunk_df in self._fetch_data_chunks(filters, columns, self.CHUNK_SIZE):
                # Write header only for first chunk
                csv_data = chunk_df.to_csv(index=False, header=first_chunk)
                await file.write(csv_data)
                
                first_chunk = False
                rows_exported += len(chunk_df)
                
                # Progress callback
                if progress_callback:
                    progress_callback(rows_exported, total_count)
                
                # Stop if we've reached the limit
                if rows_exported >= self.MAX_ROWS_CSV:
                    logger.warning(f"CSV export limited to {self.MAX_ROWS_CSV} rows")
                    break
        
        return rows_exported
    
    async def _export_to_excel(
        self,
        file_path: str,
        filters: SearchFilters,
        columns: List[str],
        total_count: int,
        progress_callback: Optional[callable] = None
    ) -> int:
        """
        Export data to Excel with chunked processing.
        
        Args:
            file_path: Output file path
            filters: Search filters
            columns: Columns to export
            total_count: Total expected rows
            progress_callback: Progress callback
        
        Returns:
            Number of rows exported
        """
        rows_exported = 0
        
        # Create Excel writer
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = workbook.add_worksheet('Carriers')
            writer.sheets['Carriers'] = worksheet
            
            # Write headers
            for col_num, col_name in enumerate(columns):
                worksheet.write(0, col_num, col_name)
            
            row_offset = 1  # Start after header
            
            # Process in chunks
            async for chunk_df in self._fetch_data_chunks(filters, columns, self.CHUNK_SIZE):
                # Write data without headers
                for row_num, row_data in enumerate(chunk_df.values):
                    for col_num, value in enumerate(row_data):
                        # Handle different data types
                        if pd.isna(value):
                            continue
                        elif isinstance(value, (int, float)):
                            worksheet.write_number(row_offset + row_num, col_num, value)
                        elif isinstance(value, datetime):
                            worksheet.write_datetime(row_offset + row_num, col_num, value)
                        else:
                            worksheet.write_string(row_offset + row_num, col_num, str(value))
                
                row_offset += len(chunk_df)
                rows_exported += len(chunk_df)
                
                # Progress callback
                if progress_callback:
                    progress_callback(rows_exported, total_count)
                
                # Stop if we've reached Excel limit
                if rows_exported >= self.MAX_ROWS_EXCEL:
                    logger.warning(f"Excel export limited to {self.MAX_ROWS_EXCEL} rows")
                    break
            
            # Auto-fit columns (optional, can be slow for large files)
            if rows_exported < 10000:  # Only for smaller exports
                for col_num, col_name in enumerate(columns):
                    worksheet.set_column(col_num, col_num, 15)
        
        return rows_exported
    
    async def _fetch_data_chunks(
        self,
        filters: SearchFilters,
        columns: List[str],
        chunk_size: int
    ) -> AsyncIterator[pd.DataFrame]:
        """
        Fetch data in chunks from database.
        
        Args:
            filters: Search filters
            columns: Columns to fetch
            chunk_size: Size of each chunk
        
        Yields:
            DataFrame chunks
        """
        offset = 0
        
        while True:
            # Build query
            query, params = self._build_export_query(filters, columns, chunk_size, offset)
            
            # Fetch chunk
            rows = await db_pool.fetch(query, *params)
            
            if not rows:
                break  # No more data
            
            # Convert to DataFrame
            data = [dict(row) for row in rows]
            df = pd.DataFrame(data, columns=columns)
            
            # Process dates
            for col in df.columns:
                if 'date' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            yield df
            
            offset += len(rows)
            
            # Check if this was the last chunk
            if len(rows) < chunk_size:
                break
    
    def _build_export_query(
        self,
        filters: SearchFilters,
        columns: List[str],
        limit: int,
        offset: int
    ) -> tuple[str, List[Any]]:
        """
        Build SQL query for export based on filters.
        
        Args:
            filters: Search filters
            columns: Columns to select
            limit: Query limit
            offset: Query offset
        
        Returns:
            Tuple of (query, parameters)
        """
        # Select columns
        select_cols = ", ".join(columns)
        
        # Build WHERE clause (similar to search endpoint)
        where_clauses = []
        params = []
        param_count = 0
        
        if filters.usdot_number:
            param_count += 1
            where_clauses.append(f"usdot_number = ${param_count}")
            params.append(filters.usdot_number)
        
        if filters.state:
            param_count += 1
            where_clauses.append(f"physical_state = ${param_count}")
            params.append(filters.state)
        
        if filters.entity_type:
            param_count += 1
            where_clauses.append(f"entity_type = ${param_count}")
            params.append(filters.entity_type)
        
        if filters.operating_status:
            param_count += 1
            where_clauses.append(f"operating_status = ${param_count}")
            params.append(filters.operating_status)
        
        if filters.insurance_expiring_days:
            param_count += 1
            where_clauses.append(
                f"liability_insurance_date BETWEEN CURRENT_DATE "
                f"AND CURRENT_DATE + INTERVAL '1 day' * ${param_count}"
            )
            params.append(filters.insurance_expiring_days)
        
        if filters.hazmat_only:
            where_clauses.append("hazmat_flag = TRUE")
        
        # Build query
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        param_count += 1
        limit_param = param_count
        params.append(limit)
        
        param_count += 1
        offset_param = param_count
        params.append(offset)
        
        query = f"""
            SELECT {select_cols}
            FROM carriers
            WHERE {where_sql}
            ORDER BY usdot_number
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        
        return query, params
    
    async def _get_filtered_count(self, filters: SearchFilters) -> int:
        """
        Get count of records matching filters.
        
        Args:
            filters: Search filters
        
        Returns:
            Total count
        """
        # Build WHERE clause
        where_clauses = []
        params = []
        param_count = 0
        
        if filters.usdot_number:
            param_count += 1
            where_clauses.append(f"usdot_number = ${param_count}")
            params.append(filters.usdot_number)
        
        if filters.state:
            param_count += 1
            where_clauses.append(f"physical_state = ${param_count}")
            params.append(filters.state)
        
        # Add other filters...
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"SELECT COUNT(*) FROM carriers WHERE {where_sql}"
        count = await db_pool.fetchval(query, *params)
        
        return count or 0
    
    async def stream_export(
        self,
        request: ExportRequest
    ) -> AsyncIterator[bytes]:
        """
        Stream export data without creating temporary file.
        Useful for direct HTTP streaming responses.
        
        Args:
            request: Export request
        
        Yields:
            Chunks of file data
        """
        columns = request.columns or self.DEFAULT_COLUMNS
        first_chunk = True
        
        async for chunk_df in self._fetch_data_chunks(
            request.filters,
            columns,
            self.CHUNK_SIZE
        ):
            if request.format == "csv":
                # Convert chunk to CSV
                csv_buffer = io.StringIO()
                chunk_df.to_csv(csv_buffer, index=False, header=first_chunk)
                yield csv_buffer.getvalue().encode('utf-8')
                first_chunk = False
            else:
                # Excel streaming is more complex, would need different approach
                raise NotImplementedError("Excel streaming not supported")
    
    def cleanup_old_exports(self, max_age_hours: int = 24):
        """
        Clean up old export files.
        
        Args:
            max_age_hours: Maximum age of files to keep
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for file_path in Path(self.TEMP_DIR).glob("*.csv"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old export: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
        
        for file_path in Path(self.TEMP_DIR).glob("*.xlsx"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old export: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")