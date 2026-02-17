from lcls_tools.common.measurements.ws_collection import WireBPMCollection
from lcls_tools.common.measurements.ws_collection_results import (
    ProfileMeasurement,
    DetectorMeasurement,
    MeasurementMetadata,
)
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import numpy as np
import logging
import sys

# Patch missing modules before importing ws_collection
sys.modules['meme'] = MagicMock()
sys.modules['meme.names'] = MagicMock()
sys.modules['edef'] = MagicMock()
sys.modules['edef.devices'] = MagicMock()


class MockWire():
    """Mock Wire device for testing."""

    def __init__(self, name="TEST_WIRE", area="TEST_AREA"):
        self.name = name
        self.area = area
        self.x_range = (100, 200)
        self.y_range = (150, 250)
        self.u_range = (200, 300)
        self.use_x_wire = True
        self.use_y_wire = True
        self.use_u_wire = True
        self.beam_rate = 120
        self.scan_pulses = 350
        self.motor_rbv = 150
        self.enabled = False
        self.metadata = MagicMock()
        self.metadata.detectors = ["LBLM:TEST_AREA", "PMT:TEST_AREA"]

    def start_scan(self):
        """Simulate starting a scan."""
        self.enabled = True

    def measure(self):
        """Return mock measurement data."""
        return np.array([100, 150, 200, 250, 300])


class MockBuffer:
    """Mock BSA buffer for testing."""

    def __init__(self, number=1):
        self.number = number
        self._acquisition_complete = False

    def start(self):
        """Start the buffer."""
        self._acquisition_complete = True

    def is_acquisition_complete(self):
        """Check if acquisition is complete."""
        return self._acquisition_complete

    def release(self):
        """Release the buffer."""
        pass


