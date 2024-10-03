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
        "WS01": {"lblms": ['PMTINJ03', 'PMTINJ04', 'PMTINJ01', 'PMTINJ02', 'PMTINJ05', 'PMTINJ06']},
        "WS02": {"lblms": ['PMTINJ03', 'PMTINJ04', 'PMTINJ01', 'PMTINJ02', 'PMTINJ05', 'PMTINJ06']},
        "WS03": {"lblms": ['PMTINJ03', 'PMTINJ04', 'PMTINJ01', 'PMTINJ02', 'PMTINJ05', 'PMTINJ06']},
        "WS04": {"lblms": ['PMTINJ03', 'PMTINJ04', 'PMTINJ01', 'PMTINJ02', 'PMTINJ05', 'PMTINJ06']},
        # LI21
        "WS11": {"lblms": ['PMT2111', 'PMT21293', 'PMT2113', 'PMT21350', 'PMT2114', 'PMT2115']},
        "WS12": {"lblms": ['PMT2111', 'PMT21293', 'PMT2113', 'PMT21350', 'PMT2114', 'PMT2115']},
        "WS13": {"lblms": ['PMT2111', 'PMT21293', 'PMT2113', 'PMT21350', 'PMT2114', 'PMT2115']},
        # LI24
        "WS24": {"lblms": ['PMT24705', 'PMT24706']},
        # LI28
        "WS27644": {"lblms": ['PTM28750', 'PMT29150', 'PMT756', 'PMT820']},
        "WS28144": {"lblms": ['PTM28750', 'PMT29150', 'PMT756', 'PMT820']},
        "WS28444": {"lblms": ['PTM28750', 'PMT29150', 'PMT756', 'PMT820']},
        "WS28744": {"lblms": ['PTM28750', 'PMT29150', 'PMT756', 'PMT820']},
        # HTR
        "WS0H04": {"lblms": ['LBLM01A']},
        # DIAG0
        "WSDG0": {"lblms": []},
        # COL1
        "WSC104": {"lblms": ['LBLM03A', 'LBLM04A']},
        "WSC106": {"lblms": ['LBLM03A', 'LBLM04A']},
        "WSC108": {"lblms": ['LBLM03A', 'LBLM04A']},
        "WSC110": {"lblms": ['LBLM03A', 'LBLM04A']},
        # EMIT2
        "WSEMIT2": {"lblms": ['LBLM04A', 'LBLM07A']},
        # BYP
        "WSBP1": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP2": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP3": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        "WSBP4": {"lblms": ["LBLM11A", "LBLM11A_1", "LBLM11A_2", "LBLM11A_3"]},
        # SPD
        "WSSP1D": {"lblms": ['LBLM22A']},
        # LTUH
        "WSVM2": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        "WSDL31": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        "WSDL4": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        "WS31": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        "WS32": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        "WS33": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        "WS34": {"lblms": ['PMT122', 'PMT246', 'PMT550', 'PMT755', 'PMT756']},
        # LTUS
        "WS31B": {"lblms": ['LBLMS32A']},
        "WS32B": {"lblms": ['LBLMS32A']},
        "WS33B": {"lblms": ['LBLMS32A']},
        "WS34B": {"lblms": ['LBLMS32A']},
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
