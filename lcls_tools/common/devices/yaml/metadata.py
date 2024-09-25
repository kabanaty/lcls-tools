from typing import List


def get_magnet_metadata(magnet_names: List[str] = []):
    # return a data structure of the form:
    # {
    #  mag-name-1 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  mag-name-2 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  ...
    # }
    if magnet_names:
        raise NotImplementedError(
            "No method of getting additional metadata for magnets."
        )
    return {}


def get_screen_metadata(screen_names: List[str] = []):
    # return a data structure of the form:
    # {
    #  scr-name-1 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  scr-name-2 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  ...
    # }
    if screen_names:
        raise NotImplementedError(
            "No method of getting additional metadata for screens."
        )
    return {}


def get_wire_metadata(wire_names: List[str] = []):
    # return a data structure of the form:
    # {
    #  wire-name-1 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  wire-name-2 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  ...
    # }
    wire_metadata = {
        "WSBP1": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP2": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP3": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP4": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
    }
    return wire_metadata


def get_lblm_metadata(lblm_names: List[str] = []):
    # return a data structure of the form:
    # {
    #  lblm-name-1 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  lblm-name-2 : {metadata-field-1 : value-1, metadata-field-2 : value-2},
    #  ...
    # }
    if lblm_names:
        raise NotImplementedError(
            "No method of getting additional metadata for wires."
        )
    return {}
