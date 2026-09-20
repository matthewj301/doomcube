"""Fixture tests for include traversal and observation accuracy."""
from pathlib import Path
import tempfile
import unittest
from check import scan


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def run_scan(self):
        return scan(self.root, 'printer.cfg', '/home/pi/printer_data/config')

    def test_sorted_includes_and_merged_sections(self):
        self.put('printer.cfg', '[include parts/*.cfg]\n')
        self.put('parts/20.cfg', '[gcode_macro M]\nvariable_b: True\ngcode:\n  G28\n')
        self.put('parts/10.cfg', '[gcode_macro M]\nvariable_a: False\n')
        result = self.run_scan()
        self.assertEqual(result['files'], ['printer.cfg', 'parts/10.cfg', 'parts/20.cfg'])
        self.assertEqual(result['macros']['M']['variables'], ['a', 'b'])
        self.assertEqual(len(result['duplicate_sections']), 1)

    def test_config_root_mapping_and_relative_parent(self):
        self.put('printer.cfg', '[include /home/pi/printer_data/config/parts/top.cfg]\n')
        self.put('parts/top.cfg', '[include ../common.cfg]\n')
        self.put('common.cfg', '[save_variables]\nfilename: data.cfg\n')
        result = self.run_scan()
        self.assertEqual(result['unresolved'], [])
        self.assertEqual(result['save_variables'], ['data.cfg'])
        self.assertIn('common.cfg', result['files'])

    def test_cycle_is_reported_without_recursing_forever(self):
        self.put('printer.cfg', '[include a.cfg]\n')
        self.put('a.cfg', '[include printer.cfg]\n')
        self.assertEqual(self.run_scan()['cycles'], ['printer.cfg'])

    def test_external_symlink_is_not_read(self):
        self.put('printer.cfg', '[include external.cfg]\n')
        (self.root / 'external.cfg').symlink_to('/etc/hosts')
        result = self.run_scan()
        self.assertEqual(result['files'], ['printer.cfg'])
        self.assertEqual(len(result['unresolved']), 1)

    def test_missing_dependency_is_incomplete_not_missing_macro_proof(self):
        self.put('printer.cfg', '[include missing.cfg]\n')
        self.assertEqual(len(self.run_scan()['unresolved']), 1)

    def test_python_include_syntax_error_is_reported(self):
        self.put('printer.cfg', '[gcode_macro M]\ngcode: !!include helper.py\n')
        self.put('helper.py', 'if:\n')
        self.assertEqual(len(self.run_scan()['python_errors']), 1)

    def test_commented_includes_ignored(self):
        self.put('printer.cfg', '# [include missing.cfg]\n# !!include absent.py\n[respond]\n')
        self.assertEqual(self.run_scan()['unresolved'], [])

    def test_parameter_inventory_both_languages_and_literals(self):
        self.put('printer.cfg', '''[gcode_macro J]
variable_flag: False
variable_label: "False"
gcode:
  {% set temperature = params.HOTEND_TEMP|int %}
[gcode_macro P]
gcode:
  !value = params.get("BED_TEMP", 0)
  !tool = params["TOOL"]
''')
        result = self.run_scan()
        self.assertEqual(result['literal_errors'], [])
        self.assertEqual(result['macros']['P']['language'], 'kalico-python')
        self.assertEqual(result['macros']['P']['parameters_observed'], ['BED_TEMP', 'TOOL'])
        self.assertEqual(result['macros']['J']['parameters_observed'], ['HOTEND_TEMP'])


if __name__ == '__main__':
    unittest.main()
