"""Regression checks on actual macro expansions; no printer motion."""
import unittest
from macro_test_support import render, state

class LifecycleTests(unittest.TestCase):
    def test_cancel_critical_actions_precede_optional_integrations(self):
        for homed in ('', 'xy', 'xyz'):
            p = state()
            p['toolhead']['homed_axes'] = homed
            p['mmu'] = {'enabled': True}
            commands = render('CANCEL_PRINT', p)
            self.assertEqual(commands[:2], ['TURN_OFF_HEATERS_BASE', 'BASE_CANCEL_PRINT'])
            self.assertLess(commands.index('M84'), commands.index('MMU_TTG_MAP RESET=1 QUIET=1'))
            self.assertFalse(any('PARK' in c or c.startswith(('G28', 'PRINT_END')) for c in commands))

    def test_cancel_preserves_motionless_compensation_cleanup(self):
        p = state()
        p['configfile']['settings']['bed_mesh'] = {}
        p['configfile']['config']['gcode_macro _BEACON_REMOVE_NOZZLE_TEMP_OFFSET'] = {}
        commands = render('CANCEL_PRINT', p)
        for command in ('BED_MESH_CLEAR', '_BEACON_REMOVE_NOZZLE_TEMP_OFFSET'):
            self.assertGreater(commands.index(command), commands.index('M84'))

    def test_pause_snapshot_precedes_park(self):
        p = state()
        p['pause_resume']['is_paused'] = False
        commands = render('PAUSE', p)
        self.assertLess(commands.index('PAUSE_BASE'), commands.index('PICK_PARK_LOCATION'))
        self.assertFalse(any(c == 'SAVE_GCODE_STATE NAME=PAUSE' for c in commands))

    def test_cold_resume_rechecks_after_wait(self):
        p = state()
        p['extruder']['can_extrude'] = False
        commands = render('RESUME', p)
        self.assertLess(commands.index('M109 S240'), commands.index('_RESUME_NON_MMU'))
        with self.assertRaisesRegex(ValueError, 'too cold'):
            render('_RESUME_NON_MMU', p)
        p['extruder']['can_extrude'] = True
        commands = render('_RESUME_NON_MMU', p)
        self.assertIn('G1 E5.0 F2700.0', commands)
        self.assertFalse(any(c.startswith('RESTORE_GCODE_STATE NAME=PAUSE ') for c in commands))
        self.assertEqual(sum(c.startswith('RESUME_BASE') for c in commands), 1)

    def test_no_prime_without_prior_retract(self):
        p = state()
        p['gcode_macro RESUME']['retracted_length'] = 0
        self.assertFalse(any(c.startswith('G1 E') for c in render('_RESUME_NON_MMU', p)))

    def test_unpaused_resume_does_not_move(self):
        p = state()
        p['pause_resume']['is_paused'] = False
        for name in ('RESUME', '_RESUME_NON_MMU'):
            with self.assertRaisesRegex(ValueError, 'not paused'):
                render(name, p)

    def test_mmu_keeps_its_position_owner(self):
        p = state()
        p['mmu'] = {'enabled': True}
        commands = render('RESUME', p)
        self.assertIn('RESUME_BASE', commands)
        self.assertFalse(any('RESTORE_GCODE_STATE' in c or '_RESUME_NON_MMU' in c for c in commands))

if __name__ == '__main__':
    unittest.main()
