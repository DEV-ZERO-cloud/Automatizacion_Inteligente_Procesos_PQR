from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class TipoPQREnum(str, enum.Enum):
    PETICION = "peticion"
    QUEJA = "queja"
    RECLAMO = "reclamo"


class EstadoPQREnum(str, enum.Enum):
    CREADO = "creado"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"


class PQR(Base):
    __tablename__ = "pqrs"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo = Column(SQLEnum(TipoPQREnum), default=TipoPQREnum.PETICION)
    estado = Column(SQLEnum(EstadoPQREnum), default=EstadoPQREnum.CREADO)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    supervisor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="pqrs_creadas", foreign_keys=[usuario_id])
    supervisor = relationship("Usuario", back_populates="pqrs_asignadas", foreign_keys=[supervisor_id])
    historial = relationship("Historial", back_populates="pqr", cascade="all, delete-orphan")
    archivos = relationship("Archivo", back_populates="pqr", cascade="all, delete-orphan")
