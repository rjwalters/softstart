import numpy as np
import matplotlib.pyplot as plt


class HybridPowerSimulation:
    def __init__(self, battery_voltage=12, pwm_frequency=100000):
        # Generator parameters
        self.VOLTAGE_RMS = 120  # RMS voltage
        self.VOLTAGE_PEAK = self.VOLTAGE_RMS * np.sqrt(2)  # Peak voltage
        self.FREQUENCY = 60  # Hz
        self.PERIOD = 1 / self.FREQUENCY  # seconds
        self.BATTERY_VOLTAGE = battery_voltage

        # PWM parameters
        self.PWM_FREQUENCY = pwm_frequency  # Hz (100kHz)
        self.PWM_PERIOD = 1 / self.PWM_FREQUENCY  # seconds

        # Capacitor parameters
        self.TAU = self.PWM_PERIOD  # Faster time constant for better tracking

        # Time array for simulation (2 cycles with very high resolution for PWM)
        samples_per_pwm = 20  # Number of samples per PWM cycle
        total_time = 2 * self.PERIOD  # 2 cycles of generator
        num_samples = int(total_time * self.PWM_FREQUENCY * samples_per_pwm)
        self.t = np.linspace(0, total_time, num_samples)

    def calculate_duty_cycle(self, target_voltage, t):
        """Calculate PWM duty cycle with enhanced control near zero crossing"""
        if abs(target_voltage) <= self.BATTERY_VOLTAGE:
            # Basic duty cycle
            basic_duty = abs(target_voltage) / self.BATTERY_VOLTAGE

            # Enhanced control near zero crossing
            # Add slight boost for better tracking
            zero_crossing_factor = np.exp(-abs(target_voltage) / 2)
            enhanced_duty = basic_duty * (1 + 0.1 * zero_crossing_factor)

            return min(enhanced_duty, 1.0)  # Ensure duty cycle doesn't exceed 1
        return 1.0

    def calculate_waveforms(self):
        """Calculate generator and PWM battery waveforms"""
        # Generator ideal voltage
        v_gen = self.VOLTAGE_PEAK * np.sin(2 * np.pi * self.FREQUENCY * self.t)

        # Initialize PWM and smoothed battery voltages
        v_pwm = np.zeros_like(self.t)
        v_smooth = np.zeros_like(self.t)

        # Calculate PWM waveform
        for i, t in enumerate(self.t):
            # Only apply battery when generator voltage is between -12V and +12V
            if abs(v_gen[i]) <= self.BATTERY_VOLTAGE:
                # Determine target voltage (match generator voltage in this range)
                target_voltage = v_gen[i]

                # Calculate duty cycle with enhanced control
                duty_cycle = self.calculate_duty_cycle(target_voltage, t)

                # Determine PWM polarity based on target voltage
                polarity = np.sign(target_voltage) if target_voltage != 0 else 1

                # Generate PWM pulse
                pwm_phase = (t % self.PWM_PERIOD) / self.PWM_PERIOD
                v_pwm[i] = (
                    self.BATTERY_VOLTAGE * polarity if pwm_phase < duty_cycle else 0
                )

        # Simulate capacitor smoothing using simple low-pass filter
        dt = self.t[1] - self.t[0]
        alpha = dt / (self.TAU + dt)
        v_smooth[0] = v_pwm[0]
        for i in range(1, len(self.t)):
            v_smooth[i] = alpha * v_pwm[i] + (1 - alpha) * v_smooth[i - 1]

        return v_gen, v_pwm, v_smooth

    def plot_waveforms(self):
        """Create plots of voltage waveforms"""
        v_gen, v_pwm, v_smooth = self.calculate_waveforms()

        # Create subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Plot full timespan
        ax1.plot(self.t * 1000, v_gen, "b-", label="Generator Voltage", alpha=0.7)
        ax1.plot(
            self.t * 1000, v_smooth, "r-", label="Smoothed Battery Voltage", linewidth=2
        )
        ax1.axhline(y=self.BATTERY_VOLTAGE, color="r", linestyle="--", alpha=0.3)
        ax1.axhline(y=-self.BATTERY_VOLTAGE, color="r", linestyle="--", alpha=0.3)
        ax1.axhline(y=0, color="k", linestyle="-", alpha=0.3)
        ax1.grid(True)
        ax1.set_xlabel("Time (ms)")
        ax1.set_ylabel("Voltage (V)")
        ax1.set_title("Generator and Smoothed Battery Voltages")
        ax1.legend()

        # Plot zoomed section around zero crossing
        # Find a zero crossing
        zero_crossings = np.where(np.diff(np.signbit(v_gen)))[0]
        if len(zero_crossings) > 0:
            zoom_center = zero_crossings[0]
            zoom_range = int(len(self.t) * 0.001)  # Show 0.1% of the waveform
            zoom_start = max(0, zoom_center - zoom_range)
            zoom_end = min(len(self.t), zoom_center + zoom_range)

            t_zoom = self.t[zoom_start:zoom_end] * 1000
            v_gen_zoom = v_gen[zoom_start:zoom_end]
            v_pwm_zoom = v_pwm[zoom_start:zoom_end]
            v_smooth_zoom = v_smooth[zoom_start:zoom_end]

            ax2.plot(t_zoom, v_gen_zoom, "b-", label="Generator Voltage", alpha=0.7)
            ax2.plot(
                t_zoom,
                v_pwm_zoom,
                "g-",
                label="PWM Battery Voltage",
                linewidth=1,
                alpha=0.5,
            )
            ax2.plot(
                t_zoom,
                v_smooth_zoom,
                "r-",
                label="Smoothed Battery Voltage",
                linewidth=2,
            )
            ax2.grid(True)
            ax2.set_xlabel("Time (ms)")
            ax2.set_ylabel("Voltage (V)")
            ax2.set_title("Zoomed View Around Zero Crossing")
            ax2.legend()

        plt.tight_layout()
        plt.show()


# Example usage
sim = HybridPowerSimulation(battery_voltage=12, pwm_frequency=100000)
sim.plot_waveforms()
