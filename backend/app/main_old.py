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
#     docs_url="/api/docs",
#     redoc_url="/api/redoc",
#     openapi_url="/api/openapi.json"
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


# @app.on_event("startup")
# async def startup_event():
#     """Create first superuser on startup if not exists"""
#     db = next(get_db())
#     try:
#         # Check if superuser already exists
#         superuser = crud_user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
#         if not superuser:
#             # Create superuser
#             user_in = UserCreate(
#                 email=settings.FIRST_SUPERUSER_EMAIL,
#                 full_name="Super Admin",
#                 password=settings.FIRST_SUPERUSER_PASSWORD,
#                 role="super_admin",
#                 is_verified=True
#             )
#             crud_user.create(db, obj_in=user_in)
#             print("✅ Super user created successfully")
#         else:
#             print("✅ Super user already exists")
#     except Exception as e:
#         print(f"❌ Error creating super user: {e}")
#     finally:
#         db.close()


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