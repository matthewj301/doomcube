import unittest
from macro_test_support import render, state

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.p = state()
        self.p['configfile']['settings'].update({
            'extruder': {'min_temp': 0, 'min_extrude_temp': 180, 'max_temp': 500},
            'heater_bed': {'min_temp': 0, 'max_temp': 120},
            'fan_generic filter': {},
            'temperature_sensor chamber': {'max_temp': 100},
        })
        self.p['temperature_sensor chamber'] = {'temperature': 35}
        self.p['gcode']['commands'] = dict.fromkeys(('LINE_PURGE', 'MAYBE_HOME', 'PREHEAT', 'PICK_PARK_LOCATION'))
        self.params = {'HOTEND_TEMP': '240', 'BED_TEMP': '105'}

    def check(self):
        return render('PRINT_START_PREFLIGHT', self.p, self.params, 'custom/macros/preflight.cfg')

    def test_nonzero_slicer_slot_without_enabled_tool_system(self):
        for mmu in (None, {'enabled': False}):
            with self.subTest(mmu=mmu):
                self.setUp()
                if mmu is not None:
                    self.p['mmu'] = mmu
                    self.p['gcode']['commands'].update(T0=None, T1=None)
                self.params.update(HOTEND_TEMP='280', BED_TEMP='105',
                                   TARGET_CHAMBER_TEMP='40', MATERIAL='ABS', TOOL='1')
                self.check()
                self.p['gcode_macro _PRINT_START_STATE']['params'] = self.params
                commands = render('_PRINT_START_AFTER_PREHEAT', self.p)
                self.assertFalse(any(c.startswith('T') and c[1:].isdigit() for c in commands))
                self.assertFalse(any(c.startswith('MMU ') for c in commands))

    def test_non_mmu_tool_system_still_requires_registered_tool(self):
        self.p['gcode']['commands']['T0'] = None
        self.params['TOOL'] = '1'
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            self.check()
        self.p['gcode']['commands']['T1'] = None
        self.check()
        self.p['gcode_macro _PRINT_START_STATE']['params'] = self.params
        self.assertIn('T1', render('_PRINT_START_AFTER_PREHEAT', self.p))

    def test_enabled_mmu_requires_requested_tool(self):
        self.p['mmu'] = {'enabled': True}
        self.params['TOOL'] = '3'
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            self.check()
        self.p['gcode']['commands']['T3'] = None
        self.check()

    def test_bad_inputs(self):
        for key, values in {'HOTEND_TEMP': ['150', '501', 'nan', 'inf', 'oops'],
                            'BED_TEMP': ['-1', '121', 'nan'],
                            'TARGET_CHAMBER_TEMP': ['-1', '101', 'nan', 'inf'],
                            'TOOL': ['-1', '1.5', 'nan', 'inf'],
                            'MATERIAL': ['ASA"\nM112', '']}.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    old = dict(self.params)
                    self.params[key] = value
                    with self.assertRaises(ValueError):
                        self.check()
                    self.params = old

    def test_missing_purge_and_sensor_fail_early(self):
        del self.p['gcode']['commands']['LINE_PURGE']
        with self.assertRaisesRegex(ValueError, 'LINE_PURGE'):
            self.check()
        self.p['gcode']['commands']['LINE_PURGE'] = None
        del self.p['temperature_sensor chamber']
        self.params['TARGET_CHAMBER_TEMP'] = '45'
        with self.assertRaisesRegex(ValueError, 'sensor'):
            self.check()

    def test_preflight_is_first_command(self):
        commands = render('_PRINT_START_BEGIN', self.p, self.params)
        self.assertNotIn('SET_SLOW_CHAMBER_FAN_SPEED', commands)

class CleanupTests(unittest.TestCase):
    def test_new_print_cancels_timer_even_when_chamber_already_hot(self):
        case = PreflightTests()
        case.setUp()
        commands = render('_PRINT_START_BEGIN', case.p, case.params)
        self.assertIn('UPDATE_DELAYED_GCODE ID=FILTER_DELAYED_STOP DURATION=0', commands)

    def test_filter_on_cancels_old_timer(self):
        commands = render('TURN_FILTER_ON', state(), path='custom/macros/fans.cfg')
        self.assertEqual(commands[0], 'UPDATE_DELAYED_GCODE ID=FILTER_DELAYED_STOP DURATION=0')

    def test_cooldown_arms_timer_after_turning_filter_on(self):
        for quick in ('0', '1'):
            commands = render('COOLDOWN_SEQUENCE', state(), {'QUICK': quick}, 'custom/macros/heating_cooling.cfg')
            timer = next(i for i,c in enumerate(commands) if c.startswith('UPDATE_DELAYED_GCODE'))
            self.assertGreater(timer, commands.index('CHAMBER_HEATING_FANS_OFF'))
            self.assertFalse(any('SET_TEMPERATURE_FAN_TARGET' in c for c in commands))

    def test_skew_clear_optional(self):
        p = state()
        self.assertEqual(render('_CLEAR_PRINT_SKEW', p, path='custom/macros/utils.cfg'), [])
        p['configfile']['settings']['skew_correction'] = {}
        self.assertEqual(render('_CLEAR_PRINT_SKEW', p, path='custom/macros/utils.cfg'), ['SET_SKEW CLEAR=1'])

if __name__ == '__main__':
    unittest.main()
