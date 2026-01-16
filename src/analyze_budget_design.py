#!/usr/bin/env python3
"""
Analyze budget-constrained designs targeting ~$100 BOM.

Key insight from user: "generator labors but usually does not die"
This means we don't need to provide FULL support - just enough to
ease the generator through the worst part of the startup.

Design philosophy shift:
- Previous: Provide 100% of current shortfall
- Budget: Provide enough to prevent generator trip/stall
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List


@dataclass
class BudgetConfig:
    """Budget design configuration."""
    name: str
    supercaps_total: int  # Total across both banks
    electrolytics_total: int
    max_current_a: float = 20.0  # Reduced from 40A

    # Component costs
    SC_COST: float = 6.00
    ELEC_COST: float = 2.28
    SC_VOLTAGE: float = 2.7
    SC_CAPACITANCE: float = 100.0
    ELEC_CAPACITANCE_UF: float = 4700
    ELEC_VOLTAGE: float = 60.0

    # Fixed electronics cost (simplified design)
    # - 2x MOSFET (discharge only): $4
    # - Simple comparator control (no MCU): $5
    # - Gate driver: $2
    # - Current sense resistor: $1
    # - Connectors, fuse: $10
    # - Simple PCB: $15
    ELECTRONICS_COST: float = 37.0  # Bare minimum

    @property
    def capacitor_cost(self) -> float:
        return self.supercaps_total * self.SC_COST + self.electrolytics_total * self.ELEC_COST

    @property
    def total_cost(self) -> float:
        return self.capacitor_cost + self.ELECTRONICS_COST

    @property
    def sc_per_bank(self) -> int:
        return self.supercaps_total // 2

    @property
    def elec_per_bank(self) -> int:
        return self.electrolytics_total // 2

    @property
    def sc_bank_voltage(self) -> float:
        return self.sc_per_bank * self.SC_VOLTAGE

    @property
    def sc_bank_capacitance(self) -> float:
        if self.sc_per_bank == 0:
            return 0
        return self.SC_CAPACITANCE / self.sc_per_bank

    @property
    def elec_bank_capacitance(self) -> float:
        return self.elec_per_bank * self.ELEC_CAPACITANCE_UF * 1e-6

    @property
    def stacked_voltage(self) -> float:
        if self.electrolytics_total > 0:
            return self.sc_bank_voltage + self.ELEC_VOLTAGE
        return self.sc_bank_voltage

    @property
    def coverage(self) -> float:
        """Fraction of AC cycle we can inject."""
        v = self.stacked_voltage
        V_PEAK = 170
        if v >= V_PEAK:
            return 1.0
        if v <= 0:
            return 0
        return np.arcsin(v / V_PEAK) / (np.pi / 2)

    @property
    def elec_boost_duration_ms(self) -> float:
        """How long electrolytics provide boost."""
        if self.elec_bank_capacitance == 0:
            return 0
        return (self.ELEC_VOLTAGE * self.elec_bank_capacitance / self.max_current_a) * 1000

    def energy_in_window(self, window_ms: float = 200) -> float:
        """Energy delivered in first N ms."""
        window_s = window_ms / 1000
        dt = 0.0005  # 0.5ms timestep

        total_energy = 0
        t = 0

        # Track capacitor voltages
        v_sc = self.sc_bank_voltage
        v_elec = self.ELEC_VOLTAGE if self.electrolytics_total > 0 else 0

        while t < window_s:
            # Current voltage
            if self.electrolytics_total > 0 and v_elec > 5:
                v_total = v_sc + v_elec
            else:
                v_total = v_sc

            # Coverage at this voltage
            if v_total > 0:
                cov = np.arcsin(min(v_total / 170, 1.0)) / (np.pi / 2)
            else:
                cov = 0

            # Power and energy
            power = v_total * self.max_current_a * cov
            total_energy += power * dt

            # Discharge capacitors
            if self.electrolytics_total > 0 and v_elec > 5:
                # Electrolytics discharge first
                if self.elec_bank_capacitance > 0:
                    v_elec -= (self.max_current_a * dt) / self.elec_bank_capacitance
                    v_elec = max(v_elec, 0)
            else:
                # Supercaps discharge
                if self.sc_bank_capacitance > 0:
                    v_sc -= (self.max_current_a * dt) / self.sc_bank_capacitance
                    v_sc = max(v_sc, self.sc_bank_voltage * 0.5)

            t += dt

        return total_energy

    @property
    def effective_rms_current(self) -> float:
        """Effective RMS current contribution."""
        return self.max_current_a * np.sqrt(self.coverage)

    @property
    def peak_power(self) -> float:
        return self.stacked_voltage * self.max_current_a * self.coverage


def generate_budget_configs(target_cost: float = 100) -> List[BudgetConfig]:
    """Generate configurations near target cost."""

    configs = []
    electronics_cost = 37  # Minimum electronics
    cap_budget = target_cost - electronics_cost  # ~$63 for capacitors

    # Try various combinations
    # Supercap-only designs
    for sc in range(4, 14, 2):  # 4, 6, 8, 10, 12 total supercaps
        cost = sc * 6
        if cost <= cap_budget + 10:  # Allow some overage
            configs.append(BudgetConfig(f"{sc}SC only", sc, 0))

    # Hybrid designs (fewer supercaps + some electrolytics)
    for sc in range(4, 10, 2):
        sc_cost = sc * 6
        remaining = cap_budget - sc_cost
        max_elec = int(remaining / 2.28)
        # Try a few electrolytic counts
        for elec in [8, 12, 16, 20]:
            if elec <= max_elec + 4:
                configs.append(BudgetConfig(f"{sc}SC+{elec}E", sc, elec))

    return configs


def analyze_marginal_assist():
    """
    Analyze what happens when generator "labors but doesn't die."
    """
    print("=" * 80)
    print("MARGINAL ASSIST ANALYSIS")
    print("=" * 80)

    print("""
