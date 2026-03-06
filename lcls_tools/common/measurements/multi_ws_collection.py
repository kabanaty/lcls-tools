import logging
import time
from datetime import datetime
from typing import Optional

from pydantic import model_validator
from typing_extensions import Self

from lcls_tools.common.devices.wire import Wire
from lcls_tools.common.logger.file_logger import custom_logger
from lcls_tools.common.measurements.beam_profile import BeamProfileMeasurement
from lcls_tools.common.measurements.ws_collection import (
    WireMeasurementCollection,
)
from lcls_tools.common.measurements.ws_collection_results import (
    MultiWireMeasurementCollectionResult,
)


class MultiWireMeasurementCollection(BeamProfileMeasurement):
    """
    Collects wire scan measurements from multiple wires simultaneously.

    Initializes all wires concurrently, then executes measurements in quick
    succession to capture beam profile data from 3-4 wire devices.

    Design note:
        This class intentionally uses composition (it manages multiple
        WireMeasurementCollection instances) instead of inheriting from
        WireMeasurementCollection, because multi-wire orchestration is not a
        single-wire measurement.

    Attributes:
        wires (list[Wire]): List of 3-4 Wire devices to measure.
        beampath (str): Beamline identifier for buffer and device selection.
        wire_collections (dict): WireMeasurementCollection objects
            by wire name.
        logger (logging.Logger): File-based measurement logger.
    """

    name: str = "Multi-Wire Beam Profile Measurement"
    wires: list[Wire]
    beampath: str

    # Extra fields to be set after validation
    wire_collections: Optional[dict] = None
    logger: Optional[logging.Logger] = None

    @model_validator(mode="after")
    def run_setup(self) -> Self:
        # Validate number of wires
        if not (3 <= len(self.wires) <= 4):
            raise ValueError(
                "MultiWireMeasurementCollection requires 3 or 4 wires"
            )

        # Check for unique wire names
        wire_names = [wire.name for wire in self.wires]
        if len(wire_names) != len(set(wire_names)):
            raise ValueError("All wire names must be unique")

        # Setup logger using standard configuration
        self.logger = self._logger_config()

        # Create WireMeasurementCollection for each wire
        self.logger.info(
            f"Initializing MultiWireMeasurementCollection with "
            f"{len(self.wires)} wires"
        )
        self.wire_collections = {}
        for wire in self.wires:
            self.logger.info(
                f"Creating WireMeasurementCollection for {wire.name}"
            )
            self.wire_collections[wire.name] = WireMeasurementCollection(
                beam_profile_device=wire,
                beampath=self.beampath,
            )

        return self

    def measure(
        self, scan_type: str = "step", initialize_timeout: int = 10
    ) -> MultiWireMeasurementCollectionResult:
        """
        Execute multi-wire scan: initialize all wires, then measure each.

        This method:
        1. Simultaneously initializes all wire devices
        2. Waits for all wires to become enabled
        3. Runs measure() on each WireMeasurementCollection in succession
        4. Collates all results into MultiWireMeasurementCollectionResult

        Parameters
        ----------
        scan_type : str, optional
            ``"on_the_fly"`` or ``"step"``. Passed to each wire's measure().
        initialize_timeout : int, optional
            Timeout (seconds) for each initialization attempt.
            Multi-wire initialization retries up to 3 attempts.

        Returns
        -------
        MultiWireMeasurementCollectionResult
            Combined results from all wire measurements.

        Raises
        ------
        RuntimeError
            If any wire fails to initialize after all retry attempts.
        """
        self.logger.info("Starting multi-wire measurement sequence")

        # Step 1/2: Initialize all wires with retry and wait until enabled
        self._initialize_all_wires_with_retry(timeout=initialize_timeout)

        self.logger.info("All wires successfully initialized")

        # Step 3: Run measure() on each wire in succession
        wire_results = {}
        measurement_timestamp = datetime.now()

        for wire_name, collection in self.wire_collections.items():
            self.logger.info(f"Starting measurement for {wire_name}")
            try:
                result = collection.measure(scan_type=scan_type)
                wire_results[wire_name] = result
                self.logger.info(
                    f"Successfully completed measurement for {wire_name}"
                )
            except Exception as e:
                self.logger.error(f"Failed to measure {wire_name}: {e}")
                raise

        # Step 4: Collate results
        self.logger.info("All measurements complete. Creating result object.")
        return MultiWireMeasurementCollectionResult(
            wire_results=wire_results,
            timestamp=measurement_timestamp,
        )

    def _wait_for_all_wires_enabled(self, timeout: int = 30) -> bool:
        """
        Wait for all wires to report as enabled.

        Parameters
        ----------
        timeout : int
            Maximum time (seconds) to wait.

        Returns
        -------
        bool
            True if all wires enabled within timeout, False otherwise.
        """
        start_time = time.time()
        check_period = 0.2  # Check every 200ms

        while time.time() - start_time < timeout:
            all_enabled = all(
                collection.my_wire.enabled
                for collection in self.wire_collections.values()
            )

            if all_enabled:
                elapsed = time.time() - start_time
                self.logger.info(f"All wires enabled after {elapsed:.1f}s")
                return True

            # Log status every 2 seconds
            if int(time.time() - start_time) % 2 == 0:
                enabled_status = {
                    name: collection.my_wire.enabled
                    for name, collection in self.wire_collections.items()
                }
                self.logger.info(f"Wire enable status: {enabled_status}")

            time.sleep(check_period)

        return False

    def _initialize_all_wires_with_retry(
        self, max_attempts: int = 3, timeout: int = 10
    ) -> None:
        """Initialize all wires with retries until all are enabled."""
        for attempt in range(1, max_attempts + 1):
            self.logger.info(
                "Initializing all wires for multi-wire scan: "
                f"(Attempt {attempt}/{max_attempts})..."
            )

            # Send initialize command only to wires not yet enabled.
            for wire_name, collection in self.wire_collections.items():
                if collection.my_wire.enabled:
                    continue
                self.logger.info(f"Sending initialize command to {wire_name}")
                collection.my_wire.initialize()

            # Wait until all wires are enabled for this attempt.
            if self._wait_for_all_wires_enabled(timeout=timeout):
                self.logger.info("All wires successfully initialized")
                return

            failed_wires = [
                name
                for name, collection in self.wire_collections.items()
                if not collection.my_wire.enabled
            ]
            self.logger.warning(
                "Some wires did not enable after "
                f"{timeout}s - retrying. Failed wires: {failed_wires}"
            )

        failed_wires = [
            name
            for name, collection in self.wire_collections.items()
            if not collection.my_wire.enabled
        ]
        raise RuntimeError(
            "Failed to initialize all wires after "
            f"{max_attempts} attempts. Failed wires: {', '.join(failed_wires)}"
        )

    def _logger_config(self) -> logging.Logger:
        """Configure logger using standard configuration."""
        date_str = datetime.now().strftime("%Y%m%d")
        log_filename = f"ws_log_{date_str}.txt"
        logger = custom_logger(
            log_file=log_filename,
            name="wire_scan_logger",
        )
        logger.propagate = False
        return logger
