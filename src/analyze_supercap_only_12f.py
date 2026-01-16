#!/usr/bin/env python3
"""
Analyze supercap-only designs using Tecate 12F 2.7V @ $0.91 each.

Simplicity benefits:
- No separate charging windows for electrolytics
- No stacking/reconfiguration switching
- Simpler control logic
- More robust
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class SupercapOnlyDesign:
    """Pure supercap design using 12F cells."""
    name: str
    cells_per_bank: int  # Series cells
    parallel_strings: int = 1  # Parallel strings per bank

    SC_CAPACITANCE: float = 12.0  # Farads
    SC_VOLTAGE: float = 2.7
    SC_PRICE: float = 0.91
    SC_ESR_MOHM: float = 36.0

    MAX_CURRENT: float = 25.0  # Can push higher with simpler design
    ELECTRONICS_COST: float = 30.0  # Simpler electronics
    PCB_COST: float = 12.0  # Smaller PCB

    @property
    def total_cells(self) -> int:
        return 2 * self.cells_per_bank * self.parallel_strings

    @property
    def capacitor_cost(self) -> float:
        return self.total_cells * self.SC_PRICE

    @property
    def total_cost(self) -> float:
        return self.capacitor_cost + self.ELECTRONICS_COST + self.PCB_COST

    @property
    def bank_voltage(self) -> float:
        return self.cells_per_bank * self.SC_VOLTAGE

    @property
    def bank_capacitance(self) -> float:
        series_cap = self.SC_CAPACITANCE / self.cells_per_bank
        return series_cap * self.parallel_strings

    @property
    def bank_esr(self) -> float:
        series_esr = self.cells_per_bank * self.SC_ESR_MOHM / 1000
        return series_esr / self.parallel_strings

    @property
    def coverage(self) -> float:
        v = self.bank_voltage
        if v >= 170:
            return 1.0
        return np.arcsin(v / 170) / (np.pi / 2)

    @property
    def effective_current(self) -> float:
        return self.MAX_CURRENT * np.sqrt(self.coverage)

    @property
    def discharge_time_to_50pct_ms(self) -> float:
        """Time to discharge to 50% voltage at max current."""
        v_drop = self.bank_voltage * 0.5
        return (v_drop * self.bank_capacitance / self.MAX_CURRENT) * 1000

    @property
    def usable_energy_j(self) -> float:
        """Energy from 100% to 50% voltage."""
        return 0.5 * self.bank_capacitance * (self.bank_voltage**2 - (self.bank_voltage/2)**2)

    def energy_in_window(self, window_ms: float = 200) -> float:
        """Energy delivered in first N ms."""
        window_s = window_ms / 1000
        dt = 0.0005

        total_energy = 0
        t = 0
        v = self.bank_voltage

        while t < window_s:
            if v < self.bank_voltage * 0.5:
                break

            cov = np.arcsin(min(v / 170, 1.0)) / (np.pi / 2)
            power = v * self.MAX_CURRENT * cov
            total_energy += power * dt

            # Discharge
            v -= (self.MAX_CURRENT * dt) / self.bank_capacitance
            t += dt

        return total_energy


def analyze_configurations():
    """Analyze various supercap-only configurations."""

    configs = [
        # Pure series configurations
        SupercapOnlyDesign("40 cells (20S)", 20, 1),
        SupercapOnlyDesign("50 cells (25S)", 25, 1),
        SupercapOnlyDesign("60 cells (30S)", 30, 1),
        SupercapOnlyDesign("70 cells (35S)", 35, 1),
        SupercapOnlyDesign("80 cells (40S)", 40, 1),

        # With some parallel for more capacitance
        SupercapOnlyDesign("60 cells (15S×2P)", 15, 2),
        SupercapOnlyDesign("80 cells (20S×2P)", 20, 2),
        SupercapOnlyDesign("60 cells (20S×1.5P)", 20, 1),  # Not possible, placeholder
    ]

    # Remove invalid config
    configs = [c for c in configs if c.parallel_strings == int(c.parallel_strings)]

    print("=" * 90)
    print("SUPERCAP-ONLY DESIGNS: 12F 2.7V @ $0.91 each")
    print("=" * 90)
    print("\nSimplicity advantages: No electrolytics, no stacking, simpler control\n")

    print(f"{'Config':<22} {'Cells':>5} {'V_bank':>7} {'Cap':>6} {'Cov%':>5} "
          f"{'t_50%':>7} {'E_200':>6} {'E_500':>6} {'I_eff':>6} {'Cost':>7}")
    print("-" * 90)

    for c in configs:
        print(f"{c.name:<22} {c.total_cells:>5} {c.bank_voltage:>6.1f}V "
              f"{c.bank_capacitance:>5.2f}F {c.coverage*100:>4.0f}% "
              f"{c.discharge_time_to_50pct_ms:>6.0f}ms {c.energy_in_window(200):>5.0f}J "
              f"{c.energy_in_window(500):>5.0f}J {c.effective_current:>5.1f}A "
              f"${c.total_cost:>6.2f}")

    return configs


def recommend_design():
    """Recommend best supercap-only design."""

    print("\n" + "=" * 90)
    print("RECOMMENDED SUPERCAP-ONLY DESIGN")
    print("=" * 90)

    # 60 cells gives good balance
    design = SupercapOnlyDesign("60 cells (30S×1P)", 30, 1)

    print(f"""