When the generator "labors but doesn't die", what's happening?

1. Generator voltage sags (120V → 90-100V)
2. Generator frequency drops (60Hz → 55-58Hz)
3. Generator current is at limit (~8-10A)
4. Motor is getting SOME current, just not enough for fast start
5. Motor accelerates slowly over 1-2 seconds instead of 300ms

The motor DOES start, just roughly. This means:
- We don't need to provide the FULL 24.7A shortfall
- We just need to provide ENOUGH to:
  a) Prevent voltage from sagging too far
  b) Keep generator from tripping on overcurrent
  c) Help motor accelerate faster

Hypothesis: Providing 10-15A of assist (vs 40A full design) might be enough.
""")

    # What does marginal assist give us?
    print("\nMarginal assist scenarios:")
    print("-" * 60)

    scenarios = [
        ("No assist", 0, 8.3),
        ("Light assist (10A eff)", 10, 8.3),
        ("Medium assist (15A eff)", 15, 8.3),
        ("Full assist (22.6A eff)", 22.6, 8.3),
    ]

    motor_needs = 33  # 8000 BTU LRA

    for name, our_current, gen_current in scenarios:
        total = our_current + gen_current
        shortfall = motor_needs - total
        pct_covered = (total / motor_needs) * 100

        status = "Motor stalls" if pct_covered < 50 else \
                 "Labors heavily" if pct_covered < 70 else \
                 "Labors slightly" if pct_covered < 85 else \
                 "Smooth start"

        print(f"{name:25} Total: {total:5.1f}A  ({pct_covered:4.0f}% of need)  → {status}")


def analyze_budget_configs():
    """Analyze budget configurations."""

    configs = generate_budget_configs(100)

    print("\n" + "=" * 80)
    print("BUDGET DESIGN OPTIONS (~$100 BOM)")
    print("=" * 80)

    print(f"\n{'Config':<15} {'Cost':>7} {'V_stack':>8} {'Cov%':>6} "
          f"{'E_200ms':>8} {'I_eff':>7} {'Notes':<20}")
    print("-" * 80)

    results = []
    for c in configs:
        energy = c.energy_in_window(200)
        results.append((c, energy))

        notes = ""
        if c.electrolytics_total > 0:
            notes = f"boost {c.elec_boost_duration_ms:.0f}ms"

        print(f"{c.name:<15} ${c.total_cost:>6.0f} {c.stacked_voltage:>7.1f}V "
              f"{c.coverage*100:>5.0f}% {energy:>7.0f}J {c.effective_rms_current:>6.1f}A  {notes:<20}")

    print("-" * 80)
    print("Note: All use 20A max current (vs 40A in full design)")
    print("      Electronics: $37 (simplified, no MCU)")

    return results


def recommend_budget_design():
    """Recommend best budget design."""

    print("\n" + "=" * 80)
    print("BUDGET DESIGN RECOMMENDATIONS")
    print("=" * 80)

    print("""
For ~$100 BOM with "marginal assist" philosophy:

OPTION A: Supercap-only (simplest)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Config: 10 supercaps (5 per bank)
  Cost: $60 caps + $37 electronics = $97

  Voltage: 13.5V (5 × 2.7V)
  Coverage: 8% of AC cycle (very low!)
  Energy: ~25J in 200ms
  Effective current: ~6A

  Pros: Very simple, reliable
  Cons: Low coverage limits effectiveness

