"""Source-template harness, not a firmware/motion simulator."""
import ast
import configparser
from copy import deepcopy
from pathlib import Path
import jinja2

ROOT = Path(__file__).resolve().parents[2]

def config(path):
    cfg = configparser.RawConfigParser(strict=False, inline_comment_prefixes=('#', ';'))
    cfg.read(ROOT / path)
    return cfg

def variables(path, name):
    return {k[9:]: ast.literal_eval(v) for k, v in config(path).items('gcode_macro ' + name) if k.startswith('variable_')}

def state():
    return {
        'gcode_macro _PRINTER_VARS': variables('printer.cfg', '_PRINTER_VARS'),
        'gcode_macro _PRINT_START_STATE': {'active': False},
        'gcode_macro RESUME': {'printing_target_temp': 240, 'retracted_length': 5},
        'gcode': {'commands': {}},
        'extruder': {'target': 240, 'can_extrude': True},
        'heater_bed': {'temperature': 100, 'target': 105},
        'pause_resume': {'is_paused': True},
        'toolhead': {'max_accel': 15000, 'homed_axes': 'xyz'},
        'save_variables': {'variables': {'current_material': 'ASA'}},
        'configfile': {'config': {}, 'settings': {'idle_timeout': {'timeout': 600}}},
    }

def render(name, printer=None, params=None, path='custom/macros/print.cfg'):
    cfg = config(path)
    env = jinja2.Environment('{%', '%}', '{', '}', extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols'])
    def fail(msg):
        raise ValueError(msg)
    context = deepcopy(printer if printer is not None else state())
    own = context.get('gcode_macro ' + name, {})
    text = env.from_string(cfg.get('gcode_macro ' + name, 'gcode')).render(
        printer=context, params=params or {}, rawparams=" ".join(f"{k}={v}" for k,v in (params or {}).items()), action_raise_error=fail,
        action_respond_info=lambda msg: '', **own)
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith('#')]
