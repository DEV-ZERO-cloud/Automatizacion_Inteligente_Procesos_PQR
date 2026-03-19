import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from ..core.config import settings


ALLOWED_EXTENSIONS = set(settings.ALLOWED_EXTENSIONS)
MAX_FILE_SIZE = settings.MAX_FILE_SIZE


def validate_file(file: UploadFile) -> bool:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    
    extension = file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Extensión no permitida. Permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return True


async def save_file(file: UploadFile, pqr_id: int) -> dict:
    validate_file(file)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    file_extension = file.filename.split(".")[-1].lower()
    unique_filename = f"{pqr_id}_{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    file_content = await file.read()
    
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    return {
        "filename": file.filename,
        "filepath": file_path,
        "mimetype": file.content_type
    }


async def delete_file(filepath: str) -> bool:
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception:
        return False


def get_file_url(filepath: str, base_url: str = "") -> str:
    filename = os.path.basename(filepath)
    return f"{base_url}/uploads/{filename}"