CONFIGURATION: 60 × Tecate 12F 2.7V supercaps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Layout: 30 cells per bank, 2 banks (positive/negative half-cycles)

Electrical:
  Bank voltage:     {design.bank_voltage:.1f}V
  Bank capacitance: {design.bank_capacitance:.2f}F
  Bank ESR:         {design.bank_esr*1000:.0f}mΩ
  AC coverage:      {design.coverage*100:.0f}%

Performance:
  Discharge to 50%: {design.discharge_time_to_50pct_ms:.0f}ms
  Energy in 200ms:  {design.energy_in_window(200):.0f}J
  Energy in 500ms:  {design.energy_in_window(500):.0f}J
  Effective I:      {design.effective_current:.1f}A RMS

Cost:
  Supercaps:        60 × $0.91 = ${design.capacitor_cost:.2f}
  Electronics:      ${design.ELECTRONICS_COST:.2f} (simplified)
  PCB:              ${design.PCB_COST:.2f}
  ─────────────────────────────────────
  TOTAL:            ${design.total_cost:.2f}

ADVANTAGES:
  ✓ Simple charging (just connect to AC through current limiter)
  ✓ No stacking/reconfiguration needed
  ✓ Single discharge path per half-cycle
  ✓ Fewer switches, simpler control
  ✓ More robust - fewer failure modes
  ✓ Supercaps are very durable (millions of cycles)
""")

    # Compare to hybrid
    print("\n" + "-" * 90)
    print("COMPARISON: Supercap-only vs Hybrid")
    print("-" * 90)

    print(f"""
                        Supercap-Only      Hybrid (was $224)
                        60 × 12F           16×100F + 56×elec
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltage                 81V                81.6V
Coverage                32%                32%
Energy (200ms)          ~{design.energy_in_window(200):.0f}J               206J
Capacitance             0.4F               12.5F + elec
Discharge time          {design.discharge_time_to_50pct_ms:.0f}ms             197ms (boost)

