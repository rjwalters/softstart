#!/usr/bin/env python3
"""
Generator Soft-Start Schematic Generator

Uses kicad-tools to programmatically create the schematic for the
supercapacitor-based power assist system.

Design spec from project.kct:
- 60x Tecate 12F 2.7V supercaps (30S x 2 banks)
- STM32G031F6P6 MCU
- H11AA1 zero-crossing detection
- INA180 current sense amplifier
- IRFB4110 discharge MOSFETs
"""

import sys
from pathlib import Path

# Add kicad-tools to path if not installed
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "kicad-tools" / "src"))

from kicad_tools.schematic.models import Schematic, SnapMode


def create_softstart_schematic():
    """Create the soft-start schematic."""

    # Create the schematic with title block info
    sch = Schematic(
        title="Generator Soft-Start",
        date="2025-01",
        revision="A",
        company="",
        comment1="Supercapacitor Power Assist for Starting AC Loads",
        comment2="Target: 8000 BTU AC on Honda EU1000i",
        paper="A3",  # Large format for 60+ components
        snap_mode=SnapMode.AUTO,
    )

    # =========================================================================
    # Define grid layout regions (in mm)
    # =========================================================================
    # Sheet is A3: 420mm x 297mm
    # Layout organized to avoid overlaps:
    #   - Left column: AC input, supercap banks
    #   - Center column: MCU, sensing
    #   - Right column: Charging, discharge

    # Left side: Power input and AC path
    AC_INPUT_X = 25
    AC_INPUT_Y = 40

    # Center-left: Supercap banks (3 rows x 10 cols, 15mm spacing)
    SUPERCAP_POS_X = 25
    SUPERCAP_POS_Y = 90
    SUPERCAP_NEG_X = 25
    SUPERCAP_NEG_Y = 170

    # Center: Control circuitry (shifted to avoid supercap area)
    MCU_X = 200
    MCU_Y = 50
    SENSING_X = 200
    SENSING_Y = 130

    # Right side: Discharge circuits (far right to avoid charging overlap)
    DISCHARGE_X = 380
    DISCHARGE_Y = 100

    # Top: Power rails / regulation
    POWER_REG_X = 120
    POWER_REG_Y = 25

    # =========================================================================
    # Power Rails (Y coordinates for horizontal rails)
    # =========================================================================
    RAIL_VCC = 25.4  # 3.3V MCU power
    RAIL_GND = 279.4  # Ground

    # =========================================================================
    # Section 1: AC Input / Power Entry (No fuse - rely on generator breaker)
    # =========================================================================
    print("Adding AC input section...")

    # AC input connector (2-pin terminal block)
    j_ac_in = sch.add_symbol(
        lib_id="Connector:Screw_Terminal_01x02",
        x=AC_INPUT_X, y=AC_INPUT_Y,
        ref="J1", value="AC_IN",
        rotation=0,
        footprint="TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
    )

    # Varistor for surge protection
    rv1 = sch.add_symbol(
        lib_id="Device:Varistor",
        x=AC_INPUT_X + 40, y=AC_INPUT_Y + 15,
        ref="RV1", value="275VAC",
        rotation=0,
        footprint="Varistor:RV_Disc_D12mm_W4.2mm_P7.5mm"
    )

    # AC output connector (pass-through to load)
    j_ac_out = sch.add_symbol(
        lib_id="Connector:Screw_Terminal_01x02",
        x=AC_INPUT_X + 70, y=AC_INPUT_Y,
        ref="J2", value="AC_OUT",
        rotation=180,
        footprint="TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
    )

    # Labels for AC nets
    sch.add_label("AC_L", AC_INPUT_X + 15, AC_INPUT_Y - 5)
    sch.add_label("AC_N", AC_INPUT_X + 15, AC_INPUT_Y + 25)

    # =========================================================================
    # Section 2: Zero-Crossing Detection
    # =========================================================================
    print("Adding zero-crossing detection...")

    # H11AA1 AC input optocoupler
    u_zc = sch.add_symbol(
        lib_id="Isolator:H11AA1",
        x=SENSING_X, y=SENSING_Y,
        ref="U2", value="H11AA1",
        rotation=0,
        footprint="Package_DIP:DIP-6_W7.62mm"
    )

    # Input current limiting resistors (0805)
    r_zc1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 30, y=SENSING_Y - 10,
        ref="R1", value="47k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_zc2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 30, y=SENSING_Y + 10,
        ref="R2", value="47k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    # Output pullup resistor (0805)
    r_zc_pull = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X + 30, y=SENSING_Y - 20,
        ref="R3", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("ZC_OUT", SENSING_X + 40, SENSING_Y)

    # =========================================================================
    # Section 3: MCU Section (STM32G031F6P6)
    # =========================================================================
    print("Adding MCU section...")

    # STM32G031F6P6 - TSSOP20
    u_mcu = sch.add_symbol(
        lib_id="MCU_ST_STM32G0:STM32G031F6Px",
        x=MCU_X, y=MCU_Y,
        ref="U1", value="STM32G031F6P6",
        rotation=0,
        footprint="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm"
    )

    # Bypass capacitors for MCU (0805)
    c_mcu1 = sch.add_symbol(
        lib_id="Device:C",
        x=MCU_X - 40, y=MCU_Y - 20,
        ref="C1", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_mcu2 = sch.add_symbol(
        lib_id="Device:C",
        x=MCU_X - 40, y=MCU_Y,
        ref="C2", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_mcu3 = sch.add_symbol(
        lib_id="Device:C",
        x=MCU_X - 40, y=MCU_Y + 20,
        ref="C3", value="4.7uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # =========================================================================
    # Section 4: 3.3V LDO Regulator
    # =========================================================================
    print("Adding power regulation...")

    # LDO regulator (AMS1117-3.3 in SOT-223)
    u_ldo = sch.add_symbol(
        lib_id="Regulator_Linear:AMS1117-3.3",
        x=POWER_REG_X, y=POWER_REG_Y,
        ref="U3", value="AMS1117-3.3",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    # Input capacitor (0805 for 10uF)
    c_ldo_in = sch.add_symbol(
        lib_id="Device:C",
        x=POWER_REG_X - 30, y=POWER_REG_Y + 15,
        ref="C4", value="10uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Output capacitors
    c_ldo_out1 = sch.add_symbol(
        lib_id="Device:C",
        x=POWER_REG_X + 30, y=POWER_REG_Y + 15,
        ref="C5", value="10uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_ldo_out2 = sch.add_symbol(
        lib_id="Device:C",
        x=POWER_REG_X + 40, y=POWER_REG_Y + 15,
        ref="C6", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Power labels
    sch.add_power("power:+3.3V", POWER_REG_X + 35, POWER_REG_Y - 10)
    sch.add_power("power:GND", POWER_REG_X, POWER_REG_Y + 30)

    # =========================================================================
    # Section 5: Current Sensing (INA180)
    # =========================================================================
    print("Adding current sensing...")

    # INA180 current sense amplifier (50V/V gain) - SOT-23-5
    u_ina = sch.add_symbol(
        lib_id="Amplifier_Current:INA180A1",
        x=SENSING_X + 80, y=SENSING_Y,
        ref="U4", value="INA180A1",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Current shunt resistor (5mOhm) - 2512 for power handling
    r_shunt = sch.add_symbol(
        lib_id="Device:R_Shunt",
        x=SENSING_X + 80, y=SENSING_Y + 40,
        ref="R4", value="5mR",
        rotation=0,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )

    # Bypass cap for INA180 (0805)
    c_ina = sch.add_symbol(
        lib_id="Device:C",
        x=SENSING_X + 100, y=SENSING_Y - 20,
        ref="C7", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    sch.add_label("I_SENSE", SENSING_X + 100, SENSING_Y)

    # =========================================================================
    # Section 6: Voltage Sensing (AC and Supercap)
    # =========================================================================
    print("Adding voltage sensing dividers...")

    # AC voltage sensing - resistor divider with protection (0805)
    r_vac1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 60, y=SENSING_Y + 50,
        ref="R5", value="1M",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_vac2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 60, y=SENSING_Y + 70,
        ref="R6", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    sch.add_label("V_AC_SENSE", SENSING_X - 50, SENSING_Y + 60)

    # Supercap bank voltage sensing (x2 for each bank) - 0805
    # Positive bank divider
    r_vsc_p1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 80, y=SENSING_Y + 50,
        ref="R7", value="820k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_vsc_p2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 80, y=SENSING_Y + 70,
        ref="R8", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    sch.add_label("V_SC_POS", SENSING_X - 70, SENSING_Y + 60)

    # Negative bank divider
    r_vsc_n1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 100, y=SENSING_Y + 50,
        ref="R9", value="820k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_vsc_n2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSING_X - 100, y=SENSING_Y + 70,
        ref="R10", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    sch.add_label("V_SC_NEG", SENSING_X - 90, SENSING_Y + 60)

    # =========================================================================
    # Section 7: Charging Circuits (2x banks)
    # =========================================================================
    print("Adding charging circuits...")

    # Charging resistors (current-limited from AC) - 2512 for 5W
    # Position charging circuits between supercaps and discharge
    CHG_X = 300  # X position for charging circuits

    # Positive bank charging
    r_chg_pos = sch.add_symbol(
        lib_id="Device:R",
        x=CHG_X, y=SUPERCAP_POS_Y,
        ref="R11", value="100R 5W",
        rotation=90,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )

    # Charging enable MOSFET (MCU controlled) - SOT-23
    q_chg_pos = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=CHG_X + 25, y=SUPERCAP_POS_Y,
        ref="Q3", value="AO3400",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23"
    )

    # Negative bank charging
    r_chg_neg = sch.add_symbol(
        lib_id="Device:R",
        x=CHG_X, y=SUPERCAP_NEG_Y,
        ref="R12", value="100R 5W",
        rotation=90,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )

    q_chg_neg = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=CHG_X + 25, y=SUPERCAP_NEG_Y,
        ref="Q4", value="AO3400",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23"
    )

    sch.add_label("CHG_EN_POS", CHG_X + 25, SUPERCAP_POS_Y - 15)
    sch.add_label("CHG_EN_NEG", CHG_X + 25, SUPERCAP_NEG_Y - 15)

    # =========================================================================
    # Section 8: Discharge Circuits (2x IRFB4110 MOSFETs)
    # =========================================================================
    print("Adding discharge circuits...")

    # Positive half-cycle discharge MOSFET - TO-220
    q_dis_pos = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=DISCHARGE_X, y=DISCHARGE_Y,
        ref="Q1", value="IRFB4110",
        rotation=0,
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )

    # Gate resistor (0805)
    r_gate_pos = sch.add_symbol(
        lib_id="Device:R",
        x=DISCHARGE_X - 30, y=DISCHARGE_Y,
        ref="R13", value="100R",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    # Gate-source pulldown (0805)
    r_gs_pos = sch.add_symbol(
        lib_id="Device:R",
        x=DISCHARGE_X - 15, y=DISCHARGE_Y + 20,
        ref="R14", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("PWM_POS", DISCHARGE_X - 40, DISCHARGE_Y)

    # Negative half-cycle discharge MOSFET - TO-220
    q_dis_neg = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=DISCHARGE_X, y=DISCHARGE_Y + 80,
        ref="Q2", value="IRFB4110",
        rotation=0,
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )

    r_gate_neg = sch.add_symbol(
        lib_id="Device:R",
        x=DISCHARGE_X - 30, y=DISCHARGE_Y + 80,
        ref="R15", value="100R",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    r_gs_neg = sch.add_symbol(
        lib_id="Device:R",
        x=DISCHARGE_X - 15, y=DISCHARGE_Y + 100,
        ref="R16", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("PWM_NEG", DISCHARGE_X - 40, DISCHARGE_Y + 80)

    # =========================================================================
    # Section 9: Supercapacitor Banks (60x total, 30 per bank)
    # =========================================================================
    print("Adding supercapacitor banks (60 cells)...")

    # Positive bank: 30 cells in series
    # Arranged in 3 rows of 10
    # Tecate TPLH-2R7/12WR10X30: 10mm dia x 30mm radial
    cap_refs_pos = []
    for row in range(3):
        for col in range(10):
            idx = row * 10 + col + 1
            ref = f"C{100 + idx}"  # C101-C130
            cap = sch.add_symbol(
                lib_id="Device:C",  # Supercap
                x=SUPERCAP_POS_X + col * 15,
                y=SUPERCAP_POS_Y + row * 20,
                ref=ref,
                value="12F 2.7V",
                rotation=0,
                footprint="Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
            )
            cap_refs_pos.append(cap)

    # Negative bank: 30 cells in series
    cap_refs_neg = []
    for row in range(3):
        for col in range(10):
            idx = row * 10 + col + 1
            ref = f"C{130 + idx}"  # C131-C160
            cap = sch.add_symbol(
                lib_id="Device:C",  # Supercap
                x=SUPERCAP_NEG_X + col * 15,
                y=SUPERCAP_NEG_Y + row * 20,
                ref=ref,
                value="12F 2.7V",
                rotation=0,
                footprint="Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
            )
            cap_refs_neg.append(cap)

    # Labels for supercap banks
    sch.add_label("SC_POS+", SUPERCAP_POS_X - 10, SUPERCAP_POS_Y)
    sch.add_label("SC_POS-", SUPERCAP_POS_X + 155, SUPERCAP_POS_Y + 40)
    sch.add_label("SC_NEG+", SUPERCAP_NEG_X - 10, SUPERCAP_NEG_Y)
    sch.add_label("SC_NEG-", SUPERCAP_NEG_X + 155, SUPERCAP_NEG_Y + 40)

    # =========================================================================
    # Section 10: Debug Header (SWD)
    # =========================================================================
    print("Adding debug header...")

    # SWD debug connector (5-pin: VCC, GND, SWDIO, SWCLK, NRST)
    j_swd = sch.add_symbol(
        lib_id="Connector:Conn_01x05_Pin",
        x=MCU_X + 80, y=MCU_Y - 20,
        ref="J3", value="SWD",
        rotation=0,
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
    )

    sch.add_label("SWDIO", MCU_X + 70, MCU_Y - 30)
    sch.add_label("SWCLK", MCU_X + 70, MCU_Y - 20)
    sch.add_label("NRST", MCU_X + 70, MCU_Y - 10)

    # =========================================================================
    # Section 11: Status LED
    # =========================================================================
    print("Adding status LED...")

    # Status LED with current limiting resistor (0805 LED and resistor)
    d_led = sch.add_symbol(
        lib_id="Device:LED",
        x=MCU_X + 60, y=MCU_Y + 40,
        ref="D1", value="Green",
        rotation=90,
        footprint="LED_SMD:LED_0805_2012Metric"
    )

    r_led = sch.add_symbol(
        lib_id="Device:R",
        x=MCU_X + 60, y=MCU_Y + 25,
        ref="R17", value="330R",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("LED_STATUS", MCU_X + 50, MCU_Y + 40)

    # =========================================================================
    # Add power symbols
    # =========================================================================
    print("Adding power symbols...")

    # Add PWR_FLAGs where power enters the design
    sch.add_pwr_flag(POWER_REG_X - 40, POWER_REG_Y)  # Input power
    sch.add_pwr_flag(POWER_REG_X + 35, POWER_REG_Y - 5)  # 3.3V output

    # Ground symbols at key locations
    gnd_mcu = sch.add_power("power:GND", MCU_X - 40, MCU_Y + 40)
    gnd_sense = sch.add_power("power:GND", SENSING_X + 80, SENSING_Y + 60)
    gnd_dis1 = sch.add_power("power:GND", DISCHARGE_X, DISCHARGE_Y + 40)
    gnd_dis2 = sch.add_power("power:GND", DISCHARGE_X, DISCHARGE_Y + 120)

    # =========================================================================
    # Section 12: Wiring - Connect all sections
    # =========================================================================
    print("Adding wiring...")

    # --- Power Rails ---
    # Define rail Y coordinates
    RAIL_3V3 = POWER_REG_Y - 15  # 3.3V rail
    RAIL_GND = POWER_REG_Y + 40  # Ground rail near LDO

    # 3.3V rail from LDO output to MCU area
    sch.add_segmented_rail(
        y=RAIL_3V3,
        x_points=[POWER_REG_X + 30, MCU_X - 40, MCU_X + 60],
        net_label="+3V3"
    )

    # --- LDO Wiring ---
    # Wire LDO input cap
    sch.wire_pins(c_ldo_in, "1", u_ldo, "VI")
    # Wire LDO output to 3.3V rail
    sch.wire_pin_to_point(u_ldo, "VO", (POWER_REG_X + 30, RAIL_3V3))
    # Wire LDO output caps to 3.3V rail
    sch.wire_to_rail(c_ldo_out1, "1", RAIL_3V3)
    sch.wire_to_rail(c_ldo_out2, "1", RAIL_3V3)
    # Wire LDO and caps to ground
    sch.wire_pin_to_point(u_ldo, "GND", (POWER_REG_X, RAIL_GND))
    sch.wire_pin_to_point(c_ldo_in, "2", (POWER_REG_X - 30, RAIL_GND))
    sch.wire_pin_to_point(c_ldo_out1, "2", (POWER_REG_X + 30, RAIL_GND))
    sch.wire_pin_to_point(c_ldo_out2, "2", (POWER_REG_X + 40, RAIL_GND))
    # Ground rail segment
    sch.add_segmented_rail(y=RAIL_GND, x_points=[POWER_REG_X - 30, POWER_REG_X, POWER_REG_X + 30, POWER_REG_X + 40])

    # --- MCU Bypass Caps Wiring ---
    # Wire MCU bypass caps to 3.3V rail
    sch.wire_to_rail(c_mcu1, "1", RAIL_3V3)
    sch.wire_to_rail(c_mcu2, "1", RAIL_3V3)
    sch.wire_to_rail(c_mcu3, "1", RAIL_3V3)
    # Wire MCU VDD to 3.3V rail
    sch.wire_pin_to_point(u_mcu, "VDD", (MCU_X, RAIL_3V3))
    # Wire MCU VSS to ground (add a local GND symbol)
    mcu_gnd_y = MCU_Y + 30
    sch.add_power("power:GND", MCU_X, mcu_gnd_y)
    sch.wire_pin_to_point(u_mcu, "VSS", (MCU_X, mcu_gnd_y - 5))
    # Wire bypass caps to MCU ground
    sch.wire_pin_to_point(c_mcu1, "2", (MCU_X - 40, mcu_gnd_y - 5))
    sch.wire_pin_to_point(c_mcu2, "2", (MCU_X - 40, mcu_gnd_y - 5))
    sch.wire_pin_to_point(c_mcu3, "2", (MCU_X - 40, mcu_gnd_y - 5))

    # --- Zero-Crossing Circuit Wiring ---
    # Wire ZC pullup to 3.3V (local power symbol)
    sch.add_power("power:+3.3V", SENSING_X + 30, SENSING_Y - 35)
    sch.wire_pin_to_point(r_zc_pull, "1", (SENSING_X + 30, SENSING_Y - 30))

    # Wire ZC input resistors in series
    sch.wire_pins(r_zc1, "2", r_zc2, "1")

    # --- Voltage Divider Wiring ---
    # Wire voltage divider pairs
    sch.wire_pins(r_vac1, "2", r_vac2, "1")
    sch.wire_pins(r_vsc_p1, "2", r_vsc_p2, "1")
    sch.wire_pins(r_vsc_n1, "2", r_vsc_n2, "1")

    # --- INA180 Current Sense Amp Wiring ---
    # Power for INA180 (local power symbols)
    ina_pwr_x = SENSING_X + 80
    sch.add_power("power:+3.3V", ina_pwr_x, SENSING_Y - 15)
    sch.wire_pin_to_point(u_ina, "V+", (ina_pwr_x, SENSING_Y - 10))
    sch.add_power("power:GND", ina_pwr_x, SENSING_Y + 15)
    sch.wire_pin_to_point(u_ina, "GND", (ina_pwr_x, SENSING_Y + 10))
    # Wire bypass cap for INA180
    sch.wire_pin_to_point(c_ina, "1", (ina_pwr_x + 20, SENSING_Y - 10))
    sch.wire_pin_to_point(c_ina, "2", (ina_pwr_x + 20, SENSING_Y + 10))

    # --- LED Wiring ---
    # Wire LED resistor to LED
    sch.wire_pins(r_led, "2", d_led, "A")

    # --- Discharge MOSFET Wiring ---
    # Wire gate resistors to MOSFETs
    sch.wire_pins(r_gate_pos, "2", q_dis_pos, "G")
    sch.wire_pins(r_gate_neg, "2", q_dis_neg, "G")

    # Wire gate-source pulldowns
    sch.wire_pins(r_gs_pos, "1", q_dis_pos, "G")
    sch.wire_pins(r_gs_neg, "1", q_dis_neg, "G")

    # --- Supercap Bank Series Wiring ---
    # Wire positive bank supercaps in series (connect adjacent caps)
    print("  Wiring positive supercap bank in series...")
    for i in range(len(cap_refs_pos) - 1):
        # Connect pin 2 of cap[i] to pin 1 of cap[i+1]
        try:
            sch.wire_pins(cap_refs_pos[i], "2", cap_refs_pos[i + 1], "1")
        except Exception as e:
            print(f"    Warning: Could not wire C{101+i} to C{102+i}: {e}")

    # Wire negative bank supercaps in series
    print("  Wiring negative supercap bank in series...")
    for i in range(len(cap_refs_neg) - 1):
        try:
            sch.wire_pins(cap_refs_neg[i], "2", cap_refs_neg[i + 1], "1")
        except Exception as e:
            print(f"    Warning: Could not wire C{131+i} to C{132+i}: {e}")

    print(f"  Added {len(sch.wires)} wires")

    # --- MCU Signal Connections ---
    print("  Wiring MCU to signals...")

    # Get MCU pin positions for signal routing
    # PA0 -> ZC_OUT (zero-crossing input)
    mcu_pa0 = u_mcu.pin_position("PA0")
    sch.add_label("ZC_OUT", mcu_pa0[0] + 10, mcu_pa0[1])
    sch.add_wire(mcu_pa0, (mcu_pa0[0] + 10, mcu_pa0[1]))

    # PA1 -> V_AC_SENSE (ADC)
    mcu_pa1 = u_mcu.pin_position("PA1")
    sch.add_label("V_AC_SENSE", mcu_pa1[0] + 10, mcu_pa1[1])
    sch.add_wire(mcu_pa1, (mcu_pa1[0] + 10, mcu_pa1[1]))

    # PA2 -> V_SC_POS (ADC)
    mcu_pa2 = u_mcu.pin_position("PA2")
    sch.add_label("V_SC_POS", mcu_pa2[0] + 10, mcu_pa2[1])
    sch.add_wire(mcu_pa2, (mcu_pa2[0] + 10, mcu_pa2[1]))

    # PA3 -> V_SC_NEG (ADC)
    mcu_pa3 = u_mcu.pin_position("PA3")
    sch.add_label("V_SC_NEG", mcu_pa3[0] + 10, mcu_pa3[1])
    sch.add_wire(mcu_pa3, (mcu_pa3[0] + 10, mcu_pa3[1]))

    # PA4 -> I_SENSE (ADC)
    mcu_pa4 = u_mcu.pin_position("PA4")
    sch.add_label("I_SENSE", mcu_pa4[0] + 10, mcu_pa4[1])
    sch.add_wire(mcu_pa4, (mcu_pa4[0] + 10, mcu_pa4[1]))

    # PA5 -> CHG_EN_POS (GPIO output)
    mcu_pa5 = u_mcu.pin_position("PA5")
    sch.add_label("CHG_EN_POS", mcu_pa5[0] + 10, mcu_pa5[1])
    sch.add_wire(mcu_pa5, (mcu_pa5[0] + 10, mcu_pa5[1]))

    # PA6 -> PWM_POS (TIM3_CH1)
    mcu_pa6 = u_mcu.pin_position("PA6")
    sch.add_label("PWM_POS", mcu_pa6[0] + 10, mcu_pa6[1])
    sch.add_wire(mcu_pa6, (mcu_pa6[0] + 10, mcu_pa6[1]))

    # PA7 -> PWM_NEG (TIM3_CH2)
    mcu_pa7 = u_mcu.pin_position("PA7")
    sch.add_label("PWM_NEG", mcu_pa7[0] + 10, mcu_pa7[1])
    sch.add_wire(mcu_pa7, (mcu_pa7[0] + 10, mcu_pa7[1]))

    # PA8 -> CHG_EN_NEG (GPIO output)
    mcu_pa8 = u_mcu.pin_position("PA8/PB0/PB1/PB2")
    sch.add_label("CHG_EN_NEG", mcu_pa8[0] + 10, mcu_pa8[1])
    sch.add_wire(mcu_pa8, (mcu_pa8[0] + 10, mcu_pa8[1]))

    # PA11 -> LED_STATUS (GPIO output)
    mcu_pa11 = u_mcu.pin_position("PA9/PA11")
    sch.add_label("LED_STATUS", mcu_pa11[0] + 10, mcu_pa11[1])
    sch.add_wire(mcu_pa11, (mcu_pa11[0] + 10, mcu_pa11[1]))

    # PA13 -> SWDIO
    mcu_pa13 = u_mcu.pin_position("PA13")
    sch.add_label("SWDIO", mcu_pa13[0] + 10, mcu_pa13[1])
    sch.add_wire(mcu_pa13, (mcu_pa13[0] + 10, mcu_pa13[1]))

    # PA14 -> SWCLK
    mcu_pa14 = u_mcu.pin_position("PA14/PA15")
    sch.add_label("SWCLK", mcu_pa14[0] + 10, mcu_pa14[1])
    sch.add_wire(mcu_pa14, (mcu_pa14[0] + 10, mcu_pa14[1]))

    # PF2 -> NRST (directly to debug header)
    mcu_nrst = u_mcu.pin_position("PF2")
    sch.add_label("NRST", mcu_nrst[0] - 10, mcu_nrst[1])
    sch.add_wire(mcu_nrst, (mcu_nrst[0] - 10, mcu_nrst[1]))

    print(f"  Total wires: {len(sch.wires)}")

    # =========================================================================
    # Save the schematic
    # =========================================================================
    output_path = Path(__file__).parent / "softstart.kicad_sch"
    print(f"Saving schematic to {output_path}...")
    sch.write(str(output_path))

    print("Schematic generation complete!")
    print(f"  Total symbols: {len(sch.symbols)}")
    print(f"  Power symbols: {len(sch.power_symbols)}")
    print(f"  Labels: {len(sch.labels)}")

    return sch


if __name__ == "__main__":
    create_softstart_schematic()