class TestWireBPMCollectionMethods(unittest.TestCase):
    """Tests for WireBPMCollection individual methods using mocked instances."""

    def setUp(self):
        """Set up test fixtures."""
        # Patch external dependencies
        self.patch_custom_logger = patch(
            'lcls_tools.common.measurements.ws_collection.custom_logger'
        )
        self.mock_logger = self.patch_custom_logger.start()
        self.mock_logger.return_value = logging.getLogger('test')

        self.patch_reserve_buffer = patch(
            'lcls_tools.common.measurements.ws_collection.reserve_buffer'
        )
        self.mock_reserve_buffer = self.patch_reserve_buffer.start()
        self.mock_reserve_buffer.return_value = MockBuffer(number=1)

        self.patch_create_lblm = patch(
            'lcls_tools.common.measurements.ws_collection.create_lblm'
        )
        self.mock_create_lblm = self.patch_create_lblm.start()
        self.mock_create_lblm.return_value = MagicMock(name="LBLM_TEST")

        self.patch_create_pmt = patch(
            'lcls_tools.common.measurements.ws_collection.create_pmt'
        )
        self.mock_create_pmt = self.patch_create_pmt.start()
        self.mock_create_pmt.return_value = MagicMock(name="PMT_TEST")

        self.patch_tmit_loss = patch(
            'lcls_tools.common.measurements.ws_collection.TMITLoss'
        )
        self.mock_tmit_loss = self.patch_tmit_loss.start()

        # Create a collection instance with mocked dependencies
        self.collection = self._create_instance()

    def tearDown(self):
        """Clean up patches."""
        self.patch_custom_logger.stop()
        self.patch_reserve_buffer.stop()
        self.patch_create_lblm.stop()
        self.patch_create_pmt.stop()
        self.patch_tmit_loss.stop()

    def _create_instance(self):
        """Create a mock collection instance."""
        collection = MagicMock(spec=WireBPMCollection)
        mock_wire = MockWire()
        mock_wire.metadata.detectors = ["LBLM:TEST_AREA", "PMT:TEST_AREA"]

        collection.beam_profile_device = mock_wire
        collection.my_wire = mock_wire
        collection.beampath = "GUNB"
        collection.my_buffer = MockBuffer(number=1)
        collection.devices = {mock_wire.name: mock_wire}
        collection.detectors = [d.split(":")[0] for d in mock_wire.metadata.detectors]
        collection.data = None
        collection.profiles = None
        collection.logger = logging.getLogger('test')

        # Bind the real methods to the mock
        collection.create_metadata = WireBPMCollection.create_metadata.__get__(collection, WireBPMCollection)
        collection._active_profiles = WireBPMCollection._active_profiles.__get__(collection, WireBPMCollection)
        collection._get_profile_range = WireBPMCollection._get_profile_range.__get__(collection, WireBPMCollection)
        collection._mono_array = WireBPMCollection._mono_array.__get__(collection, WireBPMCollection)
        collection._get_indices_in_range = WireBPMCollection._get_indices_in_range.__get__(collection, WireBPMCollection)
        collection._validate_position_data = WireBPMCollection._validate_position_data.__get__(collection, WireBPMCollection)
        collection._check_range_in_position = WireBPMCollection._check_range_in_position.__get__(collection, WireBPMCollection)
        collection._get_units_for_device = WireBPMCollection._get_units_for_device.__get__(collection, WireBPMCollection)
        collection._create_detector_measurement = WireBPMCollection._create_detector_measurement.__get__(collection, WireBPMCollection)
        collection._create_profile_measurement = WireBPMCollection._create_profile_measurement.__get__(collection, WireBPMCollection)
        collection._get_buffer_collection_method = WireBPMCollection._get_buffer_collection_method.__get__(collection, WireBPMCollection)
        collection._wait_until = WireBPMCollection._wait_until.__get__(collection, WireBPMCollection)
        collection._calc_buffer_points = WireBPMCollection._calc_buffer_points.__get__(collection, WireBPMCollection)
        collection._get_monotonic_indices = WireBPMCollection._get_monotonic_indices.__get__(collection, WireBPMCollection)
        collection._get_default_detector = WireBPMCollection._get_default_detector.__get__(collection, WireBPMCollection)
        collection._reserve_buffer = WireBPMCollection._reserve_buffer.__get__(collection, WireBPMCollection)
        collection._load_yaml_config = MagicMock(return_value=None)  # Mock yaml loading to return None

        return collection

    def test_create_metadata(self):
        """Test metadata creation."""
        metadata = self.collection.create_metadata()

        self.assertIsInstance(metadata, MeasurementMetadata)
        self.assertEqual(metadata.wire_name, self.collection.my_wire.name)
        self.assertEqual(metadata.area, self.collection.my_wire.area)
        self.assertEqual(metadata.beampath, "GUNB")
        self.assertIsInstance(metadata.timestamp, datetime)

    def test_active_profiles_all_enabled(self):
        """Test _active_profiles when all are enabled."""
        self.collection.my_wire.use_x_wire = True
        self.collection.my_wire.use_y_wire = True
        self.collection.my_wire.use_u_wire = True

        active = self.collection._active_profiles()
        self.assertEqual(active, ['x', 'y', 'u'])

    def test_active_profiles_selective(self):
        """Test _active_profiles with selective enablement."""
        self.collection.my_wire.use_x_wire = True
        self.collection.my_wire.use_y_wire = False
        self.collection.my_wire.use_u_wire = True

        active = self.collection._active_profiles()
        self.assertEqual(active, ['x', 'u'])

    def test_active_profiles_only_x(self):
        """Test _active_profiles with only X enabled."""
        self.collection.my_wire.use_x_wire = True
        self.collection.my_wire.use_y_wire = False
        self.collection.my_wire.use_u_wire = False

        active = self.collection._active_profiles()
        self.assertEqual(active, ['x'])

    def test_mono_array_monotonic_increasing(self):
        """Test _mono_array with monotonically increasing data."""
        pos = np.array([1, 2, 3, 4, 5])

        result = self.collection._mono_array(pos)

        # All should be marked as True
        self.assertTrue(np.all(result))

    def test_mono_array_with_reversal(self):
        """Test _mono_array with monotonic reversal."""
        pos = np.array([1, 2, 3, 2, 4, 5])

        result = self.collection._mono_array(pos)

        # Should stop marking as True at the reversal
        expected = np.array([True, True, True, False, False, False])
        np.testing.assert_array_equal(result, expected)

    def test_mono_array_flat(self):
        """Test _mono_array with flat data."""
        pos = np.array([1, 1, 1, 1, 1])

        result = self.collection._mono_array(pos)

        # All should be True for non-decreasing (allows equal values)
        self.assertTrue(np.all(result))

    def test_get_profile_range(self):
        """Test _get_profile_range method."""
        x_range = self.collection._get_profile_range('x')
        y_range = self.collection._get_profile_range('y')
        u_range = self.collection._get_profile_range('u')

        self.assertEqual(x_range, self.collection.my_wire.x_range)
        self.assertEqual(y_range, self.collection.my_wire.y_range)
        self.assertEqual(u_range, self.collection.my_wire.u_range)

    def test_get_indices_in_range(self):
        """Test _get_indices_in_range method."""
        position_data = np.array([100, 150, 200, 250, 300, 350])

        indices = self.collection._get_indices_in_range(position_data, 150, 250)

        expected = np.array([1, 2, 3])
        np.testing.assert_array_equal(indices, expected)

    def test_get_indices_in_range_empty(self):
        """Test _get_indices_in_range when no data in range."""
        position_data = np.array([100, 150, 200])

        indices = self.collection._get_indices_in_range(position_data, 300, 400)

        self.assertEqual(len(indices), 0)

    def test_validate_position_data_valid(self):
        """Test _validate_position_data with valid data."""
        position_data = np.array([100, 150, 200, 250])

        # Should not raise
        self.collection._validate_position_data(position_data)

    def test_validate_position_data_invariant(self):
        """Test _validate_position_data with invariant data."""
        position_data = np.array([150, 150, 150, 150])

        # Should raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.collection._validate_position_data(position_data)

    def test_check_range_in_position_valid(self):
        """Test _check_range_in_position with valid range."""
        position_data = np.array([100, 150, 200, 250, 300])

        # Should not raise
        self.collection._check_range_in_position(position_data, 'x', (100, 250))

    def test_check_range_in_position_insufficient(self):
        """Test _check_range_in_position when range minimum not reached."""
        position_data = np.array([100, 150, 200])

        # Should raise RuntimeError when max position < range minimum
        with self.assertRaises(RuntimeError):
            self.collection._check_range_in_position(position_data, 'x', (250, 400))

    def test_get_units_for_device_tmitloss(self):
        """Test _get_units_for_device for TMITLOSS."""
        units = self.collection._get_units_for_device("TMITLOSS")
        self.assertEqual(units, "%% beam loss")

    def test_get_units_for_device_other(self):
        """Test _get_units_for_device for other devices."""
        units = self.collection._get_units_for_device("LBLM")
        self.assertEqual(units, "counts")

        units = self.collection._get_units_for_device("PMT")
        self.assertEqual(units, "counts")

    def test_create_detector_measurement(self):
        """Test _create_detector_measurement."""
        data = np.array([100, 200, 300])

        measurement = self.collection._create_detector_measurement("LBLM", data)

        self.assertIsInstance(measurement, DetectorMeasurement)
        np.testing.assert_array_equal(measurement.values, data)
        self.assertEqual(measurement.units, "counts")
        self.assertEqual(measurement.label, "LBLM")

    def test_create_profile_measurement(self):
        """Test _create_profile_measurement."""
        positions = np.array([100, 150, 200])
        detectors = {
            "LBLM": DetectorMeasurement(values=np.array([1, 2, 3]), units="counts"),
            "PMT": DetectorMeasurement(values=np.array([4, 5, 6]), units="counts")
        }
        indices = np.array([0, 1, 2])

        measurement = self.collection._create_profile_measurement(positions, detectors, indices)

        self.assertIsInstance(measurement, ProfileMeasurement)
        np.testing.assert_array_equal(measurement.positions, positions)
        self.assertEqual(len(measurement.detectors), 2)
        np.testing.assert_array_equal(measurement.profile_indices, indices)

    def test_get_buffer_collection_method_wire(self):
        """Test _get_buffer_collection_method for wire device."""
        method = self.collection._get_buffer_collection_method(self.collection.my_wire.name)
        self.assertEqual(method, "position_buffer")

    def test_get_buffer_collection_method_lblm(self):
        """Test _get_buffer_collection_method for LBLM detector."""
        method = self.collection._get_buffer_collection_method("LBLM")
        self.assertEqual(method, "fast_buffer")

    def test_get_buffer_collection_method_pmt(self):
        """Test _get_buffer_collection_method for PMT detector."""
        method = self.collection._get_buffer_collection_method("PMT")
        self.assertEqual(method, "qdcraw_buffer")

    def test_get_buffer_collection_method_tmitloss(self):
        """Test _get_buffer_collection_method for TMITLOSS."""
        method = self.collection._get_buffer_collection_method("TMITLOSS")
        self.assertIsNone(method)

    def test_wait_until_condition_true(self):
        """Test _wait_until when condition becomes true."""
        call_count = [0]
        def condition():
            call_count[0] += 1
            return call_count[0] >= 3  # Return True on 3rd call

        result = self.collection._wait_until(condition, timeout=2, period=0.01)

        self.assertTrue(result)

    def test_wait_until_timeout(self):
        """Test _wait_until when timeout expires."""
        def condition():
            return False  # Never True

        result = self.collection._wait_until(condition, timeout=0.1, period=0.05)

        self.assertFalse(result)

    def test_calc_buffer_points_default_rate(self):
        """Test _calc_buffer_points with default rate."""
        self.collection.my_wire.beam_rate = 120
        self.collection.my_wire.scan_pulses = 350

        points = self.collection._calc_buffer_points()

        # Should return reasonable buffer size
        self.assertGreater(points, 0)
        self.assertLess(points, 20000)  # System limit

    def test_calc_buffer_points_high_rate(self):
        """Test _calc_buffer_points with high beam rate."""
        self.collection.my_wire.beam_rate = 16000
        self.collection.my_wire.scan_pulses = 5000

        points = self.collection._calc_buffer_points()

        # Should return larger buffer for high rate
        self.assertGreater(points, 0)
        self.assertLess(points, 20000)  # System limit

    def test_calc_buffer_points_invalid_rate(self):
        """Test _calc_buffer_points with invalid rate."""
        self.collection.my_wire.beam_rate = None
        self.collection.my_wire.scan_pulses = 350

        # Should default to 120 Hz
        points = self.collection._calc_buffer_points()

        self.assertGreater(points, 0)

    def test_get_monotonic_indices(self):
        """Test _get_monotonic_indices method."""
        position_data = np.array([100, 110, 120, 115, 130, 140])
        indices = np.array([0, 1, 2, 3, 4, 5])

        mono_indices = self.collection._get_monotonic_indices(position_data, indices)

        # Should stop at reversal
        expected = np.array([0, 1, 2])
        np.testing.assert_array_equal(mono_indices, expected)

    def test_reserve_buffer(self):
        """Test _reserve_buffer method."""
        buffer = self.collection._reserve_buffer()

        self.assertIsNotNone(buffer)
        self.mock_reserve_buffer.assert_called()


