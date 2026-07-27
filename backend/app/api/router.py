from fastapi import APIRouter

from app.api.endpoints import alerts, auth, forecast, ingestion, inventory, items, live, ops, orders, planning, routes, shipments, warehouses

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(warehouses.router, prefix='/warehouses', tags=['warehouses'])
api_router.include_router(items.router, prefix='/items', tags=['items'])
api_router.include_router(inventory.router, prefix='/inventory', tags=['inventory'])
api_router.include_router(orders.router, prefix='/orders', tags=['orders'])
api_router.include_router(ingestion.router, prefix='/ingestion', tags=['ingestion'])
api_router.include_router(forecast.router, prefix='/forecast', tags=['forecast'])
api_router.include_router(routes.router, prefix='/routes', tags=['routes'])
api_router.include_router(live.router, prefix='/live', tags=['live'])
api_router.include_router(ops.router, prefix='/ops', tags=['ops'])
api_router.include_router(shipments.router, prefix='/shipments', tags=['shipments'])
api_router.include_router(alerts.router, prefix='/alerts', tags=['alerts'])
api_router.include_router(planning.router, prefix='/planning', tags=['planning'])
