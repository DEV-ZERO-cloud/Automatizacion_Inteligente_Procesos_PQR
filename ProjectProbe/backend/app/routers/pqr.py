from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.usuario import Usuario, RolEnum
from ..models.pqr import PQR, EstadoPQREnum
from ..models.historial import Historial
from ..models.archivo import Archivo
from ..schemas.pqr import (
    PQRCreate, PQRResponse, PQRListResponse, PQRDetalleResponse,
    PQRUpdateEstado, PQRAsignar, EstadisticaResponse, HistorialResponse
)
from ..services.email_service import (
    send_email,
    get_email_template_pqr_creada,
    get_email_template_pqr_actualizada,
    get_email_template_nuevo_comentario
)
from ..services.file_service import save_file

router = APIRouter(prefix="/pqr", tags=["PQR"])


@router.post("", response_model=PQRResponse, status_code=status.HTTP_201_CREATED)
async def crear_pqr(
    pqr_data: PQRCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.USUARIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios pueden crear PQR's"
        )
    
    db_pqr = PQR(
        titulo=pqr_data.titulo,
        descripcion=pqr_data.descripcion,
        tipo=pqr_data.tipo,
        usuario_id=current_user.id
    )
    db.add(db_pqr)
    db.commit()
    db.refresh(db_pqr)
    
    historial = Historial(
        pqr_id=db_pqr.id,
        usuario_id=current_user.id,
        accion="PQR creada",
        comentario=f"Se creó la PQR con tipo {pqr_data.tipo.value}"
    )
    db.add(historial)
    db.commit()
    
    subject, html = get_email_template_pqr_creada(db_pqr.id, db_pqr.titulo)
    await send_email(current_user.email, subject, html)
    
    db.refresh(db_pqr)
    return db_pqr


@router.post("/{pqr_id}/archivos", response_model=PQRResponse)
async def subir_archivos(
    pqr_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    pqr = db.query(PQR).filter(PQR.id == pqr_id).first()
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    
    if current_user.rol == RolEnum.USUARIO and pqr.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    for file in files:
        file_data = await save_file(file, pqr_id)
        db_archivo = Archivo(
            pqr_id=pqr_id,
            filename=file_data["filename"],
            filepath=file_data["filepath"],
            mimetype=file_data["mimetype"]
        )
        db.add(db_archivo)
    
    db.commit()
    db.refresh(pqr)
    return pqr


@router.get("/mis-pqrs", response_model=List[PQRListResponse])
async def mis_pqrs(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.USUARIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios pueden ver sus PQR's"
        )
    
    pqrs = db.query(PQR).filter(PQR.usuario_id == current_user.id).order_by(PQR.created_at.desc()).all()
    
    result = []
    for pqr in pqrs:
        result.append(PQRListResponse(
            id=pqr.id,
            titulo=pqr.titulo,
            tipo=pqr.tipo,
            estado=pqr.estado,
            created_at=pqr.created_at,
            usuario_nombre=current_user.nombre,
            supervisor_nombre=pqr.supervisor.nombre if pqr.supervisor else None
        ))
    return result


@router.get("/asignadas", response_model=List[PQRListResponse])
async def pqrs_asignadas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.SUPERVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores pueden ver PQR's asignadas"
        )
    
    pqrs = db.query(PQR).filter(
        PQR.supervisor_id == current_user.id
    ).order_by(PQR.created_at.desc()).all()
    
    result = []
    for pqr in pqrs:
        result.append(PQRListResponse(
            id=pqr.id,
            titulo=pqr.titulo,
            tipo=pqr.tipo,
            estado=pqr.estado,
            created_at=pqr.created_at,
            usuario_nombre=pqr.usuario.nombre,
            supervisor_nombre=current_user.nombre
        ))
    return result


@router.get("/todas", response_model=List[PQRListResponse])
async def todas_pqrs(
    estado: str = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.OPERADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo operadores pueden ver todas las PQR's"
        )
    
    query = db.query(PQR)
    
    if estado:
        query = query.filter(PQR.estado == estado)
    if tipo:
        query = query.filter(PQR.tipo == tipo)
    
    pqrs = query.order_by(PQR.created_at.desc()).all()
    
    result = []
    for pqr in pqrs:
        result.append(PQRListResponse(
            id=pqr.id,
            titulo=pqr.titulo,
            tipo=pqr.tipo,
            estado=pqr.estado,
            created_at=pqr.created_at,
            usuario_nombre=pqr.usuario.nombre,
            supervisor_nombre=pqr.supervisor.nombre if pqr.supervisor else None
        ))
    return result


