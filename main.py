"""
Main FastAPI application for PPT generation. This module initializes the application,
sets up database connections, and includes routes for generating PowerPoint presentations.
"""
from fastapi import FastAPI
from app.routes.routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="RecMooc4All",
    description="API for Course recommendation , BASED ON PROVIDED USER QUERY.",
    version="2.0.0",
    root_path="/api/v2",
)

app.include_router(router, prefix="")