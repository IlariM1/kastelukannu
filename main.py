import time

from machine import Pin, ADC, PWM

LEFT_BUTTON_PIN = Pin(0, Pin.IN)
RIGHT_BUTTON_PIN = Pin(35, Pin.IN)
MOISTURE_PIN = ADC(Pin(12))
MOISTURE_PIN.atten(ADC.ATTN_11DB)
MOISTURE_PIN.width(ADC.WIDTH_12BIT)

WATER_PUMP_CONTROLLER_PIN = PWM(Pin(13))

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


def calculate_current_moisture(pin_value: int) -> float:
    return (max_moisture - pin_value) * 100 / (max_moisture - min_moisture)


def run():
    while True:
        pressed_button = Button.button_pressed()
        if pressed_button:
            print(pressed_button.button_name)
        pin_value = MOISTURE_PIN.read()
        print('raw value is: ', pin_value)
        current_moisture_level = calculate_current_moisture(pin_value)
        moisture = '{:.1f} %'.format(current_moisture_level)
        print('Soil Moisture:', moisture)
        print('')
        time.sleep(1)


if __name__ == '__main__':
    run()
