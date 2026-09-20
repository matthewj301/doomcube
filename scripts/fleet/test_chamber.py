"""Execute native Python scripts with the installed helper shape and separate namespaces.
The fake command sink checks orchestration/failures, not firmware, motion or thermals.
"""
import math
from pathlib import Path
from unittest.mock import patch
import unittest
from macro_test_support import ROOT, state, variables, render

class Runtime:
    def __init__(self):
        self.p = state()
        self.p['pause_resume']['is_paused'] = False
        self.p['gcode_macro _FLEET_ALERT_STATE'] = {'observed': {}, 'failure': '', 'startup_failure_file': None}
        self.p['gcode_macro TA_CHAMBER_STATE'] = {'active': False, 'job': {}}
        self.p['gcode_macro _PRINT_START_STATE'] = {'active': False, 'sd_paused': False, 'params': {}, 'filename': ''}
        self.p['virtual_sdcard'] = {'is_active': False}
        self.p['print_stats'] = {'state': 'standby', 'filename': 'sample.gcode'}
        self.p['temperature_sensor chamber'] = {'temperature': 20}
        self.p['extruder'].update(temperature=150, target=150)
        self.p['heater_bed'].update(temperature=105, target=105)
        self.p['toolhead'].update(axis_minimum=[0,0,0], axis_maximum=[305,308,300])
        self.p['configfile']['settings'].update(extruder={'min_temp': 0, 'max_temp': 500}, heater_bed={'min_temp':0, 'max_temp':120})
        self.p['configfile']['settings']['temperature_sensor chamber'] = {'max_temp':80}
        self.p['gcode_macro _PRINTER_VARS']['high_temp_heat_soak_time'] = 0
        self.out = []
        self.fail_on = None
        self.now = 100

    def emit(self, command):
        self.out.append(command)
        if self.fail_on and command.startswith(self.fail_on):
            raise ValueError('injected command failure')
        if command.startswith('M104 S'):
            self.p['extruder']['target'] = float(command[6:])
        if command.startswith('M140 S'):
            self.p['heater_bed']['target'] = float(command[6:])
        if command == 'TURN_OFF_HEATERS_BASE':
            self.p['extruder']['target'] = self.p['heater_bed']['target'] = 0
        if command in ('_TA_CHAMBER_RESET', 'CANCEL_PRINT'):
            self.p['gcode_macro TA_CHAMBER_STATE']['active'] = False
            self.p['gcode_macro _PRINT_START_STATE']['active'] = False
            self.p['gcode_macro _PRINT_START_STATE']['sd_paused'] = False
        if command == 'M25':
            self.p['virtual_sdcard']['is_active'] = False
        if command == 'M24':
            self.p['virtual_sdcard']['is_active'] = True

    def run(self, script, params=None):
        def fail(message):
            raise ValueError(message)
        def set_var(macro, variable, value):
            self.p['gcode_macro '+macro][variable] = value
        context = dict(printer=self.p, params=params or {}, rawparams='HOTEND_TEMP=240 BED_TEMP=105',
                       emit=self.emit, set_gcode_variable=set_var, respond_info=lambda msg: None,
                       raise_error=fail, math=math, wait_moves=lambda: None)
        with patch('time.monotonic', return_value=self.now):
            exec(compile((ROOT/'custom/macros/python'/script).read_text(), script, 'exec'), context, {})

    def start(self, **params):
        self.run('chamber_heating.py', {'HOTEND_TEMP':'150', 'BED_TEMP':'105', 'TARGET_CHAMBER_TEMP':'45', **params})

    def tick(self):
        self.out.clear()
        self.run('chamber_tick.py')

