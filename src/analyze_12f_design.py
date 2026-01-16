#!/usr/bin/env python3
"""
Analyze design using Tecate 12F 2.7V supercaps @ $0.91 each.

User plan:
- Source and hand-solder supercaps + electrolytics
- JLCPCB for PCB only (no assembly)
- Scale to 30 supercaps total
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SupercapDesign:
    """Design configuration using 12F cells."""
    name: str
    cells_per_bank: int  # Series cells per bank
    parallel_strings: int = 1  # Parallel strings per bank
    electrolytics_per_bank: int = 0

    # Component specs
    SC_CAPACITANCE: float = 12.0  # Farads
    SC_VOLTAGE: float = 2.7
    SC_PRICE: float = 0.91
    SC_ESR_MOHM: float = 36.0

    ELEC_CAPACITANCE_UF: float = 4700
    ELEC_VOLTAGE: float = 60.0  # Charge voltage
    ELEC_PRICE: float = 0.80  # AliExpress

    MAX_CURRENT: float = 20.0  # Amps

    @property
    def total_supercaps(self) -> int:
        return 2 * self.cells_per_bank * self.parallel_strings

    @property
    def total_electrolytics(self) -> int:
        return 2 * self.electrolytics_per_bank

    @property
    def sc_cost(self) -> float:
        return self.total_supercaps * self.SC_PRICE

    @property
    def elec_cost(self) -> float:
        return self.total_electrolytics * self.ELEC_PRICE

    @property
    def sc_bank_voltage(self) -> float:
        return self.cells_per_bank * self.SC_VOLTAGE

    @property
    def sc_bank_capacitance(self) -> float:
        """Capacitance of series-parallel bank."""
        series_cap = self.SC_CAPACITANCE / self.cells_per_bank
        return series_cap * self.parallel_strings

    @property
    def sc_bank_esr(self) -> float:
        """ESR of series-parallel bank in ohms."""
        series_esr = self.cells_per_bank * self.SC_ESR_MOHM / 1000
        return series_esr / self.parallel_strings

    @property
    def elec_bank_capacitance(self) -> float:
        return self.electrolytics_per_bank * self.ELEC_CAPACITANCE_UF * 1e-6

    @property
    def stacked_voltage(self) -> float:
        if self.electrolytics_per_bank > 0:
            return self.sc_bank_voltage + self.ELEC_VOLTAGE
        return self.sc_bank_voltage

    @property
    def coverage(self) -> float:
        v = self.stacked_voltage
        V_PEAK = 170
        if v >= V_PEAK:
            return 1.0
        return np.arcsin(v / V_PEAK) / (np.pi / 2)

    @property
    def sc_only_coverage(self) -> float:
        v = self.sc_bank_voltage
        V_PEAK = 170
        if v >= V_PEAK:
            return 1.0
        return np.arcsin(v / V_PEAK) / (np.pi / 2)

    @property
    def elec_boost_duration_ms(self) -> float:
        if self.elec_bank_capacitance == 0:
            return 0
        return (self.ELEC_VOLTAGE * self.elec_bank_capacitance / self.MAX_CURRENT) * 1000

    @property
    def sc_discharge_time_to_50pct_ms(self) -> float:
        """Time to discharge supercaps to 50% voltage."""
        v_drop = self.sc_bank_voltage * 0.5
        return (v_drop * self.sc_bank_capacitance / self.MAX_CURRENT) * 1000

    def energy_in_window(self, window_ms: float = 200) -> float:
        """Calculate energy delivered in first N ms."""
        window_s = window_ms / 1000
        dt = 0.0005

        total_energy = 0
        t = 0

        v_sc = self.sc_bank_voltage
        v_elec = self.ELEC_VOLTAGE if self.electrolytics_per_bank > 0 else 0

        while t < window_s:
            if v_elec > 5:
                v_total = v_sc + v_elec
            else:
                v_total = v_sc

            if v_total > 0:
                cov = np.arcsin(min(v_total / 170, 1.0)) / (np.pi / 2)
            else:
                cov = 0

            power = v_total * self.MAX_CURRENT * cov
            total_energy += power * dt

            # Discharge
            if v_elec > 5 and self.elec_bank_capacitance > 0:
                v_elec -= (self.MAX_CURRENT * dt) / self.elec_bank_capacitance
                v_elec = max(v_elec, 0)
            elif self.sc_bank_capacitance > 0:
                v_sc -= (self.MAX_CURRENT * dt) / self.sc_bank_capacitance
                v_sc = max(v_sc, self.sc_bank_voltage * 0.5)

            t += dt

        return total_energy

    @property
    def effective_current(self) -> float:
        return self.MAX_CURRENT * np.sqrt(self.coverage)

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"Configuration: {self.name}")
        print(f"{'='*60}")
        print(f"Supercaps: {self.total_supercaps} × 12F 2.7V")
        print(f"  Per bank: {self.cells_per_bank}S × {self.parallel_strings}P")
        print(f"  Bank voltage: {self.sc_bank_voltage:.1f}V")
        print(f"  Bank capacitance: {self.sc_bank_capacitance:.2f}F")
        print(f"  Bank ESR: {self.sc_bank_esr*1000:.0f}mΩ")
        print(f"  Cost: ${self.sc_cost:.2f}")

        if self.electrolytics_per_bank > 0:
            print(f"\nElectrolytics: {self.total_electrolytics} × 4700µF")
            print(f"  Per bank: {self.electrolytics_per_bank}")
            print(f"  Bank capacitance: {self.elec_bank_capacitance*1000:.1f}mF")
            print(f"  Boost duration: {self.elec_boost_duration_ms:.0f}ms")
            print(f"  Cost: ${self.elec_cost:.2f}")

        print(f"\nPerformance:")
        print(f"  Stacked voltage: {self.stacked_voltage:.1f}V")
        print(f"  AC coverage: {self.coverage*100:.0f}%")
        print(f"  SC discharge to 50%: {self.sc_discharge_time_to_50pct_ms:.0f}ms")
        print(f"  Energy in 200ms: {self.energy_in_window(200):.0f}J")
        print(f"  Energy in 500ms: {self.energy_in_window(500):.0f}J")
        print(f"  Effective current: {self.effective_current:.1f}A RMS")


def analyze_30_supercap_configs():
    """Analyze different ways to use 30 supercaps."""

    print("=" * 70)
    print("30 SUPERCAP (12F 2.7V @ $0.91) CONFIGURATION OPTIONS")
    print("=" * 70)

    # 30 total = 15 per bank
    configs = [
        # Pure supercap configurations
        SupercapDesign("15S per bank (no elec)", 15, 1, 0),

        # With electrolytics
        SupercapDesign("15S + 16 elec", 15, 1, 16),
        SupercapDesign("15S + 20 elec", 15, 1, 20),
        SupercapDesign("15S + 24 elec", 15, 1, 24),

        # Alternative: 10S with more parallel (32 total, slightly over)
        SupercapDesign("10S×1.5 (30 cells)", 10, 1, 20),  # Can't do 1.5P, use 10S

        # What about 12S? (24 total)
        SupercapDesign("12S (24 cells) + 20 elec", 12, 1, 20),
    ]

    print(f"\n{'Config':<25} {'SCs':>4} {'Elec':>4} {'V_stack':>8} {'Cov%':>6} "
          f"{'E_200ms':>8} {'I_eff':>6} {'SC$':>6} {'E$':>6} {'Total':>7}")
    print("-" * 95)

    for c in configs:
        # Check if stacked voltage exceeds electrolytic rating
        warning = ""
        if c.stacked_voltage > 100:
            warning = " ⚠️100V+"

        print(f"{c.name:<25} {c.total_supercaps:>4} {c.total_electrolytics:>4} "
              f"{c.stacked_voltage:>7.1f}V {c.coverage*100:>5.0f}% "
              f"{c.energy_in_window(200):>7.0f}J {c.effective_current:>5.1f}A "
              f"${c.sc_cost:>5.2f} ${c.elec_cost:>5.2f} ${c.sc_cost + c.elec_cost:>6.2f}{warning}")

    return configs


def recommend_design():
    """Recommend best design for 30 supercaps."""

    print("\n" + "=" * 70)
    print("RECOMMENDED DESIGN: 30 Supercaps + Electrolytics")
    print("=" * 70)

    # The issue: 15S gives 40.5V, stacked with 60V = 100.5V (too high for 100V caps)
    # Solutions:
    # 1. Use 120V electrolytics (more expensive)
    # 2. Charge electrolytics to lower voltage (e.g., 50V)
    # 3. Use fewer supercaps in series (e.g., 12S)

    print("""
