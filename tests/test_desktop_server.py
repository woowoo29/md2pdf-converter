import unittest
from urllib.request import urlopen

from desktop.server import DesktopServer


class DesktopServerTests(unittest.TestCase):
    def test_desktop_server_serves_healthcheck(self):
        try:
            server = DesktopServer()
        except PermissionError:
            self.skipTest("Local socket binding is not permitted in this environment.")

        try:
            server.start(timeout=10.0)

            with urlopen(server.health_url, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.read(), b'{"status":"ok"}')
        finally:
            server.stop()
