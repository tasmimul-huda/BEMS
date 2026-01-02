from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database import engine, Base, get_db
from app.api.v1.api import api_router
from app.models import user, geography, candidate, election
from app.crud.user import crud_user
from app.schemas.user import UserCreate

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    print("🚀 Starting up BEMS API...")
    
    # Create superuser on startup
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Check if superuser exists
        superuser = crud_user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
        
        if not superuser:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER_EMAIL,
                full_name="Super Admin",
                password=settings.FIRST_SUPERUSER_PASSWORD,
                role="super_admin",
                is_verified=True
            )
            crud_user.create(db, obj_in=user_in)
            print("✅ Superuser created successfully")
        else:
            print("✅ Superuser already exists")
            
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
    finally:
        # Properly close the generator
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    print("✅ BEMS API startup completed")
    yield  # Continue running app
    
    # Shutdown (if needed)
    print("🛑 Shutting down BEMS API...")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/api/docs",  # Enable Swagger UI
    redoc_url="/api/redoc",  # Enable ReDoc
    openapi_url="/api/openapi.json",  # OpenAPI JSON
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Bangladesh Election Monitoring System API",
        "version": settings.VERSION,
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bems-api"}

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )
    
    # Customize OpenAPI schema
    openapi_schema["info"]["contact"] = {
        "name": "BEMS Team",
        "email": "support@bems.gov.bd"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(
        "run:app",  # Changed from "app.main:app" to "run:app"
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )








# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.openapi.utils import get_openapi
# from sqlalchemy.orm import Session
# import uvicorn

# from app.core.config import settings
# from app.database import engine, Base, get_db
# from app.api.v1.api import api_router
# from app.models import user, geography, candidate, election
# from app.crud.user import crud_user
# from app.schemas.user import UserCreate

# # Create database tables
# Base.metadata.create_all(bind=engine)

# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     version=settings.VERSION,
#     description=settings.DESCRIPTION,
#     # docs_url="/api/docs",
#     # redoc_url="/api/redoc",
#     # openapi_url="/api/openapi.json"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include API router
# app.include_router(api_router, prefix="/api/v1")


# # @app.on_event("startup")
# # async def startup_event():
# #     """Create first superuser on startup if not exists"""
# #     db = next(get_db())
# #     try:
# #         # Check if superuser already exists
# #         superuser = crud_user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
# #         if not superuser:
# #             # Create superuser
# #             user_in = UserCreate(
# #                 email=settings.FIRST_SUPERUSER_EMAIL,
# #                 full_name="Super Admin",
# #                 password=settings.FIRST_SUPERUSER_PASSWORD,
# #                 role="super_admin",
# #                 is_verified=True
# #             )
# #             crud_user.create(db, obj_in=user_in)
# #             print("✅ Super user created successfully")
# #         else:
# #             print("✅ Super user already exists")
# #     except Exception as e:
# #         print(f"❌ Error creating super user: {e}")
# #     finally:
# #         db.close()

# # from fastapi import FastAPI
# from contextlib import asynccontextmanager

# @asynccontextmanager
# async def lifespan(app: FastAPI):

#     # open DB session using get_db generator
#     db_gen = get_db()
#     db = next(db_gen)

#     try:
#         # Check if superuser exists
#         superuser = crud_user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)

#         if not superuser:
#             # bcrypt 72-byte fix
#             password = settings.FIRST_SUPERUSER_PASSWORD

#             user_in = UserCreate(
#                 email=settings.FIRST_SUPERUSER_EMAIL,
#                 full_name="Super Admin",
#                 password=password,
#                 role="super_admin",
#                 is_verified=True
#             )
#             crud_user.create(db, obj_in=user_in)
#             print("✅ Superuser created successfully")
#         else:
#             print("✅ Superuser already exists")

#     except Exception as e:
#         print(f"❌ Error creating superuser: {e}")

#     finally:
#         # Properly close the generator so db.close() runs
#         try:
#             next(db_gen)
#         except StopIteration:
#             pass

#     yield   # Continue running app

# app = FastAPI(lifespan=lifespan)
# app = FastAPI(lifespan=lifespan)



# @app.get("/")
# async def root():
#     return {
#         "message": "Bangladesh Election Monitoring System API",
#         "version": settings.VERSION,
#         "docs": "/api/docs",
#         "health": "/api/v1/health"
#     }


# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "service": "bems-api"}


# # Custom OpenAPI schema
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
    
#     openapi_schema = get_openapi(
#         title=settings.PROJECT_NAME,
#         version=settings.VERSION,
#         description=settings.DESCRIPTION,
#         routes=app.routes,
#     )
    
#     # Customize OpenAPI schema
#     openapi_schema["info"]["contact"] = {
#         "name": "BEMS Team",
#         "email": "support@bems.gov.bd"
#     }
    
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema


# # app.openapi = custom_openapi

# # if __name__ == "__main__":
# #     uvicorn.run(
# #         "app.main:app",
# #         host="0.0.0.0",
# #         port=8000,
# #         reload=True if settings.ENVIRONMENT == "development" else False
# #     )

# if __name__ == "__main__":
#     uvicorn.run(
#         "run:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True if settings.ENVIRONMENT == "development" else False
#     )