ISSUE: 15 supercaps in series = 40.5V
       Stacked with 60V electrolytics = 100.5V
       This exceeds 100V electrolytic rating!

SOLUTIONS:

Option A: Use 120V electrolytics
  - More expensive, less common
  - But straightforward

Option B: Charge electrolytics to 50V instead of 60V  ← RECOMMENDED
  - Stacked voltage: 40.5 + 50 = 90.5V
  - Still 34% coverage
  - Uses standard 100V caps with margin

Option C: Use 12S configuration (24 supercaps)
  - Voltage: 32.4V
  - Stacked: 92.4V
  - Leftover 6 supercaps could be spares or parallel
""")

    # Analyze Option B
    print("\n" + "-" * 70)
    print("OPTION B DETAILED: 15S + electrolytics charged to 50V")
    print("-" * 70)

    @dataclass
    class ModifiedDesign(SupercapDesign):
        ELEC_VOLTAGE: float = 50.0  # Reduced charge voltage

    design = ModifiedDesign("15S + 20 elec @ 50V", 15, 1, 20)
    design.ELEC_VOLTAGE = 50.0  # Override

    print(f"""
Supercaps: 30 × 12F 2.7V @ $0.91 = ${30 * 0.91:.2f}
Electrolytics: 40 × 4700µF 100V @ $0.80 = ${40 * 0.80:.2f}

