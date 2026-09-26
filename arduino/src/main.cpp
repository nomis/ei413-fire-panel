/*
 * ei413-fire-panel - Arduino interface to panel module I/O
 * Copyright 2026  Simon Arlott
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <Arduino.h>

static constexpr unsigned long REPORT_INTERVAL_MS = 1000;
static constexpr bool RELAY_NC = true;
static constexpr bool RELAY_NO = false;

class Input {
public:
	Input(int pin, bool active_low, char output)
			: pin_(pin), active_low_(active_low), output_(output) {
	}

	void setup() {
		pinMode(pin_, INPUT_PULLUP);
	}

	bool loop() {
		bool reading = (digitalRead(pin_) == LOW) ^ active_low_;

		if (reading_ != reading) {
			reading_ = reading;
			return true;
		}

		return false;
	}

	void print() {
		SerialUSB.print(reading_ ? output_ : '_');
	}

private:
	const int pin_;
	const bool active_low_;
	const char output_;
	bool reading_{false};
};

static Input inputs[6] {
	{2, RELAY_NC, 'C'}, // Carbon Monoxide NC
	{3, RELAY_NO, 'C'}, // Carbon Monoxide NO
	{4, RELAY_NC, 'F'}, // Fire NC
	{5, RELAY_NO, 'F'}, // Fire NO
	{6, RELAY_NC, 'E'}, // Fault NC
	{7, RELAY_NO, 'E'}, // Fault NO
};

void setup() {
	for (Input& input : inputs) {
		input.setup();
	}

	SerialUSB.begin(115200);
	while (!SerialUSB);
}

void loop() {
	static unsigned long last = millis();
	bool immediate = false;

	for (Input& input : inputs) {
		immediate |= input.loop();
	}

	if (immediate || millis() - last >= REPORT_INTERVAL_MS) {
		for (Input& input : inputs) {
			input.print();
		}
		SerialUSB.println();
		last = millis();
	}
}
