#!/usr/bin/env python3
"""
Analyze supercapacitor configurations for the Generator Power Assist project.

This script calculates and plots the power delivery capability vs cost
for different numbers of supercapacitors in series.

Key insight: For supercaps in series, energy scales LINEARLY with cell count:
  E = 0.5 × (C/N) × (N×V)² = 0.5 × C × N × V²

But AC coverage (the fraction of the waveform we can inject into) follows
an arcsin curve based on bank voltage vs AC peak voltage.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple


# =============================================================================
# Configuration Parameters
# =============================================================================

@dataclass
class SupercapCell:
    """Supercapacitor cell specifications."""
    capacitance_F: float = 100.0   # Farads
    voltage_V: float = 2.7         # Volts (max rated)
    cost_USD: float = 6.0          # Cost per cell
    esr_ohm: float = 0.015         # Equivalent series resistance


@dataclass
class ACSystem:
    """AC system parameters."""
    voltage_rms: float = 120.0     # VAC RMS
    frequency_hz: float = 60.0     # Hz

    @property
    def voltage_peak(self) -> float:
        return self.voltage_rms * np.sqrt(2)  # ~170V for 120VAC

    @property
    def period_ms(self) -> float:
        return 1000.0 / self.frequency_hz  # ~16.67ms for 60Hz

    @property
    def half_period_ms(self) -> float:
        return self.period_ms / 2  # ~8.33ms


@dataclass
class SystemLimits:
    """Operating limits."""
    max_current_A: float = 40.0           # Max discharge current
    min_discharge_ratio: float = 0.5      # Discharge to 50% voltage
    assist_duration_s: float = 3.0        # Target assist duration


# =============================================================================
# Analysis Functions
# =============================================================================

def analyze_config(
    cells_per_bank: int,
    cell: SupercapCell,
    ac: ACSystem,
    limits: SystemLimits
) -> dict:
    """
    Analyze a supercapacitor configuration.

    Args:
        cells_per_bank: Number of cells in series per bank
        cell: Supercapacitor cell specs
        ac: AC system parameters
        limits: Operating limits

    Returns:
        Dictionary with all calculated parameters
    """
    N = cells_per_bank

    # Bank electrical properties
    v_bank = N * cell.voltage_V                    # Bank voltage
    c_bank = cell.capacitance_F / N                # Bank capacitance (series)
    esr_bank = N * cell.esr_ohm                    # Bank ESR (series)

    # Energy calculations
    e_bank_full = 0.5 * c_bank * v_bank**2         # Full charge energy (J)
    v_min = v_bank * limits.min_discharge_ratio    # Minimum discharge voltage
    e_bank_usable = 0.5 * c_bank * (v_bank**2 - v_min**2)  # Usable energy (J)

    # Total system (2 banks: positive + negative)
    total_cells = 2 * N
    total_cost = total_cells * cell.cost_USD
    total_energy = 2 * e_bank_full
    total_usable_energy = 2 * e_bank_usable

    # AC coverage calculation
    # We can inject when |V_ac| < V_bank
    # Coverage = arcsin(V_bank / V_peak) / (π/2)
    if v_bank >= ac.voltage_peak:
        coverage_fraction = 1.0
        coverage_angle_deg = 90.0
    else:
        coverage_angle_rad = np.arcsin(v_bank / ac.voltage_peak)
        coverage_angle_deg = np.degrees(coverage_angle_rad)
        coverage_fraction = coverage_angle_rad / (np.pi / 2)

    # Time window per half-cycle
    time_window_ms = ac.half_period_ms * coverage_fraction

    # Power delivery calculations
    # Instantaneous power when injecting
    p_instantaneous = v_bank * limits.max_current_A

    # Average power over full cycle (limited by coverage)
    # Factor of 2 because we have both positive and negative banks
    # working on their respective half-cycles
    p_average_coverage_limited = p_instantaneous * coverage_fraction

    # Energy-limited average power (if we had full coverage)
    p_average_energy_limited = total_usable_energy / limits.assist_duration_s

    # Effective power is the minimum of coverage-limited and energy-limited
    p_effective = min(p_average_coverage_limited, p_average_energy_limited)

    # Assist duration at effective power
    if p_effective > 0:
        assist_duration_actual = total_usable_energy / p_effective
    else:
        assist_duration_actual = 0

    # ESR power loss at max current
    p_loss_esr = limits.max_current_A**2 * esr_bank

    return {
        'cells_per_bank': N,
        'total_cells': total_cells,
        'total_cost_usd': total_cost,
        'bank_voltage_v': v_bank,
        'bank_capacitance_f': c_bank,
        'bank_esr_ohm': esr_bank,
        'energy_per_bank_j': e_bank_full,
        'usable_energy_per_bank_j': e_bank_usable,
        'total_energy_j': total_energy,
        'total_usable_energy_j': total_usable_energy,
        'coverage_fraction': coverage_fraction,
        'coverage_percent': coverage_fraction * 100,
        'coverage_angle_deg': coverage_angle_deg,
        'time_window_ms': time_window_ms,
        'power_instantaneous_w': p_instantaneous,
        'power_coverage_limited_w': p_average_coverage_limited,
        'power_energy_limited_w': p_average_energy_limited,
        'power_effective_w': p_effective,
        'assist_duration_s': assist_duration_actual,
        'power_loss_esr_w': p_loss_esr,
    }


def analyze_range(
    cell_counts: List[int],
    cell: SupercapCell,
    ac: ACSystem,
    limits: SystemLimits
) -> List[dict]:
    """Analyze a range of configurations."""
    return [analyze_config(n, cell, ac, limits) for n in cell_counts]


# =============================================================================
# Plotting Functions
# =============================================================================

def plot_power_vs_cost(results: List[dict], save_path: str = None):
    """
    Create comprehensive visualization of power vs cost tradeoffs.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Supercapacitor Configuration Analysis\nGenerator Power Assist',
                 fontsize=14, fontweight='bold')

    # Extract data
    costs = [r['total_cost_usd'] for r in results]
    cells = [r['total_cells'] for r in results]
    voltages = [r['bank_voltage_v'] for r in results]
    energies = [r['total_usable_energy_j'] for r in results]
    coverages = [r['coverage_percent'] for r in results]
    p_effective = [r['power_effective_w'] for r in results]
    p_coverage = [r['power_coverage_limited_w'] for r in results]
    p_energy = [r['power_energy_limited_w'] for r in results]
    durations = [r['assist_duration_s'] for r in results]

    # Plot 1: Effective Power vs Cost
    ax1 = axes[0, 0]
    ax1.plot(costs, p_effective, 'b-o', linewidth=2, markersize=6)
    ax1.set_xlabel('Total Cost (USD)')
    ax1.set_ylabel('Effective Power (W)')
    ax1.set_title('Effective Assist Power vs Cost')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max(costs) * 1.05)
    ax1.set_ylim(0, max(p_effective) * 1.1)

    # Annotate key points
    for i, n in enumerate([9, 18, 27, 36]):
        if n <= len(results):
            idx = n - 1
            ax1.annotate(f'{results[idx]["total_cells"]} cells\n{results[idx]["bank_voltage_v"]:.1f}V',
                        (costs[idx], p_effective[idx]),
                        textcoords="offset points", xytext=(10, -10),
                        fontsize=8, alpha=0.8)

    # Plot 2: Coverage vs Voltage
    ax2 = axes[0, 1]
    ax2.plot(voltages, coverages, 'g-o', linewidth=2, markersize=6)
    ax2.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='50% coverage')
    ax2.axhline(y=33, color='orange', linestyle='--', alpha=0.5, label='33% coverage')
    ax2.axvline(x=85, color='purple', linestyle='--', alpha=0.5, label='V_ac at 50%')
    ax2.set_xlabel('Bank Voltage (V)')
    ax2.set_ylabel('AC Cycle Coverage (%)')
    ax2.set_title('Waveform Coverage vs Bank Voltage')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='lower right', fontsize=8)
    ax2.set_xlim(0, max(voltages) * 1.05)
    ax2.set_ylim(0, 100)

    # Plot 3: Energy vs Cost
    ax3 = axes[0, 2]
    ax3.plot(costs, energies, 'r-o', linewidth=2, markersize=6)
    ax3.set_xlabel('Total Cost (USD)')
    ax3.set_ylabel('Usable Energy (J)')
    ax3.set_title('Energy Storage vs Cost')
    ax3.grid(True, alpha=0.3)

    # Add secondary axis showing assist duration at 500W
    ax3b = ax3.twinx()
    duration_at_500w = [e / 500 for e in energies]
    ax3b.plot(costs, duration_at_500w, 'r--', alpha=0.5)
    ax3b.set_ylabel('Duration at 500W (s)', color='red', alpha=0.7)
    ax3b.tick_params(axis='y', labelcolor='red')

    # Plot 4: Power Breakdown
    ax4 = axes[1, 0]
    ax4.plot(cells, p_coverage, 'b-o', label='Coverage-limited', linewidth=2, markersize=5)
    ax4.plot(cells, p_energy, 'r-s', label='Energy-limited', linewidth=2, markersize=5)
    ax4.plot(cells, p_effective, 'g-^', label='Effective (min)', linewidth=2, markersize=5)
    ax4.set_xlabel('Total Cells')
    ax4.set_ylabel('Power (W)')
    ax4.set_title('Power Limits vs Cell Count')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(True, alpha=0.3)

    # Highlight crossover point
    crossover_idx = None
    for i in range(len(results) - 1):
        if p_coverage[i] < p_energy[i] and p_coverage[i+1] >= p_energy[i+1]:
            crossover_idx = i
            break
    if crossover_idx:
        ax4.axvline(x=cells[crossover_idx], color='gray', linestyle=':', alpha=0.5)
        ax4.annotate('Crossover', (cells[crossover_idx], p_effective[crossover_idx]),
                    textcoords="offset points", xytext=(5, 10), fontsize=8)

    # Plot 5: Cost Efficiency (Power per Dollar)
    ax5 = axes[1, 1]
    efficiency = [p / c if c > 0 else 0 for p, c in zip(p_effective, costs)]
    ax5.plot(cells, efficiency, 'purple', linewidth=2, marker='o', markersize=6)
    ax5.set_xlabel('Total Cells')
    ax5.set_ylabel('Power per Dollar (W/$)')
    ax5.set_title('Cost Efficiency')
    ax5.grid(True, alpha=0.3)

    # Find and mark optimal point
    max_eff_idx = np.argmax(efficiency)
    ax5.annotate(f'Best: {cells[max_eff_idx]} cells\n{efficiency[max_eff_idx]:.2f} W/$',
                (cells[max_eff_idx], efficiency[max_eff_idx]),
                textcoords="offset points", xytext=(10, -15),
                fontsize=9, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))

    # Plot 6: Summary Table
    ax6 = axes[1, 2]
    ax6.axis('off')

    # Create summary table for key configurations
    key_configs = [6, 9, 12, 18, 24, 36]
    table_data = []
    for n in key_configs:
        if n <= len(results):
            r = results[n - 1]
            table_data.append([
                f"{r['total_cells']}",
                f"${r['total_cost_usd']:.0f}",
                f"{r['bank_voltage_v']:.1f}V",
                f"{r['coverage_percent']:.1f}%",
                f"{r['total_usable_energy_j']:.0f}J",
                f"{r['power_effective_w']:.0f}W",
            ])

    table = ax6.table(
        cellText=table_data,
        colLabels=['Cells', 'Cost', 'Voltage', 'Coverage', 'Energy', 'Power'],
        loc='center',
        cellLoc='center',
        colWidths=[0.12, 0.14, 0.14, 0.16, 0.16, 0.14]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    ax6.set_title('Key Configurations Summary', pad=20)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")

    return fig


def plot_motor_start_scenario(results: List[dict], save_path: str = None):
    """
    Plot a specific motor start scenario showing energy flow over time.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Motor Start Assist Scenarios', fontsize=14, fontweight='bold')

    # Scenario: Motor needs 1500W total, generator provides 800W, we need 700W
    required_assist_w = 700
    assist_duration_s = 3.0
    required_energy_j = required_assist_w * assist_duration_s

    cells = [r['total_cells'] for r in results]
    energies = [r['total_usable_energy_j'] for r in results]
    powers = [r['power_effective_w'] for r in results]
    costs = [r['total_cost_usd'] for r in results]

    # Plot 1: Can we meet the power requirement?
    ax1 = axes[0, 0]
    ax1.bar(cells, powers, color=['green' if p >= required_assist_w else 'red' for p in powers],
            alpha=0.7, edgecolor='black')
    ax1.axhline(y=required_assist_w, color='blue', linestyle='--', linewidth=2,
                label=f'Required: {required_assist_w}W')
    ax1.set_xlabel('Total Cells')
    ax1.set_ylabel('Effective Power (W)')
    ax1.set_title(f'Power Capability vs Requirement ({required_assist_w}W)')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Plot 2: Can we meet the energy requirement?
    ax2 = axes[0, 1]
    ax2.bar(cells, energies, color=['green' if e >= required_energy_j else 'orange' for e in energies],
            alpha=0.7, edgecolor='black')
    ax2.axhline(y=required_energy_j, color='blue', linestyle='--', linewidth=2,
                label=f'Required: {required_energy_j}J')
    ax2.set_xlabel('Total Cells')
    ax2.set_ylabel('Usable Energy (J)')
    ax2.set_title(f'Energy Storage vs Requirement ({required_energy_j}J)')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Minimum cost to meet requirements
    ax3 = axes[1, 0]
    meets_requirements = [p >= required_assist_w and e >= required_energy_j
                         for p, e in zip(powers, energies)]

    colors = ['green' if m else 'lightgray' for m in meets_requirements]
    ax3.bar(cells, costs, color=colors, alpha=0.7, edgecolor='black')

    # Find minimum viable configuration
    viable_configs = [(i, costs[i]) for i, m in enumerate(meets_requirements) if m]
    if viable_configs:
        min_idx, min_cost = min(viable_configs, key=lambda x: x[1])
        ax3.annotate(f'Minimum viable:\n{cells[min_idx]} cells, ${min_cost:.0f}',
                    (cells[min_idx], min_cost),
                    textcoords="offset points", xytext=(20, 20),
                    fontsize=10, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='red'))

    ax3.set_xlabel('Total Cells')
    ax3.set_ylabel('Cost (USD)')
    ax3.set_title('Cost by Configuration\n(Green = meets requirements)')
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Assist timeline simulation
    ax4 = axes[1, 1]

    # Simulate a few configurations
    configs_to_plot = [12, 18, 24, 36]
    time = np.linspace(0, 5, 500)

    for n in configs_to_plot:
        if n <= len(results):
            r = results[n - 1]
            energy = r['total_usable_energy_j']
            power = r['power_effective_w']

            # Simple model: constant power until energy depleted
            duration = energy / power if power > 0 else 0

            power_profile = np.where(time <= duration, power, 0)
            ax4.plot(time, power_profile, label=f'{r["total_cells"]} cells ({r["bank_voltage_v"]:.0f}V)',
                    linewidth=2)

    ax4.axhline(y=required_assist_w, color='red', linestyle='--', alpha=0.5,
                label=f'Target: {required_assist_w}W')
    ax4.axvline(x=assist_duration_s, color='gray', linestyle=':', alpha=0.5,
                label=f'Target duration: {assist_duration_s}s')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Assist Power (W)')
    ax4.set_title('Assist Power Timeline')
    ax4.legend(loc='upper right', fontsize=8)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 5)
    ax4.set_ylim(0, max(powers) * 1.1)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")

    return fig


def print_summary_table(results: List[dict]):
    """Print a text summary table of all configurations."""
    print("\n" + "=" * 100)
    print("SUPERCAPACITOR CONFIGURATION ANALYSIS")
    print("=" * 100)
    print(f"{'Cells':>6} {'Cost':>8} {'Voltage':>8} {'Cap':>8} {'Energy':>10} "
          f"{'Coverage':>10} {'P_eff':>10} {'Duration':>10}")
    print(f"{'':>6} {'(USD)':>8} {'(V)':>8} {'(F)':>8} {'(J)':>10} "
          f"{'(%)':>10} {'(W)':>10} {'(s)':>10}")
    print("-" * 100)

    for r in results:
        print(f"{r['total_cells']:>6} "
              f"${r['total_cost_usd']:>7.0f} "
              f"{r['bank_voltage_v']:>8.1f} "
              f"{r['bank_capacitance_f']:>8.2f} "
              f"{r['total_usable_energy_j']:>10.0f} "
              f"{r['coverage_percent']:>10.1f} "
              f"{r['power_effective_w']:>10.0f} "
              f"{r['assist_duration_s']:>10.1f}")

    print("=" * 100)


# =============================================================================
# Main
# =============================================================================

def main():
    """Run the analysis and generate plots."""
    # Define parameters
    cell = SupercapCell(
        capacitance_F=100.0,
        voltage_V=2.7,
        cost_USD=6.0,
        esr_ohm=0.015
    )

    ac = ACSystem(
        voltage_rms=120.0,
        frequency_hz=60.0
    )

    limits = SystemLimits(
        max_current_A=40.0,
        min_discharge_ratio=0.5,
        assist_duration_s=3.0
    )

    # Analyze configurations from 2 to 40 cells per bank
    # (total cells = 2x this for both banks)
    cell_counts = list(range(1, 41))
    results = analyze_range(cell_counts, cell, ac, limits)

    # Print summary
    print_summary_table(results)

    # Generate plots
    print("\nGenerating plots...")

    fig1 = plot_power_vs_cost(results, save_path='supercap_analysis.png')
    fig2 = plot_motor_start_scenario(results, save_path='motor_start_scenario.png')

    # Show plots
    plt.show()

    # Print recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    # Find optimal configurations
    efficiencies = [r['power_effective_w'] / r['total_cost_usd'] for r in results]
    best_efficiency_idx = np.argmax(efficiencies)

    print(f"\nBest cost efficiency: {results[best_efficiency_idx]['total_cells']} cells")
    print(f"  - Cost: ${results[best_efficiency_idx]['total_cost_usd']:.0f}")
    print(f"  - Power: {results[best_efficiency_idx]['power_effective_w']:.0f}W")
    print(f"  - Efficiency: {efficiencies[best_efficiency_idx]:.2f} W/$")

    # Find minimum config for 500W assist
    for r in results:
        if r['power_effective_w'] >= 500:
            print(f"\nMinimum for 500W assist: {r['total_cells']} cells")
            print(f"  - Cost: ${r['total_cost_usd']:.0f}")
            print(f"  - Actual power: {r['power_effective_w']:.0f}W")
            print(f"  - Coverage: {r['coverage_percent']:.1f}%")
            break

    # Find minimum config for 700W assist
    for r in results:
        if r['power_effective_w'] >= 700:
            print(f"\nMinimum for 700W assist: {r['total_cells']} cells")
            print(f"  - Cost: ${r['total_cost_usd']:.0f}")
            print(f"  - Actual power: {r['power_effective_w']:.0f}W")
            print(f"  - Coverage: {r['coverage_percent']:.1f}%")
            break


if __name__ == '__main__':
    main()
