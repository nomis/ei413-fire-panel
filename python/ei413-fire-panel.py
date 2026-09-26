#!/usr/bin/env python3
#
# ei413-fire-panel - Arduino interface to panel module I/O
# Copyright 2026  Simon Arlott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from multiprocessing import Process, Queue
import argparse
import os
import signal
import socket
import syslog
import termios
import traceback

import requests
import yaml

class Input:
	def __init__(self, id, session, url, entity):
		self.id = id
		self.session = session
		self.url = url
		self.entity = entity
		self.last = None

	def process(self, line):
		active = self.id in line

		if active != self.last:
			state = "on" if active else "off"
			response = self.session.post(
				f"{self.url}/api/services/input_boolean/turn_{state}",
				json={"entity_id": self.entity})
			response.raise_for_status()
			self.last = active

def hass(q, session, url, co_entity, fire_entity, fault_entity):
	inputs = [
		Input("C", session, url, co_entity),
		Input("F", session, url, fire_entity),
		Input("E", session, url, fault_entity),
	]

	while True:
		line = q.get()
		try:
			for i in inputs:
				i.process(line)
		except Exception:
			traceback.print_exc()

def listener(q, s):
	while True:
		line = q.get()
		try:
			while True:
				(data, address) = s.recvfrom(32)
				s.sendto(data + line.encode("utf8"), address)
		except BlockingIOError:
			pass
		except Exception:
			traceback.print_exc()

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("device")
	parser.add_argument("config")
	parser.add_argument("port")
	args = parser.parse_args()

	queue1 = Queue()
	queue2 = Queue()

	with open(args.config, "r") as f:
		config = yaml.safe_load(f)

	session = requests.Session()
	session.headers.update({"Authorization": f"Bearer {config['hass']['token']}"})

	s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(("::", int(args.port)))
	s.setblocking(False)

	p = Process(target=hass, args=(queue1, session, config["hass"]["url"],
		config["hass"]["entities"]["co"], config["hass"]["entities"]["fire"],
		config["hass"]["entities"]["fault"]))
	p.daemon = False
	p.start()
	p = Process(target=listener, args=(queue2, s))
	p.daemon = False
	p.start()

	syslog.openlog("ei413-fire-panel")

	fd = os.open(args.device, os.O_RDWR|os.O_NONBLOCK)
	os.set_blocking(fd, True)

	[iflag, oflag, cflag, lflag, ispeed, ospeed, cc] = termios.tcgetattr(fd)
	iflag &= ~(termios.BRKINT | termios.ICRNL | termios.IGNBRK | termios.IGNCR
		| termios.INLCR | termios.INPCK | termios.ISTRIP | termios.IXOFF
		| termios.IXON | termios.PARMRK | termios.IMAXBEL)
	oflag &= ~(termios.OPOST)
	cflag &= ~(termios.CSIZE | termios.PARENB | termios.PARODD | termios.HUPCL)
	cflag |= termios.CS8 | termios.CREAD | termios.CLOCAL
	lflag &= ~(termios.ECHO | termios.ECHOE | termios.ECHOK | termios.ECHONL
		| termios.ICANON | termios.IEXTEN | termios.ISIG | termios.NOFLSH
		| termios.TOSTOP)
	lflag |= termios.ICANON
	ispeed = termios.B115200
	ospeed = termios.B115200
	cc[termios.VMIN] = 1
	cc[termios.VTIME] = 0
	termios.tcsetattr(fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

	last_line = None
	signal.alarm(5)
	while True:
		line = os.read(fd, 1024).rstrip().decode("utf8", "replace")
		if not line:
			syslog.syslog("<EOF>")
			print("<EOF>")
			break
		if line != last_line:
			syslog.syslog(line)
			print(line)
			last_line = line
		if len(line) == 6:
			queue1.put(line)
			queue2.put(line)
			signal.alarm(5)
	os.kill(0, 15)
