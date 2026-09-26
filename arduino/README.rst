Overview
========

Arduino interface to the Ei413 fire panel module inputs. All inputs are
read twice, acting on both NC and NO states.

Hardware
========

Build the project with `PlatformIO <https://platformio.org/>`_ and
upload it to an Arduino Micro.

Connect the three relay common terminals to GND.

Connect the other terminals as follows:

+-----+----------------------------------------------------------------+
| Pin | Name                                                           |
+=====+================================================================+
|  2  | CO RELAY NC                                                    |
+-----+----------------------------------------------------------------+
|  3  | CO RELAY NO                                                    |
+-----+----------------------------------------------------------------+
|  4  | FIRE RELAY NC                                                  |
+-----+----------------------------------------------------------------+
|  5  | FIRE RELAY NO                                                  |
+-----+----------------------------------------------------------------+
|  6  | FAULT RELAY NC                                                 |
+-----+----------------------------------------------------------------+
|  7  | FAULT RELAY NO                                                 |
+-----+----------------------------------------------------------------+

Software
========

Read newline-delimited input from the serial device.

Each line will contain a list of the 6 pin states, with `C` (Carbon
Monoxide), `F` (Fire) or `E` (Fault) for active triggers or `_` for
inactive triggers.

A line is output every 1 second or immediately if any of the triggers
changes state.

Example with all triggers active::

    CCFFEE

Example with no triggers active::

    ______

Example with fire trigger active::

    __FF__

Example when disconnected from the panel module::

    C_F_E_
