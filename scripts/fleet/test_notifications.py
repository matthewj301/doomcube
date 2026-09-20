import unittest
from test_chamber import Runtime
from macro_test_support import ROOT
import math

class NotificationTests(unittest.TestCase):
    def test_successful_retry_clears_old_failure_before_first_print_command(self):
        r = Runtime()
        name = r.p['print_stats']['filename']
        r.p['gcode_macro _FLEET_ALERT_STATE'].update(
            startup_failure_file=name, observed={'state':'error', 'filename':name})
        r.p['gcode_macro _PRINT_START_STATE'].update(active=True, sd_paused=True)
        r.start(STARTUP='1')
        r.p['temperature_sensor chamber']['temperature'] = 45
        r.tick()
        self.assertIsNone(r.p['gcode_macro _FLEET_ALERT_STATE']['startup_failure_file'])
        # Fail before the periodic watcher ever sees the successful printing state.
        r.p['print_stats']['state'] = 'error'
        r.run('alert_watch.py')
        self.assertIn('_FLEET_NOTIFY EVENT=print_failed', r.out)

    def test_completion_once_and_no_historical_replay(self):
        r = Runtime()
        r.p['print_stats']['state'] = 'complete'
        r.run('alert_watch.py')
        self.assertFalse(any('NOTIFY' in c for c in r.out))
        r.p['print_stats']['state'] = 'printing'
        r.run('alert_watch.py')
        r.p['print_stats']['state'] = 'complete'
        r.run('alert_watch.py')
        r.run('alert_watch.py')
        self.assertEqual(r.out.count('_FLEET_NOTIFY EVENT=complete'), 1)

    def test_prolonged_pause_once_per_episode_with_without_mmu(self):
        for mmu in (None, {'enabled': True}, {'enabled': False}):
            r = Runtime()
            if mmu is not None:
                r.p['mmu'] = mmu
            r.p['pause_resume']['is_paused'] = True
            r.run('alert_watch.py')
            r.now += 601
            r.run('alert_watch.py')
            r.run('alert_watch.py')
            self.assertEqual(r.out.count('_FLEET_NOTIFY EVENT=prolonged_pause'), 1)
            r.p['pause_resume']['is_paused'] = False
            r.run('alert_watch.py')
            r.p['pause_resume']['is_paused'] = True
            r.run('alert_watch.py')
            r.now += 601
            r.run('alert_watch.py')
            self.assertEqual(r.out.count('_FLEET_NOTIFY EVENT=prolonged_pause'), 2)

    def test_startup_sd_hold_is_not_a_pause_alert(self):
        r = Runtime()
        r.p['print_stats']['state'] = 'paused'
        r.p['gcode_macro _PRINT_START_STATE']['active'] = True
        r.run('alert_watch.py')
        r.now += 1000
        r.run('alert_watch.py')
        self.assertFalse(any('NOTIFY' in c for c in r.out))

    def test_remote_failure_is_nonfatal_and_empty_destination_is_local(self):
        r = Runtime()
        messages = []
        calls = []
        def remote(*args, **kwargs):
            calls.append((args,kwargs))
            raise RuntimeError('offline')
        context = dict(printer=r.p, params={'EVENT':'complete'}, respond_info=messages.append,
                       call_remote_method=remote, set_gcode_variable=lambda *args: None)
        source = compile((ROOT/'custom/macros/python/notify.py').read_text(), 'notify.py', 'exec')
        exec(source, context, {})
        self.assertEqual(calls, [])
        r.p['gcode_macro _PRINTER_VARS']['notification_name'] = 'test_sink'
        exec(source, context, {})
        self.assertEqual(len(calls), 1)
        self.assertIn('unavailable', messages[-1])

    def test_explicit_startup_failure_suppresses_duplicate_error(self):
        r = Runtime()
        r.p['print_stats']['state'] = 'printing'
        r.run('alert_watch.py')
        r.p['gcode_macro _FLEET_ALERT_STATE']['startup_failure_file'] = r.p['print_stats']['filename']
        r.p['print_stats']['state'] = 'error'
        r.run('alert_watch.py')
        self.assertNotIn('_FLEET_NOTIFY EVENT=print_failed', r.out)

if __name__ == '__main__':
    unittest.main()
