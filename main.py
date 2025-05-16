import math
import time

from machine import Pin, ADC, PWM, SPI

import mip
mip.install("github:peterhinch/micropython-nano-gui")
from color_setup import ssd  # Create a display instance
from gui.core.nanogui import refresh
from gui.core.writer import CWriter
from gui.core.colors import *

U16 = 65535

LEFT_BUTTON_PIN = Pin(0, Pin.IN)
RIGHT_BUTTON_PIN = Pin(35, Pin.IN)
MOISTURE_PIN = ADC(Pin(33))
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
        return min(max(math.floor(value / 100 * U16), 0), U16)

    def stop(self):
        """
        Standby, same like stop
        """
        self._pwm.duty_u16(U16)

    def start(self):
        self._pwm.duty_u16(self.to_u16(0))


def calculate_current_moisture(pin_value: int) -> float:
    return (max_moisture - pin_value) * 100 / (max_moisture - min_moisture)


def _water_until_moist(
        *,
        moisture_pin: Pin,
        motor_controller: MotorController,
        moisture_threshold: float,
) -> None:
    current_moisture_level = calculate_current_moisture(moisture_pin.read())
    try:
        if current_moisture_level < moisture_threshold:
            motor_controller.start()
            time.sleep(.5)
    finally:
        motor_controller.stop()

def update_screen(
    *,
    moisture_level,
    trigger_treshold
):
    ssd.fill(0)
    ssd.text(f'moisture level is {moisture_level}', 10, 10, RED)
    ssd.text(f'trigger treshold is {trigger_treshold}', 10, 50, GREEN)
    ssd.show()

def run():
    motor_controller = MotorController(
        pin=WATER_PUMP_CONTROLLER_PIN,
    )
    moisture_threshold = 20.0

    while True:
        update_screen(
            moisture_level=calculate_current_moisture(MOISTURE_PIN.read()),
            trigger_treshold=moisture_threshold,
        )
        pressed_button = Button.button_pressed()
        if pressed_button:
            if pressed_button.button_name is AvailableButton.LEFT:
                moisture_threshold += 1
                print('Increasing the moisture threshold to: ', moisture_threshold)
            if pressed_button.button_name is AvailableButton.RIGHT:
                moisture_threshold -= 1
                print('Decreasing the moisture threshold to: ', moisture_threshold)

        _water_until_moist(
            moisture_pin=MOISTURE_PIN,
            motor_controller=motor_controller,
            moisture_threshold=moisture_threshold,
        )
        time.sleep(.5)
        print('moisture level is ', calculate_current_moisture(MOISTURE_PIN.read()))


if __name__ == '__main__':
    run()
