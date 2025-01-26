#libraries
from board import A1, GP20, GP21, GP22, GP28
from digitalio import DigitalInOut, Direction # Button and DigitalInOut handling
from analogio import AnalogIn # Analog input for sensor
from neopixel import NeoPixel # for LED light feedback
from time import monotonic as now # For timestamps

# Configuration
debounce_time = 0.05  # Debounce time for buttons to ensure stable readings
buffer_size = 10  # Number of data points before writing to file
adc_interval = 0.05  # Minimum time between sensor readings

# Button Class
class Button:
    def __init__(self, pin, interval):
        self.input = DigitalInOut(pin)
        self.input.direction = Direction.INPUT
        self.last_state = not self.input.value
        self.interval = interval
        self.last_time = now()

    def state(self):
        return not self.input.value

    def poll(self):
        current_state = self.state()
        if (now() - self.last_time) > self.interval:
            if not self.last_state and current_state:
                self.last_state = current_state
                self.last_time = now()
                return "Pressed"
            if self.last_state and not current_state:
                self.last_state = current_state
                self.last_time = now()
                return "Released"
        return None

# Sensor Readings
class ADC:
    def __init__(self, pin, interval):
        self.adc = AnalogIn(pin)
        self.interval = interval
        self.last_time = now()

    def poll(self):
        if (now() - self.last_time) > self.interval:
            self.last_time = now()
            return self.adc.value
        return None

# Sliding Buffer
class SlidingBuffer:
    def __init__(self, size):
        self.size = size
        self.data_buffer = []

    def put(self, adc_input):
        self.data_buffer.append(adc_input)
        if len(self.data_buffer) > self.size:
            self.data_buffer.pop(0)

    def poll(self):
        if len(self.data_buffer) == 0:
            return None
        return self.data_buffer

# RGB LED Control
class RGB:
    COLORS = {
        "Stopped": (0, 0, 0),  # Off
        "Recording": (0, 0, 255),  # Blue
        "Paused": (128, 128, 128),  # Grey
    }

    def __init__(self, pin):
        self.pixel = NeoPixel(pin, 1, brightness=0.5, auto_write=False)
        self.current_state = "Stopped"

    def run(self, state):
        if state != self.current_state:
            color = self.COLORS.get(state, (0, 0, 0))
            self.pixel.fill(color)
            self.pixel.show()
            self.current_state = state

# Phase Manager
class PhaseManager:
    def __init__(self):
        self.phases = ["Phase 1- Baseline", "Phase 2", "Phase 3"]
        self.current_phase = 0

    def next_phase(self):
        if self.current_phase < len(self.phases) - 1:
            self.current_phase += 1
            print(f"Phase changed to: {self.phases[self.current_phase]}")
        else:
            print("Experiment completed.")

    def reset_phase(self):
        """Reset to the baseline phase."""
        self.current_phase = 0
        print("Phase reset to Baseline.")

    def current_phase_name(self):
        return self.phases[self.current_phase]

# Main Function
def main():
    state = "Stopped"
    btn_1 = Button(GP20, debounce_time) #start/stop button
    btn_2 = Button(GP21, debounce_time) #record/pause button
    btn_3 = Button(GP22, debounce_time)  # Phase transition button
    
    buffer = SlidingBuffer(buffer_size)
    adc = ADC(A1, adc_interval)
    rgb = RGB(GP28)
    
    phase_manager = PhaseManager()
    recording_start_time = None

    while True:
        measure = adc.poll()
        event_1 = btn_1.poll()
        event_2 = btn_2.poll()
        event_3 = btn_3.poll()

        # Start/Stop System
        if event_1 == "Pressed":
            if state == "Stopped":
                state = "Default"
                phase_manager.reset_phase()  # Reset phase to Baseline
                print("System started. Press GP21 to record.")
            else:
                state = "Stopped"
                print("System stopped. Press GP21 to restart.")
                buffer.data_buffer.clear()

        # Record/Pause
        if event_2 == "Pressed":
            if state == "Default":
                state = "Recording"
                recording_start_time = now()
                print("Recording now.")
            elif state == "Recording":
                state = "Paused"
                print("Recording paused.")
            elif state == "Paused":
                state = "Recording"
                print("Recording resumed.")

        # Phase Transition
        if event_3 == "Pressed":
            if state == "Recording":
                phase_manager.next_phase()
                rgb.run(phase_manager.current_phase_name())  # Update LED to reflect the new phase

        # LED Control and Data Logging
        rgb.run(state)
        
        if state == "Recording" and measure is not None:
            buffer.put(measure)
            if len(buffer.data_buffer) >= buffer_size:
                data_burst = [
                    f"{recording_start_time},{phase_manager.current_phase_name()},{value}"
    for value in buffer.poll()
                ]
                print("\n".join(data_burst))
                buffer.data_buffer.clear()

# Run the main function
main()
