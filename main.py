from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.routes import router

from app.database.synchronisation import setup_sync
import logging
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="RecMooc4All API", version="2.0")

    # Middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Routes
    app.include_router(router)

    # Startup events
    @app.on_event("startup")
    async def startup_event():
        try:
            setup_sync()
            logger.info("✅ Database synchronization configured")
            logger.info("Registered routes: %s", [route.path for route in app.routes])
        except Exception as e:
            logger.error(f"❌ Error during database synchronization: {e}", exc_info=True)
            raise e

    return app


app = create_app()
