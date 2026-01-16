#!/usr/bin/env python3
"""
Generator Soft-Start PCB Generator

Creates the initial PCB layout from the schematic, placing components
in functional groups for optimal routing.

Board specifications:
- 2-layer PCB (high current paths need wide traces or copper pours)
- 100mm x 150mm target size
- 1oz copper (2oz for power nets recommended)
"""

import sys
import uuid
import re
from pathlib import Path
from dataclasses import dataclass, field

# Simple S-expression parser (avoid kicad_tools dependency on numpy)
class SExp:
    """Simple S-expression node."""
    def __init__(self, tag: str = "", children: list = None, value: str = None):
        self.tag = tag
        self.children = children or []
        self.value = value

    def find_all(self, tag: str):
        """Find all children with given tag."""
        return [c for c in self.children if isinstance(c, SExp) and c.tag == tag]

    def get(self, tag: str):
        """Get first child with given tag."""
        for c in self.children:
            if isinstance(c, SExp) and c.tag == tag:
                return c
        return None

    def get_atoms(self):
        """Get all string values from children."""
        return [c.value for c in self.children if isinstance(c, SExp) and c.value is not None]

    def get_first_atom(self):
        """Get first string value."""
        atoms = self.get_atoms()
        return atoms[0] if atoms else None


def parse_sexp(text: str) -> SExp:
    """Parse S-expression text into SExp tree."""
    tokens = tokenize(text)
    pos = [0]
    return parse_tokens(tokens, pos)


def tokenize(text: str) -> list:
    """Tokenize S-expression text."""
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c in '()':
            tokens.append(c)
            i += 1
        elif c == '"':
            # Quoted string
            j = i + 1
            while j < len(text) and text[j] != '"':
                if text[j] == '\\':
                    j += 2
                else:
                    j += 1
            tokens.append(text[i+1:j])
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            # Unquoted atom
            j = i
            while j < len(text) and text[j] not in '() \t\n\r"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def parse_tokens(tokens: list, pos: list) -> SExp:
    """Parse token list into SExp tree."""
    if pos[0] >= len(tokens):
        return SExp()

    if tokens[pos[0]] == '(':
        pos[0] += 1
        if pos[0] >= len(tokens):
            return SExp()

        # First token after '(' is the tag
        tag = tokens[pos[0]]
        pos[0] += 1

        node = SExp(tag=tag)

        while pos[0] < len(tokens) and tokens[pos[0]] != ')':
            if tokens[pos[0]] == '(':
                node.children.append(parse_tokens(tokens, pos))
            else:
                # Atom value
                node.children.append(SExp(value=tokens[pos[0]]))
                pos[0] += 1

        if pos[0] < len(tokens):
            pos[0] += 1  # Skip closing ')'

        return node
    else:
        val = tokens[pos[0]]
        pos[0] += 1
        return SExp(value=val)


def parse_file(path: str) -> SExp:
    """Parse S-expression file."""
    text = Path(path).read_text()
    return parse_sexp(text)


@dataclass
class Component:
    """A component extracted from the schematic."""
    ref: str
    value: str
    footprint: str
    lib_id: str
    x: float = 0
    y: float = 0
    rotation: float = 0
    layer: str = "F.Cu"


