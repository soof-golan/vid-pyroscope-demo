import asyncio
import hashlib

from fastapi import FastAPI
import asyncpg
from fastapi.middleware.cors import CORSMiddleware


import pyroscope

pyroscope.configure(
    application_name="some_service",
    server_address="http://localhost:4040",
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/blob/")
async def create_blob(data: str):
    with pyroscope.tag_wrapper({"endpoint": "create_blob"}):
        db = await asyncpg.connect("postgresql://root@localhost:26257/defaultdb?sslmode=disable")
        blob = hashlib.sha256(data.encode("utf-8")).hexdigest().encode("utf-8")
        _id = await db.fetch("INSERT INTO blobs (data) VALUES ($1) RETURNING id", blob)
        await db.close()
        return {"id": _id[0]["id"]}


async def seed():
    # CockroachDB connection string
    db = await asyncpg.connect("postgresql://root@localhost:26257/defaultdb?sslmode=disable")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS blobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            data BYTES NOT NULL
        );
    """)
    await db.close()


if __name__ == "__main__":
    import uvicorn

    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
    uvicorn.run(app, host="0.0.0.0")
