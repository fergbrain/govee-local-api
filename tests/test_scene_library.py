"""Tests for the temporary fork's full scene library (blob scenes)."""

import asyncio
import unittest
from unittest.mock import Mock

from govee_local_api.controller import GoveeController
from govee_local_api.light_capabilities import (
    GOVEE_LIGHT_CAPABILITIES,
    GoveeLightFeatures,
)
from govee_local_api.message import SceneCodeMessage, SceneMessages


class TestSceneLibraryRegistry(unittest.TestCase):
    def test_h805d_has_the_full_library(self):
        capabilities = GOVEE_LIGHT_CAPABILITIES["H805D"]
        self.assertEqual(len(capabilities.scene_library), 113)
        self.assertEqual(len(capabilities.available_scenes), 113)
        self.assertTrue(capabilities.features & GoveeLightFeatures.SCENES)

    def test_h805d_library_has_blob_scenes(self):
        library = GOVEE_LIGHT_CAPABILITIES["H805D"].scene_library
        blobs = [name for name, (_, param) in library.items() if param]
        self.assertEqual(len(blobs), 108)

    def test_h805d_has_nine_segments(self):
        self.assertEqual(GOVEE_LIGHT_CAPABILITIES["H805D"].segments_count, 9)

    def test_other_models_have_no_library(self):
        self.assertEqual(GOVEE_LIGHT_CAPABILITIES["H805C"].scene_library, {})


class TestSetSceneWithLibrary(unittest.TestCase):
    def _controller_and_device(self, sku: str):
        controller = GoveeController.__new__(GoveeController)
        controller._logger = Mock()
        controller._send_message = Mock()
        device = Mock()
        device.capabilities = GOVEE_LIGHT_CAPABILITIES[sku]
        return controller, device

    def test_library_scene_is_sent_with_its_blob(self):
        controller, device = self._controller_and_device("H805D")
        name, (code, param) = next(
            (n, v) for n, v in device.capabilities.scene_library.items() if v[1]
        )
        asyncio.run(controller.set_scene(device, name))
        message = controller._send_message.call_args.args[0]
        self.assertIsInstance(message, SceneCodeMessage)
        expected = SceneCodeMessage(code, param)
        self.assertEqual(bytes(message), bytes(expected))

    def test_firmware_only_model_still_uses_scene_messages(self):
        controller, device = self._controller_and_device("H805C")
        asyncio.run(controller.set_scene(device, "rainbow"))
        message = controller._send_message.call_args.args[0]
        self.assertIsInstance(message, SceneMessages)


if __name__ == "__main__":
    unittest.main()