class ChamberTests(unittest.TestCase):
    def test_preheat_omitted_targets_preserve_zero_defaults(self):
        r = Runtime()
        r.run('chamber_heating.py', {'HOTEND_TEMP': '150', 'MATERIAL': 'PLA'})
        job = r.p['gcode_macro TA_CHAMBER_STATE']['job']
        self.assertEqual((job['bed'], job['chamber']), (0, 0))
        self.assertEqual(job['points'], [])

    def test_console_start_after_old_cancel_or_error(self):
        for previous in ('cancelled', 'error'):
            r = Runtime()
            r.p['gcode_macro _PRINT_START_STATE']['active'] = True
            r.p['print_stats']['state'] = previous
            r.start(STARTUP='1')
            r.p['temperature_sensor chamber']['temperature'] = 45
            r.tick()
            self.assertIn('_PRINT_START_AFTER_PREHEAT', r.out)
            self.assertNotIn('M24', r.out)

    def test_patterns_work_with_native_separate_namespaces(self):
        for pattern, count in [('auto',5), ('grid',9), ('corners',5), ('vortex',32)]:
            r = Runtime()
            r.start(PATTERN=pattern)
            self.assertEqual(len(r.p['gcode_macro TA_CHAMBER_STATE']['job']['points']), count)
            r.tick()
            self.assertEqual(sum(c.startswith('G1 X') for c in r.out), 1)
            self.assertIn('RESTORE_GCODE_STATE NAME=_CHAMBER_STEP', r.out)
            self.assertIn('SET_VELOCITY_LIMIT ACCEL=15000', r.out)
            self.assertFalse(any(c.startswith(('M109','M190','G4')) for c in r.out))

    def test_abort_timeout_never_resumes_file(self):
        r = Runtime()
        r.p['gcode_macro _PRINT_START_STATE'].update(active=True, sd_paused=True)
        r.start(STARTUP='1', TIMEOUT='10')
        r.now += 11
        with self.assertRaisesRegex(ValueError, 'timed out'):
            r.tick()
        self.assertIn('CANCEL_PRINT', r.out)
        self.assertNotIn('M24', r.out)
        self.assertFalse(r.p['gcode_macro TA_CHAMBER_STATE']['active'])

    def test_explicit_continue_still_requires_heater_readiness(self):
        r = Runtime()
        r.start(TIMEOUT='10', ON_TIMEOUT='continue')
        r.p['extruder']['temperature'] = 50
        r.now += 11
        with self.assertRaises(ValueError):
            r.tick()
        self.assertEqual(r.p['extruder']['target'], 0)
        r = Runtime()
        r.start(TIMEOUT='10', ON_TIMEOUT='continue')
        r.now += 11
        r.tick()
        self.assertFalse(r.p['gcode_macro TA_CHAMBER_STATE']['active'])

    def test_stop_makes_queued_ticks_noops(self):
        r = Runtime()
        r.start()
        r.emit('_TA_CHAMBER_RESET')
        r.tick()
        self.assertEqual(r.out, [])
        commands = render('TA_CHAMBER_STOP', r.p, path='custom/macros/dynamic_macros/toolhead_assisted_chamber_heating.cfg')
        self.assertIn('TURN_OFF_HEATERS_BASE', commands)
        render('_TA_CHAMBER_RESET', r.p, path='custom/macros/dynamic_macros/toolhead_assisted_chamber_heating.cfg')

    def test_success_resumes_only_owned_sd_job(self):
        for mmu in (None, {'enabled':False}, {'enabled':True}):
            r = Runtime()
            if mmu is not None:
                r.p['mmu'] = mmu
            r.p['gcode_macro _PRINT_START_STATE'].update(active=True, sd_paused=True)
            r.start(STARTUP='1')
            r.p['temperature_sensor chamber']['temperature'] = 45
            r.tick()
            self.assertLess(r.out.index('_PRINT_START_AFTER_PREHEAT'), r.out.index('M24'))
            self.assertFalse(r.p['gcode_macro _PRINT_START_STATE']['active'])

    def test_continuation_failure_cancels(self):
        r = Runtime()
        r.p['gcode_macro _PRINT_START_STATE'].update(active=True, sd_paused=True)
        r.start(STARTUP='1')
        r.p['temperature_sensor chamber']['temperature'] = 45
        r.fail_on = '_PRINT_START_AFTER_PREHEAT'
        with self.assertRaisesRegex(ValueError, 'injected'):
            r.tick()
        self.assertIn('CANCEL_PRINT', r.out)
        self.assertNotIn('M24', r.out)

    def test_bad_input_does_not_heat(self):
        for params in ({'TIMEOUT':'nan'}, {'HOTEND_TEMP':'501'}, {'PATTERN':'bad'}, {'INTERVAL_S':'0'}):
            r = Runtime()
            with self.assertRaises(ValueError):
                r.start(**params)
            self.assertEqual(r.out, [])

    def test_soak_uses_elapsed_time_and_resets_on_temperature_drop(self):
        r = Runtime()
        r.p['gcode_macro _PRINTER_VARS']['high_temp_heat_soak_time'] = 1
        r.start()
        r.p['temperature_sensor chamber']['temperature'] = 45
        r.tick()
        r.now += 30
        r.p['temperature_sensor chamber']['temperature'] = 20
        r.tick()
        self.assertIsNone(r.p['gcode_macro TA_CHAMBER_STATE']['job']['ready_since'])
        r.p['temperature_sensor chamber']['temperature'] = 45
        r.tick()
        r.now += 61
        r.tick()
        self.assertFalse(r.p['gcode_macro TA_CHAMBER_STATE']['active'])

    def test_start_preflight_failure_has_no_side_effect(self):
        r = Runtime()
        r.fail_on = 'PRINT_START_PREFLIGHT'
        with self.assertRaises(ValueError):
            r.run('print_start.py', {'HOTEND_TEMP':'240'})
        self.assertEqual(r.out, ['PRINT_START_PREFLIGHT HOTEND_TEMP=240 BED_TEMP=105', '_FLEET_NOTIFY EVENT=startup_failed'])
        self.assertFalse(r.p['gcode_macro _PRINT_START_STATE']['active'])

    def test_repeat_start_rejected(self):
        r = Runtime()
        r.start()
        r.out.clear()
        with self.assertRaises(ValueError):
            r.start()
        self.assertEqual(r.out, [])

if __name__ == '__main__':
    unittest.main()
