"""
This script is meant to be run on a MicroPython enabled microcontroller.
This particular configuration was written for an ESP32 chip (running on
a NodeMCU dev board), but any microcontroller that exposed at least 14
pins that can be outputs would work. This could also be made to work with
an ESP8266 if you added an I2C expansion board for more GPIO.

The pin assignments below may seem a bit arbitrary, and they are. It's just
how I happened to wire them up to my board. The important thing to keep in
mind is that they are listed in big-endian order. That is, the first element
in each array represents the most significant bit of the address or RAM chip.

In the INSTRUCTIONS list, I have added some instructions that were not part
of Ben Eater's original microcode. See the Arduino sketch in this repository
for programming the ROM chips with these new instructions. Inspired from:
https://theshamblog.com/programs-and-more-commands-for-the-ben-eater-8-bit-breadboard-computer/
"""

from machine import Pin
import time

INSTRUCTIONS = {
    "NOP": "0000",
    "LDA": "0001",
    "ADD": "0010",
    "SUB": "0011",
    "STA": "0100",
    "LDI": "0101",
    "JMP": "0110",
    "JC" : "0111",
    "JZ" : "1000",
    "INC": "1001",
    "DEC": "1010",
    "DSP": "1011",
    "DSI": "1100",
    ""   : "1101",
    "OUT": "1110",
    "HLT": "1111",
}

ADDRESS_PINS = [
    Pin(26, Pin.OUT), # D26
    Pin(25, Pin.OUT), # D25
    Pin(33, Pin.OUT), # D33
    Pin(32, Pin.OUT), # D32
]

INSTRUCTION_PINS = [
    Pin(18, Pin.OUT), # D18
    Pin(5, Pin.OUT),  # D5
    Pin(4, Pin.OUT),  # D4
    Pin(2, Pin.OUT),  # D2
    Pin(27, Pin.OUT), # D27
    Pin(14, Pin.OUT), # D14
    Pin(12, Pin.OUT), # D12
    Pin(13, Pin.OUT), # D13
]

set_data_pin = Pin(15, Pin.OUT) # D15
# writing to RAM is active low so pull the set pin high
# so that we're not constantly writing
set_data_pin.on()


def set_address(addr: int) -> None:
    """Set the address bits

    Args:
        addr: Address value, 0-15
    """

    if not 0 <= addr <= 15:
        raise ValueError("Invalid address %s. Must be 0-15" % addr)

    bit_list = "{:0>4}".format(bin(addr)[2:])
    for index, bit in enumerate(ADDRESS_PINS):
        if bit_list[index] == "1":
            bit.on()
        else:
            bit.off()


def set_instruction(addr: int, op_code: str, data: int = None) -> None:
    """Set the instruction for the current address along
    with any data that is an argument for the instruction

    Args:
        addr: Address value for the instruction, 0-15
        op_code: The operation to perform. Must be in the
            list of valid operations
        data: If provided, used as an argument for op_code
    """

    set_address(addr)

    if op_code not in INSTRUCTIONS:
        raise ValueError("No op_code matching %s" % op_code)
    if data is None:
        data = 0

    bit_list = "{:0>4}{:0>4}".format(
        bin(int(INSTRUCTIONS[op_code], 2))[2:],
        bin(data)[2:],
    )
    for index, bit in enumerate(INSTRUCTION_PINS):
        if bit_list[index] == "1":
            bit.on()
        else:
            bit.off()
    set_data_pin.off()
    time.sleep_ms(1)
    set_data_pin.on()

# Example usage of the above code. This program will
# loop the SAP over and over, adding 3 to the accumulator
# and showing the current value in the output register
set_instruction(0, "LDI", 0)
set_instruction(1, "STA", 15)
set_instruction(2, "LDA", 15)
set_instruction(3, "INC", 3)
set_instruction(4, "STA", 15)
set_instruction(5, "DSP", 15)
set_instruction(6, "JMP", 2)