class TestWireBPMCollectionIntegration(unittest.TestCase):
    """Integration tests for WireBPMCollection workflow methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_wire = MockWire()
        self.mock_wire.metadata.detectors = ["LBLM:TEST_AREA"]

        # Patch external dependencies
        self.patch_custom_logger = patch(
            'lcls_tools.common.measurements.ws_collection.custom_logger'
        )
        self.mock_logger = self.patch_custom_logger.start()
        self.mock_logger.return_value = logging.getLogger('test')

        self.patch_reserve_buffer = patch(
            'lcls_tools.common.measurements.ws_collection.reserve_buffer'
        )
        self.mock_reserve_buffer = self.patch_reserve_buffer.start()
        self.mock_reserve_buffer.return_value = MockBuffer(number=1)

        self.patch_create_lblm = patch(
            'lcls_tools.common.measurements.ws_collection.create_lblm'
        )
        self.mock_create_lblm = self.patch_create_lblm.start()
        mock_lblm = MagicMock(name="LBLM_TEST")
        mock_lblm.measure.return_value = np.arange(100)
        self.mock_create_lblm.return_value = mock_lblm

        self.patch_create_pmt = patch(
            'lcls_tools.common.measurements.ws_collection.create_pmt'
        )
        self.mock_create_pmt = self.patch_create_pmt.start()
        self.mock_create_pmt.return_value = MagicMock(name="PMT_TEST")

        self.collection = self._create_instance()

    def tearDown(self):
        """Clean up patches."""
        self.patch_custom_logger.stop()
        self.patch_reserve_buffer.stop()
        self.patch_create_lblm.stop()
        self.patch_create_pmt.stop()

    def _create_instance(self):
        """Create a mock collection instance."""
        collection = MagicMock(spec=WireBPMCollection)

        collection.beam_profile_device = self.mock_wire
        collection.my_wire = self.mock_wire
        collection.beampath = "GUNB"
        collection.my_buffer = MockBuffer(number=1)
        collection.devices = {self.mock_wire.name: self.mock_wire}
        collection.detectors = [d.split(":")[0] for d in self.mock_wire.metadata.detectors]
        collection.data = None
        collection.profiles = None
        collection.logger = logging.getLogger('test')

        # Bind real methods
        collection.get_profile_range_indices = WireBPMCollection.get_profile_range_indices.__get__(collection, WireBPMCollection)
        collection._active_profiles = WireBPMCollection._active_profiles.__get__(collection, WireBPMCollection)
        collection._get_profile_range = WireBPMCollection._get_profile_range.__get__(collection, WireBPMCollection)
        collection._validate_position_data = WireBPMCollection._validate_position_data.__get__(collection, WireBPMCollection)
        collection._check_range_in_position = WireBPMCollection._check_range_in_position.__get__(collection, WireBPMCollection)
        collection._get_indices_in_range = WireBPMCollection._get_indices_in_range.__get__(collection, WireBPMCollection)
        collection._get_monotonic_indices = WireBPMCollection._get_monotonic_indices.__get__(collection, WireBPMCollection)
        collection._mono_array = WireBPMCollection._mono_array.__get__(collection, WireBPMCollection)

        return collection

    def test_get_profile_range_indices_workflow(self):
        """Test complete get_profile_range_indices workflow."""
        # Set up realistic position data covering all ranges
        position_data = np.linspace(100, 350, 500)  # Covers x, y, u ranges
        self.collection.data = {self.mock_wire.name: position_data}

        profile_indices = self.collection.get_profile_range_indices()

        # Should have indices for each profile
        self.assertIn('x', profile_indices)
        self.assertIn('y', profile_indices)
        self.assertIn('u', profile_indices)

        # Each profile should have some indices
        for profile in ['x', 'y', 'u']:
            self.assertGreater(len(profile_indices[profile]), 0)

    def test_organize_data_by_profile_integration(self):
        """Test organize_data_by_profile with realistic workflow."""
        # Bind organize method
        self.collection.organize_data_by_profile = WireBPMCollection.organize_data_by_profile.__get__(self.collection, WireBPMCollection)
        self.collection._create_detector_measurement = WireBPMCollection._create_detector_measurement.__get__(self.collection, WireBPMCollection)
        self.collection._create_profile_measurement = WireBPMCollection._create_profile_measurement.__get__(self.collection, WireBPMCollection)
        self.collection._get_units_for_device = WireBPMCollection._get_units_for_device.__get__(self.collection, WireBPMCollection)

        # Set up mock data
        mock_detector = MagicMock()
        mock_detector.measure = MagicMock(return_value=np.arange(3))
        self.collection.devices = {
            self.mock_wire.name: self.mock_wire,
            "LBLM": mock_detector
        }

        self.collection.data = {
            self.mock_wire.name: np.array([100, 150, 200]),
            "LBLM": np.array([1, 2, 3])
        }

        # Set up profile indices
        profile_indices = {
            'x': np.array([0, 1, 2])
        }

        profiles = self.collection.organize_data_by_profile(profile_indices)

        # Check structure
        self.assertIn('x', profiles)
        self.assertIsInstance(profiles['x'], ProfileMeasurement)
        self.assertIn("LBLM", profiles['x'].detectors)
