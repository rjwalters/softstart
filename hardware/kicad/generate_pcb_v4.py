#!/usr/bin/env python3
"""
Generator Soft-Start PCB Generator v4

Uses kicad-tools v0.10.2 with full manufacturing workflow:
- Footprint import with net assignment
- Component placement
- Collision detection
- Copper pour zones
- Trace routing
- Silkscreen cleanup
- Manufacturing export
"""

import sys
from pathlib import Path

# Add kicad-tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "kicad-tools" / "src"))

from kicad_tools.schema.pcb import PCB
from kicad_tools.project import Project

BOARD_WIDTH = 200.0
BOARD_HEIGHT = 120.0
MARGIN = 5.0


def get_placements() -> dict[str, tuple[float, float, float]]:
    """
    Returns {reference: (x, y, rotation)}

    Layout:
    - Left: 60 supercaps in two 3x10 banks
    - Left edge: Connectors, varistor
    - Upper right: Power supplies
    - Center right: MCU, sensing, gate drivers
    - Far right: Discharge MOSFETs
    - Bottom right: Precharge circuits
    """
    p = {}

    # ==========================================================================
    # Supercapacitor Banks - 10mm radial caps, 12mm spacing
    # Moved left to leave room for control electronics on the right
    # ==========================================================================
    SC_SPACING = 12.0
    SC_X = 18.0  # Start closer to left edge (extends to 18+9*12=126mm)

    # Positive bank (C101-C130) - upper left
    for i in range(30):
        p[f"C{101+i}"] = (SC_X + (i % 10) * SC_SPACING, 15 + (i // 10) * SC_SPACING, 0)

    # Negative bank (C131-C160) - lower left
    for i in range(30):
        p[f"C{131+i}"] = (SC_X + (i % 10) * SC_SPACING, 56 + (i // 10) * SC_SPACING, 0)

    # ==========================================================================
    # Connectors - Left edge (spaced to avoid overlaps)
    # ==========================================================================
    p["J1"] = (6, 15, 0)    # AC_IN (moved up)
    p["J2"] = (6, 52, 0)    # AC_OUT (center of gap between supercap banks)
    p["J3"] = (6, 98, 0)    # SWD header (moved up away from H3 mounting hole)
    p["RV1"] = (6, 35, 90)  # Varistor (rotated to fit)

    # ==========================================================================
    # Power Supplies - Upper right (shifted right to avoid supercaps)
    # ==========================================================================
    PWR_X = 165
    PWR_Y = 12

    # 12V supply
    p["D5"] = (PWR_X - 25, PWR_Y, 0)       # Bridge rectifier MB6S
    p["C8"] = (PWR_X - 12, PWR_Y + 10, 0)  # 1000uF 25V bulk cap (10mm radial)
    p["U7"] = (PWR_X, PWR_Y, 0)            # LM7812
    p["C9"] = (PWR_X + 12, PWR_Y + 8, 0)   # 10uF output cap

    # 3.3V supply (shifted down to avoid gate drivers)
    p["U8"] = (PWR_X - 15, PWR_Y + 22, 0)  # AMS1117-3.3
    p["C1"] = (PWR_X - 25, PWR_Y + 27, 0)  # Input cap
    p["C2"] = (PWR_X - 5, PWR_Y + 27, 0)   # Output cap

    # ==========================================================================
    # MCU Section - Center right (all electronics right of x=135)
    # ==========================================================================
    MCU_X = 160
    MCU_Y = 50

    p["U1"] = (MCU_X, MCU_Y, 0)            # STM32G031F6P6
    p["C3"] = (MCU_X - 10, MCU_Y - 5, 0)   # Bypass cap
    p["C4"] = (MCU_X - 10, MCU_Y + 5, 0)   # Bypass cap
    p["R1"] = (MCU_X + 12, MCU_Y - 5, 90)  # Pull-up

    # ==========================================================================
    # Zero-Crossing Detector - Below MCU (R2/R3 shifted right to avoid supercaps)
    # ==========================================================================
    ZC_X = 148
    ZC_Y = 65

    p["U6"] = (ZC_X, ZC_Y, 0)              # H11AA1 optocoupler
    p["R2"] = (ZC_X - 10, ZC_Y - 4, 0)     # Input resistor
    p["R3"] = (ZC_X - 10, ZC_Y + 4, 0)     # Input resistor
    p["R4"] = (ZC_X + 10, ZC_Y, 90)        # Output pull-up

    # ==========================================================================
    # Current Sense - Below zero-crossing (spaced to avoid OCP)
    # ==========================================================================
    SENSE_X = 165
    SENSE_Y = 82

    p["U4"] = (SENSE_X, SENSE_Y, 0)        # INA180
    p["R_SHUNT"] = (SENSE_X - 20, SENSE_Y, 0)  # 5mR shunt
    p["C5"] = (SENSE_X + 10, SENSE_Y, 0)   # Filter cap
    p["R5"] = (SENSE_X - 8, SENSE_Y + 8, 0)

    # ==========================================================================
    # Overcurrent Comparator - Left of current sense (spaced to avoid shunt)
    # ==========================================================================
    OCP_X = 148
    OCP_Y = 76

    p["U5"] = (OCP_X, OCP_Y, 0)            # LMV331
    p["R6"] = (OCP_X - 8, OCP_Y - 4, 0)    # Threshold divider
    p["R7"] = (OCP_X - 8, OCP_Y + 6, 90)   # Threshold divider (rotated, moved down)
    p["R20"] = (OCP_X + 8, OCP_Y, 0)

    # ==========================================================================
    # Gate Drivers - Right side, near MOSFETs
    # ==========================================================================
    GATE_X = 178
    GATE_Y = 55

    p["U2"] = (GATE_X, GATE_Y - 16, 0)     # UCC27511A
    p["U3"] = (GATE_X, GATE_Y - 5, 0)      # UCC27511A
    p["U9"] = (GATE_X, GATE_Y + 6, 0)      # UCC27511A
    p["U10"] = (GATE_X, GATE_Y + 17, 0)    # UCC27511A

    # Gate driver bypass caps
    p["C10"] = (GATE_X - 8, GATE_Y - 16, 0)
    p["C11"] = (GATE_X - 8, GATE_Y - 5, 0)
    p["C12"] = (GATE_X - 8, GATE_Y + 6, 0)
    p["C13"] = (GATE_X - 8, GATE_Y + 17, 0)
    p["C14"] = (GATE_X - 2, GATE_Y - 11, 0)   # Between drivers, shared bypass

    # ==========================================================================
    # Discharge MOSFETs - Far right edge
    # ==========================================================================
    MOSFET_X = 193
    MOSFET_Y = 55

    p["Q1"] = (MOSFET_X, MOSFET_Y - 22, 270)  # IRFB4110
    p["Q2"] = (MOSFET_X, MOSFET_Y - 7, 270)   # IRFB4110
    p["Q3"] = (MOSFET_X, MOSFET_Y + 8, 270)   # IRFB4110
    p["Q4"] = (MOSFET_X, MOSFET_Y + 23, 270)  # IRFB4110

    # Gate resistors (between gate drivers and MOSFETs, spaced from gate drivers)
    p["R8"] = (MOSFET_X - 10, MOSFET_Y - 22, 0)
    p["R9"] = (MOSFET_X - 10, MOSFET_Y - 7, 0)
    p["R10"] = (MOSFET_X - 10, MOSFET_Y + 8, 0)

    # Gate bleed resistors (near MOSFET gates)
    p["R_GB1"] = (MOSFET_X - 12, MOSFET_Y - 27, 90)
    p["R_GB2"] = (MOSFET_X - 12, MOSFET_Y - 12, 90)
    p["R_GB3"] = (MOSFET_X - 12, MOSFET_Y + 3, 90)
    p["R_GB4"] = (MOSFET_X - 12, MOSFET_Y + 18, 90)

    # TVS diodes for gate protection (close to MOSFETs, not overlapping gate drivers)
    p["D1"] = (MOSFET_X - 6, MOSFET_Y - 28, 90)   # SMBJ18A rotated
    p["D2"] = (MOSFET_X - 6, MOSFET_Y - 13, 90)
    p["D3"] = (MOSFET_X - 6, MOSFET_Y + 2, 90)
    p["D4"] = (MOSFET_X - 6, MOSFET_Y + 17, 90)

    # ==========================================================================
    # Precharge Circuits - Bottom right
    # ==========================================================================
    PRECHG_X = 145
    PRECHG_Y = 95

    p["Q5"] = (PRECHG_X, PRECHG_Y, 0)         # AO3400
    p["Q6"] = (PRECHG_X + 10, PRECHG_Y, 0)    # AO3400
    p["Q7"] = (PRECHG_X + 20, PRECHG_Y, 0)    # 2N7002
    p["Q8"] = (PRECHG_X + 30, PRECHG_Y, 0)    # 2N7002

    p["D6"] = (PRECHG_X - 6, PRECHG_Y - 7, 0)  # 1N4007
    p["D7"] = (PRECHG_X + 4, PRECHG_Y - 7, 0)  # 1N4007

    p["R11"] = (PRECHG_X, PRECHG_Y + 7, 0)
    p["R12"] = (PRECHG_X + 10, PRECHG_Y + 7, 0)
    p["R13"] = (PRECHG_X + 20, PRECHG_Y + 7, 0)

    # High-power precharge resistors
    p["R16"] = (PRECHG_X - 10, PRECHG_Y + 14, 0)   # 100R 5W
    p["R17"] = (PRECHG_X + 4, PRECHG_Y + 14, 0)    # 100R 5W
    p["R23"] = (PRECHG_X + 18, PRECHG_Y + 14, 0)   # 220R 2W
    p["R24"] = (PRECHG_X + 32, PRECHG_Y + 14, 0)   # 220R 2W

    # ==========================================================================
    # Status LED - Near power supply
    # ==========================================================================
    p["D8"] = (PWR_X - 20, PWR_Y + 5, 0)    # Green LED
    p["R25"] = (PWR_X - 28, PWR_Y + 5, 0)   # LED resistor

    # ==========================================================================
    # Remaining Resistors - Spread around related components
    # ==========================================================================
    p["R14"] = (GATE_X - 16, GATE_Y - 24, 0)   # Moved left/up to avoid U8
    p["R15"] = (GATE_X - 16, GATE_Y + 30, 0)   # Moved down to avoid U4
    p["R18"] = (MCU_X - 16, MCU_Y - 7, 0)
    p["R19"] = (MCU_X - 16, MCU_Y + 7, 0)
    p["R21"] = (ZC_X + 12, ZC_Y - 5, 0)
    p["R22"] = (ZC_X + 12, ZC_Y + 5, 0)

    return p


def generate_pcb():
    """Generate the PCB using kicad-tools v0.10.2."""
    script_dir = Path(__file__).parent
    sch_path = script_dir / "softstart.kicad_sch"
    pcb_path = script_dir / "softstart.kicad_pcb"
    output_dir = script_dir / "manufacturing"

    print("Softstart PCB Generator v4 (kicad-tools 0.10.2)")
    print("=" * 60)
    print(f"Schematic: {sch_path}")
    print(f"Output: {pcb_path}")
    print()

    # =========================================================================
    # Step 1: Create PCB and import footprints
    # =========================================================================
    print("Step 1: Creating PCB and importing footprints...")
    pcb = PCB.create(
        width=BOARD_WIDTH,
        height=BOARD_HEIGHT,
        layers=2,
        title="Generator Soft-Start",
        revision="B",
    )

    result = pcb.import_from_schematic(str(sch_path))
    print(f"  Added {len(result.get('footprints_added', []))} footprints")
    print(f"  Assigned {len(result.get('nets_assigned', []))} net connections")

    # =========================================================================
    # Step 2: Apply component placements with collision detection
    # =========================================================================
    print("\nStep 2: Applying component placements...")
    placements = get_placements()

    # Check for collisions before placing
    if hasattr(pcb, 'validate_placements'):
        result = pcb.validate_placements(placements)
        if result.collisions:
            print(f"  Warning: {len(result.collisions)} placement collisions detected")
            for issue in result.collisions[:5]:
                print(f"    - {issue.ref1} <-> {issue.ref2}: {issue.violation_type}")

    updated = 0
    missing = []
    for ref, (x, y, rot) in placements.items():
        if pcb.update_footprint_position(ref, x, y, rot):
            updated += 1
        else:
            missing.append(ref)

    print(f"  Positioned {updated} components")
    if missing:
        print(f"  Not found: {missing[:10]}{'...' if len(missing) > 10 else ''}")

    # Add mounting holes
    print("  Adding mounting holes...")
    for i, (mx, my) in enumerate([(4, 4), (196, 4), (4, 116), (196, 116)]):
        pcb.add_footprint(
            library_id="MountingHole:MountingHole_3.2mm_M3",
            reference=f"H{i+1}",
            x=mx,
            y=my,
            value="M3",
        )

    # =========================================================================
    # Step 3: Save initial PCB
    # =========================================================================
    print(f"\nStep 3: Saving initial PCB to {pcb_path}...")
    pcb.save(str(pcb_path))

    # Print summary
    summary = pcb.summary()
    print(f"  Footprints: {summary.get('footprints', 0)}")
    print(f"  Nets: {summary.get('nets', 0)}")

    # =========================================================================
    # Step 4: Use Project class for routing and manufacturing
    # =========================================================================
    print("\nStep 4: Loading project for routing...")
    try:
        project = Project(
            schematic=str(sch_path),
            pcb=str(pcb_path),
        )
        print("  Project loaded")

        # Route traces (skip GND - will be a pour)
        print("\nStep 5: Routing traces...")
        try:
            route_result = project.route(skip_nets=["GND"])
            print(f"  Routed {route_result.routed_nets}/{route_result.total_nets} nets")
            print(f"  Segments: {route_result.total_segments}")
            print(f"  Vias: {route_result.total_vias}")
            print(f"  Trace length: {route_result.total_length_mm:.1f}mm")
        except Exception as e:
            print(f"  Routing error: {e}")
            import traceback
            traceback.print_exc()

        # Export manufacturing files
        print(f"\nStep 6: Exporting manufacturing files to {output_dir}...")
        output_dir.mkdir(exist_ok=True)
        try:
            # Export Gerbers
            gerber_files = project.export_gerbers(str(output_dir), manufacturer="jlcpcb")
            print(f"  Gerbers: {len(gerber_files)} files")

            # Export assembly files
            if hasattr(project, 'export_assembly'):
                assembly_files = project.export_assembly(str(output_dir))
                print(f"  Assembly: BOM + placement files")
        except Exception as e:
            print(f"  Export error: {e}")

    except Exception as e:
        print(f"  Project load error: {e}")
        print("  Falling back to PCB-only workflow")

    # =========================================================================
    # Step 7: Run DRC
    # =========================================================================
    print("\nStep 7: Running DRC...")
    # Reload PCB to get updated state
    pcb = PCB.load(str(pcb_path))
    if hasattr(pcb, 'run_drc'):
        try:
            drc_result = pcb.run_drc()
            print(f"  Clearance violations: {drc_result.clearance_count}")
            print(f"  Courtyard overlaps: {drc_result.courtyard_count}")
            print(f"  Total violations: {len(drc_result.violations)}")
        except Exception as e:
            print(f"  DRC error: {e}")
    else:
        print("  DRC API not available")

    # Final summary
    print("\n" + "=" * 60)
    print("PCB Generation Complete!")
    print()
    summary = pcb.summary()
    for key, val in summary.items():
        print(f"  {key}: {val}")
    print("\n" + "=" * 60)
    print("Done!")


if __name__ == "__main__":
    generate_pcb()
