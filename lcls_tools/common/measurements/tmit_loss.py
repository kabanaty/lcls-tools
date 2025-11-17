from lcls_tools.common.devices.reader import create_bpm
from lcls_tools.common.measurements.measurement import Measurement
from lcls_tools.common.measurements.utils import collect_with_size_check
import pandas as pd
from edef import BSABuffer
from lcls_tools.common.devices.wire import Wire
from pydantic import model_validator
from typing import Optional
from pathlib import Path
import yaml


class TMITLoss(Measurement):
    name: str = "TMIT Loss Beam Size"
    my_buffer: BSABuffer
    beampath: str
    region: str
    beam_profile_device: Wire

    # Extra fields to be set after validation
    idx_before: Optional[list] = None
    idx_after: Optional[list] = None
    bpms: Optional[dict] = None

    @model_validator(mode="after")
    def run_setup(self) -> "TMITLoss":
        self.create_bpms()
        self.idx_before, self.idx_after = self.get_bpm_idx()
        return self

    def measure(self):
        """
        Compute the TMIT loss for a given beam path and region.

        This method orchestrates the full process of acquiring BPM data,
        normalizing it, and calculating TMIT loss by:
        - Reserving a data buffer.
        - Retrieving BPM elements and device names.
        - Identifying BPM indices before and after the wire.
        - Creating BPM objects.
        - Collecting TMIT data.
        - Computing the TMIT loss.

        Args:
            beampath (str): The beam path used to filter BPM elements.
            region (str): The region of interest, which determines the BPMs
                          used for before/after wire measurements.

        Returns:
            pd.Series: A Series representing the percentage TMIT loss for each
                       time sample.
        """
        # Retrieve data from BSA buffer
        data = self.get_bpm_data()

        # Calculate TMIT Loss
        tmit_loss_pd = self.calc_tmit_loss(data)
        tmit_loss = tmit_loss_pd.to_numpy()
        return tmit_loss

    def create_bpms(self):
        """
        Create BPM device objects for a given beampath.

        This method loads a YAML config file containing BPM definitions,
        filters them based on the specified beampath, and creates BPM objects.

        Returns:
            self.bpms (dict): A dictionary where the keys are BPM element
            names and the values are the corresponding BPM
            objects created using `create_bpm`.
        """
        bpms = {}
        all_bpms = self._load_yaml_config()
        bpm_strs = all_bpms[self.beampath]
        if bpm_strs is not None:
            for bpm in bpm_strs:
                name, area = bpm.split(":")
                bpm = create_bpm(name=name, area=area)
                if bpm is not None:
                    bpms[name] = bpm

        if bpms is not None:
            self.bpms = bpms
        else:
            raise LookupError("No BPM objects could be created.")

    def get_bpm_data(self):
        """
        Retrieve TMIT buffer data for a set of BPMs.

        This method iterates through a dictionary of BPM objects and attempts
        to fetch their TMIT buffer data using a specified buffer. If data
        retrieval fails for a BPM, it is assigned a `None` value.

        Args:
            bpm_obj_dict (dict): A dictionary where keys are BPM element
                                 names (str) and values are BPM objects.
            my_buffer (BSABuffer): The buffer used to retrieve TMIT data for
                                 each BPM.

        Returns:
            pd.DataFrame: A transposed DataFrame where:
                          - Rows correspond to BPM elements.
                          - Columns contain the retrieved TMIT buffer data.
        """
        data = {}

        for element, bpm in self.bpms.items():
            bpm_data = collect_with_size_check(
                bpm,
                "tmit_buffer",
                self.my_buffer,
                None,
            )
            data[element] = bpm_data

        df = pd.DataFrame(data)
        return df.T

    def get_bpm_idx(self):
        """
        Retrieve the index positions of BPMs before and after the wire for a
        given region.

        This method selects predefined BPMs based on the specified region and
        finds their corresponding indices in `bpms_devices`.

        Returns:
            tuple: A tuple containing:
                - list: Indices of BPMs located **before** the wire.
                - list: Indices of BPMs located **after** the wire.
        """
        bpms_before_wire = self.beam_profile_device.metadata.bpms_before_wire
        bpms_after_wire = self.beam_profile_device.metadata.bpms_after_wire

        # Create a lookup dictionary for index mapping
        idx_map = {value: idx for idx, value in enumerate(self.bpms.keys)}

        # Find indices of BPMs before and after the wire
        idx_before = [idx_map[item] for item in bpms_before_wire if item in idx_map]
        idx_after = [idx_map[item] for item in bpms_after_wire if item in idx_map]

        return idx_before, idx_after

    def calc_tmit_loss(self, df):
        """
        Calculate the TMIT loss.

        This method normalizes the TMIT data by computing row-wise medians,
        then standardizes it relative to BPMs before a wire. The loss is
        computed as the percentage change in mean TMIT values before and
        after the wire.

        Args:
            df (pd.DataFrame): A DataFrame containing TMIT values, where
                               rows correspond to BPMs and columns to
                               time samples.
            idx_before (list): List of row indices corresponding to BPMs
                               before the wire.
            idx_after (list): List of row indices corresponding to BPMs
                              after the wire.

        Returns:
            pd.Series: A Series representing the percentage TMIT loss for each
                       time sample.
        """
        # Compute row-wise medians and normalize the DataFrame
        row_medians = df.median(axis=1)
        df_ironed = df.div(row_medians, axis=0)

        # Compute mean ironed TMIT for BPMs before the wire
        ironed_before = df_ironed.iloc[self.idx_before, :]
        mean_iron_before = ironed_before.mean()

        # Normalize by mean TMIT before the wire
        df_normed = df_ironed.div(mean_iron_before, axis=1)

        # Compute mean ratios before and after the wire
        normed_before = df_normed.iloc[self.idx_before]
        normed_after = df_normed.iloc[self.idx_after]

        mean_before = normed_before.mean()
        mean_after = normed_after.mean()

        # Compute TMIT Loss percentage
        tmit_loss = (mean_before - mean_after) * 100
        return tmit_loss

    def _load_yaml_config(self):
        file_to_open = (
            Path(__file__).resolve().parent.parent
            / "devices"
            / "yaml"
            / "tmit_loss_bpms.yaml"
        )

        if file_to_open.exists() is False:
            msg = f"YAML config file {file_to_open} not found."
            self.logger.error(msg)
            return None

        with open(file_to_open, "r") as f:
            bpms = yaml.safe_load(f)
            return bpms
