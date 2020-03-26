# sap-tools
A repository of tools for interfacing with the SAP breadboard computer designed by Ben Eater's work

## Microcode for SAP
The microcode Arduino sketch is originally taken from: https://github.com/beneater/eeprom-programmer.
To that code, I have added the INC, DEC, DSP, and DSI instructions. These instructions all work within
the original hardware design of Ben Eater's computer (YouTube playlist: https://www.youtube.com/playlist?list=PLowKtXNTBypGqImE405J2565dvjafglHU).

## Python -> ASM
The pyasm.py script will convert a limited subset of the Python language to SAP assembly which can then
be entered into the computer and executed.

## Microcontroller Programmer
The sap.py script is an assembler and programmer for the SAP computer. It has functions to take assembly
code and translate it into binary. It will then transmit that binary code via its GPIO pins to a connected
SAP machine (no hardware modifications needed to the SAP machine).

![ESP32 Connected to the Ben Eater SAP Computer](micro_sap.jpg?raw=true "ESP32 Connected to the Ben Eater SAP Computer")

## Inspiration
If you find this repository useful, you may also enjoy the following sites:

* https://cpu.visualrealmsoftware.com/ - Web based assembler and simulator for a Ben Eater style computer
* https://github.com/LuisMichaelis/Computer-Simulation - PC based assembler and simulator for the Ben Eater style computer
* https://theshamblog.com/programs-and-more-commands-for-the-ben-eater-8-bit-breadboard-computer/ - Program ideas and new instruction ideas
