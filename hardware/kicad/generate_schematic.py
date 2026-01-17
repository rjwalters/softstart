#!/usr/bin/env python3
"""
Generator Soft-Start Schematic Generator - Revision B

Uses kicad-tools to programmatically create the schematic for the
supercapacitor-based power assist system.

Rev B changes from project.kct:
- Back-to-back FETs (4x IRFB4110) for true bidirectional off
- Gate drivers (2x UCC27211) with UVLO
- Gate protection (TVS clamps, bleeders, failsafe pull-down)
- Precharge circuits (2x paths)
- Hardware overcurrent (LMV331 comparator with blanking)
- 12V supply for gate drivers
- Droop-triggered control (not PWM)
"""

import sys
from pathlib import Path

# Add kicad-tools to path if not installed
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "kicad-tools" / "src"))

from kicad_tools.schematic.models import Schematic, SnapMode


def create_softstart_schematic():
    """Create the soft-start schematic Rev B."""

    # Create the schematic with title block info
    sch = Schematic(
        title="Generator Soft-Start",
        date="2025-01",
        revision="B",
        company="",
        comment1="Supercapacitor Power Assist - Droop Triggered",
        comment2="Back-to-back FETs, Gate Drivers, Hardware OCP",
        paper="A3",  # Large format for 60+ components
        snap_mode=SnapMode.AUTO,
    )

    # =========================================================================
    # Layout Grid (A3: 420mm x 297mm)
    # =========================================================================
    # Left: AC input, supercap banks
    # Center: MCU, sensing, power supplies
    # Right: Gate drivers, discharge FETs, precharge

    # AC Input section
    AC_X = 25
    AC_Y = 40

    # Supercap banks (3 rows x 10 cols each)
    SC_POS_X = 25
    SC_POS_Y = 85
    SC_NEG_X = 25
    SC_NEG_Y = 160

    # Power supplies (12V and 3.3V)
    PWR_X = 200
    PWR_Y = 20

    # MCU section
    MCU_X = 200
    MCU_Y = 70

    # Sensing section
    SENSE_X = 200
    SENSE_Y = 140

    # Gate drivers and discharge FETs
    GATE_X = 320
    GATE_Y = 50

    # Precharge section
    PRECHG_X = 320
    PRECHG_Y = 150

    # =========================================================================
    # Section 1: AC Input / Power Entry
    # =========================================================================
    print("Adding AC input section...")

    j_ac_in = sch.add_symbol(
        lib_id="Connector:Screw_Terminal_01x02",
        x=AC_X, y=AC_Y,
        ref="J1", value="AC_IN",
        rotation=0,
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal"
    )

    rv1 = sch.add_symbol(
        lib_id="Device:Varistor",
        x=AC_X + 30, y=AC_Y + 12,
        ref="RV1", value="275VAC",
        rotation=0,
        footprint="Varistor:RV_Disc_D12mm_W4.2mm_P7.5mm"
    )

    j_ac_out = sch.add_symbol(
        lib_id="Connector:Screw_Terminal_01x02",
        x=AC_X + 60, y=AC_Y,
        ref="J2", value="AC_OUT",
        rotation=180,
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal"
    )

    sch.add_label("AC_L", AC_X + 15, AC_Y - 2)
    sch.add_label("AC_N", AC_X + 15, AC_Y + 25)

    # =========================================================================
    # Section 2: 12V Supply for Gate Drivers
    # =========================================================================
    print("Adding 12V gate driver supply...")

    # Bridge rectifier for 12V supply (small, from AC)
    d_bridge = sch.add_symbol(
        lib_id="Diode_Bridge:MB6S",
        x=PWR_X - 60, y=PWR_Y + 15,
        ref="D5", value="MB6S",
        rotation=0,
        footprint="Package_TO_SOT_SMD:TO-269AA"
    )

    # Filter cap after bridge
    c_12v_in = sch.add_symbol(
        lib_id="Device:C",
        x=PWR_X - 35, y=PWR_Y + 25,
        ref="C8", value="100uF",
        rotation=0,
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )

    # 12V regulator (LM7812)
    u_12v = sch.add_symbol(
        lib_id="Regulator_Linear:L7812",
        x=PWR_X - 10, y=PWR_Y + 15,
        ref="U7", value="LM7812",
        rotation=0,
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )

    c_12v_out = sch.add_symbol(
        lib_id="Device:C",
        x=PWR_X + 15, y=PWR_Y + 25,
        ref="C9", value="10uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    sch.add_label("+12V", PWR_X + 20, PWR_Y + 10)

    # =========================================================================
    # Section 3: 3.3V MCU Supply
    # =========================================================================
    print("Adding 3.3V MCU supply...")

    u_3v3 = sch.add_symbol(
        lib_id="Regulator_Linear:AMS1117-3.3",
        x=PWR_X + 50, y=PWR_Y + 15,
        ref="U8", value="AMS1117-3.3",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    c_3v3_in = sch.add_symbol(
        lib_id="Device:C",
        x=PWR_X + 35, y=PWR_Y + 25,
        ref="C10", value="10uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    c_3v3_out1 = sch.add_symbol(
        lib_id="Device:C",
        x=PWR_X + 65, y=PWR_Y + 25,
        ref="C11", value="10uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    c_3v3_out2 = sch.add_symbol(
        lib_id="Device:C",
        x=PWR_X + 80, y=PWR_Y + 25,
        ref="C12", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Note: Power symbols are added during wiring phase with proper connections

    # =========================================================================
    # Section 4: MCU (STM32G031F6P6)
    # =========================================================================
    print("Adding MCU section...")

    u_mcu = sch.add_symbol(
        lib_id="MCU_ST_STM32G0:STM32G031F6Px",
        x=MCU_X, y=MCU_Y,
        ref="U1", value="STM32G031F6P6",
        rotation=0,
        footprint="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm"
    )

    # MCU bypass caps
    c_mcu1 = sch.add_symbol(
        lib_id="Device:C",
        x=MCU_X - 35, y=MCU_Y - 15,
        ref="C1", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_mcu2 = sch.add_symbol(
        lib_id="Device:C",
        x=MCU_X - 35, y=MCU_Y,
        ref="C2", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_mcu3 = sch.add_symbol(
        lib_id="Device:C",
        x=MCU_X - 35, y=MCU_Y + 15,
        ref="C3", value="4.7uF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # =========================================================================
    # Section 5: Zero-Crossing Detection (H11AA1)
    # =========================================================================
    print("Adding zero-crossing detection...")

    u_zc = sch.add_symbol(
        lib_id="Isolator:H11AA1",
        x=SENSE_X - 50, y=SENSE_Y,
        ref="U6", value="H11AA1",
        rotation=0,
        footprint="Package_DIP:DIP-6_W7.62mm"
    )

    # Place R1 and R2 at different X positions to avoid any wire overlap at same X coordinate
    r_zc1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X - 85, y=SENSE_Y - 8,  # Offset X to avoid overlap
        ref="R1", value="47k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_zc2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X - 75, y=SENSE_Y + 8,  # Different X than R1
        ref="R2", value="47k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    # Place pull-up resistor directly above the H11AA1 output for pure vertical routing
    # H11AA1 output (pin 6) is at approximately X = SENSE_X - 42.52 (157.48mm for symbol at 150mm)
    # Place resistor at same X to avoid any horizontal wire crossings
    r_zc_pull = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X - 43, y=SENSE_Y - 35,  # Directly above H11AA1 output pin
        ref="R3", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("ZC_OUT", SENSE_X - 35, SENSE_Y - 20)

    # =========================================================================
    # Section 6: Current Sensing with Hardware OCP
    # =========================================================================
    print("Adding current sensing with hardware OCP...")

    # Current shunt
    r_shunt = sch.add_symbol(
        lib_id="Device:R_Shunt",
        x=SENSE_X + 30, y=SENSE_Y + 30,
        ref="R_SHUNT", value="5mR",
        rotation=0,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )

    # INA180A3 current sense amp (100V/V)
    u_ina = sch.add_symbol(
        lib_id="Amplifier_Current:INA180A3",
        x=SENSE_X + 60, y=SENSE_Y,
        ref="U4", value="INA180A3",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    c_ina = sch.add_symbol(
        lib_id="Device:C",
        x=SENSE_X + 75, y=SENSE_Y - 15,
        ref="C4", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    sch.add_label("I_SENSE", SENSE_X + 80, SENSE_Y)

    # Single comparator for hardware OCP (LMV331 - single-unit, avoids multi-unit issues)
    u_ocp = sch.add_symbol(
        lib_id="Comparator:LMV331",
        x=SENSE_X + 60, y=SENSE_Y + 40,
        ref="U5", value="LMV331",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # OCP threshold resistor divider
    r_ocp1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X + 40, y=SENSE_Y + 35,
        ref="R18", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_ocp2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X + 40, y=SENSE_Y + 50,
        ref="R19", value="3.3k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    # Blanking RC (500ns)
    r_blank = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X + 80, y=SENSE_Y + 40,
        ref="R20", value="1k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    c_blank = sch.add_symbol(
        lib_id="Device:C",
        x=SENSE_X + 90, y=SENSE_Y + 40,
        ref="C5", value="470pF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    sch.add_label("OCP_TRIP", SENSE_X + 95, SENSE_Y + 40)

    # =========================================================================
    # Section 7: Bus Voltage Sensing
    # =========================================================================
    print("Adding voltage sensing dividers...")

    # AC bus voltage divider (1M + 10k = 100:1)
    r_vbus1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X - 20, y=SENSE_Y + 40,
        ref="R4", value="1M",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_vbus2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X - 20, y=SENSE_Y + 55,
        ref="R5", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    sch.add_label("V_BUS", SENSE_X - 10, SENSE_Y + 47)

    # Supercap bank voltage dividers (820k + 10k = 83:1)
    r_vsc_p1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X, y=SENSE_Y + 40,
        ref="R6", value="820k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_vsc_p2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X, y=SENSE_Y + 55,
        ref="R7", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    sch.add_label("V_SC_POS", SENSE_X + 10, SENSE_Y + 47)

    r_vsc_n1 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X + 20, y=SENSE_Y + 40,
        ref="R8", value="820k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_vsc_n2 = sch.add_symbol(
        lib_id="Device:R",
        x=SENSE_X + 20, y=SENSE_Y + 55,
        ref="R9", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    sch.add_label("V_SC_NEG", SENSE_X + 30, SENSE_Y + 47)

    # =========================================================================
    # Section 8: Gate Drivers (single-channel low-side drivers with UVLO)
    # =========================================================================
    print("Adding gate drivers for back-to-back FETs...")

    # Using 4x single-channel drivers (UCC27511A) for the 4 FET gates
    # Back-to-back FETs with sources tied don't need bootstrap - low-side only

    # Gate driver for Q1 (positive bank high-side)
    u_drv1 = sch.add_symbol(
        lib_id="Driver_FET:UCC27511ADBV",
        x=GATE_X, y=GATE_Y - 15,
        ref="U2", value="UCC27511A",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Gate driver for Q2 (positive bank low-side)
    u_drv2 = sch.add_symbol(
        lib_id="Driver_FET:UCC27511ADBV",
        x=GATE_X, y=GATE_Y + 15,
        ref="U3", value="UCC27511A",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Bypass cap for positive bank drivers
    c_drv_pos = sch.add_symbol(
        lib_id="Device:C",
        x=GATE_X - 25, y=GATE_Y,
        ref="C13", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    sch.add_label("DRV_POS_HI", GATE_X - 30, GATE_Y - 15)
    sch.add_label("DRV_POS_LO", GATE_X - 30, GATE_Y + 15)

    # Gate driver for Q3 (negative bank high-side)
    u_drv3 = sch.add_symbol(
        lib_id="Driver_FET:UCC27511ADBV",
        x=GATE_X, y=GATE_Y + 45,
        ref="U6", value="UCC27511A",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Gate driver for Q4 (negative bank low-side)
    u_drv4 = sch.add_symbol(
        lib_id="Driver_FET:UCC27511ADBV",
        x=GATE_X, y=GATE_Y + 75,
        ref="U7", value="UCC27511A",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Bypass cap for negative bank drivers
    c_drv_neg = sch.add_symbol(
        lib_id="Device:C",
        x=GATE_X - 25, y=GATE_Y + 60,
        ref="C14", value="100nF",
        rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    sch.add_label("DRV_NEG_HI", GATE_X - 30, GATE_Y + 45)
    sch.add_label("DRV_NEG_LO", GATE_X - 30, GATE_Y + 75)

    # =========================================================================
    # Section 9: Back-to-Back Discharge FETs (4x IRFB4110)
    # =========================================================================
    print("Adding back-to-back discharge FETs...")

    # Positive bank: Q1 (high-side) and Q2 (low-side), sources tied
    q1 = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=GATE_X + 60, y=GATE_Y - 10,
        ref="Q1", value="IRFB4110",
        rotation=0,
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )
    q2 = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=GATE_X + 60, y=GATE_Y + 20,
        ref="Q2", value="IRFB4110",
        rotation=180,  # Flipped so sources face each other
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )

    # Gate resistors (limit dI/dt)
    r_g1 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 40, y=GATE_Y - 10,
        ref="R10", value="10R",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_g2 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 40, y=GATE_Y + 20,
        ref="R11", value="10R",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    # Gate-source bleeders (prevent floating)
    r_gb1 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 55, y=GATE_Y - 20,
        ref="R_GB1", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_gb2 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 55, y=GATE_Y + 30,
        ref="R_GB2", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    # TVS gate clamps (18V)
    d_tvs1 = sch.add_symbol(
        lib_id="Device:D_TVS",
        x=GATE_X + 50, y=GATE_Y - 5,
        ref="D1", value="SMBJ18A",
        rotation=90,
        footprint="Diode_SMD:D_SMB"
    )
    d_tvs2 = sch.add_symbol(
        lib_id="Device:D_TVS",
        x=GATE_X + 50, y=GATE_Y + 25,
        ref="D2", value="SMBJ18A",
        rotation=90,
        footprint="Diode_SMD:D_SMB"
    )

    sch.add_label("SC_POS_PLUS", GATE_X + 70, GATE_Y - 20)
    sch.add_label("BUS_POS", GATE_X + 70, GATE_Y + 30)

    # Negative bank: Q3 (high-side) and Q4 (low-side)
    q3 = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=GATE_X + 60, y=GATE_Y + 50,
        ref="Q3", value="IRFB4110",
        rotation=0,
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )
    q4 = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=GATE_X + 60, y=GATE_Y + 80,
        ref="Q4", value="IRFB4110",
        rotation=180,
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )

    r_g3 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 40, y=GATE_Y + 50,
        ref="R12", value="10R",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_g4 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 40, y=GATE_Y + 80,
        ref="R13", value="10R",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    r_gb3 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 55, y=GATE_Y + 40,
        ref="R_GB3", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_gb4 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 55, y=GATE_Y + 90,
        ref="R_GB4", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    d_tvs3 = sch.add_symbol(
        lib_id="Device:D_TVS",
        x=GATE_X + 50, y=GATE_Y + 55,
        ref="D3", value="SMBJ18A",
        rotation=90,
        footprint="Diode_SMD:D_SMB"
    )
    d_tvs4 = sch.add_symbol(
        lib_id="Device:D_TVS",
        x=GATE_X + 50, y=GATE_Y + 85,
        ref="D4", value="SMBJ18A",
        rotation=90,
        footprint="Diode_SMD:D_SMB"
    )

    sch.add_label("SC_NEG_PLUS", GATE_X + 70, GATE_Y + 40)
    sch.add_label("BUS_NEG", GATE_X + 70, GATE_Y + 90)

    # =========================================================================
    # Section 10: Gate Failsafe Pull-down (tied to NRST)
    # =========================================================================
    print("Adding gate failsafe circuit...")

    # 2N7002 FETs that pull gates low when NRST is low
    q_fs1 = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=GATE_X + 25, y=GATE_Y + 10,
        ref="Q7", value="2N7002",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23"
    )
    q_fs2 = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=GATE_X + 25, y=GATE_Y + 70,
        ref="Q8", value="2N7002",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23"
    )

    r_fs1 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 15, y=GATE_Y + 10,
        ref="R14", value="10k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r_fs2 = sch.add_symbol(
        lib_id="Device:R",
        x=GATE_X + 15, y=GATE_Y + 70,
        ref="R15", value="10k",
        rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("NRST_INV", GATE_X + 5, GATE_Y + 10)

    # =========================================================================
    # Section 11: Precharge Circuits (2x paths)
    # =========================================================================
    print("Adding precharge circuits...")

    # Positive bank precharge
    r_prechg_pos = sch.add_symbol(
        lib_id="Device:R",
        x=PRECHG_X, y=PRECHG_Y,
        ref="R16", value="100R 5W",
        rotation=90,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )
    q_prechg_pos = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=PRECHG_X + 25, y=PRECHG_Y,
        ref="Q5", value="AO3400",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23"
    )
    r_pg_pos = sch.add_symbol(
        lib_id="Device:R",
        x=PRECHG_X + 15, y=PRECHG_Y - 10,
        ref="R21", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("PRECHG_POS", PRECHG_X + 5, PRECHG_Y - 15)

    # Negative bank precharge
    r_prechg_neg = sch.add_symbol(
        lib_id="Device:R",
        x=PRECHG_X, y=PRECHG_Y + 40,
        ref="R17", value="100R 5W",
        rotation=90,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )
    q_prechg_neg = sch.add_symbol(
        lib_id="Device:Q_NMOS",
        x=PRECHG_X + 25, y=PRECHG_Y + 40,
        ref="Q6", value="AO3400",
        rotation=0,
        footprint="Package_TO_SOT_SMD:SOT-23"
    )
    r_pg_neg = sch.add_symbol(
        lib_id="Device:R",
        x=PRECHG_X + 15, y=PRECHG_Y + 30,
        ref="R22", value="10k",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("PRECHG_NEG", PRECHG_X + 5, PRECHG_Y + 25)

    # =========================================================================
    # Section 12: Charging Circuits (resistor-limited)
    # =========================================================================
    print("Adding charging circuits...")

    # Place positive and negative charging circuits at different X positions
    # to avoid any possibility of wire overlap at the same X coordinate
    CHG_POS_X = 280
    CHG_NEG_X = 285  # Offset by 5mm to ensure no vertical wire overlap

    # Positive bank charging (diode + resistor from AC)
    r_chg_pos = sch.add_symbol(
        lib_id="Device:R",
        x=CHG_POS_X, y=SC_POS_Y,
        ref="R23", value="220R 2W",
        rotation=90,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )
    d_chg_pos = sch.add_symbol(
        lib_id="Device:D",
        x=CHG_POS_X + 15, y=SC_POS_Y,
        ref="D6", value="1N4007",
        rotation=0,
        footprint="Diode_SMD:D_SMA"
    )

    # Negative bank charging
    r_chg_neg = sch.add_symbol(
        lib_id="Device:R",
        x=CHG_NEG_X, y=SC_NEG_Y,
        ref="R24", value="220R 2W",
        rotation=90,
        footprint="Resistor_SMD:R_2512_6332Metric"
    )
    d_chg_neg = sch.add_symbol(
        lib_id="Device:D",
        x=CHG_NEG_X + 15, y=SC_NEG_Y,
        ref="D7", value="1N4007",
        rotation=0,
        footprint="Diode_SMD:D_SMA"
    )

    # =========================================================================
    # Section 13: Supercapacitor Banks (60x total)
    # =========================================================================
    print("Adding supercapacitor banks (60 cells)...")

    # Positive bank: C101-C130
    cap_refs_pos = []
    for row in range(3):
        for col in range(10):
            idx = row * 10 + col + 1
            ref = f"C{100 + idx}"
            cap = sch.add_symbol(
                lib_id="Device:C",
                x=SC_POS_X + col * 15,
                y=SC_POS_Y + row * 18,
                ref=ref,
                value="12F 2.7V",
                rotation=0,
                footprint="Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
            )
            cap_refs_pos.append(cap)

    # Negative bank: C131-C160
    cap_refs_neg = []
    for row in range(3):
        for col in range(10):
            idx = row * 10 + col + 1
            ref = f"C{130 + idx}"
            cap = sch.add_symbol(
                lib_id="Device:C",
                x=SC_NEG_X + col * 15,
                y=SC_NEG_Y + row * 18,
                ref=ref,
                value="12F 2.7V",
                rotation=0,
                footprint="Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
            )
            cap_refs_neg.append(cap)

    # Note: SC_*_PLUS and SC_*_MINUS labels are added in the wiring section with proper wire connections

    # =========================================================================
    # Section 14: Debug Header and Status LED
    # =========================================================================
    print("Adding debug header and status LED...")

    j_swd = sch.add_symbol(
        lib_id="Connector:Conn_01x05_Pin",
        x=MCU_X + 80, y=MCU_Y - 30,  # Moved up and right to avoid SC_POS_Y conflicts
        ref="J3", value="SWD",
        rotation=0,
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
    )

    # Note: SWD labels are added during wiring section with proper wire connections

    # Status LED
    d_led = sch.add_symbol(
        lib_id="Device:LED",
        x=MCU_X + 60, y=MCU_Y + 25,
        ref="D8", value="Green",
        rotation=90,
        footprint="LED_SMD:LED_0805_2012Metric"
    )
    r_led = sch.add_symbol(
        lib_id="Device:R",
        x=MCU_X + 60, y=MCU_Y + 12,
        ref="R25", value="330R",
        rotation=0,
        footprint="Resistor_SMD:R_0805_2012Metric"
    )

    sch.add_label("LED_STATUS", MCU_X + 50, MCU_Y + 20)

    # =========================================================================
    # Section 15: Power symbols and flags
    # =========================================================================
    print("Adding power symbols...")

    # Note: PWR_FLAG is only needed for nets with power INPUT pins but no power OUTPUT driving them
    # The +12V and +3.3V rails are driven by regulator outputs (power OUTPUT pins) - no PWR_FLAG needed
    # VBUS (from bridge rectifier) and GND need PWR_FLAG markers
    # These are added during wiring near their respective connection points

    # =========================================================================
    # Section 16: Wiring
    # =========================================================================
    print("Adding wiring...")

    # Helper function to add wire with individual coordinates
    def wire(x1, y1, x2, y2):
        sch.add_wire((x1, y1), (x2, y2))

    # -------------------------------------------------------------------------
    # AC Input wiring: J1 -> Varistor -> J2, with labels
    # -------------------------------------------------------------------------
    # J1 pin 1 (AC_L) to varistor pin 1 and to J2 pin 1
    j1_p1 = j_ac_in.pin_position("1")
    j1_p2 = j_ac_in.pin_position("2")
    rv1_p1 = rv1.pin_position("1")
    rv1_p2 = rv1.pin_position("2")
    j2_p1 = j_ac_out.pin_position("1")
    j2_p2 = j_ac_out.pin_position("2")

    # Wire J1.1 -> RV1.1 -> J2.1 (AC Line)
    # Use offset X for junction to avoid vertical wire overlap with AC_N
    ac_l_junc_x = rv1_p1[0] - 5  # Offset left
    wire(j1_p1[0], j1_p1[1], ac_l_junc_x, j1_p1[1])
    wire(ac_l_junc_x, j1_p1[1], ac_l_junc_x, rv1_p1[1])
    wire(ac_l_junc_x, rv1_p1[1], rv1_p1[0], rv1_p1[1])
    wire(ac_l_junc_x, j1_p1[1], j2_p1[0], j1_p1[1])
    wire(j2_p1[0], j1_p1[1], j2_p1[0], j2_p1[1])

    # Wire J1.2 -> RV1.2 -> J2.2 (AC Neutral)
    # Use offset X for junction to avoid vertical wire overlap with AC_L
    ac_n_junc_x = rv1_p2[0] + 5  # Offset right
    wire(j1_p2[0], j1_p2[1], ac_n_junc_x, j1_p2[1])
    wire(ac_n_junc_x, j1_p2[1], ac_n_junc_x, rv1_p2[1])
    wire(ac_n_junc_x, rv1_p2[1], rv1_p2[0], rv1_p2[1])
    wire(ac_n_junc_x, j1_p2[1], j2_p2[0], j1_p2[1])
    wire(j2_p2[0], j1_p2[1], j2_p2[0], j2_p2[1])

    # Move labels to wire intersections - use global labels for AC connections
    sch.remove_label("AC_L")
    sch.remove_label("AC_N")
    sch.add_global_label("AC_L", ac_l_junc_x, j1_p1[1], shape="passive")
    sch.add_global_label("AC_N", ac_n_junc_x, j1_p2[1], shape="passive")

    # -------------------------------------------------------------------------
    # 12V Power Supply wiring
    # -------------------------------------------------------------------------
    # Bridge rectifier: AC_L -> D5.pin1 , AC_N -> D5.pin2
    # D5.+ -> C8.1 -> U7(L7812).VI , D5.- -> C8.2 -> U7.GND
    # MB6S pin mapping: 1=AC~, 2=AC~, 3=DC+, 4=DC-
    bridge_ac1 = d_bridge.pin_position("1")  # AC input 1 (lower ~)
    bridge_ac2 = d_bridge.pin_position("2")  # AC input 2 (upper ~)
    bridge_pos = d_bridge.pin_position("3")  # DC+ (same as "+")
    bridge_neg = d_bridge.pin_position("4")  # DC- (same as "-")

    # C8 filter cap
    c8_p1 = c_12v_in.pin_position("1")
    c8_p2 = c_12v_in.pin_position("2")

    # L7812 regulator
    u7_vi = u_12v.pin_position("IN")
    u7_gnd = u_12v.pin_position("GND")
    u7_vo = u_12v.pin_position("OUT")

    # C9 output cap
    c9_p1 = c_12v_out.pin_position("1")
    c9_p2 = c_12v_out.pin_position("2")

    # Wire bridge AC inputs - use global labels
    wire(bridge_ac1[0] - 5, bridge_ac1[1], bridge_ac1[0], bridge_ac1[1])
    sch.add_global_label("AC_L", bridge_ac1[0] - 5, bridge_ac1[1], shape="passive")
    wire(bridge_ac2[0] + 5, bridge_ac2[1], bridge_ac2[0], bridge_ac2[1])
    sch.add_global_label("AC_N", bridge_ac2[0] + 5, bridge_ac2[1], shape="passive")

    # Wire bridge+ -> C8.1 -> L7812.VI
    wire(bridge_pos[0], bridge_pos[1], c8_p1[0], bridge_pos[1])
    wire(c8_p1[0], bridge_pos[1], c8_p1[0], c8_p1[1])
    wire(c8_p1[0], bridge_pos[1], u7_vi[0], bridge_pos[1])
    wire(u7_vi[0], bridge_pos[1], u7_vi[0], u7_vi[1])

    # Add PWR_FLAG for VBUS (rectified DC from bridge) to mark it as a valid power source
    sch.add_pwr_flag(bridge_pos[0], bridge_pos[1] - 5)
    wire(bridge_pos[0], bridge_pos[1] - 5, bridge_pos[0], bridge_pos[1])

    # Wire L7812.VO -> C9.1 and add +12V label
    wire(u7_vo[0], u7_vo[1], c9_p1[0], u7_vo[1])
    wire(c9_p1[0], u7_vo[1], c9_p1[0], c9_p1[1])
    wire(c9_p1[0], u7_vo[1], c9_p1[0] + 5, u7_vo[1])  # extend wire for label
    sch.remove_label("+12V")
    sch.add_label("+12V", c9_p1[0] + 5, u7_vo[1])

    # Wire GND: C8.2 -> L7812.GND -> C9.2
    gnd_y = c8_p2[1] + 5
    wire(c8_p2[0], c8_p2[1], c8_p2[0], gnd_y)
    wire(c8_p2[0], gnd_y, u7_gnd[0], gnd_y)
    wire(u7_gnd[0], gnd_y, u7_gnd[0], u7_gnd[1])
    wire(u7_gnd[0], gnd_y, c9_p2[0], gnd_y)
    wire(c9_p2[0], gnd_y, c9_p2[0], c9_p2[1])

    # Wire bridge DC- to GND bus
    wire(bridge_neg[0], bridge_neg[1], bridge_neg[0] - 5, bridge_neg[1])
    wire(bridge_neg[0] - 5, bridge_neg[1], bridge_neg[0] - 5, gnd_y)
    wire(bridge_neg[0] - 5, gnd_y, c8_p2[0], gnd_y)

    sch.add_power("power:GND", u7_gnd[0], gnd_y + 5)
    # Wire the GND power symbol to the GND rail
    wire(u7_gnd[0], gnd_y, u7_gnd[0], gnd_y + 5)
    # Add PWR_FLAG on GND to indicate it's a valid power return path
    sch.add_pwr_flag(u7_gnd[0] + 5, gnd_y + 5)
    wire(u7_gnd[0], gnd_y + 5, u7_gnd[0] + 5, gnd_y + 5)

    # -------------------------------------------------------------------------
    # 3.3V Power Supply wiring
    # -------------------------------------------------------------------------
    u8_vi = u_3v3.pin_position("VI")
    u8_gnd = u_3v3.pin_position("GND")
    u8_vo = u_3v3.pin_position("VO")

    c10_p1 = c_3v3_in.pin_position("1")
    c10_p2 = c_3v3_in.pin_position("2")
    c11_p1 = c_3v3_out1.pin_position("1")
    c11_p2 = c_3v3_out1.pin_position("2")
    c12_p1 = c_3v3_out2.pin_position("1")
    c12_p2 = c_3v3_out2.pin_position("2")

    # Wire +12V -> C10.1 -> AMS1117.VI
    pwr_12v_y = u7_vo[1]
    wire(c9_p1[0] + 5, pwr_12v_y, c10_p1[0], pwr_12v_y)
    wire(c10_p1[0], pwr_12v_y, c10_p1[0], c10_p1[1])
    wire(c10_p1[0], pwr_12v_y, u8_vi[0], pwr_12v_y)
    wire(u8_vi[0], pwr_12v_y, u8_vi[0], u8_vi[1])

    # Wire AMS1117.VO -> C11.1 -> C12.1
    wire(u8_vo[0], u8_vo[1], c11_p1[0], u8_vo[1])
    wire(c11_p1[0], u8_vo[1], c11_p1[0], c11_p1[1])
    wire(c11_p1[0], u8_vo[1], c12_p1[0], u8_vo[1])
    wire(c12_p1[0], u8_vo[1], c12_p1[0], c12_p1[1])

    # Wire GND rail for 3.3V section
    gnd_3v3_y = c10_p2[1] + 5
    wire(c10_p2[0], c10_p2[1], c10_p2[0], gnd_3v3_y)
    wire(c10_p2[0], gnd_3v3_y, u8_gnd[0], gnd_3v3_y)
    wire(u8_gnd[0], gnd_3v3_y, u8_gnd[0], u8_gnd[1])
    wire(u8_gnd[0], gnd_3v3_y, c11_p2[0], gnd_3v3_y)
    wire(c11_p2[0], gnd_3v3_y, c11_p2[0], c11_p2[1])
    wire(c11_p2[0], gnd_3v3_y, c12_p2[0], gnd_3v3_y)
    wire(c12_p2[0], gnd_3v3_y, c12_p2[0], c12_p2[1])

    # Add GND power symbol on 3.3V GND rail to connect it to the main GND net
    sch.add_power("power:GND", c12_p2[0], gnd_3v3_y + 5)
    wire(c12_p2[0], gnd_3v3_y, c12_p2[0], gnd_3v3_y + 5)

    # -------------------------------------------------------------------------
    # MCU Wiring (VDD, VSS, bypass caps)
    # -------------------------------------------------------------------------
    mcu_vdd = u_mcu.pin_position("VDD")
    mcu_vss = u_mcu.pin_position("VSS")

    # Wire MCU VDD to 3.3V rail
    wire(c12_p1[0], u8_vo[1], mcu_vdd[0], u8_vo[1])
    wire(mcu_vdd[0], u8_vo[1], mcu_vdd[0], mcu_vdd[1])

    # Wire MCU VSS to GND
    wire(mcu_vss[0], mcu_vss[1], mcu_vss[0], gnd_3v3_y)
    wire(mcu_vss[0], gnd_3v3_y, c12_p2[0], gnd_3v3_y)

    # Wire bypass caps to MCU power
    c1_p1 = c_mcu1.pin_position("1")
    c1_p2 = c_mcu1.pin_position("2")
    c2_p1 = c_mcu2.pin_position("1")
    c2_p2 = c_mcu2.pin_position("2")
    c3_p1 = c_mcu3.pin_position("1")
    c3_p2 = c_mcu3.pin_position("2")

    # Connect bypass caps directly to power symbols (no shared buses to avoid crossing MCU signals)
    # Each cap gets its own +3.3V symbol above and GND symbol below
    # This avoids any vertical bus wires that could cross SWDIO/SWCLK traces

    # C1 power connections - power symbols directly above/below the cap
    sch.add_power("power:+3.3V", c1_p1[0], c1_p1[1] - 5)
    wire(c1_p1[0], c1_p1[1] - 5, c1_p1[0], c1_p1[1])
    sch.add_power("power:GND", c1_p2[0], c1_p2[1] + 5)
    wire(c1_p2[0], c1_p2[1], c1_p2[0], c1_p2[1] + 5)

    # C2 power connections
    sch.add_power("power:+3.3V", c2_p1[0], c2_p1[1] - 5)
    wire(c2_p1[0], c2_p1[1] - 5, c2_p1[0], c2_p1[1])
    sch.add_power("power:GND", c2_p2[0], c2_p2[1] + 5)
    wire(c2_p2[0], c2_p2[1], c2_p2[0], c2_p2[1] + 5)

    # C3 power connections
    sch.add_power("power:+3.3V", c3_p1[0], c3_p1[1] - 5)
    wire(c3_p1[0], c3_p1[1] - 5, c3_p1[0], c3_p1[1])
    sch.add_power("power:GND", c3_p2[0], c3_p2[1] + 5)
    wire(c3_p2[0], c3_p2[1], c3_p2[0], c3_p2[1] + 5)

    # -------------------------------------------------------------------------
    # MCU Signal Labels - wire from MCU pins to label positions
    # -------------------------------------------------------------------------
    # Note: STM32G031F6Px in 20-pin package has multiplexed pins
    # SWD: PA13 (SWDIO), PA14/PA15 (SWCLK)
    # NRST: PF2 can be configured as NRST
    mcu_swdio = u_mcu.pin_position("PA13")
    mcu_swclk = u_mcu.pin_position("PA14/PA15")
    mcu_nrst = u_mcu.pin_position("PF2")  # PF2 can be NRST

    # Remove old labels - we'll use direct wiring instead
    sch.remove_label("SWDIO")
    sch.remove_label("SWCLK")
    sch.remove_label("NRST")

    # Label position for other MCU signals (not debug signals)
    label_x_right = MCU_X + 40  # For pins on right side of MCU

    # Route MCU debug signals (SWDIO, SWCLK, NRST) directly to SWD connector
    # Using direct wires (not labels) to avoid crossing issues with AC section
    # The SWD connector is on the right side, so we route right regardless of MCU pin side

    # SWD connector wiring - wire directly from MCU to SWD connector
    # Route on the right side of MCU to avoid crossing AC section wires
    j3_p1 = j_swd.pin_position("1")  # VCC
    j3_p2 = j_swd.pin_position("2")  # SWDIO
    j3_p3 = j_swd.pin_position("3")  # SWCLK
    j3_p4 = j_swd.pin_position("4")  # GND
    j3_p5 = j_swd.pin_position("5")  # NRST

    # VCC and GND connect to power symbols
    swd_pwr_x = j3_p1[0] - 10
    wire(j3_p1[0], j3_p1[1], swd_pwr_x, j3_p1[1])
    sch.add_power("power:+3.3V", swd_pwr_x - 5, j3_p1[1])
    wire(swd_pwr_x - 5, j3_p1[1], swd_pwr_x, j3_p1[1])

    wire(j3_p4[0], j3_p4[1], swd_pwr_x, j3_p4[1])
    sch.add_power("power:GND", swd_pwr_x - 5, j3_p4[1])
    wire(swd_pwr_x - 5, j3_p4[1], swd_pwr_x, j3_p4[1])

    # Connect MCU debug signals to SWD connector using global labels
    # This avoids physical wire crossings with the charging circuit at Y=SC_POS_Y
    mcu_swdio = u_mcu.pin_position("PA13")
    mcu_swclk = u_mcu.pin_position("PA14/PA15")
    mcu_nrst = u_mcu.pin_position("PF2")

    # SWDIO: Use global labels directly on pins (no stub wires to avoid crossings)
    sch.add_global_label("SWDIO", mcu_swdio[0], mcu_swdio[1], shape="bidirectional")
    sch.add_global_label("SWDIO", j3_p2[0], j3_p2[1], shape="bidirectional")

    # SWCLK: Use global labels directly on pins
    sch.add_global_label("SWCLK", mcu_swclk[0], mcu_swclk[1], shape="output")
    sch.add_global_label("SWCLK", j3_p3[0], j3_p3[1], shape="input")

    # NRST: Use global labels directly on pins
    sch.add_global_label("NRST", mcu_nrst[0], mcu_nrst[1], shape="bidirectional")
    sch.add_global_label("NRST", j3_p5[0], j3_p5[1], shape="bidirectional")

    # -------------------------------------------------------------------------
    # Zero-Crossing Detection Wiring
    # -------------------------------------------------------------------------
    zc_anode1 = u_zc.pin_position("1")  # Anode 1
    zc_cathode1 = u_zc.pin_position("2")  # Cathode 1
    zc_vcc = u_zc.pin_position("5")  # VCC
    zc_gnd = u_zc.pin_position("4")  # GND
    zc_out = u_zc.pin_position("6")  # Output

    r1_p1 = r_zc1.pin_position("1")
    r1_p2 = r_zc1.pin_position("2")
    r2_p1 = r_zc2.pin_position("1")
    r2_p2 = r_zc2.pin_position("2")
    r3_p1 = r_zc_pull.pin_position("1")
    r3_p2 = r_zc_pull.pin_position("2")

    # Wire ZC resistors to H11AA1 input
    # Correct circuit: AC_L -> R1 -> H11AA1 anode -> H11AA1 cathode -> R2 -> AC_N
    # R1.2 connects to H11AA1 anode (pin 1)
    wire(r1_p2[0], r1_p2[1], zc_anode1[0], r1_p2[1])
    wire(zc_anode1[0], r1_p2[1], zc_anode1[0], zc_anode1[1])

    # H11AA1 cathode (pin 2) connects to R2.1 (not R2.2)
    wire(zc_cathode1[0], zc_cathode1[1], zc_cathode1[0], r2_p1[1])
    wire(zc_cathode1[0], r2_p1[1], r2_p1[0], r2_p1[1])

    # AC input labels for ZC - use global labels to connect to AC section by name
    wire(r1_p1[0] - 5, r1_p1[1], r1_p1[0], r1_p1[1])
    sch.add_global_label("AC_L", r1_p1[0] - 5, r1_p1[1], shape="input")
    wire(r2_p2[0], r2_p2[1], r2_p2[0] + 5, r2_p2[1])
    sch.add_global_label("AC_N", r2_p2[0] + 5, r2_p2[1], shape="input")

    # Wire pull-up resistor to ZC output
    # Pull-up R3 is directly above H11AA1 output - minimal horizontal routing
    # Route: r3_p2 down to zc_out Y level, short horizontal to zc_out X, then connect
    wire(r3_p2[0], r3_p2[1], r3_p2[0], zc_out[1])  # vertical down to output Y level
    wire(r3_p2[0], zc_out[1], zc_out[0], zc_out[1])  # short horizontal to output pin
    sch.add_power("power:+3.3V", r3_p1[0], r3_p1[1] - 5)
    wire(r3_p1[0], r3_p1[1] - 5, r3_p1[0], r3_p1[1])

    # ZC output - add global label on the vertical wire above the output
    # Place it on the vertical segment to avoid any horizontal wire crossings
    sch.remove_label("ZC_OUT")
    sch.add_global_label("ZC_OUT", r3_p2[0], r3_p2[1] + 10, shape="output")

    # ZC power - VCC offset to the right to avoid crossing output wire
    sch.add_power("power:+3.3V", zc_vcc[0] + 10, zc_vcc[1] - 5)
    wire(zc_vcc[0] + 10, zc_vcc[1] - 5, zc_vcc[0] + 10, zc_vcc[1])
    wire(zc_vcc[0] + 10, zc_vcc[1], zc_vcc[0], zc_vcc[1])
    sch.add_power("power:GND", zc_gnd[0], zc_gnd[1] + 5)
    wire(zc_gnd[0], zc_gnd[1], zc_gnd[0], zc_gnd[1] + 5)

    # Wire ZC_OUT to MCU (PA0) - use global label to avoid wire crossing
    mcu_pa0 = u_mcu.pin_position("PA0")
    # Short stub wire from pin, then global label (connects by name to ZC section)
    stub_len = 5 if mcu_pa0[0] > MCU_X else -5  # Stub toward outside of MCU
    wire(mcu_pa0[0], mcu_pa0[1], mcu_pa0[0] + stub_len, mcu_pa0[1])
    sch.add_global_label("ZC_OUT", mcu_pa0[0] + stub_len, mcu_pa0[1], shape="input")

    # -------------------------------------------------------------------------
    # Voltage dividers wiring
    # -------------------------------------------------------------------------
    sch.wire_pins(r_vbus1, "2", r_vbus2, "1")
    sch.wire_pins(r_vsc_p1, "2", r_vsc_p2, "1")
    sch.wire_pins(r_vsc_n1, "2", r_vsc_n2, "1")

    # Connect voltage divider Pin 1 (top) to bus voltage labels
    vbus1_p1 = r_vbus1.pin_position("1")
    vsc_p1_p1 = r_vsc_p1.pin_position("1")
    vsc_n1_p1 = r_vsc_n1.pin_position("1")

    wire(vbus1_p1[0], vbus1_p1[1] - 5, vbus1_p1[0], vbus1_p1[1])
    sch.add_label("BUS_POS", vbus1_p1[0], vbus1_p1[1] - 5)

    wire(vsc_p1_p1[0], vsc_p1_p1[1] - 5, vsc_p1_p1[0], vsc_p1_p1[1])
    sch.add_label("SC_POS_PLUS", vsc_p1_p1[0], vsc_p1_p1[1] - 5)

    wire(vsc_n1_p1[0], vsc_n1_p1[1] - 5, vsc_n1_p1[0], vsc_n1_p1[1])
    sch.add_label("SC_NEG_PLUS", vsc_n1_p1[0], vsc_n1_p1[1] - 5)

    # Add labels at divider midpoints
    sch.remove_label("V_BUS")
    sch.remove_label("V_SC_POS")
    sch.remove_label("V_SC_NEG")

    vbus_mid = r_vbus1.pin_position("2")
    vsc_pos_mid = r_vsc_p1.pin_position("2")
    vsc_neg_mid = r_vsc_n1.pin_position("2")

    # Voltage divider outputs - use global labels to connect to MCU
    wire(vbus_mid[0], vbus_mid[1], vbus_mid[0] + 5, vbus_mid[1])
    sch.add_global_label("V_BUS", vbus_mid[0] + 5, vbus_mid[1], shape="output")

    wire(vsc_pos_mid[0], vsc_pos_mid[1], vsc_pos_mid[0] + 5, vsc_pos_mid[1])
    sch.add_global_label("V_SC_POS", vsc_pos_mid[0] + 5, vsc_pos_mid[1], shape="output")

    wire(vsc_neg_mid[0], vsc_neg_mid[1], vsc_neg_mid[0] + 5, vsc_neg_mid[1])
    sch.add_global_label("V_SC_NEG", vsc_neg_mid[0] + 5, vsc_neg_mid[1], shape="output")

    # GND for voltage dividers
    vbus2_p2 = r_vbus2.pin_position("2")
    vsc_p2_p2 = r_vsc_p2.pin_position("2")
    vsc_n2_p2 = r_vsc_n2.pin_position("2")

    vdiv_gnd_y = vbus2_p2[1] + 5
    wire(vbus2_p2[0], vbus2_p2[1], vbus2_p2[0], vdiv_gnd_y)
    wire(vsc_p2_p2[0], vsc_p2_p2[1], vsc_p2_p2[0], vdiv_gnd_y)
    wire(vsc_n2_p2[0], vsc_n2_p2[1], vsc_n2_p2[0], vdiv_gnd_y)
    wire(vbus2_p2[0], vdiv_gnd_y, vsc_n2_p2[0], vdiv_gnd_y)
    sch.add_power("power:GND", vsc_p2_p2[0], vdiv_gnd_y + 5)
    wire(vsc_p2_p2[0], vdiv_gnd_y, vsc_p2_p2[0], vdiv_gnd_y + 5)

    # Wire MCU signals to labels - always route right to avoid AC section crossings
    def mcu_label_x(pin_pos):
        """Return label X - always use right side to avoid wire crossings"""
        return label_x_right  # Always route right to avoid AC section wires

    # ADC inputs - use global labels with short stubs to avoid wire crossings
    mcu_pa1 = u_mcu.pin_position("PA1")
    stub = 5 if mcu_pa1[0] > MCU_X else -5
    wire(mcu_pa1[0], mcu_pa1[1], mcu_pa1[0] + stub, mcu_pa1[1])
    sch.add_global_label("V_BUS", mcu_pa1[0] + stub, mcu_pa1[1], shape="input")

    mcu_pa4 = u_mcu.pin_position("PA4")
    stub = 5 if mcu_pa4[0] > MCU_X else -5
    wire(mcu_pa4[0], mcu_pa4[1], mcu_pa4[0] + stub, mcu_pa4[1])
    sch.add_global_label("V_SC_POS", mcu_pa4[0] + stub, mcu_pa4[1], shape="input")

    mcu_pa5 = u_mcu.pin_position("PA5")
    stub = 5 if mcu_pa5[0] > MCU_X else -5
    wire(mcu_pa5[0], mcu_pa5[1], mcu_pa5[0] + stub, mcu_pa5[1])
    sch.add_global_label("V_SC_NEG", mcu_pa5[0] + stub, mcu_pa5[1], shape="input")

    # No-connect flags for unused MCU pins
    mcu_pc15 = u_mcu.pin_position("PC15")
    mcu_pb9_pc14 = u_mcu.pin_position("PB9/PC14")
    sch.add_no_connect(mcu_pc15[0], mcu_pc15[1])
    sch.add_no_connect(mcu_pb9_pc14[0], mcu_pb9_pc14[1])

    # -------------------------------------------------------------------------
    # Current Sensing Wiring
    # -------------------------------------------------------------------------
    # R_Shunt is a 4-terminal Kelvin resistor:
    # Pins 1, 2: Current path (high current)
    # Pins 3, 4: Kelvin sense pins (connect to current sense amplifier)
    shunt_p1 = r_shunt.pin_position("1")
    shunt_p2 = r_shunt.pin_position("2")
    shunt_p3 = r_shunt.pin_position("3")
    shunt_p4 = r_shunt.pin_position("4")
    ina_plus = u_ina.pin_position("+")
    ina_minus = u_ina.pin_position("-")
    ina_out = u_ina.pin_position("1")
    ina_vcc = u_ina.pin_position("V+")
    ina_gnd = u_ina.pin_position("GND")

    # Wire Kelvin sense pins (3, 4) to INA180 inputs
    wire(shunt_p3[0], shunt_p3[1], ina_plus[0], shunt_p3[1])
    wire(ina_plus[0], shunt_p3[1], ina_plus[0], ina_plus[1])

    wire(shunt_p4[0], shunt_p4[1], ina_minus[0], shunt_p4[1])
    wire(ina_minus[0], shunt_p4[1], ina_minus[0], ina_minus[1])

    # Wire current path pins (1, 2) to bus labels
    wire(shunt_p1[0], shunt_p1[1] - 5, shunt_p1[0], shunt_p1[1])
    sch.add_label("BUS_POS", shunt_p1[0], shunt_p1[1] - 5)
    wire(shunt_p2[0], shunt_p2[1] + 5, shunt_p2[0], shunt_p2[1])
    sch.add_label("SC_POS_PLUS", shunt_p2[0], shunt_p2[1] + 5)

    # INA power and bypass cap
    c4_p1 = c_ina.pin_position("1")
    c4_p2 = c_ina.pin_position("2")
    wire(ina_vcc[0], ina_vcc[1], c4_p1[0], ina_vcc[1])
    wire(c4_p1[0], ina_vcc[1], c4_p1[0], c4_p1[1])
    sch.add_power("power:+3.3V", c4_p1[0], ina_vcc[1] - 5)
    wire(c4_p1[0], ina_vcc[1] - 5, c4_p1[0], ina_vcc[1])

    sch.add_power("power:GND", ina_gnd[0], ina_gnd[1] + 5)
    wire(ina_gnd[0], ina_gnd[1], ina_gnd[0], ina_gnd[1] + 5)
    wire(c4_p2[0], c4_p2[1], c4_p2[0], ina_gnd[1] + 5)
    wire(c4_p2[0], ina_gnd[1] + 5, ina_gnd[0], ina_gnd[1] + 5)  # Horizontal to connect C4 to GND

    # I_SENSE output - use global label to connect to MCU and OCP without wire crossings
    sch.remove_label("I_SENSE")
    wire(ina_out[0], ina_out[1], ina_out[0] + 5, ina_out[1])
    sch.add_global_label("I_SENSE", ina_out[0] + 5, ina_out[1], shape="output")

    # Wire I_SENSE to MCU ADC - use global label
    mcu_pa2 = u_mcu.pin_position("PA2")
    stub_len = 5 if mcu_pa2[0] > MCU_X else -5
    wire(mcu_pa2[0], mcu_pa2[1], mcu_pa2[0] + stub_len, mcu_pa2[1])
    sch.add_global_label("I_SENSE", mcu_pa2[0] + stub_len, mcu_pa2[1], shape="input")

    # -------------------------------------------------------------------------
    # OCP Comparator Wiring
    # -------------------------------------------------------------------------
    sch.wire_pins(r_ocp1, "2", r_ocp2, "1")

    ocp_plus = u_ocp.pin_position("+")
    ocp_minus = u_ocp.pin_position("-")
    ocp_out = u_ocp.pin_position("~")  # LMV331 output pin is named ~
    ocp_vcc = u_ocp.pin_position("V+")
    ocp_gnd = u_ocp.pin_position("V-")

    # Wire I_SENSE to comparator + input - use global label
    wire(ocp_plus[0] - 10, ocp_plus[1], ocp_plus[0], ocp_plus[1])
    sch.add_global_label("I_SENSE", ocp_plus[0] - 10, ocp_plus[1], shape="input")

    # Wire threshold divider to comparator - input
    r_ocp1_p2 = r_ocp1.pin_position("2")
    wire(r_ocp1_p2[0], r_ocp1_p2[1], ocp_minus[0], r_ocp1_p2[1])
    wire(ocp_minus[0], r_ocp1_p2[1], ocp_minus[0], ocp_minus[1])

    # OCP divider power
    r_ocp1_p1 = r_ocp1.pin_position("1")
    r_ocp2_p2 = r_ocp2.pin_position("2")
    sch.add_power("power:+3.3V", r_ocp1_p1[0], r_ocp1_p1[1] - 5)
    wire(r_ocp1_p1[0], r_ocp1_p1[1] - 5, r_ocp1_p1[0], r_ocp1_p1[1])
    sch.add_power("power:GND", r_ocp2_p2[0], r_ocp2_p2[1] + 5)
    wire(r_ocp2_p2[0], r_ocp2_p2[1], r_ocp2_p2[0], r_ocp2_p2[1] + 5)

    # OCP power
    sch.add_power("power:+3.3V", ocp_vcc[0], ocp_vcc[1] - 5)
    wire(ocp_vcc[0], ocp_vcc[1] - 5, ocp_vcc[0], ocp_vcc[1])
    sch.add_power("power:GND", ocp_gnd[0], ocp_gnd[1] + 5)
    wire(ocp_gnd[0], ocp_gnd[1], ocp_gnd[0], ocp_gnd[1] + 5)

    # Wire OCP output through blanking RC
    r_blank_p1 = r_blank.pin_position("1")
    r_blank_p2 = r_blank.pin_position("2")
    c_blank_p1 = c_blank.pin_position("1")
    c_blank_p2 = c_blank.pin_position("2")

    wire(ocp_out[0], ocp_out[1], r_blank_p1[0], ocp_out[1])
    wire(r_blank_p1[0], ocp_out[1], r_blank_p1[0], r_blank_p1[1])
    sch.wire_pins(r_blank, "2", c_blank, "1")
    sch.add_power("power:GND", c_blank_p2[0], c_blank_p2[1] + 5)
    wire(c_blank_p2[0], c_blank_p2[1], c_blank_p2[0], c_blank_p2[1] + 5)

    # OCP_TRIP label
    sch.remove_label("OCP_TRIP")
    wire(r_blank_p2[0], r_blank_p2[1], r_blank_p2[0] + 5, r_blank_p2[1])
    sch.add_global_label("OCP_TRIP", r_blank_p2[0] + 5, r_blank_p2[1], shape="output")

    # Wire OCP_TRIP to MCU - use global label
    mcu_pa3 = u_mcu.pin_position("PA3")
    stub = 5 if mcu_pa3[0] > MCU_X else -5
    wire(mcu_pa3[0], mcu_pa3[1], mcu_pa3[0] + stub, mcu_pa3[1])
    sch.add_global_label("OCP_TRIP", mcu_pa3[0] + stub, mcu_pa3[1], shape="input")

    # -------------------------------------------------------------------------
    # Gate Driver Wiring
    # -------------------------------------------------------------------------
    # Each UCC27511A: IN -> driver -> OUT
    # Power from +12V rail

    # Driver 1 (Q1 gate - positive bank high-side)
    drv1_in = u_drv1.pin_position("IN+")
    drv1_in_neg = u_drv1.pin_position("IN-")
    drv1_out = u_drv1.pin_position("OUTH")
    drv1_outl = u_drv1.pin_position("OUTL")
    drv1_vdd = u_drv1.pin_position("V_{DD}")
    drv1_gnd = u_drv1.pin_position("GND")

    # Driver 2 (Q2 gate - positive bank low-side)
    drv2_in = u_drv2.pin_position("IN+")
    drv2_in_neg = u_drv2.pin_position("IN-")
    drv2_out = u_drv2.pin_position("OUTH")
    drv2_outl = u_drv2.pin_position("OUTL")
    drv2_vdd = u_drv2.pin_position("V_{DD}")
    drv2_gnd = u_drv2.pin_position("GND")

    # Wire driver inputs - use global labels to connect to MCU
    sch.remove_label("DRV_POS_HI")
    sch.remove_label("DRV_POS_LO")

    wire(drv1_in[0] - 10, drv1_in[1], drv1_in[0], drv1_in[1])
    sch.add_global_label("DRV_POS_HI", drv1_in[0] - 10, drv1_in[1], shape="input")

    wire(drv2_in[0] - 10, drv2_in[1], drv2_in[0], drv2_in[1])
    sch.add_global_label("DRV_POS_LO", drv2_in[0] - 10, drv2_in[1], shape="input")

    # MCU outputs for gate drivers (using multiplexed pin names)
    mcu_pa6 = u_mcu.pin_position("PA6")
    mcu_pa7 = u_mcu.pin_position("PA7")
    mcu_drv_neg = u_mcu.pin_position("PA8/PB0/PB1/PB2")  # DRV_NEG_HI and LO share one physical pin in this package

    # Use global labels with short stubs to avoid wire crossings
    stub = 5 if mcu_pa6[0] > MCU_X else -5
    wire(mcu_pa6[0], mcu_pa6[1], mcu_pa6[0] + stub, mcu_pa6[1])
    sch.add_global_label("DRV_POS_HI", mcu_pa6[0] + stub, mcu_pa6[1], shape="output")

    stub = 5 if mcu_pa7[0] > MCU_X else -5
    wire(mcu_pa7[0], mcu_pa7[1], mcu_pa7[0] + stub, mcu_pa7[1])
    sch.add_global_label("DRV_POS_LO", mcu_pa7[0] + stub, mcu_pa7[1], shape="output")

    # Driver power (12V)
    c13_p1 = c_drv_pos.pin_position("1")
    c13_p2 = c_drv_pos.pin_position("2")

    drv_pwr_y = drv1_vdd[1] - 10
    wire(drv1_vdd[0], drv1_vdd[1], drv1_vdd[0], drv_pwr_y)
    wire(drv2_vdd[0], drv2_vdd[1], drv2_vdd[0], drv_pwr_y)
    wire(drv1_vdd[0], drv_pwr_y, drv2_vdd[0], drv_pwr_y)
    wire(c13_p1[0], c13_p1[1], c13_p1[0], drv_pwr_y)
    wire(c13_p1[0], drv_pwr_y, drv1_vdd[0], drv_pwr_y)
    wire(c13_p1[0] - 10, drv_pwr_y, c13_p1[0], drv_pwr_y)
    sch.add_label("+12V", c13_p1[0] - 10, drv_pwr_y)

    drv_gnd_y = drv2_gnd[1] + 10
    wire(drv1_gnd[0], drv1_gnd[1], drv1_gnd[0], drv_gnd_y)
    wire(drv2_gnd[0], drv2_gnd[1], drv2_gnd[0], drv_gnd_y)
    wire(drv1_gnd[0], drv_gnd_y, drv2_gnd[0], drv_gnd_y)
    wire(c13_p2[0], c13_p2[1], c13_p2[0], drv_gnd_y)
    wire(c13_p2[0], drv_gnd_y, drv1_gnd[0], drv_gnd_y)
    sch.add_power("power:GND", c13_p2[0], drv_gnd_y + 5)
    wire(c13_p2[0], drv_gnd_y, c13_p2[0], drv_gnd_y + 5)

    # Wire driver outputs to gate resistors
    r10_p1 = r_g1.pin_position("1")
    r10_p2 = r_g1.pin_position("2")
    r11_p1 = r_g2.pin_position("1")
    r11_p2 = r_g2.pin_position("2")

    wire(drv1_out[0], drv1_out[1], r10_p1[0], drv1_out[1])
    wire(r10_p1[0], drv1_out[1], r10_p1[0], r10_p1[1])

    wire(drv2_out[0], drv2_out[1], r11_p1[0], drv2_out[1])
    wire(r11_p1[0], drv2_out[1], r11_p1[0], r11_p1[1])

    # Wire IN- pins to GND (enables non-inverting operation)
    wire(drv1_in_neg[0], drv1_in_neg[1], drv1_gnd[0], drv1_in_neg[1])
    wire(drv1_gnd[0], drv1_in_neg[1], drv1_gnd[0], drv1_gnd[1])
    wire(drv2_in_neg[0], drv2_in_neg[1], drv2_gnd[0], drv2_in_neg[1])
    wire(drv2_gnd[0], drv2_in_neg[1], drv2_gnd[0], drv2_gnd[1])

    # Wire OUTL in parallel with OUTH (both outputs to gate resistor)
    wire(drv1_outl[0], drv1_outl[1], r10_p1[0], drv1_outl[1])
    wire(r10_p1[0], drv1_outl[1], r10_p1[0], drv1_out[1])
    wire(drv2_outl[0], drv2_outl[1], r11_p1[0], drv2_outl[1])
    wire(r11_p1[0], drv2_outl[1], r11_p1[0], drv2_out[1])

    # Wire gate resistors to FET gates
    q1_g = q1.pin_position("G")
    q2_g = q2.pin_position("G")

    wire(r10_p2[0], r10_p2[1], q1_g[0], r10_p2[1])
    wire(q1_g[0], r10_p2[1], q1_g[0], q1_g[1])

    wire(r11_p2[0], r11_p2[1], q2_g[0], r11_p2[1])
    wire(q2_g[0], r11_p2[1], q2_g[0], q2_g[1])

    # -------------------------------------------------------------------------
    # FET wiring (Q1, Q2 - positive bank)
    # -------------------------------------------------------------------------
    q1_d = q1.pin_position("D")
    q1_s = q1.pin_position("S")
    q2_d = q2.pin_position("D")
    q2_s = q2.pin_position("S")

    # Sources tied together
    wire(q1_s[0], q1_s[1], q2_s[0], q1_s[1])
    wire(q2_s[0], q1_s[1], q2_s[0], q2_s[1])

    # SC_POS_PLUS label at Q1 drain
    sch.remove_label("SC_POS_PLUS")
    wire(q1_d[0], q1_d[1], q1_d[0] + 5, q1_d[1])
    sch.add_label("SC_POS_PLUS", q1_d[0] + 5, q1_d[1])

    # BUS_POS label at Q2 drain
    sch.remove_label("BUS_POS")
    wire(q2_d[0], q2_d[1], q2_d[0] + 5, q2_d[1])
    sch.add_label("BUS_POS", q2_d[0] + 5, q2_d[1])

    # Gate bleeders - connect between FET gate and source
    r_gb1_p1 = r_gb1.pin_position("1")
    r_gb1_p2 = r_gb1.pin_position("2")
    r_gb2_p1 = r_gb2.pin_position("1")
    r_gb2_p2 = r_gb2.pin_position("2")

    # R_GB1: Pin 1 to Q1 gate, Pin 2 to Q1 source
    wire(r_gb1_p1[0], r_gb1_p1[1], q1_g[0], r_gb1_p1[1])
    wire(q1_g[0], r_gb1_p1[1], q1_g[0], q1_g[1])  # Vertical to gate
    wire(r_gb1_p2[0], r_gb1_p2[1], q1_s[0], r_gb1_p2[1])
    wire(q1_s[0], r_gb1_p2[1], q1_s[0], q1_s[1])  # Vertical to source

    # R_GB2: Pin 1 to Q2 gate, Pin 2 to Q2 source
    wire(r_gb2_p1[0], r_gb2_p1[1], q2_g[0], r_gb2_p1[1])
    wire(q2_g[0], r_gb2_p1[1], q2_g[0], q2_g[1])  # Vertical to gate
    wire(r_gb2_p2[0], r_gb2_p2[1], q2_s[0], r_gb2_p2[1])
    wire(q2_s[0], r_gb2_p2[1], q2_s[0], q2_s[1])  # Vertical to source

    # TVS clamps (bidirectional, A1 and A2 pins)
    tvs1_a1 = d_tvs1.pin_position("A1")
    tvs1_a2 = d_tvs1.pin_position("A2")
    tvs2_a1 = d_tvs2.pin_position("A1")
    tvs2_a2 = d_tvs2.pin_position("A2")

    # D1: A1 to Q1 gate, A2 to Q1 source
    wire(tvs1_a1[0], tvs1_a1[1], q1_g[0], tvs1_a1[1])
    wire(q1_g[0], tvs1_a1[1], q1_g[0], q1_g[1])  # Vertical to gate
    wire(tvs1_a2[0], tvs1_a2[1], q1_s[0], tvs1_a2[1])
    wire(q1_s[0], tvs1_a2[1], q1_s[0], q1_s[1])  # Vertical to source

    # D2: A1 to Q2 gate, A2 to Q2 source
    wire(tvs2_a1[0], tvs2_a1[1], q2_g[0], tvs2_a1[1])
    wire(q2_g[0], tvs2_a1[1], q2_g[0], q2_g[1])  # Vertical to gate
    wire(tvs2_a2[0], tvs2_a2[1], q2_s[0], tvs2_a2[1])
    wire(q2_s[0], tvs2_a2[1], q2_s[0], q2_s[1])  # Vertical to source

    # -------------------------------------------------------------------------
    # Negative bank drivers and FETs (similar structure)
    # -------------------------------------------------------------------------
    drv3_in = u_drv3.pin_position("IN+")
    drv3_in_neg = u_drv3.pin_position("IN-")
    drv3_out = u_drv3.pin_position("OUTH")
    drv3_outl = u_drv3.pin_position("OUTL")
    drv3_vdd = u_drv3.pin_position("V_{DD}")
    drv3_gnd = u_drv3.pin_position("GND")

    drv4_in = u_drv4.pin_position("IN+")
    drv4_in_neg = u_drv4.pin_position("IN-")
    drv4_out = u_drv4.pin_position("OUTH")
    drv4_outl = u_drv4.pin_position("OUTL")
    drv4_vdd = u_drv4.pin_position("V_{DD}")
    drv4_gnd = u_drv4.pin_position("GND")

    sch.remove_label("DRV_NEG_HI")
    sch.remove_label("DRV_NEG_LO")

    # Use global labels for driver inputs
    wire(drv3_in[0] - 10, drv3_in[1], drv3_in[0], drv3_in[1])
    sch.add_global_label("DRV_NEG_HI", drv3_in[0] - 10, drv3_in[1], shape="input")

    wire(drv4_in[0] - 10, drv4_in[1], drv4_in[0], drv4_in[1])
    sch.add_global_label("DRV_NEG_LO", drv4_in[0] - 10, drv4_in[1], shape="input")

    # MCU outputs for DRV_NEG - use global labels with short stubs
    # Using PA9/PA11 for DRV_NEG_HI
    mcu_drv_neg_hi = u_mcu.pin_position("PA9/PA11")
    stub = 5 if mcu_drv_neg_hi[0] > MCU_X else -5
    wire(mcu_drv_neg_hi[0], mcu_drv_neg_hi[1], mcu_drv_neg_hi[0] + stub, mcu_drv_neg_hi[1])
    sch.add_global_label("DRV_NEG_HI", mcu_drv_neg_hi[0] + stub, mcu_drv_neg_hi[1], shape="output")

    # Using PA10/PA12 for DRV_NEG_LO
    mcu_drv_neg_lo = u_mcu.pin_position("PA10/PA12")
    stub = 5 if mcu_drv_neg_lo[0] > MCU_X else -5
    wire(mcu_drv_neg_lo[0], mcu_drv_neg_lo[1], mcu_drv_neg_lo[0] + stub, mcu_drv_neg_lo[1])
    sch.add_global_label("DRV_NEG_LO", mcu_drv_neg_lo[0] + stub, mcu_drv_neg_lo[1], shape="output")

    # Driver 3,4 power
    c14_p1 = c_drv_neg.pin_position("1")
    c14_p2 = c_drv_neg.pin_position("2")

    drv_neg_pwr_y = drv3_vdd[1] - 10
    wire(drv3_vdd[0], drv3_vdd[1], drv3_vdd[0], drv_neg_pwr_y)
    wire(drv4_vdd[0], drv4_vdd[1], drv4_vdd[0], drv_neg_pwr_y)
    wire(drv3_vdd[0], drv_neg_pwr_y, drv4_vdd[0], drv_neg_pwr_y)
    wire(c14_p1[0], c14_p1[1], c14_p1[0], drv_neg_pwr_y)
    wire(c14_p1[0], drv_neg_pwr_y, drv3_vdd[0], drv_neg_pwr_y)
    wire(c14_p1[0] - 10, drv_neg_pwr_y, c14_p1[0], drv_neg_pwr_y)
    sch.add_label("+12V", c14_p1[0] - 10, drv_neg_pwr_y)

    drv_neg_gnd_y = drv4_gnd[1] + 10
    wire(drv3_gnd[0], drv3_gnd[1], drv3_gnd[0], drv_neg_gnd_y)
    wire(drv4_gnd[0], drv4_gnd[1], drv4_gnd[0], drv_neg_gnd_y)
    wire(drv3_gnd[0], drv_neg_gnd_y, drv4_gnd[0], drv_neg_gnd_y)
    wire(c14_p2[0], c14_p2[1], c14_p2[0], drv_neg_gnd_y)
    wire(c14_p2[0], drv_neg_gnd_y, drv3_gnd[0], drv_neg_gnd_y)
    sch.add_power("power:GND", c14_p2[0], drv_neg_gnd_y + 5)
    wire(c14_p2[0], drv_neg_gnd_y, c14_p2[0], drv_neg_gnd_y + 5)

    # Wire driver 3,4 outputs to gate resistors
    r12_p1 = r_g3.pin_position("1")
    r12_p2 = r_g3.pin_position("2")
    r13_p1 = r_g4.pin_position("1")
    r13_p2 = r_g4.pin_position("2")

    wire(drv3_out[0], drv3_out[1], r12_p1[0], drv3_out[1])
    wire(r12_p1[0], drv3_out[1], r12_p1[0], r12_p1[1])

    wire(drv4_out[0], drv4_out[1], r13_p1[0], drv4_out[1])
    wire(r13_p1[0], drv4_out[1], r13_p1[0], r13_p1[1])

    # Wire IN- pins to GND (enables non-inverting operation)
    wire(drv3_in_neg[0], drv3_in_neg[1], drv3_gnd[0], drv3_in_neg[1])
    wire(drv3_gnd[0], drv3_in_neg[1], drv3_gnd[0], drv3_gnd[1])
    wire(drv4_in_neg[0], drv4_in_neg[1], drv4_gnd[0], drv4_in_neg[1])
    wire(drv4_gnd[0], drv4_in_neg[1], drv4_gnd[0], drv4_gnd[1])

    # Wire OUTL in parallel with OUTH (both outputs to gate resistor)
    wire(drv3_outl[0], drv3_outl[1], r12_p1[0], drv3_outl[1])
    wire(r12_p1[0], drv3_outl[1], r12_p1[0], drv3_out[1])
    wire(drv4_outl[0], drv4_outl[1], r13_p1[0], drv4_outl[1])
    wire(r13_p1[0], drv4_outl[1], r13_p1[0], drv4_out[1])

    # Wire to Q3, Q4 gates
    q3_g = q3.pin_position("G")
    q3_d = q3.pin_position("D")
    q3_s = q3.pin_position("S")
    q4_g = q4.pin_position("G")
    q4_d = q4.pin_position("D")
    q4_s = q4.pin_position("S")

    wire(r12_p2[0], r12_p2[1], q3_g[0], r12_p2[1])
    wire(q3_g[0], r12_p2[1], q3_g[0], q3_g[1])

    wire(r13_p2[0], r13_p2[1], q4_g[0], r13_p2[1])
    wire(q4_g[0], r13_p2[1], q4_g[0], q4_g[1])

    # Q3, Q4 sources tied
    wire(q3_s[0], q3_s[1], q4_s[0], q3_s[1])
    wire(q4_s[0], q3_s[1], q4_s[0], q4_s[1])

    # SC_NEG_PLUS and BUS_NEG labels
    sch.remove_label("SC_NEG_PLUS")
    wire(q3_d[0], q3_d[1], q3_d[0] + 5, q3_d[1])
    sch.add_label("SC_NEG_PLUS", q3_d[0] + 5, q3_d[1])
    sch.add_label("SC_POS_MINUS", q3_d[0] + 5, q3_d[1])  # Series junction with SC_NEG_PLUS

    sch.remove_label("BUS_NEG")
    wire(q4_d[0], q4_d[1], q4_d[0] + 5, q4_d[1])
    sch.add_label("BUS_NEG", q4_d[0] + 5, q4_d[1])

    # Q3, Q4 gate bleeders and TVS
    r_gb3_p1 = r_gb3.pin_position("1")
    r_gb3_p2 = r_gb3.pin_position("2")
    r_gb4_p1 = r_gb4.pin_position("1")
    r_gb4_p2 = r_gb4.pin_position("2")
    tvs3_a1 = d_tvs3.pin_position("A1")
    tvs3_a2 = d_tvs3.pin_position("A2")
    tvs4_a1 = d_tvs4.pin_position("A1")
    tvs4_a2 = d_tvs4.pin_position("A2")

    # R_GB3: Pin 1 to Q3 gate, Pin 2 to Q3 source (with vertical segments)
    wire(r_gb3_p1[0], r_gb3_p1[1], q3_g[0], r_gb3_p1[1])
    wire(q3_g[0], r_gb3_p1[1], q3_g[0], q3_g[1])  # Vertical to gate
    wire(r_gb3_p2[0], r_gb3_p2[1], q3_s[0], r_gb3_p2[1])
    wire(q3_s[0], r_gb3_p2[1], q3_s[0], q3_s[1])  # Vertical to source

    # R_GB4: Pin 1 to Q4 gate, Pin 2 to Q4 source (with vertical segments)
    wire(r_gb4_p1[0], r_gb4_p1[1], q4_g[0], r_gb4_p1[1])
    wire(q4_g[0], r_gb4_p1[1], q4_g[0], q4_g[1])  # Vertical to gate
    wire(r_gb4_p2[0], r_gb4_p2[1], q4_s[0], r_gb4_p2[1])
    wire(q4_s[0], r_gb4_p2[1], q4_s[0], q4_s[1])  # Vertical to source

    # TVS3: A1 to Q3 gate, A2 to Q3 source (with vertical segments)
    wire(tvs3_a1[0], tvs3_a1[1], q3_g[0], tvs3_a1[1])
    wire(q3_g[0], tvs3_a1[1], q3_g[0], q3_g[1])  # Vertical to gate
    wire(tvs3_a2[0], tvs3_a2[1], q3_s[0], tvs3_a2[1])
    wire(q3_s[0], tvs3_a2[1], q3_s[0], q3_s[1])  # Vertical to source

    # TVS4: A1 to Q4 gate, A2 to Q4 source (with vertical segments)
    wire(tvs4_a1[0], tvs4_a1[1], q4_g[0], tvs4_a1[1])
    wire(q4_g[0], tvs4_a1[1], q4_g[0], q4_g[1])  # Vertical to gate
    wire(tvs4_a2[0], tvs4_a2[1], q4_s[0], tvs4_a2[1])
    wire(q4_s[0], tvs4_a2[1], q4_s[0], q4_s[1])  # Vertical to source

    # -------------------------------------------------------------------------
    # Failsafe FET Wiring
    # -------------------------------------------------------------------------
    q7_g = q_fs1.pin_position("G")
    q7_d = q_fs1.pin_position("D")
    q7_s = q_fs1.pin_position("S")
    q8_g = q_fs2.pin_position("G")
    q8_d = q_fs2.pin_position("D")
    q8_s = q_fs2.pin_position("S")

    r14_p1 = r_fs1.pin_position("1")
    r14_p2 = r_fs1.pin_position("2")
    r15_p1 = r_fs2.pin_position("1")
    r15_p2 = r_fs2.pin_position("2")

    # Failsafe gates driven by NRST_INV
    sch.remove_label("NRST_INV")
    wire(r14_p1[0] - 5, r14_p1[1], r14_p1[0], r14_p1[1])
    sch.add_label("NRST_INV", r14_p1[0] - 5, r14_p1[1])
    wire(r14_p2[0], r14_p2[1], q7_g[0], r14_p2[1])
    wire(q7_g[0], r14_p2[1], q7_g[0], q7_g[1])

    wire(r15_p1[0] - 5, r15_p1[1], r15_p1[0], r15_p1[1])
    sch.add_label("NRST_INV", r15_p1[0] - 5, r15_p1[1])
    wire(r15_p2[0], r15_p2[1], q8_g[0], r15_p2[1])
    wire(q8_g[0], r15_p2[1], q8_g[0], q8_g[1])

    # Failsafe drains to gate buses, sources to GND
    # Q7 drain connects to Q1/Q2 gate bus (need horizontal + vertical wire)
    wire(q7_d[0], q7_d[1], q1_g[0], q7_d[1])
    wire(q1_g[0], q7_d[1], q1_g[0], q1_g[1])  # Vertical to connect to gate bus
    sch.add_power("power:GND", q7_s[0], q7_s[1] + 5)
    wire(q7_s[0], q7_s[1], q7_s[0], q7_s[1] + 5)

    # Q8 drain connects to Q3/Q4 gate bus
    wire(q8_d[0], q8_d[1], q3_g[0], q8_d[1])
    wire(q3_g[0], q8_d[1], q3_g[0], q3_g[1])  # Vertical to connect to gate bus
    sch.add_power("power:GND", q8_s[0], q8_s[1] + 5)
    wire(q8_s[0], q8_s[1], q8_s[0], q8_s[1] + 5)

    # -------------------------------------------------------------------------
    # Precharge Circuit Wiring
    # -------------------------------------------------------------------------
    r16_p1 = r_prechg_pos.pin_position("1")
    r16_p2 = r_prechg_pos.pin_position("2")
    q5_g = q_prechg_pos.pin_position("G")
    q5_d = q_prechg_pos.pin_position("D")
    q5_s = q_prechg_pos.pin_position("S")
    r21_p1 = r_pg_pos.pin_position("1")
    r21_p2 = r_pg_pos.pin_position("2")

    # Wire precharge resistor in series with FET
    wire(r16_p2[0], r16_p2[1], q5_d[0], r16_p2[1])
    wire(q5_d[0], r16_p2[1], q5_d[0], q5_d[1])

    # Gate pull-down
    wire(r21_p2[0], r21_p2[1], q5_g[0], r21_p2[1])
    wire(q5_g[0], r21_p2[1], q5_g[0], q5_g[1])
    sch.add_power("power:GND", r21_p1[0], r21_p1[1] - 5)
    wire(r21_p1[0], r21_p1[1] - 5, r21_p1[0], r21_p1[1])

    # PRECHG_POS control - use global label to avoid wire crossing
    sch.remove_label("PRECHG_POS")
    wire(q5_g[0] - 10, q5_g[1], q5_g[0], q5_g[1])
    sch.add_global_label("PRECHG_POS", q5_g[0] - 10, q5_g[1], shape="input")

    # Connect precharge to bus
    wire(r16_p1[0] - 5, r16_p1[1], r16_p1[0], r16_p1[1])
    sch.add_label("BUS_POS", r16_p1[0] - 5, r16_p1[1])
    wire(q5_s[0], q5_s[1], q5_s[0] + 5, q5_s[1])
    sch.add_label("SC_POS_PLUS", q5_s[0] + 5, q5_s[1])

    # MCU precharge control - use global label with short stub
    mcu_prechg_pos = u_mcu.pin_position("PA8/PB0/PB1/PB2")
    stub = 5 if mcu_prechg_pos[0] > MCU_X else -5
    wire(mcu_prechg_pos[0], mcu_prechg_pos[1], mcu_prechg_pos[0] + stub, mcu_prechg_pos[1])
    sch.add_global_label("PRECHG_POS", mcu_prechg_pos[0] + stub, mcu_prechg_pos[1], shape="output")

    # Negative bank precharge (similar)
    r17_p1 = r_prechg_neg.pin_position("1")
    r17_p2 = r_prechg_neg.pin_position("2")
    q6_g = q_prechg_neg.pin_position("G")
    q6_d = q_prechg_neg.pin_position("D")
    q6_s = q_prechg_neg.pin_position("S")
    r22_p1 = r_pg_neg.pin_position("1")
    r22_p2 = r_pg_neg.pin_position("2")

    wire(r17_p2[0], r17_p2[1], q6_d[0], r17_p2[1])
    wire(q6_d[0], r17_p2[1], q6_d[0], q6_d[1])

    wire(r22_p2[0], r22_p2[1], q6_g[0], r22_p2[1])
    wire(q6_g[0], r22_p2[1], q6_g[0], q6_g[1])
    sch.add_power("power:GND", r22_p1[0], r22_p1[1] - 5)
    wire(r22_p1[0], r22_p1[1] - 5, r22_p1[0], r22_p1[1])

    # PRECHG_NEG control - use global label to avoid wire crossing
    sch.remove_label("PRECHG_NEG")
    wire(q6_g[0] - 10, q6_g[1], q6_g[0], q6_g[1])
    sch.add_global_label("PRECHG_NEG", q6_g[0] - 10, q6_g[1], shape="input")

    wire(r17_p1[0] - 5, r17_p1[1], r17_p1[0], r17_p1[1])
    sch.add_label("BUS_NEG", r17_p1[0] - 5, r17_p1[1])
    wire(q6_s[0], q6_s[1], q6_s[0] + 5, q6_s[1])
    sch.add_label("SC_NEG_PLUS", q6_s[0] + 5, q6_s[1])

    # PRECHG_NEG MCU control - use global label with short stub
    mcu_prechg_neg = u_mcu.pin_position("PB3/PB4/PB5/PB6")
    stub = 5 if mcu_prechg_neg[0] > MCU_X else -5
    wire(mcu_prechg_neg[0], mcu_prechg_neg[1], mcu_prechg_neg[0] + stub, mcu_prechg_neg[1])
    sch.add_global_label("PRECHG_NEG", mcu_prechg_neg[0] + stub, mcu_prechg_neg[1], shape="output")

    # -------------------------------------------------------------------------
    # LED wiring
    # -------------------------------------------------------------------------
    sch.wire_pins(r_led, "2", d_led, "A")

    led_k = d_led.pin_position("K")
    sch.add_power("power:GND", led_k[0], led_k[1] + 5)
    wire(led_k[0], led_k[1], led_k[0], led_k[1] + 5)

    # LED_STATUS - use global label to avoid wire crossing
    r25_p1 = r_led.pin_position("1")
    sch.remove_label("LED_STATUS")
    wire(r25_p1[0] - 5, r25_p1[1], r25_p1[0], r25_p1[1])
    sch.add_global_label("LED_STATUS", r25_p1[0] - 5, r25_p1[1], shape="input")

    # LED_STATUS MCU control - use global label with short stub
    mcu_led = u_mcu.pin_position("PB7/PB8")
    stub = 5 if mcu_led[0] > MCU_X else -5
    wire(mcu_led[0], mcu_led[1], mcu_led[0] + stub, mcu_led[1])
    sch.add_global_label("LED_STATUS", mcu_led[0] + stub, mcu_led[1], shape="output")

    # -------------------------------------------------------------------------
    # Supercapacitor bank wiring
    # -------------------------------------------------------------------------
    print("  Wiring positive supercap bank in series...")
    for i in range(len(cap_refs_pos) - 1):
        try:
            sch.wire_pins(cap_refs_pos[i], "2", cap_refs_pos[i + 1], "1")
        except Exception:
            pass

    print("  Wiring negative supercap bank in series...")
    for i in range(len(cap_refs_neg) - 1):
        try:
            sch.wire_pins(cap_refs_neg[i], "2", cap_refs_neg[i + 1], "1")
        except Exception:
            pass

    # Supercap bank labels (added with wire connections)
    # First cap of positive bank
    cap_pos_first_p1 = cap_refs_pos[0].pin_position("1")
    wire(cap_pos_first_p1[0] - 5, cap_pos_first_p1[1], cap_pos_first_p1[0], cap_pos_first_p1[1])
    sch.add_label("SC_POS_PLUS", cap_pos_first_p1[0] - 5, cap_pos_first_p1[1])

    # Last cap of positive bank
    cap_pos_last_p2 = cap_refs_pos[-1].pin_position("2")
    wire(cap_pos_last_p2[0], cap_pos_last_p2[1], cap_pos_last_p2[0] + 5, cap_pos_last_p2[1])
    sch.add_label("SC_POS_MINUS", cap_pos_last_p2[0] + 5, cap_pos_last_p2[1])

    # First cap of negative bank
    cap_neg_first_p1 = cap_refs_neg[0].pin_position("1")
    wire(cap_neg_first_p1[0] - 5, cap_neg_first_p1[1], cap_neg_first_p1[0], cap_neg_first_p1[1])
    sch.add_label("SC_NEG_PLUS", cap_neg_first_p1[0] - 5, cap_neg_first_p1[1])

    # Last cap of negative bank
    cap_neg_last_p2 = cap_refs_neg[-1].pin_position("2")
    wire(cap_neg_last_p2[0], cap_neg_last_p2[1], cap_neg_last_p2[0] + 5, cap_neg_last_p2[1])
    sch.add_label("SC_NEG_MINUS", cap_neg_last_p2[0] + 5, cap_neg_last_p2[1])

    # Connect SC_NEG_MINUS to GND (negative bank return path)
    wire(cap_neg_last_p2[0] + 5, cap_neg_last_p2[1], cap_neg_last_p2[0] + 5, cap_neg_last_p2[1] + 10)
    sch.add_power("power:GND", cap_neg_last_p2[0] + 5, cap_neg_last_p2[1] + 10)

    # Connect supercap banks: SC_POS_MINUS = SC_NEG_PLUS (series junction), SC_NEG_MINUS = GND
    # The FETs switch between supercap and bus

    # -------------------------------------------------------------------------
    # Charging circuit wiring
    # -------------------------------------------------------------------------
    r23_p1 = r_chg_pos.pin_position("1")
    r23_p2 = r_chg_pos.pin_position("2")
    d6_a = d_chg_pos.pin_position("A")
    d6_k = d_chg_pos.pin_position("K")

    wire(r23_p2[0], r23_p2[1], d6_a[0], r23_p2[1])
    wire(d6_a[0], r23_p2[1], d6_a[0], d6_a[1])

    # Use different X offsets to prevent vertical wire overlap - use global labels
    wire(r23_p1[0] - 10, r23_p1[1], r23_p1[0], r23_p1[1])
    sch.add_global_label("AC_L", r23_p1[0] - 10, r23_p1[1], shape="passive")
    wire(d6_k[0], d6_k[1], d6_k[0] + 5, d6_k[1])
    sch.add_label("SC_POS_PLUS", d6_k[0] + 5, d6_k[1])

    r24_p1 = r_chg_neg.pin_position("1")
    r24_p2 = r_chg_neg.pin_position("2")
    d7_a = d_chg_neg.pin_position("A")
    d7_k = d_chg_neg.pin_position("K")

    wire(r24_p2[0], r24_p2[1], d7_a[0], r24_p2[1])
    wire(d7_a[0], r24_p2[1], d7_a[0], d7_a[1])

    # Use same offset as AC_L - use global labels
    wire(r24_p1[0] - 10, r24_p1[1], r24_p1[0], r24_p1[1])
    sch.add_global_label("AC_N", r24_p1[0] - 10, r24_p1[1], shape="passive")
    wire(d7_k[0], d7_k[1], d7_k[0] + 5, d7_k[1])
    sch.add_label("SC_NEG_PLUS", d7_k[0] + 5, d7_k[1])

    print(f"  Added {len(sch.wires)} wires")

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
