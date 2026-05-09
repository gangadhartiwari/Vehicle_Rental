"""Aggregates all v1 endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, partners, vehicles, bookings, ratings, admin, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(partners.router)
api_router.include_router(vehicles.partner_router)
api_router.include_router(vehicles.public_router)
api_router.include_router(bookings.router)
api_router.include_router(bookings.partner_bookings)
api_router.include_router(ratings.router)
api_router.include_router(admin.router)
