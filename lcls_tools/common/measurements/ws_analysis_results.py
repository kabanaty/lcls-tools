from pydantic import BaseModel, ConfigDict
from lcls_tools.common.measurements.beam_profile import BeamProfileMeasurementResult
from lcls_tools.common.measurements.utils import NDArrayAnnotatedType
from typing import Dict
from lcls_tools.common.measurements.ws_collection_results import(
        WireBPMCollectionResult,
)


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
    collection_results: WireBPMCollectionResult


class WireBPMAnalysisResults(BeamProfileMeasurementResult):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    fit_result: FitResult
    collection_results: WireBPMCollectionResult
