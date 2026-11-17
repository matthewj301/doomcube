import unittest
from macro_test_support import render, state

UTILS = 'custom/macros/utils.cfg'

def mpc_set(commands):
    line = next(c for c in commands if c.startswith('MPC_SET'))
    return dict(kv.split('=') for kv in line.split()[1:])

class MpcMaterialTests(unittest.TestCase):
    def setUp(self):
        self.p = state()
        self.p['configfile']['settings']['extruder'] = {'control': 'mpc', 'filament_density': 1.07}

    def test_slicer_density_is_used(self):
        got = mpc_set(render('_SET_MPC_MATERIAL', self.p, {'MATERIAL': 'ABS', 'FILAMENT_DENSITY': '1.06'}, UTILS))
        self.assertEqual(float(got['FILAMENT_DENSITY']), 1.06)
        self.assertEqual(float(got['FILAMENT_HEAT_CAPACITY']), 1.80)

    def test_missing_density_uses_extruder_config_default(self):
        got = mpc_set(render('_SET_MPC_MATERIAL', self.p, {'MATERIAL': 'PETG'}, UTILS))
        self.assertEqual(float(got['FILAMENT_DENSITY']), 1.07)

    def test_abs_md_gf15_has_its_own_heat_capacity(self):
        got = mpc_set(render('_SET_MPC_MATERIAL', self.p, {'MATERIAL': 'abs-md-gf15', 'FILAMENT_DENSITY': '1.23'}, UTILS))
        self.assertEqual(float(got['FILAMENT_HEAT_CAPACITY']), 1.65)

    def test_unknown_material_keeps_generic_heat_capacity(self):
        got = mpc_set(render('_SET_MPC_MATERIAL', self.p, {'MATERIAL': 'HIPS', 'FILAMENT_DENSITY': '1.04'}, UTILS))
        self.assertEqual(float(got['FILAMENT_HEAT_CAPACITY']), 1.80)

    def test_print_start_begin_forwards_density_only_when_given(self):
        self.p['gcode']['commands'] = {}
        base = {'HOTEND_TEMP': '250', 'BED_TEMP': '100', 'MATERIAL': 'ASA'}
        with_density = render('_PRINT_START_BEGIN', self.p, dict(base, FILAMENT_DENSITY='1.07'))
        self.assertIn('_SET_MPC_MATERIAL MATERIAL="ASA" FILAMENT_DENSITY=1.07', with_density)
        without = render('_PRINT_START_BEGIN', self.p, base)
        self.assertIn('_SET_MPC_MATERIAL MATERIAL="ASA"', without)

    def test_pid_extruder_skips_mpc(self):
        self.p['configfile']['settings']['extruder']['control'] = 'pid'
        commands = render('_PRINT_START_BEGIN', self.p, {'HOTEND_TEMP': '250', 'MATERIAL': 'ASA', 'FILAMENT_DENSITY': '1.07'})
        self.assertFalse(any(c.startswith('_SET_MPC_MATERIAL') for c in commands))

if __name__ == '__main__':
    unittest.main()
