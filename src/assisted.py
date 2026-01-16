import numpy as np
import matplotlib.pyplot as plt


class VoltageAssistSimulation:
    def __init__(self):
        # System parameters
        self.VOLTAGE_RMS = 120  # Generator RMS voltage
        self.VOLTAGE_PEAK = self.VOLTAGE_RMS * np.sqrt(2)
        self.FREQUENCY = 60  # Hz
        self.PERIOD = 1 / self.FREQUENCY
        self.ASSIST_VOLTAGE = 12  # Voltage assistance level

        # PWM parameters
        self.PWM_FREQ = 20000  # 20 kHz PWM frequency
        self.PWM_PERIOD = 1 / self.PWM_FREQ

        # Zero crossing parameters
        self.ZERO_CROSS_THRESHOLD = 5  # Voltage threshold for assistance
        self.ZERO_CROSS_WINDOW = 0.0005  # Time window around zero crossing (500µs)

        # Time array (3 cycles with high resolution for PWM)
        self.t = np.linspace(0, 3 * self.PERIOD, 10000)

    def generate_pwm(self, t, duty_cycle, polarity):
        """Generate PWM signal with given duty cycle and polarity"""
        # Calculate number of PWM periods elapsed
        pwm_periods = t / self.PWM_PERIOD
        # Calculate position within current PWM period
        pwm_position = (pwm_periods - np.floor(pwm_periods)) * self.PWM_PERIOD
        # Generate PWM pulse
        pwm = (pwm_position < (duty_cycle * self.PWM_PERIOD)).astype(float)
        return pwm * self.ASSIST_VOLTAGE * polarity

    def calculate_duty_cycle(self, voltage):
        """Calculate PWM duty cycle based on instantaneous voltage"""
        # Simple linear duty cycle based on proximity to zero
        return max(0, 1 - abs(voltage) / self.ZERO_CROSS_THRESHOLD)

    def calculate_waveforms(self):
        """Calculate all system waveforms"""
        # Generate base generator voltage
        v_gen = self.VOLTAGE_PEAK * np.sin(2 * np.pi * self.FREQUENCY * self.t)

        # Initialize assist voltage array
        v_assist = np.zeros_like(self.t)

        # Calculate assist voltage for each time point
        for i, t_val in enumerate(self.t):
            # Determine if we're near a zero crossing
            if abs(v_gen[i]) < self.ZERO_CROSS_THRESHOLD:
                # Calculate duty cycle
                duty_cycle = self.calculate_duty_cycle(v_gen[i])
                # Determine polarity based on voltage slope
                if i > 0:
                    polarity = 1 if v_gen[i] > v_gen[i - 1] else -1
                else:
                    polarity = 1
                # Generate PWM pulse
                v_assist[i] = self.generate_pwm(t_val, duty_cycle, polarity)

        # Calculate combined voltage
        v_total = v_gen + v_assist

        return v_gen, v_assist, v_total

    def plot_waveforms(self):
        """Create visualization of all waveforms"""
        v_gen, v_assist, v_total = self.calculate_waveforms()

        # Create subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

        # Plot generator voltage
        ax1.plot(self.t * 1000, v_gen, "b-", label="Generator Voltage")
        ax1.grid(True)
        ax1.set_ylabel("Voltage (V)")
        ax1.set_title("Generator Output Voltage")
        ax1.legend()

        # Plot assist voltage
        ax2.plot(self.t * 1000, v_assist, "r-", label="Assist Voltage")
        ax2.grid(True)
        ax2.set_ylabel("Voltage (V)")
        ax2.set_title("PWM Assist Voltage")
        ax2.legend()

        # Plot combined voltage
        ax3.plot(self.t * 1000, v_total, "g-", label="Combined Voltage")
        ax3.plot(self.t * 1000, v_gen, "b--", alpha=0.5, label="Original Voltage")
        ax3.grid(True)
        ax3.set_xlabel("Time (ms)")
        ax3.set_ylabel("Voltage (V)")
        ax3.set_title("Combined Output Voltage")
        ax3.legend()

        plt.tight_layout()
        plt.show()

    def plot_detail_view(self, start_ms=8.0, duration_ms=2.0):
        """Create detailed view around a zero crossing"""
        v_gen, v_assist, v_total = self.calculate_waveforms()

        # Calculate array indices for the detail window
        start_idx = int(start_ms * 1e-3 / (self.t[1] - self.t[0]))
        end_idx = int((start_ms + duration_ms) * 1e-3 / (self.t[1] - self.t[0]))

        # Create detail plot
        plt.figure(figsize=(12, 6))
        plt.plot(
            self.t[start_idx:end_idx] * 1000,
            v_gen[start_idx:end_idx],
            "b-",
            label="Generator Voltage",
        )
        plt.plot(
            self.t[start_idx:end_idx] * 1000,
            v_assist[start_idx:end_idx],
            "r-",
            label="Assist Voltage",
        )
        plt.plot(
            self.t[start_idx:end_idx] * 1000,
            v_total[start_idx:end_idx],
            "g-",
            label="Combined Voltage",
        )
        plt.grid(True)
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage (V)")
        plt.title(
            f"Detailed View of Zero Crossing ({start_ms}-{start_ms+duration_ms}ms)"
        )
        plt.legend()
        plt.show()


# Create and run simulation
sim = VoltageAssistSimulation()

# Show overall waveforms
sim.plot_waveforms()

# Show detailed view around a zero crossing
sim.plot_detail_view(start_ms=8.0, duration_ms=2.0)