def parse_schematic(sch_path: str) -> list[Component]:
    """Parse schematic and extract all components with footprints."""
    doc = parse_file(sch_path)
    components = []

    # Find all symbol nodes at root level (skip lib_symbols section)
    for child in doc.children:
        if not isinstance(child, SExp):
            continue

        # Skip lib_symbols - these are library definitions, not placed components
        if child.tag == "lib_symbols":
            continue

        if child.tag != "symbol":
            continue

        sym = child

        # Check if this is a placed symbol (has lib_id child)
        lib_id_node = sym.get("lib_id")
        if not lib_id_node:
            continue

        lib_id = lib_id_node.get_first_atom()
        if not lib_id:
            continue

        # Skip power symbols
        if str(lib_id).startswith("power:"):
            continue

        # Get reference, value, and footprint from properties
        ref = ""
        value = ""
        footprint = ""

        for prop in sym.find_all("property"):
            prop_atoms = prop.get_atoms()
            if len(prop_atoms) >= 2:
                prop_name = str(prop_atoms[0])
                prop_value = str(prop_atoms[1])

                if prop_name == "Reference":
                    ref = prop_value
                elif prop_name == "Value":
                    value = prop_value
                elif prop_name == "Footprint":
                    footprint = prop_value

        if ref and footprint:
            components.append(Component(
                ref=ref,
                value=value,
                footprint=footprint,
                lib_id=str(lib_id)
            ))
            print(f"  Found: {ref} ({value}) -> {footprint}")

    return components


def group_components(components: list[Component]) -> dict[str, list[Component]]:
    """Group components by function."""
    groups = {
        "supercap_pos": [],
        "supercap_neg": [],
        "connectors": [],
        "mcu": [],
        "sensing": [],
        "discharge": [],
        "charging": [],
        "power": [],
        "passives": [],
    }

    for comp in components:
        ref = comp.ref

        # Supercaps: C101-C130 positive bank, C131-C160 negative bank
        if ref.startswith("C") and len(ref) > 1:
            try:
                num = int(ref[1:])
                if 101 <= num <= 130:
                    groups["supercap_pos"].append(comp)
                    continue
                elif 131 <= num <= 160:
                    groups["supercap_neg"].append(comp)
                    continue
            except ValueError:
                pass

        # Connectors
        if ref.startswith("J"):
            groups["connectors"].append(comp)

        # MCU
        elif ref == "U1":
            groups["mcu"].append(comp)

        # Zero-crossing detector (H11AA1)
        elif ref == "U2":
            groups["sensing"].append(comp)

        # LDO regulator
        elif ref == "U3":
            groups["power"].append(comp)

        # Current sense amplifier (INA180)
        elif ref == "U4":
            groups["sensing"].append(comp)

        # Discharge MOSFETs (Q1, Q2 are IRFB4110)
        elif ref in ["Q1", "Q2"]:
            groups["discharge"].append(comp)

        # Charging MOSFETs and their resistors (Q3, Q4, R11, R12)
        elif ref in ["Q3", "Q4", "R11", "R12"]:
            groups["charging"].append(comp)

        # Varistor
        elif ref.startswith("RV"):
            groups["connectors"].append(comp)

        # LEDs and diodes
        elif ref.startswith("D") or ref.startswith("LED"):
            groups["passives"].append(comp)

        # Everything else (resistors, small caps, etc.)
        else:
            groups["passives"].append(comp)

    return groups


