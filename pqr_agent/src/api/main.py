import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router, embedding_generator, rule_engine
from dotenv import load_dotenv
load_dotenv()

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ejecuta lógica de arranque y apagado."""
    logger.info("startup", rules=len(rule_engine.rules), model="loaded")
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Clasificador Inteligente de PQR",
    description="API para clasificación automática de Peticiones, Quejas y Reclamos.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")