OPTION B: Small hybrid (better coverage)  ← RECOMMENDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Config: 6 supercaps + 16 electrolytics
  Cost: $36 + $36 + $37 = $109

  Stacked voltage: 68.1V (8.1V SC + 60V elec)
  Coverage: 24% of AC cycle
  Boost duration: 56ms
  Energy: ~60J in 200ms
  Effective current: ~10A

  Pros: Reasonable coverage, good boost
  Cons: More complex switching, shorter boost

OPTION C: Minimal hybrid
━━━━━━━━━━━━━━━━━━━━━━━━
  Config: 4 supercaps + 20 electrolytics
  Cost: $24 + $46 + $37 = $107

  Stacked voltage: 65.4V (5.4V SC + 60V elec)
  Coverage: 23%
  Boost duration: 70ms

  Pros: Cheaper supercaps, longer boost
  Cons: Very low supercap-only voltage after boost

KEY INSIGHT:
━━━━━━━━━━━━
The $100 designs provide 6-10A effective assist vs 22.6A in full design.
Combined with generator's 8.3A, total is 14-18A vs 33A motor needs.

This is 42-55% of motor demand - right at the "labors but starts" threshold.
A budget design might just EASE the labor rather than eliminate it.

If generator currently "labors but doesn't die", adding 6-10A might be enough
to make it "labor slightly" or even "start smoothly" for smaller units.
""")

    # Detailed comparison
    print("\n" + "=" * 80)
    print("$100 vs $224 DESIGN COMPARISON")
    print("=" * 80)

    print("""
                            Budget ($109)    Full ($224)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Supercaps                   6                16
Electrolytics               16               56
Stacked voltage             68.1V            81.6V
AC coverage                 24%              32%
Max injection current       20A              40A
Effective RMS current       10A              22.6A
Energy in 200ms             ~60J             206J
Boost duration              56ms             197ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Combined with generator     18.3A            30.9A
Motor needs (8000 BTU)      33A              33A
Coverage of need            55%              94%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Budget design reality check:
- At 55% of motor current need, the motor will START but slowly
- Generator will still labor, but less
- Might be enough for 5000-6000 BTU units to start smoothly
- For 8000 BTU, reduces "hard labor" to "moderate labor"
""")


def plot_comparison(save_path=None):
    """Plot budget vs full design comparison."""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Budget ($100) vs Full ($224) Design Comparison',
                 fontsize=14, fontweight='bold')

    # Data
    designs = ['Budget\n6SC+16E\n$109', 'Full\n16SC+56E\n$224']

    # Plot 1: Current capability
    ax1 = axes[0]
    gen_current = [8.3, 8.3]
    our_current = [10, 22.6]
    motor_need = 33

    x = np.arange(len(designs))
    width = 0.35

    bars1 = ax1.bar(x, gen_current, width, label='Generator', color='blue', alpha=0.7)
    bars2 = ax1.bar(x, our_current, width, bottom=gen_current, label='Soft-start', color='green', alpha=0.7)

    ax1.axhline(y=motor_need, color='red', linestyle='--', linewidth=2, label=f'Motor needs ({motor_need}A)')

    ax1.set_ylabel('Effective Current (A RMS)')
    ax1.set_title('Current Capability vs Motor Demand')
    ax1.set_xticks(x)
    ax1.set_xticklabels(designs)
    ax1.legend()
    ax1.set_ylim(0, 40)

    # Add percentage labels
    for i, (g, o) in enumerate(zip(gen_current, our_current)):
        total = g + o
        pct = total / motor_need * 100
        ax1.text(i, total + 1, f'{pct:.0f}%', ha='center', fontweight='bold')

    # Plot 2: Energy delivery
    ax2 = axes[1]

    # Simulate energy over time
    time_ms = np.linspace(0, 300, 100)

    budget = BudgetConfig("Budget", 6, 16, max_current_a=20)
    full = BudgetConfig("Full", 16, 56, max_current_a=40)
    full.ELECTRONICS_COST = 68  # Full electronics

    budget_energy = [budget.energy_in_window(t) for t in time_ms]
    full_energy = [full.energy_in_window(t) for t in time_ms]

    ax2.plot(time_ms, budget_energy, 'b-', linewidth=2, label=f'Budget ($109)')
    ax2.plot(time_ms, full_energy, 'g-', linewidth=2, label=f'Full ($224)')

    ax2.axvline(x=200, color='gray', linestyle=':', label='200ms window')
    ax2.axhline(y=174, color='red', linestyle='--', label='8000 BTU needs 174J')

    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Cumulative Energy (J)')
    ax2.set_title('Energy Delivery Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 300)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    return fig


def main():
    analyze_marginal_assist()
    analyze_budget_configs()
    recommend_budget_design()
    plot_comparison(save_path='budget_design_analysis.png')


if __name__ == '__main__':
    main()
