"""Consumer adaptations: execute source against a command recorder, never a printer."""
import ast
import configparser
from pathlib import Path
from types import SimpleNamespace
import unittest
import math
import shlex
import jinja2
from test_chamber import Runtime
from macro_test_support import ROOT


def read_config(path):
    cfg = configparser.RawConfigParser(strict=False, inline_comment_prefixes=('#',';'))
    cfg.read(path)
    return cfg

class ConsumerRuntime(Runtime):
    def __init__(self, repo):
        super().__init__()
        self.root = ROOT.parent / repo
        cfg = read_config(self.root/'printer.cfg')
        self.p['gcode_macro _PRINTER_VARS'] = {
            k[9:]: ast.literal_eval(v) for k,v in cfg.items('gcode_macro _PRINTER_VARS') if k.startswith('variable_')}
        self.p['configfile']['settings']['printer'] = {'max_accel': 7500}
        self.p['gcode_macro BEACON_VARS'] = {'beacon_contact_calibration_temp':150}
        self.p['configfile']['settings']['beacon'] = {}
        self.p['configfile']['settings']['bed_mesh'] = {}
        self.p['configfile']['settings']['z_tilt'] = {}
        self.p['configfile']['settings']['extruder']['min_extrude_temp'] = 180
        self.p['configfile']['config'].update({
            'gcode_macro CLEAN_NOZZLE': {}, 'gcode_macro _BEACON_SET_NOZZLE_TEMP_OFFSET': {},
            'gcode_macro LINE_PURGE': {},
        })
        self.p['gcode']['commands'] = dict.fromkeys(('MAYBE_HOME','PREHEAT','PICK_PARK_LOCATION','LINE_PURGE','_BEACON_SET_NOZZLE_TEMP_OFFSET'))
        self.p['gcode_macro _PRINT_START_STATE']['params'] = {'HOTEND_TEMP':'260','BED_TEMP':'105','TARGET_CHAMBER_TEMP':'40','MATERIAL':'ASA','TOOL':'0'}

    def emit(self, command):
        super().emit(command)
        if command.startswith('SET_GCODE_VARIABLE '):
            fields=dict(item.split('=',1) for item in shlex.split(command)[1:])
            self.p['gcode_macro '+fields['MACRO']][fields['VARIABLE']]=ast.literal_eval(fields['VALUE'])

    def macro(self,name,params=None):
        for path in sorted((self.root/'custom/macros').rglob('*.cfg')):
            cfg=read_config(path)
            section='gcode_macro '+name
            if cfg.has_section(section):
                self.p.setdefault(section,{})
                for key,value in cfg.items(section):
                    if key.startswith('variable_'): self.p[section].setdefault(key[9:],ast.literal_eval(value))
                body=cfg.get(section,'gcode').strip()
                break
        else:
            raise AssertionError('Missing macro '+name)
        params=params or {}
        def fail(msg): raise ValueError(msg)
        context=dict(printer=self.p, params=params, rawparams='', emit=self.emit, math=math,
                     respond_info=lambda msg: None, raise_error=fail,
                     set_gcode_variable=lambda macro,key,value:self.p['gcode_macro '+macro].__setitem__(key,value),
                     own_vars=SimpleNamespace(**self.p.get(section,{})))
        if body.startswith('!!include '):
            source=(path.parent/body.split(maxsplit=1)[1]).read_text()
            exec(compile(source,name,'exec'),context,{})
        elif body.startswith('!'):
            source='\n'.join(line.lstrip()[1:] for line in body.splitlines())
            exec(compile(source,name,'exec'),context,{})
        else:
            env=jinja2.Environment('{%','%}','{','}',extensions=['jinja2.ext.do','jinja2.ext.loopcontrols'])
            result=env.from_string(body).render(**context,action_raise_error=fail,action_respond_info=lambda m:'',**self.p.get(section,{}))
            for line in result.splitlines():
                line=line.strip()
                if line and not line.startswith('#'): self.emit(line)

