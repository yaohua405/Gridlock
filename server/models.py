from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sso_domain: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    projects: Mapped[list["Project"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)
    geom: Mapped[bytes] = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_doc_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    tenant: Mapped[Tenant] = relationship(back_populates="projects")
    project_a_matches: Mapped[list["Match"]] = relationship(back_populates="project_a")
    project_b_matches: Mapped[list["Match"]] = relationship(back_populates="project_b")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_a_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    project_b_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    synergy_score: Mapped[int] = mapped_column(Integer, nullable=False)
    spatial_distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="identified")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    project_a: Mapped[Project] = relationship(foreign_keys=[project_a_id], back_populates="project_a_matches")
    project_b: Mapped[Project] = relationship(foreign_keys=[project_b_id], back_populates="project_b_matches")
    workspace: Mapped["Workspace"] = relationship(back_populates="match")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), nullable=False, unique=True)
    nda_signed_a: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nda_signed_b: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    match: Mapped[Match] = relationship(back_populates="workspace")
