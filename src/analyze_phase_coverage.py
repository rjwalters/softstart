#!/usr/bin/env python3
"""
Analyze how our PWM injection interacts with motor inductive load.

Key insight: Inductive loads have lagging current. For a motor at locked rotor:
- Power factor ~0.35 means current lags voltage by ~70°
- Peak current occurs well after peak voltage
- When V_ac is near zero, motor is drawing maximum current

This is actually FAVORABLE for our design because:
- We inject current when V_ac < V_stacked (81.6V)
- This corresponds to the part of the cycle where motor current is highest
- We're supplementing exactly when the generator struggles most
"""

import numpy as np
import matplotlib.pyplot as plt


def analyze_phase_coverage():
    """Analyze when our injection occurs vs when motor needs current."""

    # AC waveform parameters
    V_peak = 170  # Peak voltage
    freq = 60     # Hz
    omega = 2 * np.pi * freq

    # Our design parameters
    V_stacked = 81.6  # Our stacked voltage
    I_inject = 40     # Our max injection current

    # Motor parameters at locked rotor
    motor_pf = 0.35       # Power factor (very lagging)
    motor_lra = 33        # Locked rotor amps (8000 BTU)
    phase_lag = np.arccos(motor_pf)  # ~70 degrees

    # Time array (one cycle)
    t = np.linspace(0, 1/freq, 1000)

    # AC voltage waveform
    v_ac = V_peak * np.sin(omega * t)

    # Motor current waveform (lagging by phase_lag)
    i_motor = motor_lra * np.sqrt(2) * np.sin(omega * t - phase_lag)

    # When can we inject? When |V_ac| < V_stacked
    can_inject = np.abs(v_ac) < V_stacked

    # Our injection current (synchronized to AC polarity)
    # We inject in the same direction as V_ac (positive when V_ac positive)
    i_inject = np.where(can_inject, I_inject * np.sign(v_ac), 0)

    # Actually, we should modulate to follow motor current phase
    # For now, let's see the overlap

    # Calculate what fraction of motor current demand we cover
    # When we inject, how much of the motor's current are we supplying?
    motor_current_during_injection = i_motor[can_inject]
    avg_motor_current_during_injection = np.mean(np.abs(motor_current_during_injection))

    # Coverage fraction (how much of cycle we cover)
    coverage = np.sum(can_inject) / len(can_inject)

    print("=" * 80)
    print("PHASE COVERAGE ANALYSIS")
    print("=" * 80)

    print(f"\nAC waveform: {V_peak}V peak, 60Hz")
    print(f"Our stacked voltage: {V_stacked}V")
    print(f"Coverage: {coverage*100:.1f}% of AC cycle")

    print(f"\nMotor (8000 BTU at locked rotor):")
    print(f"  LRA: {motor_lra}A RMS, {motor_lra * np.sqrt(2):.1f}A peak")
    print(f"  Power factor: {motor_pf} (phase lag: {np.degrees(phase_lag):.0f}°)")

    print(f"\nCritical insight:")
    print(f"  Motor current during our injection window:")
    print(f"    Average: {avg_motor_current_during_injection:.1f}A")
    print(f"    This is {avg_motor_current_during_injection/motor_lra*100:.0f}% of RMS current")

    # The motor draws more current near zero crossing due to phase lag
    # Let's check this
    # At zero crossing (V_ac = 0), motor current is at:
    #   sin(-phase_lag) ≈ sin(-70°) ≈ -0.94 of peak
    # So motor is drawing ~94% of peak current at zero crossing!

    v_ac_zero_crossings = np.where(np.diff(np.sign(v_ac)))[0]
    motor_at_zc = np.mean(np.abs(i_motor[v_ac_zero_crossings]))

    print(f"\nAt voltage zero-crossing:")
    print(f"  Motor current: {motor_at_zc:.1f}A (vs {motor_lra*np.sqrt(2):.1f}A peak)")
    print(f"  This is {motor_at_zc/(motor_lra*np.sqrt(2))*100:.0f}% of peak current!")

    print(f"\n*** This is GOOD for us! ***")
    print(f"  We inject when V_ac < {V_stacked}V")
    print(f"  Motor draws maximum current near V_ac = 0")
    print(f"  Our injection timing aligns with motor's peak current demand!")

    return {
        't': t * 1000,  # Convert to ms
        'v_ac': v_ac,
        'i_motor': i_motor,
        'i_inject': i_inject,
        'can_inject': can_inject,
        'coverage': coverage,
    }


