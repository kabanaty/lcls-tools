import logging
from typing import Any, Dict
from pydantic import ConfigDict
import lcls_tools.common.model.gaussian as gaussian
from lcls_tools.common.measurements.beam_profile import BeamProfileAnalysis
from lcls_tools.common.measurements.ws_analysis_results import (
    FitResult,
    DetectorFit,
)
from lcls_tools.common.measurements.ws_collection_results import WireBPMCollectionResult
import numpy as np


class WireBPMAnalysis(BeamProfileAnalysis):
    """
    Analyzes wire scan measurement data and performs Gaussian fitting.

    Takes raw wire beam profile measurement results and applies curve fitting
    to extract beam parameters (centroid, RMS size, amplitude) for each detector
    and profile.

    Attributes:
        collection_result (WireBPMCollectionResult): Raw measurement data from wire scan.
        logger (logging.Logger): Logger for diagnostic messages.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    fit_result: Dict[str, FitResult]

    def _extract_wire_angle(self) -> dict:
        """Extract the wire install angle (in radians) for coordinate conversion."""
        # For now, return unit scale. In future, could extract from device metadata.
        rad = np.deg2rad(self.collection_result.beam_profile_device.install_angle)
        return {"x": np.sin(rad), "y": np.cos(rad), "u": 1.0}

    def _convert_stage_to_beam_coords(self, profile: str, positions: np.ndarray) -> np.ndarray:
        """Convert stage positions to beam coordinates for a given profile."""
        scale = self._extract_wire_angle()
        return positions * abs(scale[profile])

    def _peak_window(self, x: np.ndarray, y: np.ndarray, n_stds: float = 6, filter_size: int = 5) -> tuple:
        """
        Extract peak window from 1D detector data using statistical windowing.

        Applies median filtering, triangle thresholding, and n-sigma windowing
        around the signal centroid.

        Parameters:
            x (np.ndarray): Position data.
            y (np.ndarray): Detector signal values.
            n_stds (float): Number of standard deviations for windowing. Default is 6.
            filter_size (int): Median filter kernel size. Default is 5.

        Returns:
            tuple: (windowed_x, windowed_y, (left_idx, right_idx))
        """
        from scipy.ndimage import median_filter
        from skimage.filters import threshold_triangle

        x = np.asarray(x)
        y = np.asarray(y)

        # Smooth the signal
        y_filtered = median_filter(y, size=filter_size)

        # Apply triangle threshold
        threshold = threshold_triangle(y_filtered)
        y_thresholded = np.clip(y_filtered - threshold, 0, None)

        # Find centroid and RMS of thresholded signal
        if y_thresholded.sum() == 0:
            # Fallback to simple peak finding if no signal above threshold
            self.logger.warning(
                "No signal above threshold. Using simple peak finding for window."
            )
            i = np.argmax(y)
            center = x[i]
            rms = (x[-1] - x[0]) / 4  # Default quarter-range
        else:
            # Weighted centroid
            weights = y_thresholded
            center = np.sum(x * weights) / weights.sum()
            # Weighted RMS
            rms = np.sqrt(np.sum(weights * (x - center) ** 2) / weights.sum())

        # Define window as center ± n_stds * rms
        left_bound = center - n_stds * rms
        right_bound = center + n_stds * rms

        # Find indices
        left = np.searchsorted(x, left_bound, side="left")
        right = np.searchsorted(x, right_bound, side="right")

        # Clip to valid range
        left = max(0, left)
        right = min(len(y) - 1, right)

        return x[left : right + 1], y[left : right + 1], (left, right)

    def _fit_detector_in_profile(self, x_beam: np.ndarray, detector_signal: np.ndarray) -> DetectorFit:
        """
        Fit a single detector signal within a profile using Gaussian curve.

        Parameters:
            x_beam (np.ndarray): Position data in beam coordinates.
            detector_signal (np.ndarray): Detector signal values.

        Returns:
            DetectorFit: Fit parameters and curve.
        """
        peak_window = self._peak_window(x=x_beam, y=detector_signal)

        # Get fit parameters
        fp = gaussian.fit(pos=peak_window[0], data=peak_window[1])

        # Generate fit curve
        fit_curve = gaussian.curve(
            x=peak_window[0],
            mean=fp["mean"],
            sigma=fp["sigma"],
            amp=fp["amp"],
            off=fp["off"],
        )

        return DetectorFit(
            mean=fp["mean"],
            sigma=fp["sigma"],
            amplitude=fp["amp"],
            offset=fp["off"],
            curve=fit_curve,
            positions=peak_window[0],
        )

    def _fit_profile(self, profile: str, detectors: list) -> FitResult:
        """
        Fit all detectors within a single profile.

        Parameters:
            profile (str): Profile name ('x', 'y', or 'u').
            detectors (list): List of detector names.

        Returns:
            FitResult: Fit results for all detectors in the profile.
        """
        profile_data = self.collection_result.profiles[profile]
        x_stage = profile_data.positions
        x_beam = self._convert_stage_to_beam_coords(profile, x_stage)

        detector_fits = {}
        for detector_name in detectors:
            if detector_name not in profile_data.detectors:
                self.logger.warning(f"Detector {detector_name} not in profile {profile}. Skipping.")
                continue

            detector_fits[detector_name] = self._fit_detector_in_profile(
                x_beam, profile_data.detectors[detector_name].values
            )

        return FitResult(detectors=detector_fits)

    def fit_data_by_profile(self) -> dict:
        """
        Fit detector data for each profile and device using Gaussian curves.
        Applies beam fitting to x, y, and u projections for all detectors
        in the measurement result.

        Returns:
            dict: Fit results organized by profile and detector.
        """
        self.logger.info("Fitting profile data...")

        profiles = self.collection_result.profiles
        detectors = list(self.collection_result.metadata.detectors)

        fit_result = {
            profile: self._fit_profile(profile, detectors)
            for profile in profiles
        }

        self.logger.info("Profile data fit.")
        return fit_result

    def get_rms_sizes(self, fit_result: dict) -> tuple | None:
        """
        Extract RMS beam sizes from fit results.

        Computes RMS sizes from x and y profile fits using the default detector.

        Parameters:
            fit_result (dict): Fit results from fit_data_by_profile().

        Returns:
            tuple or None: (x_rms, y_rms) in meters, or None if both profiles not present.
        """
        if "x" in fit_result and "y" in fit_result:
            default_det = self.collection_result.metadata.default_detector
            x_fit = fit_result["x"].detectors[default_det]
            y_fit = fit_result["y"].detectors[default_det]

            self.logger.info("Getting RMS beam size...")
            rms_sizes = (x_fit.sigma, y_fit.sigma)
        else:
            self.logger.warning(
                "Both x and y profiles not found. Skipping RMS size calculation."
            )
            rms_sizes = None
        return rms_sizes

    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete analysis: fit profiles and extract RMS sizes.

        Returns:
            dict: Analysis results containing:
                - fit_result: Gaussian fit parameters per profile and detector
                - rms_sizes: Computed RMS beam sizes (if both x and y profiles present)
        """
        fit_result = self.fit_data_by_profile()
        rms_sizes = self.get_rms_sizes(fit_result)

        return {
            "fit_result": fit_result,
            "rms_sizes": rms_sizes,
        }
