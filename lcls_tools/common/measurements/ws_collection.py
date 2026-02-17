from lcls_tools.common.measurements.beam_profile import BeamProfileMeasurement
from lcls_tools.common.devices.wire import Wire
import logging
from pathlib import Path
from typing import Optional
from lcls_tools.common.devices.reader import create_lblm, create_pmt
import time
from datetime import datetime
from pydantic import model_validator
from lcls_tools.common.measurements.tmit_loss import TMITLoss
from lcls_tools.common.measurements.ws_collection_results import (
    WireMeasurementCollectionResult,
    ProfileMeasurement,
    DetectorMeasurement,
    MeasurementMetadata,
)
import yaml
import numpy as np
from typing_extensions import Self
from lcls_tools.common.measurements.buffer_reservation import reserve_buffer
from lcls_tools.common.measurements.utils import (
    collect_with_size_check,
)
from lcls_tools.common.logger.file_logger import custom_logger


class WireMeasurementCollection(BeamProfileMeasurement):
    """
    Performs a wire scan measurement and splits raw data
    into beam profiles.

    Attributes:
        name (str): Scan object name required by Measurement class.
        my_wire (Wire): Wire device used to perform the scan.
        beampath (str): Beamline path identifier for buffer and device
                        selection.
        my_buffer (edef.BSABuffer): edef buffer object to manage data
                                    acquisition.
        devices (dict): Holds all slac-tools device objects associated
                        with this measurement (wires, detectors, bpms, etc).
        data (dict): Raw data object for all devices defined above.
        profile_measurements (dict): Collected data organized by profile.
        logger (logging.Logger): Object for log file management.
    """

    name: str = "Wire Beam Profile Measurement"
    beam_profile_device: Wire
    beampath: str

    # Extra fields to be set after validation
    # Must be optional to start
    my_buffer: Optional[object] = None
    devices: Optional[dict] = None
    detectors: Optional[list] = None
    data: Optional[dict] = None
    profiles: Optional[dict] = None
    logger: Optional[logging.Logger] = None

    # alias so beam_profile_device can also be accessed with name my_wire
    @property
    def my_wire(self) -> Wire:
        return self.beam_profile_device

    @my_wire.setter
    def my_wire(self, value):
        self.beam_profile_device = value

    @model_validator(mode="after")
    def run_setup(self) -> Self:
        self.logger = self._logger_config()

        # Reserve BSA buffer
        self.my_buffer = self._reserve_buffer()

        # Get list of detector names from wire metadata
        self.detectors = [d.split(":")[0] for d in self.my_wire.metadata.detectors]

        # Generate dictionary of all requried lcls-tools device objects
        self.devices = self.create_device_dictionary()
        return self

    def measure(self) -> WireMeasurementCollectionResult:
        """
        Perform a wire scan measurement and organize data into beam profiles.

        Executes a complete wire scan: reserves a BSA buffer, commands the wire
        to motion, collects synchronized detector data across all profiles,
        separates the raw data by profile (x, y, u), and returns organized
        measurements without fitting or post-processing.

        Returns
        -------
        WireBeamProfileMeasurementResult
            Raw measurement data organized by profile, including:
            - profiles: Dict of ProfileMeasurement objects (positions and detector values per profile)
            - raw_data: Complete raw buffered data from all devices
            - metadata: Measurement timestamp, wire name, area, beampath, and detector list

        Notes
        -----
        Fitting and RMS size calculation are performed by downstream analysis
        code. This method focuses on hardware orchestration and data organization.
        """
        # Reserve a new buffer if necessary
        if self.my_buffer is None:
            self.my_buffer = self._reserve_buffer()

        # Create measurement metadata object
        metadata = self.create_metadata()

        # Send command to start wire motion sequence and wait for initialization
        self.scan_with_wire()

        # Start BSA buffer and wait for acquisition to complete
        self.start_timing_buffer()

        # Get position and detector data from the buffer
        self.data = self.get_data_from_buffer()

        # Determine the profile range indices
        # e.g., u range = (13000, 18000) -> position_data[100:450]
        profile_indices = self.get_profile_range_indices()

        # Separate detector data by profile
        self.profiles = self.organize_data_by_profile(profile_indices)

        # Release EDEF/BSA
        self.logger.info("Releasing BSA buffer.")
        self.my_buffer.release()
        self.my_buffer = None

        return WireMeasurementCollectionResult(
            raw_data=self.data,
            metadata=metadata,
        )

    def create_device_dictionary(self) -> dict:
        """
        Creates a device dictionary for a wire scan setup.  Includes the wire
        device and any associated detectors from metadata.

        Returns:
            dict: A mapping of device names to device objects.
        """

        self.logger.info("Creating device dictionary...")

        # Instantiate device dictionary with wire device
        devices = {self.my_wire.name: self.my_wire}

        # ds is a colon-separated detector string from metadata
        # e.g. "LBLM:TEST" -> name = "LBLM", area = "TEST"
        for ds in self.my_wire.metadata.detectors:
            name, area = ds.split(":")

            if name == "TMITLOSS":
                devices["TMITLOSS"] = TMITLoss(
                    my_buffer=self.my_buffer,
                    my_wire=self.my_wire,
                    beampath=self.beampath,
                    region=self.my_wire.area,
                )
            else:
                detector = self._instantiate_device(name, area)
                if detector is not None:
                    devices[name] = detector

        self.logger.info("Device dictionary built.")
        return devices

    def scan_with_wire(self) -> None:
        """
        Starts the buffer and wire scan with brief delays.

        Delays ensure the buffer is active before the scan begins
        and allows time for the buffer to update its state.
        """
        # Reserve a new buffer if necessary
        if self.my_buffer is None:
            self.my_buffer = self._reserve_buffer()
        self._start_scan_with_retry()

    def start_timing_buffer(self) -> None:
        """
        Start a BSA buffer and wait for it to complete.  Post wire position to
        the log every second.
        """
        # Start buffer
        self.logger.info("Starting BSA buffer...")
        self.my_buffer.start()

        # Wait briefly before checking buffer 'ready'
        # Wire is already moving, data is already collecting...
        time.sleep(0.5)

        # Wait for buffer 'ready'
        i = 0
        while not self.my_buffer.is_acquisition_complete():
            # Check for completion every 0.1 s, post position 1s
            time.sleep(0.1)
            if i % 10 == 0:
                self.logger.info("Wire position: %s", self.my_wire.motor_rbv)
            i += 1

        self.logger.info(
            "BSA buffer %s acquisition complete after %s seconds",
            self.my_buffer.number,
            i / 10,
        )

    def get_data_from_buffer(self) -> dict:
        """
        Collects wire scan and detector data after buffer completes.

        Returns:
            dict: Collected data keyed by device name.
        """
        self.logger.info("Getting data from BSA buffer...")
        data = {name: self._collect_device_data(name) for name in self.devices.keys()}
        self.logger.info("Data retrieved from buffer. Scan complete.")
        return data

    def get_profile_range_indices(self) -> dict:
        """
        Finds sequential scan indices within each profile's position range.

        Returns:
            dict: Profile keys ('x', 'y', 'u') with lists of index arrays.
        """
        self.logger.info("Getting profile range indices...")
        position_data = self.data[self.my_wire.name]

        # Single validation pass
        self._validate_position_data(position_data)

        profile_indices = {}
        for p in self._active_profiles():
            profile_range = self._get_profile_range(p)
            self._check_range_in_position(position_data, p, profile_range)

            indices = self._get_indices_in_range(
                position_data, profile_range[0], profile_range[1]
            )

            monotonic_indices = self._get_monotonic_indices(position_data, indices)

            profile_indices[p] = monotonic_indices

        self.logger.info("Profile range indices collected.")
        return profile_indices

    def organize_data_by_profile(self, profile_indices) -> dict:
        """
        Organizes detector data by scan profile for each device.

        Returns:
            dict: Nested dict with profiles as keys and device
                  data per profile.
        """
        self.logger.info("Creating profile data objects...")
        profile_measurements = {}

        for profile, index in profile_indices.items():
            detectors = {}
            positions = None
            for device_name in self.devices:
                data_slice = self.data[device_name][index]

                if device_name == self.my_wire.name:
                    positions = data_slice
                else:
                    detectors[device_name] = self._create_detector_measurement(
                        device_name, data_slice
                    )

            profile_measurements[profile] = self._create_profile_measurement(
                positions, detectors, index
            )

        self.logger.info("Profile data objects created.")
        return profile_measurements

    def create_metadata(self) -> MeasurementMetadata:
        """
        Make additional metadata.
        """
        scan_ranges = {
            "x": self.my_wire.x_range,
            "y": self.my_wire.y_range,
            "u": self.my_wire.u_range,
        }

        return MeasurementMetadata(
            wire_name=self.my_wire.name,
            buffer_number=self.my_buffer.number,
            area=self.my_wire.area,
            beampath=self.beampath,
            detectors=self.detectors,
            default_detector=self._get_default_detector(),
            scan_ranges=scan_ranges,
            timestamp=datetime.now(),
            active_profiles=self._active_profiles(),
            notes=None,
        )

    def _logger_config(self) -> logging.Logger:
        # Configure custom logger
        date_str = datetime.now().strftime("%Y%m%d")
        log_filename = f"ws_log_{date_str}.txt"
        logger = custom_logger(
            log_file=log_filename,
            name="wire_scan_logger",
        )
        logger.propagate = False

        return logger

    def _instantiate_device(self, name: str, area: str):
        """
        Instantiate a single device by name and area
        """
        create_by_prefix = {
            "LBLM": create_lblm,
            "PMT": create_pmt,
        }

        creator = next(
            (f for prefix, f in create_by_prefix.items() if name.startswith(prefix)),
            None,
        )

        if creator is None:
            self.logger.warning("Unknown device type '%s'. Skipping.", name)
            return None

        device = creator(area=area, name=name)
        if device is None:
            self.logger.warning("Device creation for %s returned None. Skipping.", name)

        return device

    def _start_scan_with_retry(self, max_attempts: int = 3, timeout: int = 10):
        """
        Start wire scan with retry logic.
        """
        for attempt in range(1, max_attempts + 1):
            self.logger.info(
                f"Initializing {self.my_wire.name}: (Attempt {attempt}/{max_attempts})..."
            )
            self.my_wire.start_scan()

            # If returns True within timeout, proceed
            if self._wait_until(lambda: self.my_wire.enabled, timeout=timeout):
                self.logger.info(f"{self.my_wire.name} initialized.")
                return

            # After timeout, log and iterate through for loop again
            else:
                self.logger.warning(
                    f"{self.my_wire.name} did not enable after {timeout}s - retrying..."
                )

        raise RuntimeError(
            f"Failed to initialize {self.my_wire.name} after {max_attempts} attempts."
        )

    def _get_buffer_collection_method(self, device_name: str) -> Optional[str]:
        """
        Determine the buffer collection method for a given device based on its name.
        Returns None for devices that don't collect data this way (e.g., TMITLOSS).
        """
        if device_name == self.my_wire.name:
            return "position_buffer"
        elif device_name.startswith("LBLM"):
            return "fast_buffer"
        elif device_name.startswith("PMT"):
            return "qdcraw_buffer"
        else:
            return None

    def _collect_device_data(self, device_name: str) -> np.ndarray:
        """Collect data for a given device using the appropriate method."""
        device = self.devices[device_name]
        buffer_method = self._get_buffer_collection_method(device_name)

        if buffer_method is None:
            return (
                device.measure()
            )  # For devices like TMITLOSS that don't use buffer collection

        return collect_with_size_check(
            device, buffer_method, self.my_buffer, self.logger
        )

    def _validate_position_data(self, position_data: np.ndarray) -> None:
        """
        Validates the position data to ensure it is suitable for analysis.
        """
        if position_data.min() == position_data.max():
            msg = "Min and max position are the same. Check scan data and collection. Exiting scan."
            self.logger.error(msg)
            raise RuntimeError(msg)

    def _get_units_for_device(self, device_name: str) -> str:
        """Get the appropriate units for a given device based on its name."""
        if device_name == "TMITLOSS":
            return "%% beam loss"
        return "counts"

    def _active_profiles(self) -> list:
        """
        Returns a list of active scan profiles based on wire settings.
        """
        return [
            axis
            for axis, use in zip(
                "xyu",
                [
                    self.my_wire.use_x_wire,
                    self.my_wire.use_y_wire,
                    self.my_wire.use_u_wire,
                ],
            )
            if use
        ]

    def _calc_buffer_points(self) -> int:
        """
        Determine the number of buffer points for a wire scan.

        The beam rate and pulses per profile are used here to calculate the
        wire speed, which in turn defines how many BSA buffer points are needed
        to capture the full scan. The minimum safe wire speed is calculated
        separately and enforced by the motion IOC. The buffer size must be
        sufficient for data collection while staying under the 20,000-point
        operational limit.

        In the historical mode (120 Hz, 350 pulses), ~1,600 points are
        required; this function returns 1,595. In the expected high-rate mode
        (16 kHz, 5,000 pulses), the function estimates ~19,166 points, still
        within the system limit.

        Returns
        -------
        int
            Estimated number of buffer points to allocate for the scan.
        """

        rate = self.my_wire.beam_rate
        if rate is None or rate <= 0:
            self.logger.warning(
                "Invalid beam rate '%s'. Defaulting to 120 Hz for buffer size calculation.",
                rate,
            )
            rate = 120
        pulses = self.my_wire.scan_pulses

        # 16000 max rate, 10 min rate
        log_range = np.log10(16000) - np.log10(10)
        rate_factor = (np.log10(rate) - np.log10(10)) / log_range
        fudge = 1.5 - 0.4 * rate_factor  # Fudge the calculation by 1.1 to 1.5

        buffer_points = pulses * 3 * fudge + rate / 6
        return int(buffer_points)

    def _load_yaml_config(self) -> Optional[dict]:
        file_to_open = (
            Path(__file__).resolve().parent.parent
            / "devices"
            / "yaml"
            / "wire_lblms.yaml"
        )

        if file_to_open.exists() is False:
            msg = f"YAML config file {file_to_open} not found."
            self.logger.error(msg)
            return None

        with open(file_to_open, "r") as f:
            wire_lblms = yaml.safe_load(f)
            return wire_lblms

    def _get_default_detector(self) -> str:
        lblm_config = self._load_yaml_config()
        if lblm_config is None:
            return self.detectors[0]
        else:
            default_detector = lblm_config[self.my_wire.name]
            return default_detector

    def _wait_until(self, condition, timeout=5, period=0.1) -> bool:
        # Returns True if condition met within timeout
        start = time.time()
        while time.time() - start < timeout:
            if condition():
                return True
            time.sleep(period)
        return False

    def _reserve_buffer(self) -> object:
        return reserve_buffer(
            beampath=self.beampath,
            name="LCLS Tools Wire Scan",
            n_measurements=self._calc_buffer_points(),
            destination_mode="Inclusion",
            logger=self.logger,
        )
