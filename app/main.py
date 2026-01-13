import os
import uvicorn
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from app.database import init_db
from app.services.attio_service import sync_attio_to_postgres

# 1. Configuración de Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AttioWorker")

app = FastAPI()

# 2. Inicializar base de datos al arrancar
# Esto asegura que las tablas se creen antes de recibir el primer webhook
init_db()

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Attio Sync Server is running"}

@app.post("/attio-to-postgres")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Error parseando JSON: {e}")
        return {"status": "error", "reason": "invalid json"}

    events = payload.get("events", [])
    if not events:
        return {"status": "empty payload"}

    event = events[0]
    
    # Seguridad: solo procesar si el actor es miembro del workspace
    if event.get("actor", {}).get("type") != "workspace-member":
        return {"status": "ignored", "reason": "not workspace member"}

    # LOG de recepción
    logger.info(f"📩 Webhook recibido: {event.get('event_type')}")

    # LANZAR PROCESO EN SEGUNDO PLANO
    # Pasamos 'background_tasks' para que el servicio de Attio pueda disparar Airtable después
    background_tasks.add_task(sync_attio_to_postgres, event, background_tasks)
    
    return {"status": "accepted", "detail": "Processing in background"}

if __name__ == "__main__":
    # Configuración para ejecución local
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)