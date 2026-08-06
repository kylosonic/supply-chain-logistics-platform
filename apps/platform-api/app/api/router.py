from fastapi import APIRouter

from app.api.endpoints import (
    activation,
    alerts,
    auth,
    billing,
    feedback,
    forecast,
    ingestion,
    inventory,
    invoices,
    items,
    live,
    notifications,
    ops,
    orders,
    planning,
    providers,
    receipt_reversals,
    receipts,
    routes,
    shipments,
    subscriptions,
    warehouses,
    weather,
)

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
api_router.include_router(subscriptions.router, prefix='/subscriptions', tags=['subscriptions'])
api_router.include_router(providers.router, prefix='/providers', tags=['providers'])
api_router.include_router(weather.router, prefix='/weather', tags=['weather'])
api_router.include_router(invoices.router, prefix='/invoices', tags=['invoices'])
api_router.include_router(billing.router, prefix='/billing', tags=['billing'])
api_router.include_router(notifications.router, prefix='/notifications', tags=['notifications'])
api_router.include_router(feedback.router, prefix='/feedback', tags=['feedback'])
api_router.include_router(receipts.router, prefix='/receipts', tags=['receipts'])
# Reversals must register AFTER receipts so the static suffixes
# (/audit, /trusted-payers) are never shadowed by a {receipt_id} pattern.
api_router.include_router(receipt_reversals.router, prefix='/receipts', tags=['receipts'])
api_router.include_router(activation.router, prefix='/activation', tags=['activation'])
