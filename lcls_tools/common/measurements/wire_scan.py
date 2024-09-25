from lcls_tools.common.devices.wire import Wire
from lcls_tools.common.devices.lblm import LBLM
from lcls_tools.common.devices.reader import create_wire
from lcls_tools.common.devices.reader import create_lblm
from lcls_tools.common.measurements.measurement import Measurement
import time
import edef
import os


class WireScanMeasurement(Measurement):
    name: str = "wire_scan"
    wire: Wire

    def measure(self, beam_path, area, wire_name) -> dict:
        """
        Perform a wire scan measurement.

        Parameters:
        - beam_path (str): The selected beam path determines which timing buffer to reserve.
        - area (str): The area of the physical devices.
        - name (str): The MAD name of the wire scanner device.

        Returns:
        dict: A dictionary containing the measured bunch charge values and additional
        statistics if multiple shots are taken.

        If n_shots is 1, the function returns a dictionary with the key "bunch_charge_nC"
        and the corresponding single measurement value.

        If n_shots is greater than 1, the function performs multiple measurements with
        the specified wait time and returns a dictionary with the key "bunch_charge_nC"
        containing a list of measured values. Additionally, statistical information
        (mean, standard deviation, etc.) is included in the dictionary.


        """
        # Create dictionary to hold all relevant objects (Wires, LBLMs, BPMs)
        # and create those objects from Wire metadata
        my_wire = create_wire(area=area, name=wire_name)
        devices = {wire_name: my_wire}
        devices.update({lblm: create_lblm(area=area, name=lblm) for lblm in my_wire.metadata.lblms})
        results = {}

        # 1) Acquire EDEF/BSA buffer
        user = os.getlogin()
        if 'SC' in beam_path:
            my_buffer = edef.BSABuffer("LCLS Tools Wire Scan", user=user)
        elif 'CU' in beam_path:
            my_buffer = edef.EventDefinition("LCLS Tools Wire Scan", user=user)
        else:
            return

        # 2) Start timing buffer
        my_buffer.start()
        # Wait for buffer to set to 'Not Ready' before moving wire
        time.sleep(0.1)

        # 3) Start wire scan
        my_wire.start_scan()

        # 4) Wait for buffer 'ready'
        while not my_buffer.is_acquisition_complete():
            time.sleep(0.1)

        # 5) Get buffer data and put into results dictionary
        results[wire_name] = my_wire.position_buffer(my_buffer)
        if 'SC' in beam_path:
            results.update({lblm: devices[lblm].fast_buffer(my_buffer) for lblm in my_wire.metadata.lblms})
        elif 'CU' in beam_path:
            results.update({lblm: devices[lblm].qdcraw_buffer(my_buffer) for lblm in my_wire.metadata.lblms})

        # 6) Release EDEF/BSA
        my_buffer.release()

        # 7) Return dictionary of Wire position, LBLM waveforms, BPM waveforms
        return results
