import os
import uvicorn
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from database import init_db
from services.attio_service import sync_attio_to_postgres

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AttioWorker")

app = FastAPI()

@app.post("/attio-to-postgres")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except:
        return {"status": "error", "reason": "invalid json"}

    events = payload.get("events", [])
    if not events:
        return {"status": "empty payload"}

    event = events[0]
    
    # Seguridad básica
    if event.get("actor", {}).get("type") != "workspace-member":
        return {"status": "ignored"}

    # Llamamos al servicio de forma asíncrona en segundo plano
    background_tasks.add_task(sync_attio_to_postgres, event)
    
    return {"status": "accepted"}

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)