@router.get("/{pqr_id}", response_model=PQRDetalleResponse)
async def detalle_pqr(
    pqr_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    pqr = db.query(PQR).filter(PQR.id == pqr_id).first()
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    
    if current_user.rol == RolEnum.USUARIO and pqr.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    if current_user.rol == RolEnum.SUPERVISOR and pqr.supervisor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    historial_list = []
    for h in pqr.historial:
        historial_list.append(HistorialResponse(
            id=h.id,
            accion=h.accion,
            comentario=h.comentario,
            created_at=h.created_at,
            usuario_nombre=h.usuario.nombre
        ))
    
    return PQRDetalleResponse(
        id=pqr.id,
        titulo=pqr.titulo,
        descripcion=pqr.descripcion,
        tipo=pqr.tipo,
        estado=pqr.estado,
        usuario_id=pqr.usuario_id,
        supervisor_id=pqr.supervisor_id,
        created_at=pqr.created_at,
        updated_at=pqr.updated_at,
        usuario_nombre=pqr.usuario.nombre,
        supervisor_nombre=pqr.supervisor.nombre if pqr.supervisor else None,
        archivos=pqr.archivos,
        historial=historial_list
    )


@router.put("/{pqr_id}/estado", response_model=PQRResponse)
async def actualizar_estado(
    pqr_id: int,
    data: PQRUpdateEstado,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.SUPERVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores pueden actualizar el estado"
        )
    
    pqr = db.query(PQR).filter(PQR.id == pqr_id).first()
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    
    if pqr.supervisor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Esta PQR no está asignada a ti")
    
    old_estado = pqr.estado
    pqr.estado = data.estado
    pqr.updated_at = datetime.utcnow()
    
    historial = Historial(
        pqr_id=pqr.id,
        usuario_id=current_user.id,
        accion=f"Estado actualizado de {old_estado.value} a {data.estado.value}",
        comentario=data.comentario
    )
    db.add(historial)
    db.commit()
    db.refresh(pqr)
    
    usuario = pqr.usuario
    subject, html = get_email_template_pqr_actualizada(pqr.id, pqr.titulo, data.estado.value)
    await send_email(usuario.email, subject, html)
    
    return pqr


@router.put("/{pqr_id}/comentario", response_model=HistorialResponse)
async def agregar_comentario(
    pqr_id: int,
    comentario: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.SUPERVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores pueden agregar comentarios"
        )
    
    pqr = db.query(PQR).filter(PQR.id == pqr_id).first()
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    
    historial = Historial(
        pqr_id=pqr.id,
        usuario_id=current_user.id,
        accion="Nuevo comentario",
        comentario=comentario
    )
    db.add(historial)
    db.commit()
    db.refresh(historial)
    
    usuario = pqr.usuario
    subject, html = get_email_template_nuevo_comentario(pqr.id, pqr.titulo, comentario)
    await send_email(usuario.email, subject, html)
    
    return HistorialResponse(
        id=historial.id,
        accion=historial.accion,
        comentario=historial.comentario,
        created_at=historial.created_at,
        usuario_nombre=current_user.nombre
    )


@router.put("/{pqr_id}/asignar", response_model=PQRResponse)
async def asignar_supervisor(
    pqr_id: int,
    data: PQRAsignar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.OPERADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo operadores pueden asignar supervisores"
        )
    
    pqr = db.query(PQR).filter(PQR.id == pqr_id).first()
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    
    supervisor = db.query(Usuario).filter(
        Usuario.id == data.supervisor_id,
        Usuario.rol == RolEnum.SUPERVISOR
    ).first()
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    
    pqr.supervisor_id = data.supervisor_id
    pqr.updated_at = datetime.utcnow()
    
    historial = Historial(
        pqr_id=pqr.id,
        usuario_id=current_user.id,
        accion="Supervisor asignado",
        comentario=f"Se asignó a {supervisor.nombre} como supervisor"
    )
    db.add(historial)
    db.commit()
    db.refresh(pqr)
    
    return pqr


@router.get("/estadisticas/dashboard", response_model=EstadisticaResponse)
async def estadisticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != RolEnum.OPERADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo operadores pueden ver estadísticas"
        )
    
    total = db.query(PQR).count()
    creados = db.query(PQR).filter(PQR.estado == EstadoPQREnum.CREADO).count()
    en_proceso = db.query(PQR).filter(PQR.estado == EstadoPQREnum.EN_PROCESO).count()
    resueltos = db.query(PQR).filter(PQR.estado == EstadoPQREnum.RESUELTO).count()
    
    pqrs = db.query(PQR).all()
    por_tipo = {"peticion": 0, "queja": 0, "reclamo": 0}
    for pqr in pqrs:
        por_tipo[pqr.tipo.value] = por_tipo.get(pqr.tipo.value, 0) + 1
    
    return EstadisticaResponse(
        total=total,
        creados=creados,
        en_proceso=en_proceso,
        resueltos=resueltos,
        por_tipo=por_tipo
    )
