from pydantic import BaseModel, ConfigDict
from lcls_tools.common.measurements.utils import NDArrayAnnotatedType
from typing import Any, Optional, Dict, Tuple
from datetime import datetime
from lcls_tools.common.measurements.beam_profile import (
    BeamProfileCollectionResult,
)
import h5py
import numpy as np


class MeasurementMetadata(BaseModel):
    wire_name: str
    area: str
    beampath: str
    detectors: list[str]
    default_detector: str
    scan_ranges: Dict[str, Tuple[int, int]]
    timestamp: datetime
    notes: Optional[str] = None


class DetectorMeasurement(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    values: NDArrayAnnotatedType
    units: str | None = None
    label: str | None = None


class ProfileMeasurement(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    positions: NDArrayAnnotatedType
    detectors: dict[str, DetectorMeasurement]
    profile_idxs: NDArrayAnnotatedType


class WireBPMCollectionResult(BeamProfileCollectionResult):
    """
    Stores the results of a wire beam profile collection.

    Attributes:
        model_config: Allows use of non-standard types
                      like NDArrayAnnotatedType.
        profiles (dict): Dictionary of ProfileMeasurement objects
                         that contains raw data organized by profile.
        metadata (MeasurementMetadata): Metadata information related to
                                        the measurement.

    Inherited Attributes:
        raw_data (dict): Dictionary of device data as np.ndarrays.
                         Keys are device names.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    profiles: Dict[str, ProfileMeasurement]
    raw_data: Dict[str, Any]
    metadata: MeasurementMetadata

    def save_to_h5(self, filepath: str) -> None:
        """
        Save wire beam profile collection results to an HDF5 file.

        The file structure is organized as follows:
        - /metadata: Measurement metadata (wire_name, area, beampath, etc.)
        - /profiles/{profile_name}: Profile measurements
            - positions: Position data for the profile
            - profile_idxs: Profile range indices
            - detectors/{detector_name}: Detector measurement data
                - values: Detector values
                - units: Units of measurement (attribute)
                - label: Measurement label (attribute)
        - /raw_data/{device_name}: Raw detector data

        Parameters
        ----------
        filepath : str
            Path where the HDF5 file will be saved.
        """
        with h5py.File(filepath, "w") as f:
            # Save metadata
            metadata_group = f.create_group("metadata")
            self._save_metadata(metadata_group)

            # Save profiles
            profiles_group = f.create_group("profiles")
            self._save_profiles(profiles_group)

            # Save raw data
            raw_data_group = f.create_group("raw_data")
            self._save_raw_data(raw_data_group)

    def _save_metadata(self, group: h5py.Group) -> None:
        """Save measurement metadata as HDF5 attributes and datasets."""
        meta = self.metadata

        # Store scalar metadata as attributes
        group.attrs["wire_name"] = meta.wire_name
        group.attrs["area"] = meta.area
        group.attrs["beampath"] = meta.beampath
        group.attrs["default_detector"] = meta.default_detector
        group.attrs["timestamp"] = meta.timestamp.isoformat()

        if meta.notes:
            group.attrs["notes"] = meta.notes

        # Store list of detectors
        group.create_dataset(
            "detectors",
            data=np.array(meta.detectors, dtype="S"),
        )

        # Store scan ranges as a structured dataset
        scan_ranges_group = group.create_group("scan_ranges")
        for axis_name, (start, end) in meta.scan_ranges.items():
            scan_ranges_group.attrs[f"{axis_name}_start"] = start
            scan_ranges_group.attrs[f"{axis_name}_end"] = end

    def _save_profiles(self, group: h5py.Group) -> None:
        """Save profile measurement data."""
        for profile_name, profile in self.profiles.items():
            profile_group = group.create_group(profile_name)

            # Save positions
            profile_group.create_dataset("positions", data=profile.positions)

            # Save profile indices
            profile_group.create_dataset("profile_indices", data=profile.profile_indices)

            # Save detector measurements
            detectors_group = profile_group.create_group("detectors")
            for detector_name, measurement in profile.detectors.items():
                detector_group = detectors_group.create_group(detector_name)
                detector_group.create_dataset("values", data=measurement.values)

                if measurement.units:
                    detector_group.attrs["units"] = measurement.units
                if measurement.label:
                    detector_group.attrs["label"] = measurement.label

    def _save_raw_data(self, group: h5py.Group) -> None:
        """Save raw detector and wire data."""
        for device_name, data in self.raw_data.items():
            if isinstance(data, np.ndarray):
                group.create_dataset(device_name, data=data)
            else:
                # Try to convert to numpy array
                try:
                    group.create_dataset(device_name, data=np.array(data))
                except (TypeError, ValueError):
                    # Store as string representation if conversion fails
                    group.attrs[f"{device_name}_unsupported"] = str(data)


def load_from_h5(filepath: str) -> WireBPMCollectionResult:
    """
    Load wire beam profile measurement results from an HDF5 file.

    Parameters
    ----------
    filepath : str
        Path to the HDF5 file to load.

    Returns
    -------
    WireBeamProfileMeasurementResult
        The loaded measurement results.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the file is missing required groups or data.
    """
    with h5py.File(filepath, "r") as f:
        # Load metadata
        metadata = _load_metadata(f["metadata"])

        # Load profiles
        profiles = _load_profiles(f["profiles"])

        # Load raw data
        raw_data = _load_raw_data(f["raw_data"])

    return WireBPMCollectionResult(
        profiles=profiles,
        raw_data=raw_data,
        metadata=metadata,
    )


def _load_metadata(group: h5py.Group) -> MeasurementMetadata:
    """Load measurement metadata from HDF5 group."""
    # Load scalar attributes
    wire_name = group.attrs["wire_name"]
    area = group.attrs["area"]
    beampath = group.attrs["beampath"]
    default_detector = group.attrs["default_detector"]
    timestamp_str = group.attrs["timestamp"]
    timestamp = datetime.fromisoformat(timestamp_str)
    notes = group.attrs.get("notes", None)

    # Load detectors list
    detectors = [d.decode() if isinstance(d, bytes) else d for d in group["detectors"]]

    # Load scan ranges
    scan_ranges = {}
    scan_ranges_group = group["scan_ranges"]
    for axis_name in set(k.rsplit("_", 1)[0] for k in scan_ranges_group.attrs.keys()):
        start = scan_ranges_group.attrs[f"{axis_name}_start"]
        end = scan_ranges_group.attrs[f"{axis_name}_end"]
        scan_ranges[axis_name] = (start, end)

    return MeasurementMetadata(
        wire_name=wire_name,
        area=area,
        beampath=beampath,
        detectors=detectors,
        default_detector=default_detector,
        scan_ranges=scan_ranges,
        timestamp=timestamp,
        notes=notes,
    )


def _load_profiles(group: h5py.Group) -> Dict[str, ProfileMeasurement]:
    """Load profile measurement data from HDF5 group."""
    profiles = {}

    for profile_name in group.keys():
        profile_group = group[profile_name]

        # Load positions and profile indices
        positions = profile_group["positions"][:]
        profile_indices = profile_group["profile_idxs"][:]

        # Load detector measurements
        detectors = {}
        detectors_group = profile_group["detectors"]
        for detector_name in detectors_group.keys():
            detector_group = detectors_group[detector_name]
            values = detector_group["values"][:]
            units = detector_group.attrs.get("units", None)
            label = detector_group.attrs.get("label", None)

            detectors[detector_name] = DetectorMeasurement(
                values=values, units=units, label=label
            )

        profiles[profile_name] = ProfileMeasurement(
            positions=positions,
            detectors=detectors,
            profile_indices=profile_indices,
        )

    return profiles


def _load_raw_data(group: h5py.Group) -> Dict[str, Any]:
    """Load raw detector data from HDF5 group."""
    raw_data = {}

    for device_name in group.keys():
        raw_data[device_name] = group[device_name][:]

    return raw_data