def place_components(groups: dict[str, list[Component]], board_width: float, board_height: float,
                     compact: bool = False):
    """
    Assign positions to all components.

    Layout strategy:
    - Compact (4-layer, 160x100mm): Tighter spacing, control below supercaps
    - Standard (2-layer, 200x120mm): Generous spacing, control on right
    """

    margin = 4.0 if compact else 5.0

    if compact:
        # ==========================================================================
        # COMPACT LAYOUT (160x100mm, 4-layer)
        # Supercaps on top half, control on bottom half
        # ==========================================================================

        # Supercap spacing: 11mm for 10mm caps (tight but workable)
        sc_spacing = 11.0
        sc_start_x = margin + 8
        sc_start_y_pos = margin + 8

        # Positive bank - top left (3 rows x 10 cols)
        for i, comp in enumerate(sorted(groups["supercap_pos"], key=lambda c: int(c.ref[1:]))):
            row = i // 10
            col = i % 10
            comp.x = sc_start_x + col * sc_spacing
            comp.y = sc_start_y_pos + row * sc_spacing
            comp.rotation = 0

        # Negative bank - below positive with minimal gap
        sc_start_y_neg = sc_start_y_pos + 3 * sc_spacing + 4

        for i, comp in enumerate(sorted(groups["supercap_neg"], key=lambda c: int(c.ref[1:]))):
            row = i // 10
            col = i % 10
            comp.x = sc_start_x + col * sc_spacing
            comp.y = sc_start_y_neg + row * sc_spacing
            comp.rotation = 0

        # Control section starts after supercaps
        ctrl_y = sc_start_y_neg + 3 * sc_spacing + 8

        # Connectors - left side, below supercaps
        conn_x = margin + 8
        for i, comp in enumerate(groups["connectors"]):
            comp.x = conn_x + i * 15
            comp.y = ctrl_y + 5
            comp.rotation = 0

        # Discharge MOSFETs - right edge
        mosfet_x = board_width - margin - 10
        mosfet_y = ctrl_y + 10
        for i, comp in enumerate(groups["discharge"]):
            comp.x = mosfet_x
            comp.y = mosfet_y + i * 15
            comp.rotation = 270

        # MCU - center of control area
        mcu_x = board_width / 2
        mcu_y = ctrl_y + 8
        for comp in groups["mcu"]:
            comp.x = mcu_x
            comp.y = mcu_y
            comp.rotation = 0

        # Sensing - near MCU
        sense_x = mcu_x + 25
        sense_y = mcu_y
        for i, comp in enumerate(groups["sensing"]):
            comp.x = sense_x
            comp.y = sense_y + i * 10
            comp.rotation = 0

        # Power (LDO) - near MCU
        for comp in groups["power"]:
            comp.x = mcu_x - 15
            comp.y = mcu_y
            comp.rotation = 0

        # Charging circuits - between connectors and MOSFETs
        charge_x = board_width - margin - 45
        charge_y = ctrl_y + 5
        for i, comp in enumerate(groups["charging"]):
            comp.x = charge_x + (i % 2) * 10
            comp.y = charge_y + (i // 2) * 8
            comp.rotation = 0

        # Passives - distributed near their ICs
        passive_x = mcu_x - 25
        passive_y = ctrl_y + 20
        for i, comp in enumerate(groups["passives"]):
            row = i // 6
            col = i % 6
            comp.x = passive_x + col * 6
            comp.y = passive_y + row * 5
            comp.rotation = 0

    else:
        # ==========================================================================
        # STANDARD LAYOUT (200x120mm, 2-layer)
        # Supercaps on left, control on right
        # ==========================================================================

        sc_spacing = 12.0
        sc_start_x = margin + 25
        sc_start_y_pos = margin + 15

        # Positive bank - upper left
        for i, comp in enumerate(sorted(groups["supercap_pos"], key=lambda c: int(c.ref[1:]))):
            row = i // 10
            col = i % 10
            comp.x = sc_start_x + col * sc_spacing
            comp.y = sc_start_y_pos + row * sc_spacing
            comp.rotation = 0

        # Negative bank - lower left
        sc_start_y_neg = sc_start_y_pos + 3 * sc_spacing + 10
        for i, comp in enumerate(sorted(groups["supercap_neg"], key=lambda c: int(c.ref[1:]))):
            row = i // 10
            col = i % 10
            comp.x = sc_start_x + col * sc_spacing
            comp.y = sc_start_y_neg + row * sc_spacing
            comp.rotation = 0

        # Connectors - left edge
        conn_x = margin + 8
        conn_y = 25
        for i, comp in enumerate(groups["connectors"]):
            comp.x = conn_x
            comp.y = conn_y + i * 18
            comp.rotation = 0

        # Discharge MOSFETs - right edge
        mosfet_x = board_width - margin - 12
        mosfet_y = board_height / 2
        for i, comp in enumerate(groups["discharge"]):
            comp.x = mosfet_x
            comp.y = mosfet_y - 10 + i * 20
            comp.rotation = 270

        # MCU - top right
        mcu_x = board_width - margin - 40
        mcu_y = margin + 20
        for comp in groups["mcu"]:
            comp.x = mcu_x
            comp.y = mcu_y
            comp.rotation = 0

        # Sensing - right side
        sense_x = board_width - margin - 50
        sense_y = margin + 45
        for i, comp in enumerate(groups["sensing"]):
            comp.x = sense_x
            comp.y = sense_y + i * 12
            comp.rotation = 0

        # Power (LDO)
        for comp in groups["power"]:
            comp.x = mcu_x - 18
            comp.y = mcu_y
            comp.rotation = 0

        # Charging circuits
        charge_x = board_width - margin - 70
        charge_y = board_height / 2 + 10
        for i, comp in enumerate(groups["charging"]):
            comp.x = charge_x + (i % 2) * 12
            comp.y = charge_y + (i // 2) * 10
            comp.rotation = 0

        # Passives
        passive_x = board_width - margin - 55
        passive_y = margin + 75
        for i, comp in enumerate(groups["passives"]):
            row = i // 5
            col = i % 5
            comp.x = passive_x + col * 7
            comp.y = passive_y + row * 5
            comp.rotation = 0


def generate_uuid() -> str:
    """Generate a UUID for KiCad elements."""
    return str(uuid.uuid4())


def format_coord(val: float) -> str:
    """Format coordinate value."""
    return f"{val:.4f}"


def generate_pcb(components: list[Component], board_width: float, board_height: float,
                  num_layers: int = 4) -> str:
    """Generate KiCad PCB file content."""

    # Collect all unique nets (placeholder - real nets come from schematic)
    nets = {
        "": 0,
        "GND": 1,
        "+3.3V": 2,
        "AC_L": 3,
        "AC_N": 4,
        "SC_POS": 5,
        "SC_NEG": 6,
    }

    sections = []

    # Layer definitions based on board type
    if num_layers == 4:
        layer_def = '''  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal)
    (2 "In2.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )'''
        stackup_comment = f"{board_width:.0f}x{board_height:.0f}mm 4-layer: F.Cu/GND/PWR/B.Cu"
    else:
        layer_def = '''  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )'''
        stackup_comment = f"{board_width:.0f}x{board_height:.0f}mm 2-layer PCB"

    # Header
    sections.append(f'''(kicad_pcb
  (version 20241229)
  (generator "generate_pcb.py")
  (generator_version "1.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (title_block
    (title "Generator Soft-Start")
    (date "2025-01")
    (rev "A")
    (comment 1 "Supercapacitor Power Assist")
    (comment 2 "{stackup_comment}")
  )
{layer_def}
  (setup
    (pad_to_mask_clearance 0.05)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
    )
  )''')

    # Nets
    net_lines = []
    for name, num in sorted(nets.items(), key=lambda x: x[1]):
        net_lines.append(f'  (net {num} "{name}")')
    sections.append("\n".join(net_lines))

    # Board outline (Edge.Cuts)
    outline_uuid = generate_uuid()
    sections.append(f'''
  (gr_rect
    (start 0 0)
    (end {format_coord(board_width)} {format_coord(board_height)})
    (stroke
      (width 0.15)
      (type solid)
    )
    (fill none)
    (layer "Edge.Cuts")
    (uuid "{outline_uuid}")
  )''')

    # Mounting holes (M3, 4 corners)
    mount_offset = 4.0
    mount_positions = [
        (mount_offset, mount_offset),
        (board_width - mount_offset, mount_offset),
        (mount_offset, board_height - mount_offset),
        (board_width - mount_offset, board_height - mount_offset),
    ]

    for i, (mx, my) in enumerate(mount_positions):
        fp_uuid = generate_uuid()
        sections.append(f'''
  (footprint "MountingHole:MountingHole_3.2mm_M3"
    (layer "F.Cu")
    (uuid "{fp_uuid}")
    (at {format_coord(mx)} {format_coord(my)})
    (property "Reference" "H{i+1}"
      (at 0 -3 0)
      (layer "F.SilkS")
      (uuid "{generate_uuid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Value" "MountingHole"
      (at 0 3 0)
      (layer "F.Fab")
      (uuid "{generate_uuid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Footprint" "MountingHole:MountingHole_3.2mm_M3"
      (at 0 0 0)
      (layer "F.Fab")
      (hide yes)
      (uuid "{generate_uuid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (pad "1" thru_hole circle
      (at 0 0)
      (size 6.4 6.4)
      (drill 3.2)
      (layers "*.Cu" "*.Mask")
      (remove_unused_layers no)
      (uuid "{generate_uuid()}")
    )
  )''')

    # Component footprints
    for comp in components:
        fp_uuid = generate_uuid()
        ref_uuid = generate_uuid()
        val_uuid = generate_uuid()
        fp_prop_uuid = generate_uuid()

        # Escape footprint name for S-expression
        footprint = comp.footprint.replace('"', '\\"')

        sections.append(f'''
  (footprint "{footprint}"
    (layer "{comp.layer}")
    (uuid "{fp_uuid}")
    (at {format_coord(comp.x)} {format_coord(comp.y)} {comp.rotation})
    (property "Reference" "{comp.ref}"
      (at 0 -2 0)
      (layer "F.SilkS")
      (uuid "{ref_uuid}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Value" "{comp.value}"
      (at 0 2 0)
      (layer "F.Fab")
      (uuid "{val_uuid}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Footprint" "{footprint}"
      (at 0 0 0)
      (layer "F.Fab")
      (hide yes)
      (uuid "{fp_prop_uuid}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
  )''')

    # Close
    sections.append(")")

    return "\n".join(sections)


def main():
    """Generate PCB from schematic."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate PCB layout from schematic")
    parser.add_argument("--compact", "-c", action="store_true",
                       help="Use compact 4-layer layout (160x100mm)")
    parser.add_argument("--output", "-o", type=str, default=None,
                       help="Output PCB filename")
    args = parser.parse_args()

    # Paths
    script_dir = Path(__file__).parent
    sch_path = script_dir / "softstart.kicad_sch"

    if args.output:
        pcb_path = script_dir / args.output
    else:
        pcb_path = script_dir / "softstart.kicad_pcb"

    # Board configuration
    if args.compact:
        # Compact 4-layer board
        board_width = 160.0
        board_height = 100.0
        num_layers = 4
        compact = True
        layout_name = "Compact 4-layer"
    else:
        # Standard 2-layer board
        board_width = 200.0
        board_height = 120.0
        num_layers = 2
        compact = False
        layout_name = "Standard 2-layer"

    print("Generator Soft-Start PCB Generator")
    print("=" * 40)
    print(f"Layout: {layout_name}")
    print(f"Board size: {board_width}mm x {board_height}mm")
    print(f"Layers: {num_layers}")
    print()

    # Parse schematic
    print(f"Parsing schematic: {sch_path}")
    components = parse_schematic(str(sch_path))
    print(f"Found {len(components)} components")

    # Group components
    groups = group_components(components)
    for name, comps in groups.items():
        if comps:
            print(f"  {name}: {len(comps)} components")

    # Place components
    print("\nPlacing components...")
    place_components(groups, board_width, board_height, compact=compact)

    # Flatten groups back to list
    all_components = []
    for comps in groups.values():
        all_components.extend(comps)

    # Generate PCB
    print("\nGenerating PCB file...")
    pcb_content = generate_pcb(all_components, board_width, board_height, num_layers=num_layers)

    # Write PCB file
    pcb_path.write_text(pcb_content)
    print(f"Wrote: {pcb_path}")
    print(f"File size: {pcb_path.stat().st_size} bytes")

    print("\nPCB generation complete!")
    print("Next steps:")
    print("  1. Open in KiCad to import footprints from libraries")
    print("  2. Update netlist from schematic (Tools > Update PCB from Schematic)")
    if num_layers == 4:
        print("  3. Add copper pours: In1.Cu=GND, In2.Cu=split SC_POS/SC_NEG")
    print("  4. Route the board")


if __name__ == "__main__":
    main()
