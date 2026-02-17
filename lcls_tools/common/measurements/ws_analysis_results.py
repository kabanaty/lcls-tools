from pydantic import BaseModel, ConfigDict
from lcls_tools.common.measurements.beam_profile import BeamProfileMeasurementResult
from lcls_tools.common.measurements.utils import NDArrayAnnotatedType
from typing import Dict
from lcls_tools.common.measurements.ws_collection_results import (
    WireMeasurementCollectionResult,
)


class DetectorProfileMeasurement(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    values: NDArrayAnnotatedType
    units: str | None = None
    label: str | None = None


class ProfileMeasurement(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    positions: NDArrayAnnotatedType
    detectors: dict[str, DetectorProfileMeasurement]
    profile_indices: NDArrayAnnotatedType


class DetectorFit(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    mean: float
    sigma: float
    amplitude: float
    offset: float
    curve: NDArrayAnnotatedType
    positions: NDArrayAnnotatedType


class FitResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    detectors: Dict[str, DetectorFit]
    collection_results: WireMeasurementCollectionResult
    

class WireMeasurementAnalysisResults(BeamProfileMeasurementResult):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    fit_result: FitResult
    collection_results: WireMeasurementCollectionResult
