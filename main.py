import math
import time

from machine import Pin, ADC, PWM

U16 = 65535

LEFT_BUTTON_PIN = Pin(0, Pin.IN)
RIGHT_BUTTON_PIN = Pin(35, Pin.IN)
MOISTURE_PIN = ADC(Pin(12))
MOISTURE_PIN.atten(ADC.ATTN_11DB)
MOISTURE_PIN.width(ADC.WIDTH_12BIT)

WATER_PUMP_CONTROLLER_PIN = Pin(13)

min_moisture = 2000
max_moisture = 3500


class AvailableButton:
    LEFT = 'left'
    RIGHT = 'right'


class ButtonData:

    def __init__(
            self,
            *,
            button: str,
            pin: Pin,
    ):
        self.button_name = button
        self._pin = pin

    def is_pressed(self) -> bool:
        return not bool(self._pin.value())


class Button:
    LEFT = ButtonData(
        button=AvailableButton.LEFT,
        pin=LEFT_BUTTON_PIN,
    )
    RIGHT = ButtonData(
        button=AvailableButton.RIGHT,
        pin=RIGHT_BUTTON_PIN,
    )

    @classmethod
    def _iter_buttons(cls):
        for button in (
                cls.LEFT,
                cls.RIGHT,
        ):
            yield button

    @classmethod
    def button_pressed(cls) -> ButtonData | None:
        for button in cls._iter_buttons():
            if button.is_pressed():
                return button
        return None


class MotorController:
    def __init__(
            self,
            *,
            pin: Pin,
    ):
        self._pwm = PWM(pin,freq=1000, duty_u16=U16)

    @staticmethod
    def to_u16(value) -> int:
        print(min(max(math.floor(value / 100 * U16), 0), U16))
        return min(max(math.floor(value / 100 * U16), 0), U16)

    def stop(self):
        """
        Standby, same like stop
        """
        print('stopping the engine')
        self._pwm.duty_u16(U16)

    def start(self, speed: float | int = 50):
        print('starting the engine with speed of :', speed)
        self._pwm.duty_u16(self.to_u16(0))


def calculate_current_moisture(pin_value: int) -> float:
    return (max_moisture - pin_value) * 100 / (max_moisture - min_moisture)


def run():
    motor_controller = MotorController(
        pin=WATER_PUMP_CONTROLLER_PIN,
    )

    while True:
        pressed_button = Button.button_pressed()
        if pressed_button:
            if pressed_button.button_name is AvailableButton.LEFT:
                motor_controller.start()
            else:
                motor_controller.stop()


        pin_value = MOISTURE_PIN.read()
        # print('raw value is: ', pin_value)
        current_moisture_level = calculate_current_moisture(pin_value)
        moisture = '{:.1f} %'.format(current_moisture_level)
        # print('Soil Moisture:', moisture)
        # print('')
        time.sleep(1)


if __name__ == '__main__':
    run()
