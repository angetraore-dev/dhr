"""
Schémas GeoJSON.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GeoJSONPoint(BaseModel):
    """Point GeoJSON — [longitude, latitude]."""

    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float] = Field(
        ..., description="[longitude, latitude]"
    )


class GeoJSONFeature(BaseModel):
    """Feature GeoJSON."""

    type: Literal["Feature"] = "Feature"
    id: str | None = None
    geometry: GeoJSONPoint
    properties: dict[str, Any]


class FeatureCollectionPoints(BaseModel):
    """FeatureCollection GeoJSON."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature]
    meta: dict[str, Any] = Field(default_factory=dict)