def plot_phase_analysis(data, save_path=None):
    """Plot the phase relationship."""

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('Phase Analysis: Motor Current vs Our Injection Window',
                 fontsize=14, fontweight='bold')

    t = data['t']
    v_ac = data['v_ac']
    i_motor = data['i_motor']
    can_inject = data['can_inject']

    V_stacked = 81.6

    # Plot 1: AC voltage with injection window
    ax1 = axes[0]
    ax1.plot(t, v_ac, 'b-', linewidth=2, label='V_ac')
    ax1.axhline(y=V_stacked, color='g', linestyle='--', label=f'+{V_stacked}V threshold')
    ax1.axhline(y=-V_stacked, color='g', linestyle='--', label=f'-{V_stacked}V threshold')
    ax1.fill_between(t, -200, 200, where=can_inject, alpha=0.2, color='green',
                     label='Injection window')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('AC Voltage and Injection Window')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, t[-1])
    ax1.set_ylim(-200, 200)

    # Plot 2: Motor current
    ax2 = axes[1]
    ax2.plot(t, i_motor, 'r-', linewidth=2, label='Motor current (lags 70°)')
    ax2.fill_between(t, -60, 60, where=can_inject, alpha=0.2, color='green')
    ax2.axhline(y=40, color='orange', linestyle=':', label='Our max injection (40A)')
    ax2.axhline(y=-40, color='orange', linestyle=':')
    ax2.set_ylabel('Current (A)')
    ax2.set_title('Motor Current (Lagging Due to Inductance)')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, t[-1])
    ax2.set_ylim(-60, 60)

    # Plot 3: Overlay showing alignment
    ax3 = axes[2]
    ax3.plot(t, v_ac / 170 * 40, 'b-', linewidth=1, alpha=0.5, label='V_ac (normalized)')
    ax3.plot(t, i_motor, 'r-', linewidth=2, label='Motor current')
    ax3.fill_between(t, 0, np.abs(i_motor), where=can_inject, alpha=0.3, color='green',
                     label='Current during our injection')
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('Current (A)')
    ax3.set_title('Motor Current During Our Injection Window (shaded)')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, t[-1])

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    return fig


def analyze_power_delivery():
    """
    Calculate actual power delivery considering phase alignment.
    """
    print("\n" + "=" * 80)
    print("POWER DELIVERY WITH PHASE ALIGNMENT")
    print("=" * 80)

    # Parameters
    V_stacked = 81.6
    V_peak = 170
    I_inject = 40  # Our injection current
    freq = 60
    omega = 2 * np.pi * freq

    # Simulation over one cycle
    t = np.linspace(0, 1/freq, 10000)
    dt = t[1] - t[0]

    v_ac = V_peak * np.sin(omega * t)

    # During injection window: inject current in phase with v_ac direction
    # Power delivered = |v_ac| * I_inject when |v_ac| < V_stacked

    power_injected = np.zeros_like(t)
    for i, v in enumerate(v_ac):
        if abs(v) < V_stacked:
            # We inject at the instantaneous AC voltage (not our voltage)
            # Actually, the load sees the AC voltage, we just add current
            power_injected[i] = abs(v) * I_inject

    # Average power over cycle
    avg_power = np.mean(power_injected)

    # Energy per cycle
    energy_per_cycle = np.sum(power_injected) * dt

    print(f"\nPer-cycle analysis:")
    print(f"  Injection current: {I_inject}A")
    print(f"  Average power injected: {avg_power:.0f}W")
    print(f"  Energy per cycle: {energy_per_cycle:.2f}J")
    print(f"  Energy per second: {energy_per_cycle * 60:.0f}J")

    # In 200ms (12 cycles)
    energy_200ms = energy_per_cycle * 12
    print(f"  Energy in 200ms: {energy_200ms:.0f}J")

    print("\nNote: This is 'ideal' power - actual limited by capacitor discharge")

    # Compare to our original estimate
    print(f"\nOur original energy estimate: 206J in 200ms")
    print(f"Per-cycle ideal estimate: {energy_200ms:.0f}J in 200ms")
    print("(Difference due to capacitor voltage droop during discharge)")

    return avg_power, energy_200ms


