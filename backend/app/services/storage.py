import os
import hashlib
import zipfile
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings

class LocalObjectStore:
    def __init__(self):
        self.storage_dir = settings.STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        return os.path.basename(filename)

    async def save_upload_file(self, upload_file: UploadFile, case_id: str) -> dict:
        """
        Saves the file in chunks, calculates SHA-256, and extracts if ZIP.
        """
        filename = self._sanitize_filename(upload_file.filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in [".raw", ".dmp", ".mem", ".zip"]:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        case_dir = os.path.join(self.storage_dir, case_id)
        os.makedirs(case_dir, exist_ok=True)
        
        file_path = os.path.join(case_dir, filename)
        
        sha256_hash = hashlib.sha256()
        file_size = 0
        
        # Stream file to disk and calculate hash
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await upload_file.read(1024 * 1024): # 1MB chunks
                file_size += len(chunk)
                sha256_hash.update(chunk)
                await out_file.write(chunk)
                
        hash_hex = sha256_hash.hexdigest()
        
        final_target = file_path
        
        # If zip, safely extract
        if ext == ".zip":
            final_target = self._safe_extract_zip(file_path, case_dir)
            
        return {
            "filename": filename,
            "file_size": file_size,
            "sha256": hash_hex,
            "storage_path": final_target
        }
        
    def _safe_extract_zip(self, zip_path: str, extract_dir: str) -> str:
        """
        Extracts zip file and prevents path traversal. 
        Returns path to the extracted dump file.
        """
        extracted_dump = None
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                # Prevent path traversal
                if member.filename.startswith('/') or '..' in member.filename:
                    continue
                
                ext = os.path.splitext(member.filename)[1].lower()
                if ext in [".raw", ".dmp", ".mem"]:
                    zf.extract(member, extract_dir)
                    extracted_dump = os.path.join(extract_dir, member.filename)
                    break # Extract the first valid dump we find
                    
        if not extracted_dump:
            raise HTTPException(status_code=400, detail="No valid memory dump found in ZIP")
            
        return extracted_dump
