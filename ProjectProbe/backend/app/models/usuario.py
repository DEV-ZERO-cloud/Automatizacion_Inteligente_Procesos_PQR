from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class RolEnum(str, enum.Enum):
    USUARIO = "usuario"
    SUPERVISOR = "supervisor"
    OPERADOR = "operador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    rol = Column(SQLEnum(RolEnum), default=RolEnum.USUARIO, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    pqrs_creadas = relationship("PQR", back_populates="usuario", foreign_keys="PQR.usuario_id")
    pqrs_asignadas = relationship("PQR", back_populates="supervisor", foreign_keys="PQR.supervisor_id")
    historial = relationship("Historial", back_populates="usuario")
