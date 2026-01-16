import numpy as np
import matplotlib.pyplot as plt


class GeneratorSimulation:
    def __init__(self, motor_start_ms=16.67):  # Default to ~1 cycle (16.67ms)
        # Generator parameters
        self.VOLTAGE_RMS = 120  # RMS voltage
        self.VOLTAGE_PEAK = self.VOLTAGE_RMS * np.sqrt(2)  # Peak voltage
        self.FREQUENCY = 60  # Hz
        self.PERIOD = 1 / self.FREQUENCY  # seconds

        # Modified motor parameters for higher loading
        self.MOTOR_L = 0.05  # Reduced inductance (H) to allow higher initial current
        self.MOTOR_R = 2.0  # Reduced resistance (Ohms) to draw more current
        self.MOTOR_STARTUP_MULTIPLIER = 8  # Increased inrush multiplier

        # Modified generator parameters to show more voltage drop
        self.GEN_INTERNAL_R = 5.0  # Increased internal resistance (Ohms)

        # Motor start time (convert from ms to seconds)
        self.MOTOR_START_TIME = motor_start_ms / 1000.0

        # Time array for simulation (5 cycles)
        self.t = np.linspace(0, 5 * self.PERIOD, 1000)

    def calculate_motor_impedance(self, t_since_start):
        """Calculate time-varying motor impedance during startup"""
        # Modified startup characteristics
        startup_decay = np.exp(-t_since_start / 0.1)  # Longer time constant (100ms)

        # More dramatic resistance change during startup
        effective_R = self.MOTOR_R * (1 + 7 * (1 - startup_decay))

        # Calculate inductive reactance
        XL = 2 * np.pi * self.FREQUENCY * self.MOTOR_L

        # During startup, reduce effective impedance to simulate higher inrush
        startup_factor = 1 - 0.8 * startup_decay  # More pronounced effect

        return (effective_R + XL * 1j) * startup_factor

    def calculate_waveforms(self):
        """Calculate voltage and current waveforms"""
        # Generator ideal voltage
        v_gen_ideal = self.VOLTAGE_PEAK * np.sin(2 * np.pi * self.FREQUENCY * self.t)

        # Initialize arrays
        v_gen_loaded = np.zeros_like(self.t, dtype=complex)
        i_motor = np.zeros_like(self.t, dtype=complex)

        # Calculate for each time point
        for i, t_val in enumerate(self.t):
            if t_val < self.MOTOR_START_TIME:  # Before motor start
                v_gen_loaded[i] = v_gen_ideal[i]
                i_motor[i] = 0
            else:
                # Calculate motor impedance at this point
                t_since_start = t_val - self.MOTOR_START_TIME
                Z_motor = self.calculate_motor_impedance(t_since_start)

                # Calculate current and voltage with load
                v_instantaneous = v_gen_ideal[i]
                i_motor[i] = v_instantaneous / (Z_motor + self.GEN_INTERNAL_R)
                v_gen_loaded[i] = v_instantaneous - i_motor[i] * self.GEN_INTERNAL_R

        return v_gen_ideal, np.real(v_gen_loaded), np.real(i_motor)

    def plot_waveforms(self):
        """Create plots of voltage and current waveforms"""
        v_gen_ideal, v_gen_loaded, i_motor = self.calculate_waveforms()

        # Create subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Plot voltages
        ax1.plot(
            self.t * 1000, v_gen_ideal, "b-", label="Ideal Generator Voltage", alpha=0.5
        )
        ax1.plot(self.t * 1000, v_gen_loaded, "r-", label="Loaded Generator Voltage")
        ax1.grid(True)
        ax1.set_xlabel("Time (ms)")
        ax1.set_ylabel("Voltage (V)")
        ax1.set_title("Generator Voltage Waveforms")
        ax1.axhline(y=0, color="k", linestyle="-", alpha=0.3)
        ax1.axvline(
            x=self.MOTOR_START_TIME * 1000,
            color="g",
            linestyle="--",
            label=f"Motor Start ({self.MOTOR_START_TIME*1000:.1f}ms)",
        )
        ax1.legend()

        # Plot current
        ax2.plot(self.t * 1000, i_motor, "g-", label="Motor Current")
        ax2.grid(True)
        ax2.set_xlabel("Time (ms)")
        ax2.set_ylabel("Current (A)")
        ax2.set_title("Motor Current Waveform")
        ax2.axhline(y=0, color="k", linestyle="-", alpha=0.3)
        ax2.axvline(
            x=self.MOTOR_START_TIME * 1000,
            color="g",
            linestyle="--",
            label=f"Motor Start ({self.MOTOR_START_TIME*1000:.1f}ms)",
        )
        ax2.legend()

        plt.tight_layout()
        plt.show()


# Example usage
sim = GeneratorSimulation(motor_start_ms=25)
sim.plot_waveforms()
