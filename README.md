### Sperry Tech - The Gridlock Challenge

How to run the project:

Open two terminals in the workspace root, the run these commands:
1. start the backend:


cd E:\Gridlock\server
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8000

This starts the FastAPI API on:
http://localhost:8000

2) Start the frontend:

   
cd E:\Gridlock\client
npm install
npm run dev -- --host 0.0.0.0

This starts the React app on:
http://localhost:5173


Open the app, visit: http://localhost:5173

If you want the full stack with Docker
From the workspace root:
cd E:\Gridlock
docker-compose up --build


This starts:

PostGIS database,
Redis,
FastAPI backend,
The frontend still runs separately with Vite for local development, which is the usual setup for this repo.

Quick health check
You can confirm the backend is working by visiting:

http://localhost:8000/health
Expected response:
{"status":"ok","service":"gridlock-api"}
