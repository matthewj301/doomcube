# Each timer invocation emits at most one mixing move, then releases G-code ownership.
import time
vars = printer['gcode_macro _PRINTER_VARS']
state = printer['gcode_macro TA_CHAMBER_STATE']
startup = params.get('STARTUP', '0') == '1'
if state['active']:
    raise_error('PREHEAT: warmup is already active; stop it before restarting')
if startup and not printer['gcode_macro _PRINT_START_STATE']['active']:
    raise_error('PREHEAT: STARTUP is reserved for PRINT_START')
if not startup and (printer['virtual_sdcard']['is_active'] or printer['pause_resume']['is_paused']):
    raise_error('PREHEAT: cannot run during a print or pause')
settings = printer['configfile']['settings']
# PREHEAT preserves its zero bed/chamber defaults; TA_CHAMBER_HEAT supplies its own.
chamber = float(params.get('TARGET_CHAMBER_TEMP', 0))
bed = float(params.get('BED_TEMP', 0))
hotend = float(params.get('HOTEND_TEMP', vars['default_chamber_assist_extruder_temp']))
timeout = float(params.get('TIMEOUT', vars['chamber_heat_timeout']))
interval = float(params.get('INTERVAL_S', vars['chamber_status_interval']))
delta = float(params.get('START_DELTA', vars['chamber_start_delta']))
policy = params.get('ON_TIMEOUT', 'abort').lower()
pattern = params.get('PATTERN', 'auto').lower()
quick = params.get('QUICK', '0')
material = params.get('MATERIAL', vars['default_material']).upper()
sensor = 'temperature_sensor ' + vars['chamber_sensor_name']
for name, value in [('extruder', hotend), ('heater_bed', bed)]:
    limits = settings[name]
    if not math.isfinite(value) or not (value == 0 or float(limits['min_temp']) <= value <= float(limits['max_temp'])):
        raise_error('PREHEAT: invalid target for ' + name)
if not math.isfinite(chamber) or chamber < 0:
    raise_error('PREHEAT: invalid chamber target')
if chamber > 0 and (sensor not in printer or sensor not in settings):
    raise_error('PREHEAT: chamber sensor is unavailable')
if chamber > 0 and chamber > float(settings[sensor]['max_temp']):
    raise_error('PREHEAT: chamber target exceeds sensor limit')
if not (1 <= interval <= 30 and 1 <= timeout <= 14400 and 0 <= delta <= 10):
    raise_error('PREHEAT: invalid interval, timeout or start delta')
if policy not in ('abort', 'continue') or pattern not in ('auto', 'grid', 'corners', 'vortex') or quick not in ('0', '1'):
    raise_error('PREHEAT: invalid policy, pattern or QUICK')
if startup and quick == '1':
    raise_error('PREHEAT: startup requires full warmup')
warp = material in [m.strip().upper() for m in vars['warp_prone_materials'].split(',')]
soak = 60 * float(vars['high_temp_heat_soak_time'] if warp or bed >= float(vars['high_temp_threshold']) else vars['standard_heat_soak_time'])
if not math.isfinite(soak) or soak < 0 or int(vars['chamber_heat_max_cycles']) < 1:
    raise_error('PREHEAT: invalid soak or cycle limit')
points = []
if chamber > 0 and quick == '0':
    lo = printer['toolhead']['axis_minimum']
    hi = printer['toolhead']['axis_maximum']
    size = ((hi[0]-lo[0]) + (hi[1]-lo[1])) / 2
    margin = 40 if size >= 400 else 30 if size >= 300 else 20
    x0, x1, y0, y1 = lo[0]+margin, hi[0]-margin, lo[1]+margin, hi[1]-margin
    cx, cy = (x0+x1)/2, (y0+y1)/2
    if x0 >= x1 or y0 >= y1:
        raise_error('PREHEAT: mixing margins do not fit this machine')
    if pattern == 'grid':
        for y in (y0,cy,y1):
            for x in (x0,cx,x1):
                points.append((x,y))
    elif pattern == 'corners':
        points = [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(cx,cy)]
    elif pattern == 'vortex':
        # Explicit loops: native Python macros execute with separate globals/locals.
        for scale in (1,.75,.5,.25):
            radius = min(x1-cx,y1-cy)*scale
            for angle in range(0,360,45):
                points.append((cx+radius*math.cos(math.radians(angle)),cy+radius*math.sin(math.radians(angle))))
    else:
        points = [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(cx,cy)]
    speed = float(vars['chamber_move_speed_fast'] if size >= 400 else vars['chamber_move_speed_medium'] if size >= 300 else vars['chamber_move_speed_slow'])
    z = max(lo[2]+2, min(hi[2]-2, float(vars['chamber_printhead_height'])))
else:
    speed, z = 0, 0
job = dict(startup=startup, sd_owned=startup and printer['gcode_macro _PRINT_START_STATE']['sd_paused'], chamber=chamber, bed=bed, hotend=hotend, sensor=sensor,
           deadline=time.monotonic()+timeout, interval=interval, delta=delta, policy=policy,
           soak=soak, ready_since=None, points=points, index=0, cycles=0, speed=speed, z=z,
           filename=printer['print_stats']['filename'])
try:
    emit('UPDATE_DELAYED_GCODE ID=FILTER_DELAYED_STOP DURATION=0')
    emit('M140 S%s' % bed)
    emit('M104 S%s' % hotend)
    if bed >= float(vars['chamber_assist_temp']) or chamber > 0:
        emit('CHAMBER_FANS_ON')
    else:
        emit('ALL_CHAMBER_FANS_OFF')
    if quick == '0':
        if points:
            emit('MAYBE_HOME')
            if printer['toolhead']['homed_axes'] != 'xyz':
                raise_error('PREHEAT: mixing requires all axes homed')
        set_gcode_variable('TA_CHAMBER_STATE', 'job', job)
        set_gcode_variable('TA_CHAMBER_STATE', 'active', True)
        emit('UPDATE_DELAYED_GCODE ID=_TA_CHAMBER_TIMER DURATION=0.1')
        respond_info('Preheat scheduled; TA_CHAMBER_STOP stops it. Timeout policy: ' + policy)
except Exception:
    emit('TURN_OFF_HEATERS_BASE')
    emit('M107')
    emit('_TA_CHAMBER_RESET')
    raise
