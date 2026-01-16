#!/usr/bin/env python3
"""
Optimize minimal hybrid configuration for ~200J energy delivery.

Goal: Find the cheapest combination of supercaps + electrolytics that delivers
approximately 200J during the critical motor start window (first 200ms).
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from itertools import product


@dataclass
class Config:
    """Hybrid configuration."""
    supercap_cells_per_bank: int
    electrolytic_count_per_bank: int

    # Constants
    SC_CAPACITANCE_F: float = 100.0
    SC_VOLTAGE_V: float = 2.7
    SC_COST: float = 6.0

    ELEC_CAPACITANCE_UF: float = 4700.0
    ELEC_VOLTAGE_V: float = 60.0  # Charge voltage (derated)
    ELEC_COST: float = 2.28
    ELEC_RIPPLE_CURRENT_A: float = 3.0  # Per cap

    V_AC_PEAK: float = 170.0
    MAX_CURRENT_A: float = 40.0

    @property
    def total_supercaps(self) -> int:
        return 2 * self.supercap_cells_per_bank

    @property
    def total_electrolytics(self) -> int:
        return 2 * self.electrolytic_count_per_bank

    @property
    def total_cost(self) -> float:
        return (self.total_supercaps * self.SC_COST +
                self.total_electrolytics * self.ELEC_COST)

    @property
    def sc_bank_voltage(self) -> float:
        return self.supercap_cells_per_bank * self.SC_VOLTAGE_V

    @property
    def sc_bank_capacitance(self) -> float:
        if self.supercap_cells_per_bank == 0:
            return 0
        return self.SC_CAPACITANCE_F / self.supercap_cells_per_bank

    @property
    def elec_bank_capacitance(self) -> float:
        return self.electrolytic_count_per_bank * self.ELEC_CAPACITANCE_UF * 1e-6

    @property
    def stacked_voltage(self) -> float:
        return self.sc_bank_voltage + self.ELEC_VOLTAGE_V

    @property
    def coverage_stacked(self) -> float:
        v = self.stacked_voltage
        if v >= self.V_AC_PEAK:
            return 1.0
        return np.arcsin(v / self.V_AC_PEAK) / (np.pi / 2)

    @property
    def coverage_sc_only(self) -> float:
        v = self.sc_bank_voltage
        if v >= self.V_AC_PEAK:
            return 1.0
        if v <= 0:
            return 0
        return np.arcsin(v / self.V_AC_PEAK) / (np.pi / 2)

    @property
    def elec_discharge_time_s(self) -> float:
        if self.elec_bank_capacitance == 0:
            return 0
        return self.ELEC_VOLTAGE_V * self.elec_bank_capacitance / self.MAX_CURRENT_A

    @property
    def elec_current_ok(self) -> bool:
        """Check if electrolytics can handle the current."""
        if self.electrolytic_count_per_bank == 0:
            return True
        current_per_cap = self.MAX_CURRENT_A / self.electrolytic_count_per_bank
        return current_per_cap <= self.ELEC_RIPPLE_CURRENT_A * 2  # Allow 2x for short bursts

    @property
    def min_electrolytics_for_current(self) -> int:
        """Minimum electrolytics needed for current handling."""
        return int(np.ceil(self.MAX_CURRENT_A / (self.ELEC_RIPPLE_CURRENT_A * 2)))

    def energy_delivered_in_window(self, window_ms: float) -> float:
        """Calculate energy delivered in first N milliseconds."""
        window_s = window_ms / 1000.0
        dt = 0.001  # 1ms timestep

        total_energy = 0
        t = 0

        while t < window_s:
            if t < self.elec_discharge_time_s:
                # Stacked mode
                # Voltage decreases as electrolytics discharge
                v_elec = self.ELEC_VOLTAGE_V - (self.MAX_CURRENT_A * t / self.elec_bank_capacitance) if self.elec_bank_capacitance > 0 else 0
                v_elec = max(v_elec, 0)
                v_total = self.sc_bank_voltage + v_elec
            else:
                # Supercap only mode
                t_sc = t - self.elec_discharge_time_s
                v_drop = self.MAX_CURRENT_A * t_sc / self.sc_bank_capacitance if self.sc_bank_capacitance > 0 else 0
                v_total = max(self.sc_bank_voltage - v_drop, self.sc_bank_voltage * 0.5)

            # Calculate coverage and power at this voltage
            if v_total >= self.V_AC_PEAK:
                coverage = 1.0
            elif v_total <= 0:
                coverage = 0
            else:
                coverage = np.arcsin(v_total / self.V_AC_PEAK) / (np.pi / 2)

            power = v_total * self.MAX_CURRENT_A * coverage
            total_energy += power * dt
            t += dt

        return total_energy

    def peak_power(self) -> float:
        """Peak effective power at t=0."""
        return self.stacked_voltage * self.MAX_CURRENT_A * self.coverage_stacked


def find_optimal_configs(target_energy_j: float = 200, window_ms: float = 200):
    """Find configurations that deliver target energy at minimum cost."""

    results = []

    # Search space
    sc_range = range(2, 15)  # 2-14 supercaps per bank
    elec_range = range(0, 25)  # 0-24 electrolytics per bank

    for sc, elec in product(sc_range, elec_range):
        config = Config(sc, elec)

        # Skip if electrolytics can't handle current
        if elec > 0 and not config.elec_current_ok:
            continue

        energy = config.energy_delivered_in_window(window_ms)

        results.append({
            'config': config,
            'sc_per_bank': sc,
            'elec_per_bank': elec,
            'total_sc': config.total_supercaps,
            'total_elec': config.total_electrolytics,
            'cost': config.total_cost,
            'energy_200ms': energy,
            'peak_power': config.peak_power(),
            'sc_voltage': config.sc_bank_voltage,
            'stacked_voltage': config.stacked_voltage,
            'coverage_stacked': config.coverage_stacked * 100,
            'elec_boost_ms': config.elec_discharge_time_s * 1000,
        })

    return results


def plot_results(results, target_energy=200, save_path=None):
    """Plot optimization results."""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Minimal Hybrid Optimization (Target: {target_energy}J in 200ms)',
                 fontsize=14, fontweight='bold')

    # Filter to reasonable energy range
    filtered = [r for r in results if r['energy_200ms'] >= target_energy * 0.8]

    costs = [r['cost'] for r in filtered]
    energies = [r['energy_200ms'] for r in filtered]
    peak_powers = [r['peak_power'] for r in filtered]

    # Color by whether it has electrolytics
    colors = ['green' if r['total_elec'] > 0 else 'blue' for r in filtered]

    # Plot 1: Energy vs Cost
    ax1 = axes[0, 0]
    ax1.scatter(costs, energies, c=colors, alpha=0.6, s=50)
    ax1.axhline(y=target_energy, color='red', linestyle='--', label=f'Target: {target_energy}J')
    ax1.set_xlabel('Total Cost (USD)')
    ax1.set_ylabel('Energy Delivered in 200ms (J)')
    ax1.set_title('Energy vs Cost')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Find Pareto frontier (minimum cost for each energy level)
    pareto = []
    sorted_by_energy = sorted(filtered, key=lambda x: x['energy_200ms'])
    min_cost = float('inf')
    for r in sorted_by_energy:
        if r['cost'] < min_cost:
            pareto.append(r)
            min_cost = r['cost']

    pareto_costs = [r['cost'] for r in pareto]
    pareto_energies = [r['energy_200ms'] for r in pareto]
    ax1.plot(pareto_costs, pareto_energies, 'r-', linewidth=2, label='Pareto frontier')

    # Plot 2: Peak Power vs Cost
    ax2 = axes[0, 1]
    ax2.scatter(costs, peak_powers, c=colors, alpha=0.6, s=50)
    ax2.set_xlabel('Total Cost (USD)')
    ax2.set_ylabel('Peak Power (W)')
    ax2.set_title('Peak Power vs Cost\n(Blue=SC only, Green=Hybrid)')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Cost breakdown for configs meeting target
    ax3 = axes[1, 0]
    meeting_target = [r for r in results if r['energy_200ms'] >= target_energy]
    meeting_target.sort(key=lambda x: x['cost'])

    if meeting_target:
        top_10 = meeting_target[:10]
        labels = [f"{r['total_sc']}SC+{r['total_elec']}E" for r in top_10]
        sc_costs = [r['total_sc'] * 6 for r in top_10]
        elec_costs = [r['total_elec'] * 2.28 for r in top_10]

        x = np.arange(len(labels))
        width = 0.6

        ax3.bar(x, sc_costs, width, label='Supercaps', color='blue', alpha=0.7)
        ax3.bar(x, elec_costs, width, bottom=sc_costs, label='Electrolytics', color='orange', alpha=0.7)
        ax3.set_xlabel('Configuration')
        ax3.set_ylabel('Cost (USD)')
        ax3.set_title(f'Top 10 Cheapest Configs Meeting {target_energy}J Target')
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, rotation=45, ha='right')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Summary table
    ax4 = axes[1, 1]
    ax4.axis('off')

    if meeting_target:
        table_data = []
        for r in meeting_target[:8]:
            table_data.append([
                f"{r['total_sc']}",
                f"{r['total_elec']}",
                f"${r['cost']:.0f}",
                f"{r['stacked_voltage']:.1f}V",
                f"{r['coverage_stacked']:.0f}%",
                f"{r['elec_boost_ms']:.0f}ms",
                f"{r['energy_200ms']:.0f}J",
                f"{r['peak_power']:.0f}W",
            ])

        table = ax4.table(
            cellText=table_data,
            colLabels=['SCs', 'Elecs', 'Cost', 'V_stack', 'Cov%', 'Boost', 'E_200ms', 'P_peak'],
            loc='center',
            cellLoc='center',
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        ax4.set_title(f'Cheapest Configs Delivering ≥{target_energy}J in 200ms', pad=20)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    return fig


def print_recommendations(results, target_energy=200):
    """Print recommendations."""

    meeting_target = [r for r in results if r['energy_200ms'] >= target_energy]
    meeting_target.sort(key=lambda x: x['cost'])

    print("\n" + "=" * 90)
    print(f"OPTIMIZATION RESULTS: Target {target_energy}J in 200ms")
    print("=" * 90)

    print(f"\n{'Config':<15} {'Cost':>8} {'V_stack':>10} {'Coverage':>10} {'Boost':>10} {'E_200ms':>10} {'P_peak':>10}")
    print("-" * 90)

    for r in meeting_target[:15]:
        name = f"{r['total_sc']}SC+{r['total_elec']}E"
        print(f"{name:<15} ${r['cost']:>7.0f} {r['stacked_voltage']:>10.1f}V "
              f"{r['coverage_stacked']:>9.0f}% {r['elec_boost_ms']:>9.0f}ms "
              f"{r['energy_200ms']:>10.0f}J {r['peak_power']:>10.0f}W")

    print("=" * 90)

    if meeting_target:
        best = meeting_target[0]
        print(f"\n*** RECOMMENDED: {best['total_sc']} supercaps + {best['total_elec']} electrolytics ***")
        print(f"    Total cost: ${best['cost']:.0f}")
        print(f"    Stacked voltage: {best['stacked_voltage']:.1f}V")
        print(f"    Coverage: {best['coverage_stacked']:.0f}%")
        print(f"    Electrolytic boost duration: {best['elec_boost_ms']:.0f}ms")
        print(f"    Energy in 200ms: {best['energy_200ms']:.0f}J")
        print(f"    Peak power: {best['peak_power']:.0f}W")

        # Cost breakdown
        sc_cost = best['total_sc'] * 6
        elec_cost = best['total_elec'] * 2.28
        print(f"\n    Cost breakdown:")
        print(f"      Supercaps: {best['total_sc']} × $6.00 = ${sc_cost:.0f}")
        print(f"      Electrolytics: {best['total_elec']} × $2.28 = ${elec_cost:.0f}")

    # Compare to supercap-only
    sc_only = [r for r in meeting_target if r['total_elec'] == 0]
    if sc_only:
        best_sc = sc_only[0]
        print(f"\n    Compare to supercap-only: {best_sc['total_sc']}SC @ ${best_sc['cost']:.0f}")
        if meeting_target[0]['total_elec'] > 0:
            savings = best_sc['cost'] - meeting_target[0]['cost']
            print(f"    Hybrid saves: ${savings:.0f}")


def main():
    print("Searching for optimal configurations...")
    results = find_optimal_configs(target_energy_j=200, window_ms=200)

    print_recommendations(results, target_energy=200)

    plot_results(results, target_energy=200, save_path='minimal_hybrid_optimization.png')
    plt.show()


if __name__ == '__main__':
    main()