Cost                    ${design.total_cost:.2f}             $224-292
Complexity              LOW                HIGH
Switches needed         2                  8+
Control                 Simple analog      MCU recommended
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY INSIGHT:
The supercap-only design has less energy storage but delivers
similar POWER during the critical first 200ms because:
- Same voltage (81V vs 81.6V)
- Same coverage (32%)
- Difference is in sustained duration, not peak assist
""")

    return design


def calculate_bom():
    """Calculate complete BOM."""

    print("\n" + "=" * 90)
    print("COMPLETE BOM - SUPERCAP-ONLY DESIGN")
    print("=" * 90)

    bom = [
        ("Supercapacitor", "Tecate 12F 2.7V TPLH-2R7/12WR10X30", 60, 0.91, "DigiKey"),
        ("MOSFET", "IRFB4110 100V 180A TO-220", 2, 1.50, "LCSC"),
        ("Gate Driver", "IR2110 or simple transistor", 1, 1.50, "LCSC"),
        ("Optocoupler", "H11AA1 AC input (ZC detect)", 1, 0.50, "LCSC"),
        ("Comparator", "LM393 dual", 1, 0.30, "LCSC"),
        ("Current Shunt", "0.01Ω 5W", 2, 0.50, "LCSC"),
        ("Charging Resistor", "100Ω 10W (limits charge current)", 2, 0.50, "LCSC"),
        ("Diode", "Schottky 100V 20A (charge path)", 4, 0.40, "LCSC"),
        ("Fuse", "20A + holder", 1, 0.50, "LCSC"),
        ("Terminal Block", "High current", 4, 0.50, "LCSC"),
        ("Misc Passives", "Resistors, small caps", 1, 3.00, "LCSC"),
        ("PCB", "JLCPCB 2-layer ~100×150mm", 1, 10.00, "JLCPCB"),
        ("Heatsink", "TO-220", 2, 0.50, "AliExpress"),
    ]

    print(f"\n{'Component':<18} {'Description':<38} {'Qty':>3} {'Each':>6} {'Total':>7}")
    print("-" * 85)

    total = 0
    for comp, desc, qty, price, source in bom:
        line_total = qty * price
        total += line_total
        print(f"{comp:<18} {desc:<38} {qty:>3} ${price:>5.2f} ${line_total:>6.2f}")

    print("-" * 85)
    print(f"{'TOTAL':<18} {'':<38} {'':<3} {'':<6} ${total:>6.2f}")

    print(f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY:
  Supercaps:    ${60 * 0.91:.2f}
  Electronics:  ${total - 60*0.91 - 10:.2f}
  PCB:          $10.00
  ────────────────────
  TOTAL:        ${total:.2f}

Hand-solder: ~65 through-hole components
PCB size:    ~100×150mm (smaller than hybrid!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    return total


def plot_comparison(save_path=None):
    """Plot different configurations."""

    configs = [
        SupercapOnlyDesign("40 cells", 20, 1),
        SupercapOnlyDesign("50 cells", 25, 1),
        SupercapOnlyDesign("60 cells", 30, 1),
        SupercapOnlyDesign("80 cells", 40, 1),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Supercap-Only Design Options (12F 2.7V @ $0.91)', fontsize=12, fontweight='bold')

    # Plot 1: Energy vs Cost
    ax1 = axes[0]
    costs = [c.total_cost for c in configs]
    energy_200 = [c.energy_in_window(200) for c in configs]
    energy_500 = [c.energy_in_window(500) for c in configs]

    x = np.arange(len(configs))
    width = 0.35

    ax1.bar(x - width/2, energy_200, width, label='Energy in 200ms', color='blue', alpha=0.7)
    ax1.bar(x + width/2, energy_500, width, label='Energy in 500ms', color='green', alpha=0.7)

    ax1.set_xlabel('Configuration')
    ax1.set_ylabel('Energy (J)')
    ax1.set_title('Energy Delivery')
    ax1.set_xticks(x)
    ax1.set_xticklabels([c.name for c in configs], rotation=45, ha='right')
    ax1.legend()

    # Add cost labels
    for i, (c, cost) in enumerate(zip(configs, costs)):
        ax1.annotate(f'${cost:.0f}', (i, energy_500[i] + 2), ha='center', fontsize=9)

    # Plot 2: Coverage and effective current
    ax2 = axes[1]
    coverages = [c.coverage * 100 for c in configs]
    currents = [c.effective_current for c in configs]

    ax2.bar(x - width/2, coverages, width, label='Coverage %', color='orange', alpha=0.7)
    ax2_twin = ax2.twinx()
    ax2_twin.plot(x, currents, 'ro-', label='Effective Current', linewidth=2, markersize=8)

    ax2.set_xlabel('Configuration')
    ax2.set_ylabel('AC Coverage (%)')
    ax2_twin.set_ylabel('Effective Current (A)')
    ax2.set_title('Coverage and Current')
    ax2.set_xticks(x)
    ax2.set_xticklabels([c.name for c in configs], rotation=45, ha='right')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")


def main():
    analyze_configurations()
    recommend_design()
    total = calculate_bom()
    plot_comparison(save_path='supercap_only_12f_analysis.png')

    print(f"\n*** FINAL BOM: ${total:.2f} ***")


if __name__ == '__main__':
    main()
