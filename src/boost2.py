import numpy as np
import matplotlib.pyplot as plt


class DualBoostCircuitSimulation:
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

        # Charge pump parameters
        self.PUMP_FREQUENCY = 20000  # 20 kHz charge pump frequency
        self.PUMP_EFFICIENCY = 0.85  # Charge pump efficiency

        # Load parameters
        self.LOAD_R = 10  # Load resistance in ohms

        # Timing parameters
        self.CHARGE_TIME = 0.002  # 2ms charging time
        self.ASSIST_WINDOW = 0.001  # 1ms assistance window
        self.ZERO_CROSS_THRESHOLD = 5  # Voltage threshold for assistance

        # Time array (2 cycles with high resolution)
        self.t = np.linspace(0, 2 * self.PERIOD, 20000)  # Increased resolution
        self.dt = self.t[1] - self.t[0]

    def calculate_waveforms(self):
        """Calculate all circuit waveforms"""
        # Initialize arrays
        v_gen = self.VOLTAGE_PEAK * np.sin(2 * np.pi * self.FREQUENCY * self.t)
        v_cap1 = np.zeros_like(self.t)  # 12V capacitor bank
        v_cap2 = np.zeros_like(self.t)  # 24V capacitor bank
        v_assist = np.zeros_like(self.t)
        i_cap1 = np.zeros_like(self.t)
        i_cap2 = np.zeros_like(self.t)
        u1_gate = np.zeros_like(self.t)  # FET U1 gate drive (12V charging)
        u2_gate = np.zeros_like(self.t)  # FET U2 gate drive (12V boost)
        u3_gate = np.zeros_like(self.t)  # FET U3 gate drive (24V boost)

        # Initial capacitor voltages
        v_cap1[0] = 0
        v_cap2[0] = 0

        # Process each time step
        for i in range(1, len(self.t)):
            # Calculate generator voltage slope
            slope = (v_gen[i] - v_gen[i - 1]) / self.dt

            # U1 control (charging 12V bank)
            if v_cap1[i - 1] < self.BATTERY_VOLTAGE * 0.95:
                u1_gate[i] = 1
                i_cap1[i] = (self.BATTERY_VOLTAGE - v_cap1[i - 1]) / self.FET_RON
                v_cap1[i] = v_cap1[i - 1] + (i_cap1[i] * self.dt) / self.CAPACITOR_F
            else:
                u1_gate[i] = 0
                v_cap1[i] = v_cap1[i - 1]

            # Charge pump control (24V bank)
            if (
                v_cap1[i] > self.BATTERY_VOLTAGE * 0.9
                and v_cap2[i - 1] < self.BATTERY_VOLTAGE * 1.9
            ):
                # Simulate charge pump action
                pump_current = (
                    self.BATTERY_VOLTAGE * self.PUMP_EFFICIENCY
                ) / self.FET_RON
                v_cap2[i] = v_cap2[i - 1] + (pump_current * self.dt) / self.CAPACITOR_F
                i_cap2[i] = pump_current
            else:
                v_cap2[i] = v_cap2[i - 1]
                i_cap2[i] = 0

            # Boost control logic
            if abs(v_gen[i]) < self.ZERO_CROSS_THRESHOLD:
                if abs(slope) > 0:  # Determine which boost level to use
                    if abs(slope) > 1000:  # High slope - use 24V boost
                        u3_gate[i] = 1
                        u2_gate[i] = 0
                        v_assist[i] = v_cap2[i] * np.sign(slope)
                        # Discharge 24V cap
                        i_cap2[i] = -v_cap2[i] / self.LOAD_R
                        v_cap2[i] += (i_cap2[i] * self.dt) / self.CAPACITOR_F
                    else:  # Lower slope - use 12V boost
                        u2_gate[i] = 1
                        u3_gate[i] = 0
                        v_assist[i] = v_cap1[i] * np.sign(slope)
                        # Discharge 12V cap
                        i_cap1[i] = -v_cap1[i] / self.LOAD_R
                        v_cap1[i] += (i_cap1[i] * self.dt) / self.CAPACITOR_F
            else:
                u2_gate[i] = 0
                u3_gate[i] = 0
                v_assist[i] = 0

        # Calculate combined voltage
        v_total = v_gen + v_assist

        return (
            v_gen,
            v_cap1,
            v_cap2,
            v_assist,
            v_total,
            u1_gate,
            u2_gate,
            u3_gate,
            i_cap1,
            i_cap2,
        )

    def plot_waveforms(self):
        """Create visualization of all waveforms"""
        (
            v_gen,
            v_cap1,
            v_cap2,
            v_assist,
            v_total,
            u1_gate,
            u2_gate,
            u3_gate,
            i_cap1,
            i_cap2,
        ) = self.calculate_waveforms()

        # Create subplots
        fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(12, 15))

        # Plot generator and total voltage
        ax1.plot(self.t * 1000, v_gen, "b-", label="Generator Voltage", alpha=0.5)
        ax1.plot(self.t * 1000, v_total, "g-", label="Combined Voltage")
        ax1.grid(True)
        ax1.set_ylabel("Voltage (V)")
        ax1.set_title("Generator and Combined Voltage")
        ax1.legend()

        # Plot capacitor voltages
        ax2.plot(self.t * 1000, v_cap1, "r-", label="12V Bank")
        ax2.plot(self.t * 1000, v_cap2, "b-", label="24V Bank")
        ax2.grid(True)
        ax2.set_ylabel("Voltage (V)")
        ax2.set_title("Capacitor Bank Voltages")
        ax2.legend()

        # Plot assist voltage
        ax3.plot(self.t * 1000, v_assist, "m-", label="Assist Voltage")
        ax3.grid(True)
        ax3.set_ylabel("Voltage (V)")
        ax3.set_title("Combined Assist Voltage")
        ax3.legend()

        # Plot FET gate drives
        ax4.plot(self.t * 1000, u1_gate * 12, "b-", label="U1 Gate (Charge)")
        ax4.plot(self.t * 1000, u2_gate * 12, "r-", label="U2 Gate (12V Boost)")
        ax4.plot(self.t * 1000, u3_gate * 12, "g-", label="U3 Gate (24V Boost)")
        ax4.grid(True)
        ax4.set_ylabel("Gate Drive (V)")
        ax4.set_title("FET Gate Drive Signals")
        ax4.legend()

        # Plot capacitor currents
        ax5.plot(self.t * 1000, i_cap1, "r-", label="12V Bank Current")
        ax5.plot(self.t * 1000, i_cap2, "b-", label="24V Bank Current")
        ax5.grid(True)
        ax5.set_xlabel("Time (ms)")
        ax5.set_ylabel("Current (A)")
        ax5.set_title("Capacitor Bank Currents")
        ax5.legend()

        plt.tight_layout()
        plt.show()


# Create and run simulation
sim = DualBoostCircuitSimulation()
sim.plot_waveforms()
