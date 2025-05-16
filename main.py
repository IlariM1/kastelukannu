import math
import time

from machine import Pin, ADC, PWM, SPI

import mip
mip.install("github:peterhinch/micropython-nano-gui")
import gc
from drivers.st7789.st7789_4bit import *

from gui.core.nanogui import refresh
from gui.core.writer import CWriter
from gui.core.colors import *

SSD = ST7789

TFT_MOSI =   19  # (SDA on schematic pdf) SPI interface output/input pin.
TFT_SCLK =   18  # This pin is used to be serial interface clock.
TFT_CS =      5  # Chip selection pin, low enable, high disable.
TFT_DC =     16  # Display data/command selection pin in 4-line serial interface.
TFT_RST =    23  # This signal will reset the device,Signal is active low.
TFT_BL =      4  # (LEDK on schematic pdf) Display backlight control pin

pdc = Pin(TFT_DC, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(TFT_CS, Pin.OUT, value=1)
prst = Pin(TFT_RST, Pin.OUT, value=1)
pbl = Pin(TFT_BL, Pin.OUT, value=1)
print('arbitrary pins initialized')
gc.collect()
print('gc collect done')
spi = SPI(1, 30_000_000, sck=Pin(18), mosi=Pin(19))
print('SPI initializied')
ssd = SSD(spi, height=135, width=240, dc=pdc, cs=pcs, rst=prst, disp_mode=LANDSCAPE, display=TDISPLAY)
print('SSD initialized')
ssd.fill(0)
ssd.line(0, 0, ssd.width - 1, ssd.height - 1, GREEN)  # Green diagonal corner-to-corner
ssd.rect(0, 0, 15, 15, RED)  # Red square at top left
ssd.rect(ssd.width -15, ssd.height -15, 15, 15, BLUE)  # Blue square at bottom right
ssd.show()

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


def run():
    motor_controller = MotorController(
        pin=WATER_PUMP_CONTROLLER_PIN,
    )
    moisture_threshold = 20.0

    while True:
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
