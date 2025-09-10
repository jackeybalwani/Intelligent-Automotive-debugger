"""
File Utilities
Handles file operations for the application
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional
import aiofiles

logger = logging.getLogger(__name__)

async def save_uploaded_file(file) -> str:
    """
    Save uploaded file to disk
    """
    try:
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()
        file_extension = Path(file.filename).suffix
        unique_filename = f"{file_hash}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"File saved: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise

def get_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of file
    """
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return ""
