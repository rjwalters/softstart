#!/usr/bin/env python3
"""
Analyze actual motor startup power requirements for window AC compressors.

Based on research:
- LRA is typically 5-7x FLA (running current)
- Initial magnetizing surge (0-8ms): up to 20x FLA
- Locked rotor phase (8-180ms): 4-9x FLA
- Acceleration phase (180-600ms): decreasing to FLA
- Good compressor reaches speed in ~180ms
- Stressed compressor (low voltage) takes 550-600ms

Sources:
- HVAC School, Ametherm, Victron Community forums
- Typical 8000 BTU window AC: ~7A FLA, ~35A LRA
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class WindowACSpec:
    """Window AC unit specifications."""
    name: str
    btu: int
    running_watts: float  # Steady state power
    running_amps: float   # FLA
    lra_multiplier: float = 5.5  # LRA/FLA ratio (typically 5-7)
    power_factor_running: float = 0.85
    power_factor_locked: float = 0.35  # Very poor during locked rotor

    @property
    def lra(self) -> float:
        return self.running_amps * self.lra_multiplier

    @property
    def locked_rotor_va(self) -> float:
        return self.lra * 120  # At 120V

    @property
    def locked_rotor_watts(self) -> float:
        return self.locked_rotor_va * self.power_factor_locked


@dataclass
class GeneratorSpec:
    """Generator specifications."""
    name: str
    rated_watts: float
    max_watts: float
    voltage: float = 120.0

    @property
    def rated_amps(self) -> float:
        return self.rated_watts / self.voltage

    @property
    def max_amps(self) -> float:
        return self.max_watts / self.voltage


def motor_current_profile(t_ms: float, ac: WindowACSpec,
                          startup_time_ms: float = 300) -> float:
    """
    Model motor current draw over time during startup.

    Returns current in Amps RMS.

    Profile:
    - 0-8ms: Initial magnetizing surge (peak current, brief)
    - 8ms-180ms: Locked rotor current (LRA)
    - 180ms-startup_time: Exponential decay to FLA
    - After startup_time: FLA (steady state)
    """
    if t_ms < 0:
        return 0

    # Phase 1: Initial magnetizing surge (first half-cycle)
    if t_ms < 8.3:
        # Brief spike, up to 2x LRA (asymmetric first cycle)
        return ac.lra * (1.5 + 0.5 * np.exp(-t_ms / 2))

    # Phase 2: Locked rotor (motor accelerating from standstill)
    if t_ms < 100:
        # Current stays near LRA as motor starts to move
        return ac.lra * (1.0 - 0.1 * (t_ms - 8.3) / 91.7)

    # Phase 3: Motor acceleration (current drops as back-EMF builds)
    if t_ms < startup_time_ms:
        # Exponential decay from ~0.9*LRA to FLA
        progress = (t_ms - 100) / (startup_time_ms - 100)
        current = ac.lra * 0.9 * (1 - progress) + ac.running_amps * progress
        # Add some exponential character
        decay = np.exp(-3 * progress)
        return ac.lra * 0.9 * decay + ac.running_amps * (1 - decay)

    # Phase 4: Running
    return ac.running_amps


def motor_power_factor_profile(t_ms: float, ac: WindowACSpec,
                                startup_time_ms: float = 300) -> float:
    """
    Model power factor during startup.

    PF is very low during locked rotor (mostly magnetizing current),
    improves as motor reaches speed.
    """
    if t_ms < 0:
        return 0

    if t_ms < 50:
        # Initial surge - very low PF
        return ac.power_factor_locked

    if t_ms < startup_time_ms:
        # Gradual improvement
        progress = (t_ms - 50) / (startup_time_ms - 50)
        return ac.power_factor_locked + (ac.power_factor_running - ac.power_factor_locked) * progress

    return ac.power_factor_running


def calculate_power_demand(ac: WindowACSpec, gen: GeneratorSpec,
                           startup_time_ms: float = 300,
                           dt_ms: float = 1.0) -> dict:
    """
    Calculate power demand profile and energy requirements.
    """
    times = np.arange(0, 2000, dt_ms)  # 2 second simulation

    currents = []
    power_factors = []
    apparent_powers = []
    real_powers = []

    for t in times:
        i = motor_current_profile(t, ac, startup_time_ms)
        pf = motor_power_factor_profile(t, ac, startup_time_ms)

        currents.append(i)
        power_factors.append(pf)
        apparent_powers.append(i * 120)  # VA
        real_powers.append(i * 120 * pf)  # Watts

    currents = np.array(currents)
    power_factors = np.array(power_factors)
    apparent_powers = np.array(apparent_powers)
    real_powers = np.array(real_powers)

    # What the generator can provide
    gen_current_limit = np.minimum(currents, gen.max_amps)
    gen_power = gen_current_limit * 120 * power_factors

    # Current shortfall (what we need to supplement)
    current_shortfall = np.maximum(currents - gen.max_amps, 0)
    power_shortfall = current_shortfall * 120 * power_factors

    # Energy calculations
    dt_s = dt_ms / 1000

    # Total energy needed by motor in first 500ms
    mask_500 = times < 500
    energy_needed_500ms = np.sum(real_powers[mask_500]) * dt_s

    # Energy generator can provide in first 500ms
    energy_gen_500ms = np.sum(gen_power[mask_500]) * dt_s

    # Energy shortfall in first 500ms
    energy_shortfall_500ms = np.sum(power_shortfall[mask_500]) * dt_s

    # Same for 200ms window
    mask_200 = times < 200
    energy_shortfall_200ms = np.sum(power_shortfall[mask_200]) * dt_s

    # Peak values
    peak_current = np.max(currents)
    peak_power = np.max(real_powers)
    peak_shortfall_current = np.max(current_shortfall)
    peak_shortfall_power = np.max(power_shortfall)

    return {
        'times': times,
        'currents': currents,
        'power_factors': power_factors,
        'apparent_powers': apparent_powers,
        'real_powers': real_powers,
        'gen_power': gen_power,
        'current_shortfall': current_shortfall,
        'power_shortfall': power_shortfall,
        'peak_current': peak_current,
        'peak_power': peak_power,
        'peak_shortfall_current': peak_shortfall_current,
        'peak_shortfall_power': peak_shortfall_power,
        'energy_needed_500ms': energy_needed_500ms,
        'energy_gen_500ms': energy_gen_500ms,
        'energy_shortfall_500ms': energy_shortfall_500ms,
        'energy_shortfall_200ms': energy_shortfall_200ms,
        'ac': ac,
        'gen': gen,
        'startup_time_ms': startup_time_ms,
    }


def analyze_scenarios():
    """Analyze different window AC sizes with Honda EU1000i."""

    # Define window AC units
    ac_units = [
        WindowACSpec("5000 BTU", 5000, 450, 3.8),
        WindowACSpec("6000 BTU", 6000, 540, 4.5),
        WindowACSpec("8000 BTU", 8000, 720, 6.0),
        WindowACSpec("10000 BTU", 10000, 900, 7.5),
        WindowACSpec("12000 BTU", 12000, 1080, 9.0),
    ]

    # Honda EU1000i
    gen = GeneratorSpec("Honda EU1000i", 900, 1000)

    results = []
    for ac in ac_units:
        result = calculate_power_demand(ac, gen)
        results.append(result)

    return results


def plot_analysis(results: List[dict], save_path: str = None):
    """Plot comprehensive analysis."""

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('Window AC Startup Analysis with Honda EU1000i Generator',
                 fontsize=14, fontweight='bold')

    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(results)))

    # Plot 1: Current profiles
    ax1 = axes[0, 0]
    for i, r in enumerate(results):
        ax1.plot(r['times'], r['currents'], color=colors[i],
                linewidth=2, label=r['ac'].name)
    ax1.axhline(y=results[0]['gen'].max_amps, color='red', linestyle='--',
                linewidth=2, label=f"Generator limit ({results[0]['gen'].max_amps:.1f}A)")
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Current (A)')
    ax1.set_title('Motor Current Draw During Startup')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 800)

    # Plot 2: Real power profiles
    ax2 = axes[0, 1]
    for i, r in enumerate(results):
        ax2.plot(r['times'], r['real_powers'], color=colors[i], linewidth=2)
    ax2.axhline(y=results[0]['gen'].max_watts, color='red', linestyle='--',
                linewidth=2, label=f"Generator limit ({results[0]['gen'].max_watts:.0f}W)")
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Real Power (W)')
    ax2.set_title('Real Power Demand During Startup')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 800)

    # Plot 3: Current shortfall (what we need to provide)
    ax3 = axes[0, 2]
    for i, r in enumerate(results):
        ax3.fill_between(r['times'], 0, r['current_shortfall'],
                        color=colors[i], alpha=0.3)
        ax3.plot(r['times'], r['current_shortfall'], color=colors[i],
                linewidth=2, label=r['ac'].name)
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('Current Shortfall (A)')
    ax3.set_title('Current That Must Be Supplemented')
    ax3.legend(loc='upper right', fontsize=8)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 800)

    # Plot 4: Power shortfall
    ax4 = axes[1, 0]
    for i, r in enumerate(results):
        ax4.fill_between(r['times'], 0, r['power_shortfall'],
                        color=colors[i], alpha=0.3)
        ax4.plot(r['times'], r['power_shortfall'], color=colors[i], linewidth=2)
    ax4.set_xlabel('Time (ms)')
    ax4.set_ylabel('Power Shortfall (W)')
    ax4.set_title('Power That Must Be Supplemented')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 800)

    # Plot 5: Cumulative energy shortfall
    ax5 = axes[1, 1]
    for i, r in enumerate(results):
        energy_cum = np.cumsum(r['power_shortfall']) * 0.001  # dt = 1ms
        ax5.plot(r['times'], energy_cum, color=colors[i], linewidth=2,
                label=r['ac'].name)
    ax5.axhline(y=206, color='green', linestyle=':', linewidth=2,
                label='Our design: 206J')
    ax5.set_xlabel('Time (ms)')
    ax5.set_ylabel('Cumulative Energy (J)')
    ax5.set_title('Cumulative Energy Shortfall')
    ax5.legend(loc='upper left', fontsize=8)
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim(0, 800)

    # Plot 6: Summary table
    ax6 = axes[1, 2]
    ax6.axis('off')

    table_data = []
    for r in results:
        table_data.append([
            r['ac'].name,
            f"{r['ac'].running_amps:.1f}A",
            f"{r['ac'].lra:.0f}A",
            f"{r['peak_shortfall_current']:.0f}A",
            f"{r['peak_shortfall_power']:.0f}W",
            f"{r['energy_shortfall_200ms']:.0f}J",
            f"{r['energy_shortfall_500ms']:.0f}J",
        ])

    table = ax6.table(
        cellText=table_data,
        colLabels=['Unit', 'FLA', 'LRA', 'Peak\nShortfall', 'Peak P\nShortfall',
                   'E (200ms)', 'E (500ms)'],
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.6)
    ax6.set_title('Power Requirements Summary\n(With Honda EU1000i)', pad=20)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    return fig


def print_analysis(results: List[dict]):
    """Print detailed analysis."""

    gen = results[0]['gen']

    print("\n" + "=" * 100)
    print("WINDOW AC STARTUP ANALYSIS")
    print(f"Generator: {gen.name} ({gen.rated_watts}W rated, {gen.max_watts}W peak)")
    print("=" * 100)

    print(f"\n{'Unit':<12} {'FLA':>6} {'LRA':>6} {'Peak I':>8} {'Peak P':>8} "
          f"{'E@200ms':>10} {'E@500ms':>10} {'Can Start?':>12}")
    print("-" * 100)

    for r in results:
        ac = r['ac']

        # Can the generator + our 206J design start this?
        # Simple heuristic: if shortfall < 206J in 200ms, probably yes
        can_start = "YES" if r['energy_shortfall_200ms'] < 200 else "MARGINAL" if r['energy_shortfall_200ms'] < 300 else "NO"

        print(f"{ac.name:<12} {ac.running_amps:>5.1f}A {ac.lra:>5.0f}A "
              f"{r['peak_shortfall_current']:>7.0f}A {r['peak_shortfall_power']:>7.0f}W "
              f"{r['energy_shortfall_200ms']:>9.0f}J {r['energy_shortfall_500ms']:>9.0f}J "
              f"{can_start:>12}")

    print("=" * 100)

    print("\nKEY FINDINGS:")
    print("-" * 50)

    # Find the largest unit we can support
    for r in results:
        if r['energy_shortfall_200ms'] < 200:
            largest = r['ac'].name

    print(f"\nWith Honda EU1000i + our hybrid boost (206J in 200ms):")
    print(f"  - Can confidently start: up to {largest}")

    # Detailed breakdown for 8000 BTU
    r_8k = next(r for r in results if r['ac'].btu == 8000)
    print(f"\n8000 BTU Window AC detailed analysis:")
    print(f"  - Running power: {r_8k['ac'].running_watts:.0f}W ({r_8k['ac'].running_amps:.1f}A)")
    print(f"  - LRA: {r_8k['ac'].lra:.0f}A (peak current)")
    print(f"  - Peak current shortfall: {r_8k['peak_shortfall_current']:.0f}A")
    print(f"  - Peak power shortfall: {r_8k['peak_shortfall_power']:.0f}W")
    print(f"  - Energy needed (first 200ms): {r_8k['energy_shortfall_200ms']:.0f}J")
    print(f"  - Energy needed (first 500ms): {r_8k['energy_shortfall_500ms']:.0f}J")

    print(f"\nOur current design provides:")
    print(f"  - 206J in 200ms (16SC+56E, $224)")
    print(f"  - Peak power: ~1000W")
    print(f"  - Stacked voltage: 81.6V (32% AC coverage)")

    if r_8k['energy_shortfall_200ms'] > 206:
        deficit = r_8k['energy_shortfall_200ms'] - 206
        print(f"\n  *** WARNING: {deficit:.0f}J SHORT for 8000 BTU unit! ***")
        print(f"  Consider upgrading to 20SC+56E ($248, 235J) or adding more electrolytics")


def analyze_design_adequacy():
    """
    Check if our current design can handle the target loads.
    """
    print("\n" + "=" * 100)
    print("DESIGN ADEQUACY ANALYSIS")
    print("=" * 100)

    # Our design parameters
    design_energy_200ms = 206  # Joules
    design_peak_power = 1000   # Watts
    design_voltage = 81.6      # Volts (stacked)
    design_coverage = 0.32     # 32% of AC cycle
    design_max_current = 40    # Amps

    print(f"\nCurrent Design: 16SC + 56E")
    print(f"  Energy delivery: {design_energy_200ms}J in 200ms")
    print(f"  Peak power: {design_peak_power}W")
    print(f"  Stacked voltage: {design_voltage}V")
    print(f"  AC coverage: {design_coverage*100:.0f}%")
    print(f"  Max current: {design_max_current}A")

    # Calculate effective current contribution
    # Our device injects current during 32% of the AC cycle
    # The RMS equivalent contribution is lower

    # When we inject 40A peak during 32% of cycle:
    # Effective RMS contribution ≈ 40A * sqrt(0.32) ≈ 22.6A
    effective_current_rms = design_max_current * np.sqrt(design_coverage)

    print(f"\nEffective current contribution:")
    print(f"  Peak injection: {design_max_current}A")
    print(f"  Effective RMS: ~{effective_current_rms:.1f}A (due to {design_coverage*100:.0f}% coverage)")

    print("\nThis effective current is what the motor 'sees' as additional supply.")
    print("Combined with generator's 8.3A, total available: ~{:.1f}A".format(
        8.3 + effective_current_rms))

    return {
        'design_energy': design_energy_200ms,
        'design_power': design_peak_power,
        'effective_current': effective_current_rms,
    }


def main():
    print("Analyzing window AC startup requirements...")

    results = analyze_scenarios()
    print_analysis(results)

    analyze_design_adequacy()

    plot_analysis(results, save_path='motor_startup_analysis.png')
    # plt.show()  # Skip interactive display


if __name__ == '__main__':
    main()
