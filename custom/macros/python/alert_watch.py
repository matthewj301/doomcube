import time
try:
    if 'print_stats' in printer:
        stats = printer['print_stats']
        state = printer['gcode_macro _FLEET_ALERT_STATE']
        observed = dict(state['observed'])
        current = stats['state']
        filename = stats['filename']
        previous = observed.get('state')
        same_file = observed.get('filename') == filename
        startup = printer['gcode_macro _PRINT_START_STATE']['active']
        # Do not replay historical completion/error just because firmware restarted.
        if previous is not None and (current != previous or not same_file):
            if current == 'complete':
                emit('_FLEET_NOTIFY EVENT=complete')
            elif current == 'error' and state['startup_failure_file'] != filename:
                emit('_FLEET_NOTIFY EVENT=print_failed')
        if current == 'printing' and not startup:
            set_gcode_variable('_FLEET_ALERT_STATE', 'startup_failure_file', None)
        paused = printer['pause_resume']['is_paused'] or current == 'paused'
        now = time.monotonic()
        if paused and not startup:
            since = observed.get('paused_since') if same_file else None
            if since is None:
                since = now
                observed['pause_notified'] = False
            observed['paused_since'] = since
            delay = float(printer['gcode_macro _PRINTER_VARS']['notification_pause_seconds'])
            if delay > 0 and now-since >= delay and not observed.get('pause_notified', False):
                emit('_FLEET_NOTIFY EVENT=prolonged_pause')
                observed['pause_notified'] = True
        else:
            observed['paused_since'] = None
            observed['pause_notified'] = False
        observed['state'] = current
        observed['filename'] = filename
        set_gcode_variable('_FLEET_ALERT_STATE', 'observed', observed)
finally:
    emit('UPDATE_DELAYED_GCODE ID=_FLEET_ALERT_TIMER DURATION=5')