Configuration:
  - 15 supercaps per bank (series)
  - 20 electrolytics per bank (parallel)
  - Electrolytics charged to 50V (not 60V)

Performance:
  - Supercap voltage: 40.5V
  - Stacked voltage: 90.5V
  - AC coverage: {np.arcsin(90.5/170)/(np.pi/2)*100:.0f}%
  - Electrolytic boost: {50 * 20 * 4700e-6 / 20 * 1000:.0f}ms
  - Bank capacitance: {12/15:.2f}F supercap + {20*4700e-6*1000:.0f}mF electrolytic

Estimated energy in 200ms: ~120-150J
Effective current: ~12-15A RMS
""")


def calculate_full_bom():
    """Calculate complete BOM for recommended design."""

    print("\n" + "=" * 70)
    print("COMPLETE BOM - HAND-SOLDER DESIGN")
    print("=" * 70)

    bom = [
        ("Supercapacitor", "Tecate 12F 2.7V (TPLH-2R7/12WR10X30)", 30, 0.91, "DigiKey"),
        ("Electrolytic", "4700µF 100V radial", 40, 0.80, "AliExpress"),
        ("MOSFET", "IRFB4110 100V 180A TO-220", 4, 1.50, "LCSC"),
        ("Gate Driver", "IR2110 or equivalent", 2, 1.50, "LCSC"),
        ("Optocoupler", "H11AA1 AC input", 2, 0.50, "LCSC"),
        ("Comparator", "LM393 dual", 2, 0.30, "LCSC"),
        ("Current Shunt", "0.01Ω 5W", 2, 0.50, "LCSC"),
        ("Fuse Holder", "5×20mm PCB mount", 2, 0.30, "LCSC"),
        ("Fuse", "25A fast-blow 5×20mm", 2, 0.20, "LCSC"),
        ("Inductor", "100µH 20A (or hand-wind)", 2, 2.00, "LCSC"),
        ("Terminal Block", "High current screw terminal", 4, 0.50, "LCSC"),
        ("Misc passives", "Resistors, small caps", 1, 3.00, "LCSC"),
        ("PCB", "JLCPCB 2-layer ~150×200mm", 1, 15.00, "JLCPCB"),
        ("Heatsink", "TO-220 heatsink", 4, 0.50, "AliExpress"),
    ]

    print(f"\n{'Component':<20} {'Description':<35} {'Qty':>4} {'Unit$':>7} {'Total':>8} {'Source':<12}")
    print("-" * 100)

    total = 0
    for comp, desc, qty, price, source in bom:
        line_total = qty * price
        total += line_total
        print(f"{comp:<20} {desc:<35} {qty:>4} ${price:>6.2f} ${line_total:>7.2f} {source:<12}")

    print("-" * 100)
    print(f"{'TOTAL':<20} {'':<35} {'':<4} {'':<7} ${total:>7.2f}")

    print(f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COST SUMMARY:
  Capacitors (hand-solder):  ${30*0.91 + 40*0.80:.2f}
  Electronics:               ${total - 30*0.91 - 40*0.80 - 15:.2f}
  PCB (JLCPCB):              $15.00
  ─────────────────────────────────
  TOTAL BOM:                 ${total:.2f}

LABOR: Hand-solder ~70 through-hole components
       Estimated time: 2-3 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    return total


def main():
    configs = analyze_30_supercap_configs()
    recommend_design()
    total = calculate_full_bom()

    print(f"\n*** FINAL BOM: ${total:.2f} ***")
    print("Targeting 8000 BTU window AC with Honda EU1000i")


if __name__ == '__main__':
    main()
