vars = printer['gcode_macro _PRINTER_VARS']
alert = printer['gcode_macro _FLEET_ALERT_STATE']
event = params.get('EVENT', 'status')
filename = printer['print_stats']['filename'] if 'print_stats' in printer else ''
labels = {'complete': 'Print complete', 'startup_failed': 'Print startup failed',
          'print_failed': 'Print failed', 'prolonged_pause': 'Print remains paused',
          'preheat_failed': 'Preheat failed'}
message = '%s: %s' % (vars['notification_printer_name'], labels.get(event, event))
if filename:
    message += ' — ' + filename
if event in ('startup_failed', 'preheat_failed'):
    message += ': ' + alert['failure']
if event == 'print_failed':
    message += ': ' + printer['print_stats']['message']
if event == 'startup_failed':
    set_gcode_variable('_FLEET_ALERT_STATE', 'startup_failure_file', filename)
respond_info(message)
name = vars['notification_name']
if name:
    # Delivery errors must never interrupt motion, cleanup or resume.
    try:
        call_remote_method('notify', name=name, message=message)
    except Exception as error:
        respond_info('Notification delivery unavailable: %s' % error)
