from __future__ import annotations

import os
from datetime import date
from typing import Any, Literal
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from database import SessionLocal

app = FastAPI(
    title="Gridlock Platform API",
    version="0.1.0",
    description="Geo-enabled utility coordination platform for project ingestion, map visualization, and match alerts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class ProjectIngestionItem(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    geojson_boundary: GeoJSONPolygon


class ProjectIngestionRequest(BaseModel):
    tenant_id: str
    source_document_id: str
    projects: list[ProjectIngestionItem]


class PendingProject(BaseModel):
    id: str
    tenant_name: str
    name: str
    type: str
    status: str
    start_date: str
    end_date: str
    source_document_id: str


document_store: dict[str, dict[str, Any]] = {}


def _extract_lines_from_textract(response: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for block in response.get("Blocks", []):
        if block.get("BlockType") == "LINE" and block.get("Text"):
            lines.append(block["Text"].strip())
    return [line for line in lines if line]


def _build_demo_extraction(filename: str, pages_count: int = 1) -> dict[str, Any]:
    demo_text = (
        f"Demo extraction for {filename}: This PDF was uploaded to Gridlock and queued for Textract processing. "
        "The document contains a utility project summary, planning window, and geographic boundary details for review. "
        "Please configure AWS credentials and a valid Textract-enabled environment to process real PDFs."
    )
    return {
        "status": "demo",
        "filename": filename,
        "pages": pages_count,
        "text": demo_text,
        "summary": demo_text[:220],
        "message": "Textract is not configured in this environment; demo output was generated instead.",
    }


def _analyze_with_textract(pdf_bytes: bytes, filename: str) -> dict[str, Any]:
    enabled = os.getenv("AWS_TEXTRACT_ENABLED", "true").lower() not in {"0", "false", "no"}
    if not enabled:
        return _build_demo_extraction(filename)

    try:
        client = boto3.client(
            "textract",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        response = client.analyze_document(
            Document={"Bytes": pdf_bytes},
            FeatureTypes=["TABLES", "FORMS"],
        )
    except (NoCredentialsError, BotoCoreError, ClientError):
        if os.getenv("AWS_TEXTRACT_DEMO_MODE", "true").lower() not in {"0", "false", "no"}:
            return _build_demo_extraction(filename)
        raise HTTPException(status_code=503, detail="Amazon Textract is not configured for this deployment.")

    lines = _extract_lines_from_textract(response)
    text = "\n".join(lines) if lines else "No text blocks were returned by Amazon Textract."
    summary = text[:500].strip()
    return {
        "status": "success",
        "filename": filename,
        "pages": max(1, len(response.get("DocumentMetadata", {}).get("Pages", [1]))),
        "text": text,
        "summary": summary,
        "message": "Amazon Textract successfully extracted the document content.",
    }


project_store: list[dict[str, Any]] = [
    {
        "id": "p_8841",
        "tenant_id": "tenant_a",
        "tenant_name": "Utility A",
        "name": "Line 24 Rebuild",
        "project_type": "transmission",
        "start_date": "2027-04-01",
        "end_date": "2027-11-01",
        "geom": {
            "type": "Polygon",
            "coordinates": [
                [[-75.16, 39.94], [-75.12, 39.95], [-75.10, 39.90], [-75.15, 39.88], [-75.16, 39.94]]
            ],
        },
        "source_document_id": "doc_9912",
    },
    {
        "id": "p_3321",
        "tenant_id": "tenant_b",
        "tenant_name": "Utility B",
        "name": "Substation Alpha Expansion",
        "project_type": "substation",
        "start_date": "2027-07-01",
        "end_date": "2027-12-15",
        "geom": {
            "type": "Polygon",
            "coordinates": [
                [[-75.14, 39.92], [-75.09, 39.93], [-75.08, 39.88], [-75.12, 39.87], [-75.14, 39.92]]
            ],
        },
        "source_document_id": "doc_2143",
    },
    {
        "id": "p_1125",
        "tenant_id": "tenant_a",
        "tenant_name": "Utility A",
        "name": "ROW Clearing South",
        "project_type": "right_of_way",
        "start_date": "2027-08-01",
        "end_date": "2027-10-31",
        "geom": {
            "type": "Polygon",
            "coordinates": [
                [[-75.18, 39.89], [-75.14, 39.89], [-75.13, 39.84], [-75.17, 39.83], [-75.18, 39.89]]
            ],
        },
        "source_document_id": "doc_1954",
    },
]

match_store = [
    {
        "match_id": "m_102",
        "synergy_score": 85,
        "my_project": {"id": "p_8841", "name": "Line 24 Rebuild"},
        "external_project": {"id": "p_3321", "tenant_name": "Utility B", "name": "Substation Alpha Expansion"},
        "temporal_overlap_months": 4,
        "status": "identified",
    },
    {
        "match_id": "m_204",
        "synergy_score": 78,
        "my_project": {"id": "p_8841", "name": "Line 24 Rebuild"},
        "external_project": {"id": "p_1125", "tenant_name": "Utility A", "name": "ROW Clearing South"},
        "temporal_overlap_months": 3,
        "status": "in_discussion",
    },
]


@app.get("/health")
def healthcheck() -> dict[str, Any]:
    db_status = "unknown"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"

    return {"status": "ok", "service": "gridlock-api", "database": db_status}


@app.get("/api/v1/projects/pending")
def get_pending_projects() -> list[PendingProject]:
    return [
        PendingProject(
            id=item["id"],
            tenant_name=item["tenant_name"],
            name=item["name"],
            type=item["project_type"],
            status="pending_validation",
            start_date=item["start_date"],
            end_date=item["end_date"],
            source_document_id=item["source_document_id"],
        )
        for item in project_store
    ]


@app.post("/api/v1/projects/ingest")
def ingest_projects(payload: ProjectIngestionRequest) -> dict[str, Any]:
    inserted: list[str] = []
    for item in payload.projects:
        if item.end_date < item.start_date:
            raise HTTPException(status_code=400, detail=f"Project {item.name} has an invalid date range.")

        project = {
            "id": f"p_{uuid4().hex[:8]}",
            "tenant_id": payload.tenant_id,
            "tenant_name": "Utility Tenant",
            "name": item.name,
            "project_type": item.type,
            "start_date": item.start_date.isoformat(),
            "end_date": item.end_date.isoformat(),
            "geom": item.geojson_boundary.model_dump(),
            "source_document_id": payload.source_document_id,
        }
        project_store.append(project)
        inserted.append(project["id"])

    return {"message": "Projects ingested", "count": len(inserted), "project_ids": inserted}


@app.get("/api/v1/projects/map")
def get_map_projects(
    min_lon: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lon: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    year: int = Query(..., ge=2020, le=2100),
) -> dict[str, Any]:
    features = []
    for project in project_store:
        coords = project["geom"]["coordinates"][0]
        all_lons = [point[0] for point in coords]
        all_lats = [point[1] for point in coords]
        if not (
            min_lon <= min(all_lons) and max_lon >= max(all_lons)
            and min_lat <= min(all_lats) and max_lat >= max(all_lats)
        ):
            continue

        project_year = int(project["start_date"][:4])
        if project_year != year:
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": project["geom"],
                "properties": {
                    "project_id": project["id"],
                    "name": project["name"],
                    "tenant_name": project["tenant_name"],
                    "match_count": 1 if project["id"] in {"p_8841", "p_3321"} else 0,
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


@app.get("/api/v1/matches/alerts")
def get_match_alerts() -> dict[str, list[dict[str, Any]]]:
    return {"data": match_store}


@app.post("/api/v1/documents/analyze")
async def analyze_uploaded_document(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    document_id = f"doc_{uuid4().hex[:10]}"
    extraction = _analyze_with_textract(pdf_bytes, file.filename)
    document_store[document_id] = {
        "document_id": document_id,
        "filename": file.filename,
        "status": extraction["status"],
        "pages": extraction["pages"],
        "text": extraction["text"],
        "summary": extraction["summary"],
        "message": extraction["message"],
    }

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": extraction["status"],
        "pages": extraction["pages"],
        "text": extraction["text"],
        "summary": extraction["summary"],
        "message": extraction["message"],
    }


@app.get("/api/v1/documents/{document_id}")
def get_document_analysis(document_id: str) -> dict[str, Any]:
    document = document_store.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document
