#!/usr/bin/env python3
"""
Analyze hybrid supercap + electrolytic stacking configurations.

Concept: Charge supercaps and electrolytics separately at different voltage windows,
then switch them in SERIES during discharge for higher total voltage and coverage.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class HybridConfig:
    """Configuration for hybrid stacking design."""
    # Supercap parameters
    supercap_cells: int
    supercap_capacitance_F: float = 100.0
    supercap_voltage_V: float = 2.7
    supercap_cost_each: float = 6.0

    # Electrolytic parameters
    electrolytic_count: int = 0
    electrolytic_capacitance_uF: float = 4700.0
    electrolytic_voltage_V: float = 60.0  # Charge voltage (derated from 100V rating)
    electrolytic_cost_each: float = 2.28

    # System parameters
    v_ac_peak: float = 170.0
    max_current_A: float = 40.0

    @property
    def supercap_bank_voltage(self) -> float:
        return self.supercap_cells * self.supercap_voltage_V

    @property
    def supercap_bank_capacitance(self) -> float:
        return self.supercap_capacitance_F / self.supercap_cells

    @property
    def electrolytic_total_capacitance_F(self) -> float:
        # Electrolytics in parallel
        return self.electrolytic_count * self.electrolytic_capacitance_uF * 1e-6

    @property
    def total_series_voltage(self) -> float:
        return self.supercap_bank_voltage + self.electrolytic_voltage_V

    @property
    def coverage_supercap_only(self) -> float:
        v = self.supercap_bank_voltage
        if v >= self.v_ac_peak:
            return 1.0
        return np.arcsin(v / self.v_ac_peak) / (np.pi / 2)

    @property
    def coverage_stacked(self) -> float:
        v = self.total_series_voltage
        if v >= self.v_ac_peak:
            return 1.0
        return np.arcsin(v / self.v_ac_peak) / (np.pi / 2)

    @property
    def electrolytic_discharge_time_s(self) -> float:
        """Time for electrolytics to fully discharge at max current."""
        if self.electrolytic_total_capacitance_F == 0:
            return 0
        return self.electrolytic_voltage_V * self.electrolytic_total_capacitance_F / self.max_current_A

    @property
    def supercap_energy_J(self) -> float:
        # Per bank, discharge to 50%
        c = self.supercap_bank_capacitance
        v = self.supercap_bank_voltage
        return 0.5 * c * (v**2 - (v/2)**2)

    @property
    def electrolytic_energy_J(self) -> float:
        c = self.electrolytic_total_capacitance_F
        v = self.electrolytic_voltage_V
        return 0.5 * c * v**2

    @property
    def total_cost(self) -> float:
        # ×2 for positive and negative banks
        supercap_cost = 2 * self.supercap_cells * self.supercap_cost_each
        elec_cost = 2 * self.electrolytic_count * self.electrolytic_cost_each
        return supercap_cost + elec_cost

    def power_at_time(self, t: float) -> Tuple[float, float, str]:
        """
        Calculate effective power at time t during discharge.

        Returns: (power_watts, coverage_fraction, phase_description)
        """
        if t < self.electrolytic_discharge_time_s:
            # Stacked mode - high voltage
            v = self.total_series_voltage - (self.max_current_A * t / self.electrolytic_total_capacitance_F) if self.electrolytic_total_capacitance_F > 0 else self.supercap_bank_voltage
            v = max(v, self.supercap_bank_voltage)  # Can't go below supercap voltage
            coverage = np.arcsin(min(v / self.v_ac_peak, 1.0)) / (np.pi / 2)
            power = v * self.max_current_A * coverage
            return power, coverage, "stacked"
        else:
            # Supercap-only mode
            # Account for supercap discharge
            t_supercap = t - self.electrolytic_discharge_time_s
            v = self.supercap_bank_voltage - (self.max_current_A * t_supercap / self.supercap_bank_capacitance)
            v = max(v, self.supercap_bank_voltage / 2)  # Don't discharge below 50%
            coverage = np.arcsin(min(v / self.v_ac_peak, 1.0)) / (np.pi / 2)
            power = v * self.max_current_A * coverage
            return power, coverage, "supercap_only"


def simulate_discharge(config: HybridConfig, duration_s: float = 3.0, dt: float = 0.001) -> dict:
    """Simulate discharge over time."""
    times = np.arange(0, duration_s, dt)
    powers = []
    coverages = []
    phases = []
    energies = []

    total_energy = 0
    for t in times:
        p, c, phase = config.power_at_time(t)
        powers.append(p)
        coverages.append(c)
        phases.append(phase)
        total_energy += p * dt
        energies.append(total_energy)

    return {
        'times': times,
        'powers': powers,
        'coverages': coverages,
        'phases': phases,
        'cumulative_energy': energies,
        'average_power': total_energy / duration_s,
        'config': config
    }


def compare_configurations():
    """Compare various hybrid configurations."""
    configs = [
        # Supercap only configurations
        HybridConfig(supercap_cells=9, electrolytic_count=0),   # Current design
        HybridConfig(supercap_cells=18, electrolytic_count=0),  # Double supercaps
        HybridConfig(supercap_cells=25, electrolytic_count=0),  # For 67.5V

        # Hybrid stacking configurations
        HybridConfig(supercap_cells=9, electrolytic_count=10),  # Small boost
        HybridConfig(supercap_cells=9, electrolytic_count=20),  # Medium boost
        HybridConfig(supercap_cells=9, electrolytic_count=40),  # Large boost

        # Larger supercap + boost
        HybridConfig(supercap_cells=12, electrolytic_count=20),
        HybridConfig(supercap_cells=15, electrolytic_count=20),
    ]

    # Run simulations
    results = [simulate_discharge(c) for c in configs]

    return results


def plot_comparison(results: List[dict], save_path: str = None):
    """Plot comparison of configurations."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Hybrid Stacking Analysis: Supercaps + Electrolytics', fontsize=14, fontweight='bold')

    # Color map
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))

    # Plot 1: Power over time
    ax1 = axes[0, 0]
    for i, r in enumerate(results):
        c = r['config']
        label = f"{c.supercap_cells*2}SC"
        if c.electrolytic_count > 0:
            label += f"+{c.electrolytic_count*2}E"
        label += f" (${c.total_cost:.0f})"
        ax1.plot(r['times'] * 1000, r['powers'], color=colors[i], linewidth=2, label=label)

    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Effective Power (W)')
    ax1.set_title('Power Delivery Over Time')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 500)  # Focus on first 500ms
    ax1.axvline(x=100, color='gray', linestyle=':', alpha=0.5)
    ax1.axvline(x=200, color='gray', linestyle=':', alpha=0.5)
    ax1.text(100, ax1.get_ylim()[1]*0.95, '100ms', fontsize=8, ha='center')
    ax1.text(200, ax1.get_ylim()[1]*0.95, '200ms', fontsize=8, ha='center')

    # Plot 2: Coverage over time
    ax2 = axes[0, 1]
    for i, r in enumerate(results):
        c = r['config']
        ax2.plot(r['times'] * 1000, [cov * 100 for cov in r['coverages']],
                color=colors[i], linewidth=2)

    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('AC Coverage (%)')
    ax2.set_title('Waveform Coverage Over Time')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 500)
    ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50% coverage')
    ax2.legend()

    # Plot 3: Average power vs cost
    ax3 = axes[1, 0]
    costs = [r['config'].total_cost for r in results]
    avg_powers = [r['average_power'] for r in results]

    # Separate hybrid vs supercap-only
    for i, r in enumerate(results):
        c = r['config']
        marker = 's' if c.electrolytic_count > 0 else 'o'
        color = 'blue' if c.electrolytic_count == 0 else 'green'
        label = 'Supercap only' if c.electrolytic_count == 0 and i == 0 else None
        label = 'Hybrid' if c.electrolytic_count > 0 and i == 3 else label
        ax3.scatter(costs[i], avg_powers[i], color=color, marker=marker, s=100, label=label)

        # Annotate
        txt = f"{c.supercap_cells*2}SC"
        if c.electrolytic_count > 0:
            txt += f"+{c.electrolytic_count*2}E"
        ax3.annotate(txt, (costs[i], avg_powers[i]), textcoords="offset points",
                    xytext=(5, 5), fontsize=8)

    ax3.set_xlabel('Total Cost (USD)')
    ax3.set_ylabel('Average Power over 3s (W)')
    ax3.set_title('Average Power vs Cost')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Summary table
    ax4 = axes[1, 1]
    ax4.axis('off')

    table_data = []
    for r in results:
        c = r['config']
        sc_str = f"{c.supercap_cells*2}"
        elec_str = f"{c.electrolytic_count*2}" if c.electrolytic_count > 0 else "-"
        table_data.append([
            sc_str,
            elec_str,
            f"${c.total_cost:.0f}",
            f"{c.supercap_bank_voltage:.1f}V",
            f"{c.total_series_voltage:.1f}V" if c.electrolytic_count > 0 else "-",
            f"{c.coverage_stacked*100:.1f}%" if c.electrolytic_count > 0 else f"{c.coverage_supercap_only*100:.1f}%",
            f"{c.electrolytic_discharge_time_s*1000:.0f}ms" if c.electrolytic_count > 0 else "-",
            f"{r['average_power']:.0f}W",
        ])

    table = ax4.table(
        cellText=table_data,
        colLabels=['SCs', 'Elecs', 'Cost', 'V_sc', 'V_stack', 'Coverage', 'Boost', 'Avg P'],
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.4)
    ax4.set_title('Configuration Summary', pad=20)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")

    return fig


