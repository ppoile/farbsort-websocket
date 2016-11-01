import unittest

from hal import HAL_simulated as HAL


class TestHAL(unittest.TestCase):
    def test_instance(self):
        hal = HAL()

    def test_input_default(self):
        hal = HAL()
        self.assertEqual(hal.get_input("Input1"), None)

    def test_input_set(self):
        hal = HAL()
        hal.set_input("Input1", True)
        self.assertTrue(hal.get_input("Input1"))
        hal.set_input("Input1", False)
        self.assertFalse(hal.get_input("Input1"))

    def _callback_func(self, *args):
        self._callback_args = args

    def test_on_input_change_callback(self):
        hal = HAL()
        hal.register_on_input_change_callback(self._callback_func)
        hal.set_input("Input1", True)
        hal.get_input("Input1")
        self.assertEqual(self._callback_args, ("Input1", True, None))
        hal.set_input("Input1", False)
        hal.get_input("Input1")
        self.assertEqual(self._callback_args, ("Input1", False, True))

    def test_output_default(self):
        hal = HAL()
        self.assertEqual(hal.get_output("Output1"), None)

    def test_output_set(self):
        hal = HAL()
        hal.set_output("Output1", True)
        self.assertTrue(hal.get_output("Output1"))
        hal.set_output("Output1", False)
        self.assertFalse(hal.get_output("Output1"))

    def test_analog_input_default(self):
        hal = HAL()
        self.assertEqual(hal.get_analog_input("AnalogInput1"), None)

    def test_analog_input_set(self):
        hal = HAL()
        set_value = 3
        hal.set_analog_input("AnalogInput1", set_value)
        self.assertEqual(hal.get_analog_input("AnalogInput1"), set_value)