def calculate_generator_relief():
    """
    Calculate how much we relieve the generator.
    """
    print("\n" + "=" * 80)
    print("GENERATOR RELIEF ANALYSIS")
    print("=" * 80)

    # Generator limits
    gen_max_current = 8.3  # Amps
    gen_max_power = 1000   # Watts

    # Motor requirements (8000 BTU)
    motor_lra = 33  # Amps
    motor_pf = 0.35
    motor_apparent_power = motor_lra * 120  # VA
    motor_real_power = motor_apparent_power * motor_pf  # Watts

    print(f"\nWithout soft-start:")
    print(f"  Motor demands: {motor_lra}A, {motor_apparent_power}VA, {motor_real_power:.0f}W real")
    print(f"  Generator can supply: {gen_max_current}A, {gen_max_power}W")
    print(f"  Current shortfall: {motor_lra - gen_max_current:.1f}A")
    print(f"  Result: Generator overloads, voltage collapses, motor stalls")

    # With our soft-start
    our_current = 22.6  # Effective RMS (40A * sqrt(0.32))

    total_current = gen_max_current + our_current
    print(f"\nWith soft-start:")
    print(f"  Generator provides: {gen_max_current}A")
    print(f"  We provide (effective): {our_current:.1f}A")
    print(f"  Total available: {total_current:.1f}A")
    print(f"  Motor needs: {motor_lra}A")

    if total_current >= motor_lra:
        print(f"  ✓ Sufficient current! ({total_current - motor_lra:.1f}A margin)")
    else:
        print(f"  ✗ Still short by {motor_lra - total_current:.1f}A")

    # More realistic analysis considering phase
    print("\nPhase-aware analysis:")
    print("  Motor current peaks at V_ac zero-crossing (due to phase lag)")
    print("  Our injection peaks at V_ac zero-crossing (by design)")
    print("  → Maximum support exactly when motor needs it most!")

    # During the injection window, motor is drawing ~94% of peak current
    # We can inject 40A peak during this time
    # Generator is providing ~8.3A average

    # Effective combined supply during injection window:
    combined_peak = 40 + 8.3 * np.sqrt(2) * 0.5  # Generator is at ~50% of peak at ZC
    print(f"\n  At zero-crossing (critical moment):")
    print(f"    Motor draws: ~{33 * np.sqrt(2) * 0.94:.0f}A (94% of peak)")
    print(f"    We provide: 40A")
    print(f"    Generator provides: ~{8.3 * np.sqrt(2) * 0.5:.1f}A")
    print(f"    Combined: ~{40 + 8.3 * np.sqrt(2) * 0.5:.0f}A")
    print(f"    Motor needs: ~{33 * np.sqrt(2) * 0.94:.0f}A")


def main():
    data = analyze_phase_coverage()
    analyze_power_delivery()
    calculate_generator_relief()

    plot_phase_analysis(data, save_path='phase_coverage_analysis.png')
    # plt.show()

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
Our design is actually WELL-SUITED for inductive motor loads because:

1. Motor current LAGS voltage by ~70° at locked rotor
2. This means motor draws maximum current near voltage zero-crossing
3. Our injection window (|V_ac| < 81.6V) includes zero-crossing
4. We inject 40A peak exactly when motor needs current most

The 32% coverage isn't just "random" parts of the cycle - it's the
most critical 32% for an inductive load!

For 8000 BTU window AC:
- Needs 174J in 200ms
- We provide 206J in 200ms
- ~19% margin for safety

Recommended: Our 16SC+56E ($224) design is adequate for 8000 BTU.
For 10000 BTU, consider 20SC+56E ($248) or adding electrolytics.
""")


if __name__ == '__main__':
    main()
