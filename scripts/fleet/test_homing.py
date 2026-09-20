"""Render the actual MAYBE_HOME template; does not move a printer.
Run with a Python environment containing Jinja2: python -m unittest discover
-s scripts/fleet -p 'test_*.py'. Tested with Jinja2 3.1.6.
"""
import configparser
from pathlib import Path
import unittest
import jinja2


class HomingTests(unittest.TestCase):
    def render(self, homed='', params=None, printing=False, overridden=False):
        config = configparser.RawConfigParser(strict=False, inline_comment_prefixes=('#', ';'))
        config.read(Path(__file__).resolve().parents[2] / 'custom/macros/homing.cfg')
        env = jinja2.Environment('{%', '%}', '{', '}', extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols'])
        template = env.from_string(config.get('gcode_macro MAYBE_HOME', 'gcode'))
        output = template.render(printer={
            'save_variables': {'variables': {'is_printing_gcode': printing}},
            'toolhead': {'homed_axes': homed},
            'gcode_macro MAYBE_HOME': {'is_kinematic_position_overriden': overridden},
        }, params=params or {})
        return [line.strip() for line in output.splitlines() if line.strip()]

    def homes(self, **kwargs):
        return [line for line in self.render(**kwargs) if line == 'G28' or line.startswith('G28 ')]

    def test_default_missing_axes(self):
        self.assertEqual(self.homes(homed='x'), ['G28 Y Z'])

    def test_requested_axis_is_homed(self):
        self.assertEqual(self.homes(params={'X': '1'}), ['G28 X'])

    def test_only_requested_unhomed_axes(self):
        self.assertEqual(self.homes(homed='x', params={'X': '1', 'Z': '1'}), ['G28 Z'])

    def test_already_homed_no_motion(self):
        self.assertEqual(self.homes(homed='xyz'), [])
        self.assertEqual(self.homes(homed='x', params={'X': '1'}), [])

    def test_no_homing_during_print(self):
        for flag in (True, 'True'):
            self.assertEqual(self.homes(printing=flag), [])

    def test_false_string_does_not_suppress_homing(self):
        self.assertEqual(self.homes(printing='False'), ['G28 X Y Z'])

    def test_debug_override_preserves_full_rehome(self):
        for flag in (True, 'True'):
            commands = self.render(overridden=flag)
            self.assertIn('G28', commands)
            self.assertIn('SET_GCODE_VARIABLE MACRO=MAYBE_HOME VARIABLE=is_kinematic_position_overriden VALUE=False', commands)

    def test_false_override_is_false(self):
        self.assertEqual(self.homes(homed='xyz', overridden='False'), [])


if __name__ == '__main__':
    unittest.main()