class K3PortTests(unittest.TestCase):
    def test_cold_home_then_wipe_contact_mesh_order(self):
        r=ConsumerRuntime('K3D')
        r.macro('_PRINT_START_BEGIN',r.p['gcode_macro _PRINT_START_STATE']['params'])
        self.assertIn('MAYBE_HOME',r.out)
        self.assertFalse(any(c.startswith('M104') for c in r.out))
        self.assertLess(r.out.index('_CLEAR_PRINT_SKEW'),r.out.index('MAYBE_HOME'))
        r.out.clear()
        r.macro('_PRINT_START_AFTER_PREHEAT')
        self.assertLess(r.out.index('WIPE_NOZZLE'),r.out.index('G28 Z METHOD=CONTACT CALIBRATE=0'))
        self.assertLess(r.out.index('G28 Z METHOD=CONTACT CALIBRATE=0'),r.out.index('BED_MESH_CALIBRATE ADAPTIVE=1'))

    def test_pause_keeps_heater_off_and_single_firmware_return(self):
        r=ConsumerRuntime('K3D')
        r.macro('PAUSE')
        self.assertLess(r.out.index('PAUSE_BASE'),r.out.index('PICK_PARK_LOCATION'))
        self.assertIn('M104 S0',r.out)
        r.p['pause_resume']['is_paused']=True
        r.out.clear()
        r.macro('RESUME')
        self.assertEqual(sum(c.startswith('RESUME_BASE') for c in r.out),1)
        self.assertFalse(any(c.startswith('RESTORE_GCODE_STATE NAME=PAUSE ') for c in r.out))
        self.assertIn('SET_IDLE_TIMEOUT TIMEOUT=600',r.out)

    def test_completion_retains_motors_cancel_is_motionless(self):
        r=ConsumerRuntime('K3D')
        r.macro('PRINT_END')
        self.assertNotIn('DISABLE_ALL_MOTORS',r.out)
        self.assertIn('COOLDOWN_SEQUENCE QUICK=1',r.out)
        r.out.clear()
        r.macro('CANCEL_PRINT')
        self.assertEqual(r.out[:2],['TURN_OFF_HEATERS_BASE','BASE_CANCEL_PRINT'])
        self.assertIn('COOLDOWN_SEQUENCE QUICK=0',r.out)
        self.assertFalse(any('PARK' in c or c.startswith('G28') for c in r.out))