def print_summary(results: List[dict]):
    """Print detailed summary."""
    print("\n" + "=" * 100)
    print("HYBRID STACKING ANALYSIS")
    print("=" * 100)

    print(f"\n{'Config':<20} {'Cost':>8} {'V_sc':>8} {'V_stack':>10} {'Coverage':>10} "
          f"{'Boost dur':>10} {'Avg Power':>10}")
    print("-" * 100)

    for r in results:
        c = r['config']
        name = f"{c.supercap_cells*2}SC"
        if c.electrolytic_count > 0:
            name += f"+{c.electrolytic_count*2}E"

        v_stack = f"{c.total_series_voltage:.1f}V" if c.electrolytic_count > 0 else "-"
        coverage = c.coverage_stacked if c.electrolytic_count > 0 else c.coverage_supercap_only
        boost = f"{c.electrolytic_discharge_time_s*1000:.0f}ms" if c.electrolytic_count > 0 else "-"

        print(f"{name:<20} ${c.total_cost:>7.0f} {c.supercap_bank_voltage:>8.1f}V {v_stack:>10} "
              f"{coverage*100:>9.1f}% {boost:>10} {r['average_power']:>10.0f}W")

    print("=" * 100)

    # Find best value configurations
    print("\nKEY FINDINGS:")

    # Best supercap-only
    sc_only = [r for r in results if r['config'].electrolytic_count == 0]
    best_sc = max(sc_only, key=lambda r: r['average_power'] / r['config'].total_cost)
    print(f"\nBest supercap-only: {best_sc['config'].supercap_cells*2} cells")
    print(f"  Cost: ${best_sc['config'].total_cost:.0f}, Power: {best_sc['average_power']:.0f}W")

    # Best hybrid
    hybrid = [r for r in results if r['config'].electrolytic_count > 0]
    if hybrid:
        best_hybrid = max(hybrid, key=lambda r: r['average_power'] / r['config'].total_cost)
        print(f"\nBest hybrid: {best_hybrid['config'].supercap_cells*2}SC + {best_hybrid['config'].electrolytic_count*2}E")
        print(f"  Cost: ${best_hybrid['config'].total_cost:.0f}, Power: {best_hybrid['average_power']:.0f}W")
        print(f"  Boost duration: {best_hybrid['config'].electrolytic_discharge_time_s*1000:.0f}ms")
        print(f"  Stacked voltage: {best_hybrid['config'].total_series_voltage:.1f}V")
        print(f"  Coverage during boost: {best_hybrid['config'].coverage_stacked*100:.1f}%")


def main():
    results = compare_configurations()
    print_summary(results)
    plot_comparison(results, save_path='hybrid_stacking_analysis.png')
    plt.show()


if __name__ == '__main__':
    main()
