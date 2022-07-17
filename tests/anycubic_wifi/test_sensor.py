"""The tests for Octoptint binary sensor module."""

import threading
import unittest
import time
from typing import Iterable
from uart_wifi.communication import UartWifi
from uart_wifi.simulate_printer import AnycubicSimulator
from uart_wifi.response import MonoXResponseType, MonoXStatus


class TestComms(unittest.TestCase):
    """Tests"""

    # This will be set to zero by default in fake_printer. We test this
    # value until it changes to something other than zero during setup_class
    # . This gives us a randomized port number to use for the test.
    port = 0

    @classmethod
    def setup_class(cls):
        """Called when setting up the class to start the fake printer"""
        # start a fake printer on a new thread.
        fake_printer = AnycubicSimulator("127.0.0.1", 0)
        thread = threading.Thread(target=fake_printer.start_server)
        thread.daemon = False
        thread.start()
        # Get the testing port number from the fake printer.
        while TestComms.port == 0:
            print("Sleeping while fake printer starts")
            time.sleep(0.2)
            TestComms.port = fake_printer.port
            print("Port is: " + str(TestComms.port))
        # Give it plenty of time to ensure it is listening.
        time.sleep(1)
        TestComms.port = fake_printer.port
        print("Fake printer started")

    def test_connection(self):
        """Validate the connection to the printer.  If this works, then
        further online testing should be possible.  This is a simple test to
        validate the connection to the fake printer."""
        uart_wifi: UartWifi = get_api()
        response: Iterable[MonoXStatus] = uart_wifi.send_request("getstatus,")
        assert len(response) > 0, "No response from Fake Printer"
        assert (
            response[0].status == "stop\r\n"
        ), "Invalid response from Fake Printer"

    @classmethod
    def teardown_class(cls):
        """Called when setting up the class to start the fake printer"""

        uart = UartWifi("127.0.0.1", TestComms.port)
        response: list[MonoXResponseType] = uart.send_request("shutdown,")
        try:
            print(response[0].print())
        except IndexError:
            pass


def get_api() -> UartWifi:
    """ "Get the UartWifi device to use for testing"""
    port = TestComms.port
    print(f"connecting to 127.0.0.1:{port}")
    uart_wifi: UartWifi = UartWifi("127.0.0.1", TestComms.port)
    return uart_wifi
