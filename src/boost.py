import numpy as np
import matplotlib.pyplot as plt


class BoostCircuitSimulation:
    def __init__(self):
        # System parameters
        self.VOLTAGE_RMS = 120  # Generator RMS voltage
        self.VOLTAGE_PEAK = self.VOLTAGE_RMS * np.sqrt(2)
        self.FREQUENCY = 60  # Hz
        self.PERIOD = 1 / self.FREQUENCY

        # Boost circuit parameters
        self.BATTERY_VOLTAGE = 12  # Battery voltage
        self.CAPACITOR_UF = 4700  # Capacitor size in µF
        self.CAPACITOR_F = self.CAPACITOR_UF * 1e-6  # Convert to Farads
        self.FET_RON = 0.01  # FET on-resistance in ohms

        # Load parameters (simplified AC motor model)
        self.LOAD_R = 10  # Load resistance in ohms

        # Timing parameters
        self.CHARGE_TIME = 0.002  # 2ms charging time
        self.ASSIST_WINDOW = 0.001  # 1ms assistance window
        self.ZERO_CROSS_THRESHOLD = 5  # Voltage threshold for assistance

        # Time array (2 cycles with high resolution)
        self.t = np.linspace(0, 2 * self.PERIOD, 10000)
        self.dt = self.t[1] - self.t[0]

    def calculate_waveforms(self):
        """Calculate all circuit waveforms"""
        # Initialize arrays
        v_gen = self.VOLTAGE_PEAK * np.sin(2 * np.pi * self.FREQUENCY * self.t)
        v_cap = np.zeros_like(self.t)
        v_assist = np.zeros_like(self.t)
        i_cap = np.zeros_like(self.t)
        u1_gate = np.zeros_like(self.t)  # FET U1 gate drive
        u2_gate = np.zeros_like(self.t)  # FET U2 gate drive

        # Initial capacitor voltage
        v_cap[0] = 0

        # Process each time step
        for i in range(1, len(self.t)):
            # Detect approaching zero crossing (positive slope)
            approaching_zero = (
                abs(v_gen[i]) < self.ZERO_CROSS_THRESHOLD and v_gen[i] > v_gen[i - 1]
            )

            # U1 control (charging FET)
            if (
                v_cap[i - 1] < self.BATTERY_VOLTAGE * 0.95
            ):  # Charge when below 95% of battery voltage
                u1_gate[i] = 1
                # Calculate charging current and new capacitor voltage
                i_cap[i] = (self.BATTERY_VOLTAGE - v_cap[i - 1]) / self.FET_RON
                v_cap[i] = v_cap[i - 1] + (i_cap[i] * self.dt) / self.CAPACITOR_F
            else:
                u1_gate[i] = 0
                v_cap[i] = v_cap[i - 1]  # Maintain voltage (ignoring leakage)

            # U2 control (boost FET)
            if approaching_zero:
                u2_gate[i] = 1
                # Apply boost voltage
                v_assist[i] = v_cap[i]
                # Calculate capacitor discharge
                i_cap[i] = -v_cap[i] / self.LOAD_R
                v_cap[i] = v_cap[i - 1] + (i_cap[i] * self.dt) / self.CAPACITOR_F
            else:
                u2_gate[i] = 0
                v_assist[i] = 0

        # Calculate combined voltage
        v_total = v_gen + v_assist

        return v_gen, v_cap, v_assist, v_total, u1_gate, u2_gate, i_cap

    def plot_waveforms(self):
        """Create visualization of all waveforms"""
        v_gen, v_cap, v_assist, v_total, u1_gate, u2_gate, i_cap = (
            self.calculate_waveforms()
        )

        # Create subplots
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 12))

        # Plot generator and total voltage
        ax1.plot(self.t * 1000, v_gen, "b-", label="Generator Voltage", alpha=0.5)
        ax1.plot(self.t * 1000, v_total, "g-", label="Combined Voltage")
        ax1.grid(True)
        ax1.set_ylabel("Voltage (V)")
        ax1.set_title("Generator and Combined Voltage")
        ax1.legend()

        # Plot capacitor voltage
        ax2.plot(self.t * 1000, v_cap, "r-", label="Capacitor Voltage")
        ax2.grid(True)
        ax2.set_ylabel("Voltage (V)")
        ax2.set_title("Capacitor Voltage")
        ax2.legend()

        # Plot FET gate drives
        ax3.plot(self.t * 1000, u1_gate * 12, "b-", label="U1 Gate (Charge)")
        ax3.plot(self.t * 1000, u2_gate * 12, "r-", label="U2 Gate (Boost)")
        ax3.grid(True)
        ax3.set_ylabel("Gate Drive (V)")
        ax3.set_title("FET Gate Drive Signals")
        ax3.legend()

        # Plot capacitor current
        ax4.plot(self.t * 1000, i_cap, "m-", label="Capacitor Current")
        ax4.grid(True)
        ax4.set_xlabel("Time (ms)")
        ax4.set_ylabel("Current (A)")
        ax4.set_title("Capacitor Current")
        ax4.legend()

        plt.tight_layout()
        plt.show()


# Create and run simulation
sim = BoostCircuitSimulation()
sim.plot_waveforms()
