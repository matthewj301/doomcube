import time
state = printer['gcode_macro TA_CHAMBER_STATE']
if state['active']:
    job = dict(state['job'])
    vars = printer['gcode_macro _PRINTER_VARS']
    try:
        if job['sd_owned']:
            stats = printer['print_stats']
            if stats['state'] in ('cancelled', 'error') or stats['filename'] != job['filename']:
                raise_error('Preheat: print was cancelled, failed, or replaced')
        # Cancelling via a UI heater-off control also stops the scheduled continuation.
        if printer['heater_bed']['target'] != job['bed'] or printer['extruder']['target'] != job['hotend']:
            raise_error('Preheat: heater targets changed; stopping pending startup')
        now = time.monotonic()
        heaters_ready = ((job['bed'] == 0 or abs(printer['heater_bed']['temperature']-job['bed']) <= 2)
                         and (job['hotend'] == 0 or abs(printer['extruder']['temperature']-job['hotend']) <= 2))
        chamber_ready = job['chamber'] == 0 or printer[job['sensor']]['temperature'] >= job['chamber']-job['delta']
        expired = now >= job['deadline'] or job['cycles'] >= int(vars['chamber_heat_max_cycles'])
        complete = False
        if expired:
            if job['policy'] == 'continue' and heaters_ready:
                respond_info('WARNING: preheat deadline/cycle limit reached; continuing by explicit ON_TIMEOUT=continue policy')
                complete = True
            else:
                raise_error('Preheat timed out; startup cancelled (required temperatures/soak not reached)')
        elif heaters_ready and chamber_ready:
            if job['ready_since'] is None:
                job['ready_since'] = now
                respond_info('Preheat targets reached; soaking for %s seconds' % job['soak'])
            complete = now-job['ready_since'] >= job['soak']
        else:
            job['ready_since'] = None
        if complete:
            set_gcode_variable('TA_CHAMBER_STATE', 'active', False)
            emit('UPDATE_DELAYED_GCODE ID=_TA_CHAMBER_TIMER DURATION=0')
            emit('M107')
            respond_info('Preheat complete')
            if job['startup']:
                # Errors in the continuation are caught here; SD never resumes on failure.
                emit('_PRINT_START_AFTER_PREHEAT')
                emit('_PRINT_START_CHECK_READY')
                start = printer['gcode_macro _PRINT_START_STATE']
                resume_sd = start['sd_paused']
                if resume_sd and printer['print_stats']['filename'] != job['filename']:
                    raise_error('PRINT_START: SD file changed during startup')
                set_gcode_variable('_PRINT_START_STATE', 'active', False)
                set_gcode_variable('_PRINT_START_STATE', 'sd_paused', False)
                set_gcode_variable('_FLEET_ALERT_STATE', 'startup_failure_file', None)
                if resume_sd:
                    set_gcode_variable('_FLEET_ALERT_STATE', 'observed',
                                       dict(state='printing', filename=job['filename'],
                                            paused_since=None, pause_notified=False))
                    emit('M24')
        else:
            if job['points'] and not chamber_ready:
                if printer['toolhead']['homed_axes'] != 'xyz':
                    raise_error('Preheat: homing was lost while mixing')
                # Each tick owns and restores its motion state; no long-lived saved state.
                accel = printer['toolhead']['max_accel']
                emit('SAVE_GCODE_STATE NAME=_CHAMBER_STEP')
                try:
                    emit('SET_VELOCITY_LIMIT ACCEL=%s' % float(vars['travel_accel']))
                    emit('G90')
                    emit('G1 Z%s F%s' % (job['z'], float(vars['z_travel_speed'])*60))
                    point = job['points'][job['index']]
                    emit('G1 X%s Y%s F%s' % (point[0],point[1],job['speed']*60))
                    emit('M106 S%s' % int(255*float(vars['chamber_printhead_fan_speed'])))
                    wait_moves()
                finally:
                    emit('RESTORE_GCODE_STATE NAME=_CHAMBER_STEP')
                    emit('SET_VELOCITY_LIMIT ACCEL=%s' % accel)
                job['index'] = (job['index']+1) % len(job['points'])
                if job['index'] == 0:
                    job['cycles'] += 1
            else:
                emit('M107')
            set_gcode_variable('TA_CHAMBER_STATE', 'job', job)
            emit('UPDATE_DELAYED_GCODE ID=_TA_CHAMBER_TIMER DURATION=%s' % job['interval'])
    except Exception as error:
        # delayed_gcode only logs exceptions; explicitly shut down and cancel here.
        emit('TURN_OFF_HEATERS_BASE')
        emit('M107')
        if job['startup']:
            emit('CANCEL_PRINT')
        else:
            emit('_TA_CHAMBER_RESET')
        set_gcode_variable('_FLEET_ALERT_STATE', 'failure', str(error))
        emit('_FLEET_NOTIFY EVENT=%s' % ('startup_failed' if job['startup'] else 'preheat_failed'))
        raise