class RatRacePortTests(unittest.TestCase):
    def test_start_retains_awdsync_and_contact_temperature_order(self):
        r=ConsumerRuntime('rat-race')
        r.macro('_PRINT_START_BEGIN',r.p['gcode_macro _PRINT_START_STATE']['params'])
        self.assertIn('SYNC_MOTORS ACCEL_CHIP=beacon',r.out)
        self.assertLess(r.out.index('_CLEAR_PRINT_SKEW'),r.out.index('MAYBE_HOME'))
        r.out.clear()
        r.macro('_PRINT_START_AFTER_PREHEAT')
        wipe=r.out.index('CLEAN_NOZZLE SKIP_HEATING=1')
        wait=r.out.index('TEMPERATURE_WAIT SENSOR=extruder MINIMUM=148')
        contact=r.out.index('G28 Z METHOD=CONTACT CALIBRATE=0')
        self.assertLess(wipe,wait)
        self.assertLess(wait,contact)
        self.assertLess(contact,r.out.index('M104 S260.0'))
        self.assertIn('Z_TILT_ADJUST',r.out)
        self.assertIn('_PRINT_START_CHECK_READY',r.out)

    def test_pause_and_resume_keep_distinct_mmu_ownership(self):
        for enabled in (False,True):
            with self.subTest(mmu=enabled):
                r=ConsumerRuntime('rat-race')
                r.p['mmu']={'enabled':enabled}
                r.p['extruder']['target']=260
                r.macro('PAUSE')
                self.assertIn('M104 S180',r.out)
                self.assertIn('SET_IDLE_TIMEOUT TIMEOUT=14400',r.out)
                if enabled:
                    self.assertIn('_MMU_SAVE_POSITION', [c.split(';')[0].strip() for c in r.out])
                    self.assertNotIn('PICK_PARK_LOCATION',r.out)
                else:
                    self.assertLess(r.out.index('PAUSE_BASE'),r.out.index('PICK_PARK_LOCATION'))
                    self.assertIn('M83',r.out)
                r.p['pause_resume']['is_paused']=True
                r.out.clear()
                r.macro('RESUME')
                self.assertIn('M109 S260',r.out)
                if enabled:
                    self.assertLess(r.out.index('M109 S260'),r.out.index('_MMU_RESTORE_POSITION'))
                    self.assertIn('SET_IDLE_TIMEOUT TIMEOUT=600',r.out)
                else:
                    self.assertIn('_RESUME_NON_MMU',r.out)
                    r.macro('_RESUME_NON_MMU')
                self.assertEqual(sum(c.startswith('RESUME_BASE') for c in r.out),1)
                self.assertFalse(any(c.startswith('RESTORE_GCODE_STATE NAME=PAUSE ') for c in r.out))

    def test_resume_rechecks_cold_nozzle_after_wait(self):
        r=ConsumerRuntime('rat-race')
        r.p['pause_resume']['is_paused']=True
        r.p['gcode_macro RESUME']['retracted_length']=5
        r.p['extruder']['can_extrude']=False
        with self.assertRaisesRegex(ValueError,'too cold'):
            r.macro('_RESUME_NON_MMU')
        self.assertFalse(r.out)

    def test_motionless_cancel_and_normal_completion_motor_policy(self):
        r=ConsumerRuntime('rat-race')
        r.macro('CANCEL_PRINT')
        self.assertEqual(r.out[:2],['TURN_OFF_HEATERS_BASE','BASE_CANCEL_PRINT'])
        self.assertIn('M84',r.out)
        self.assertFalse(any('PARK' in c or c.startswith('G28') for c in r.out))
        r.out.clear()
        r.macro('PRINT_END')
        self.assertIn('COOLDOWN_SEQUENCE QUICK=0',r.out)
        self.assertNotIn('DISABLE_ALL_MOTORS',r.out)
        cfg=read_config(r.root/'mmu/base/mmu_macro_vars.cfg')
        for option in ('printing','standalone','disabled'):
            self.assertNotIn('cancel',ast.literal_eval(cfg.get('gcode_macro _MMU_SEQUENCE_VARS','variable_enable_park_'+option)).split(','))

class SharedPortTests(unittest.TestCase):
    def test_shared_python_matches_validated_master(self):
        for repo in ('K3D','rat-race'):
            for name in ('print_start.py','chamber_heating.py','chamber_tick.py','notify.py','alert_watch.py'):
                relative=Path('custom/macros/python')/name
                self.assertEqual((ROOT/relative).read_bytes(),(ROOT.parent/repo/relative).read_bytes(),(repo,name))

    def test_preflight_disabled_and_absent_mmu_accepts_slicer_slot(self):
        for repo in ('K3D','rat-race'):
            for mmu in (None,{'enabled':False}):
                r=ConsumerRuntime(repo)
                if mmu is not None: r.p['mmu']=mmu
                for fan in ('filter_fan','bed_fan','chamber_fan'):
                    name=r.p['gcode_macro _PRINTER_VARS'][fan]
                    if name: r.p['configfile']['settings']['fan_generic '+name]={}
                r.macro('PRINT_START_PREFLIGHT',{'HOTEND_TEMP':'260','TOOL':'1'})
                self.assertTrue(any('ignoring slicer TOOL=1' in c for c in r.out))

    def test_filter_timer_is_armed_after_fans_for_each_cooldown_branch(self):
        for repo in ('K3D','rat-race'):
            for quick in ('0','1'):
                r=ConsumerRuntime(repo)
                r.p['gcode_macro _PRINTER_VARS']['filter_fan']='test_filter'
                r.p['save_variables']['variables']['current_material']='ABS'
                r.macro('COOLDOWN_SEQUENCE',{'QUICK':quick})
                armed=next(i for i,c in enumerate(r.out) if c.startswith('UPDATE_DELAYED_GCODE ID=FILTER_DELAYED_STOP DURATION=') and not c.endswith('=0'))
                self.assertLess(r.out.index('CHAMBER_HEATING_FANS_OFF'),armed)

if __name__=='__main__': unittest.main()

