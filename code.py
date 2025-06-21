import time
import board
import analogio
from digitalio import DigitalInOut, Direction, Pull
import pwmio
import usb_cdc
from adafruit_motor import motor


led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

serial = usb_cdc.console

PWM_PIN_A = board.GP16  # Pick two PWM pins on their own channels
PWM_PIN_B = board.GP17
PWM_FREQ = 20000  # PWMOut min/max 1Hz/50kHz, default is 500Hz
DECAY_MODE = motor.SLOW_DECAY  # Set controller to Slow Decay (braking) mode
THROTTLE_HOLD = 1  # Hold the throttle (seconds)

# # DC motor setup; Set pins to custom PWM frequency
pwm_a = pwmio.PWMOut(PWM_PIN_A, frequency=PWM_FREQ)
pwm_b = pwmio.PWMOut(PWM_PIN_B, frequency=PWM_FREQ)
motor = motor.DCMotor(pwm_a, pwm_b)
motor.decay_mode = DECAY_MODE
motor.throttle = 0  # Stop motor

class Motor:
    def __init__(self):
        self.throttle = 0
    def set(self, throttle: float):
        if throttle < 0 or throttle > 1:
            throttle = 0
        motor.throttle = throttle

class Sensor:
    def __init__(self, pin):
        self.pin = pin
        self.last_measurement = 0
        self.last_tick = 0
        self.state = 0
        self.measurements = []
    def add_measurement(self):
        MAX_MEASUREMENTS = 100
        ADC_THRESHOLD = 20000
        ONE_SEC = 1000000000
        MEASUREMENTS_PER_SEC = 2 * ONE_SEC
        now = time.monotonic_ns()
        
        delta = now - self.last_measurement
        if now - self.last_measurement < 1/MEASUREMENTS_PER_SEC:
            # print(now, self.last_measurement)
            return

        self.last_measurement = now

        raw_val = self.pin.value
        speed = 0
        new_state = self.state

        if raw_val > ADC_THRESHOLD and self.state == 0:
            new_state = 1
        if raw_val < ADC_THRESHOLD and self.state == 1:
            new_state = 0

        if self.state != new_state:
            self.state = new_state
            delta = now - self.last_tick
            if delta > 0:
                speed = 1.0/delta
                print("delta", delta, self.last_tick, now)

            self.last_tick = now
            # print("raw_val", raw_val, self.measurements)
            self.measurements.append(speed)

        self.measurements.append(speed)
        while len(self.measurements) > MAX_MEASUREMENTS:
            del self.measurements[0]
        
        avg = sum(self.measurements) / len(self.measurements)
        avg = float(avg)
        output = "{:.4f}\r\n".format(avg)
        output = "%f\r\n" % avg
        # print(avg, output)
        # serial.write(output)

class State:
    def __init__(self):
        self.speed = 0
        
        self.direction = False
        # self.count = 0
    def get(self):
        return self.state

def main():
    adc = analogio.AnalogIn(board.A0)
    sensor = Sensor(adc)
    motor = Motor()
    state = State()

    # Sweep up through 50 duty cycle values
    # for duty_cycle in range(0, 101, 2):
    #     throttle = duty_cycle / 100  # Convert to throttle value (0 to 1.0)
    #     # motor.throttle = throttle
    #     print((throttle,))  # Plot/print current throttle value
    #     time.sleep(0.1)  # Hold at current throttle value

    while 1:
        sensor.add_measurement()
        while serial.in_waiting > 0:
            # print("will try to read", serial.in_waiting)
            byte = serial.read(1)
            val = ord(byte)
            # print("got ssomething", val)
            # print(val)
            serial.write("%s\r\n" % val)
        
        time.sleep(0.1)

if __name__=="__main__":
    main()










