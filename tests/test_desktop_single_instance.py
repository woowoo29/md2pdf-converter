import tempfile
import time
import unittest
from pathlib import Path

from desktop.single_instance import SingleInstanceController


class SingleInstanceControllerTests(unittest.TestCase):
    def test_notify_returns_false_when_no_primary_instance_exists(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            controller = SingleInstanceController(Path(tmp_dir) / "instance.sock")
            self.assertFalse(controller.notify_existing_instance([]))

    def test_secondary_launch_message_reaches_primary_instance(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            socket_path = Path(tmp_dir) / "instance.sock"
            received = []
            controller = SingleInstanceController(socket_path)
            try:
                controller.start(received.append)
            except PermissionError:
                self.skipTest("Unix socket binding is not permitted in this environment.")

            try:
                sent = controller.notify_existing_instance([Path("/tmp/test.md")])
                self.assertTrue(sent)

                deadline = time.time() + 2
                while time.time() < deadline and not received:
                    time.sleep(0.05)

                self.assertEqual(
                    received,
                    [{"action": "activate", "open_paths": ["/tmp/test.md"]}],
                )
            finally:
                controller.stop()
