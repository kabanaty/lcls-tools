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
        # IN10
        "WS10561": {"lblms": []},
        # LI11
        "WS11444": {"lblms": []},
        "WS11614": {"lblms": []},
        "WS11744": {"lblms": []},
        # LI12
        "WS12214": {"lblms": []},
        # LI18
        "WS18944": {"lblms": []},
        # LI19
        "WS19144": {"lblms": []},
        "WS19244": {"lblms": []},
        "WS19344": {"lblms": []},
        # LI20
        "IPWS1": {"lblms": []},
        "IPWS3": {"lblms": []},
        # IN20
        "WS01": {"lblms": []},
        "WS02": {"lblms": []},
        "WS03": {"lblms": []},
        "WS04": {"lblms": []},
        # LI21
        "WS11": {"lblms": []},
        "WS12": {"lblms": []},
        "WS13": {"lblms": []},
        # LI24
        "WS24": {"lblms": []},
        # LI28
        "WS27644": {"lblms": []},
        "WS28144": {"lblms": []},
        "WS28444": {"lblms": []},
        "WS28744": {"lblms": []},
        # HTR
        "WS0H04": {"lblms": []},
        # DIAG0
        "WSDG0": {"lblms": []},
        # COL1
        "WSC104": {"lblms": []},
        "WSC106": {"lblms": []},
        "WSC108": {"lblms": []},
        "WSC110": {"lblms": []},
        # EMIT2
        "WSEMIT2": {"lblms": []},
        # BYP
        "WSBP1": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP2": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP3": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP4": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        # SPD
        "WSSP1D": {"lblms": []},
        # LTUH
        "WSVM2": {"lblms": []},
        "WSDL31": {"lblms": []},
        "WSDL4": {"lblms": []},
        "WS31": {"lblms": []},
        "WS32": {"lblms": []},
        "WS33": {"lblms": []},
        "WS34": {"lblms": []},
        # LTUS
        "WS31B": {"lblms": []},
        "WS32B": {"lblms": []},
        "WS33B": {"lblms": []},
        "WS34B": {"lblms": []},
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
