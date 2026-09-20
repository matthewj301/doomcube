# Kalico native Python macro. No motion/heat is emitted before preflight passes.
start = printer['gcode_macro _PRINT_START_STATE']
if start['active'] or printer['gcode_macro TA_CHAMBER_STATE']['active']:
    raise_error('PRINT_START: another startup/preheat is active; stop it first')
if printer['pause_resume']['is_paused']:
    raise_error('PRINT_START: cannot start over a paused print')
set_gcode_variable('_FLEET_ALERT_STATE', 'startup_failure_file', None)
if printer['virtual_sdcard']['is_active']:
    set_gcode_variable('_FLEET_ALERT_STATE', 'observed',
                       dict(state='startup', filename=printer['print_stats']['filename'],
                            paused_since=None, pause_notified=False))
try:
    emit('PRINT_START_PREFLIGHT ' + rawparams)
except Exception as error:
    set_gcode_variable('_FLEET_ALERT_STATE', 'failure', str(error))
    emit('_FLEET_NOTIFY EVENT=startup_failed')
    raise
set_gcode_variable('_PRINT_START_STATE', 'params', dict(params))
set_gcode_variable('_PRINT_START_STATE', 'filename', printer['print_stats']['filename'])
set_gcode_variable('_PRINT_START_STATE', 'sd_paused', False)
set_gcode_variable('_PRINT_START_STATE', 'active', True)
try:
    # M25 pauses only the SD stream, without HH/user PAUSE parking or snapshots.
    if printer['virtual_sdcard']['is_active']:
        emit('M25')
        set_gcode_variable('_PRINT_START_STATE', 'sd_paused', True)
    emit('_PRINT_START_BEGIN ' + rawparams)
    vars = printer['gcode_macro _PRINTER_VARS']
    hotend = float(params['HOTEND_TEMP'])
    if 'beacon' in printer['configfile']['settings']:
        hotend = float(printer['gcode_macro BEACON_VARS']['beacon_contact_calibration_temp'])
    material = params.get('MATERIAL', vars['default_material']).upper()
    emit('PREHEAT STARTUP=1 HOTEND_TEMP=%s BED_TEMP=%s TARGET_CHAMBER_TEMP=%s MATERIAL="%s"' % (
        hotend, params.get('BED_TEMP', 0), params.get('TARGET_CHAMBER_TEMP', 0), material))
except Exception as error:
    emit('CANCEL_PRINT')
    set_gcode_variable('_FLEET_ALERT_STATE', 'failure', str(error))
    emit('_FLEET_NOTIFY EVENT=startup_failed')
    raise
