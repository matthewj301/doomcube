vars = printer["gcode_macro _PRINTER_VARS"]
chamber_target = float(params.get("TARGET_CHAMBER_TEMP", vars["default_chamber_target"]))
bed_target = float(params.get("BED_TEMP", vars["chamber_heat_default_bed_temp"]))
hotend_target = float(params.get("HOTEND_TEMP", vars["default_chamber_assist_extruder_temp"]))
pattern = params.get("PATTERN", "auto").lower()
interval_s = float(params.get("INTERVAL_S", vars["chamber_status_interval"]))

sensor_name = vars["chamber_sensor_name"]
sensor_key = f"temperature_sensor {sensor_name}"

if chamber_target <= 0 or sensor_key not in printer:
    respond_info(f"!! Chamber sensor missing or TARGET<=0 (sensor='{sensor_key}')")
else:
    emit("MAYBE_HOME")
    respond_info(f"Chamber heat: pattern={pattern}, target={chamber_target}C")
    emit(f"M140 S{bed_target}")
    emit(f"M104 S{hotend_target}")

    z_speed = int(float(vars["z_travel_speed"]) * 60)
    emit("CHAMBER_FANS_ON")
    emit("G90")
    emit(f"G1 Z{float(vars['chamber_printhead_height'])} F{z_speed}")
    emit(f"M106 S{int(255 * float(vars['chamber_printhead_fan_speed']))}")
    set_gcode_variable("TA_CHAMBER_STATE", "stop", 0)

    wait_moves()

    max_cycles = int(vars["chamber_heat_max_cycles"])
    reached = False

    for cycle in range(max_cycles):
        if int(printer["gcode_macro TA_CHAMBER_STATE"]["stop"]) == 1:
            emit("TURN_PART_COOLING_FAN_OFF")
            respond_info("Chamber mixing aborted by user")
            break

        if printer[sensor_key]["temperature"] >= chamber_target:
            emit(f"M190 S{bed_target}")
            emit(f"M109 S{hotend_target}")
            emit("TURN_PART_COOLING_FAN_OFF")
            respond_info(f"Chamber reached {round(chamber_target, 1)}C - mixing complete")
            reached = True
            break

        x_min = printer["toolhead"]["axis_minimum"][0]
        x_max = printer["toolhead"]["axis_maximum"][0]
        y_min = printer["toolhead"]["axis_minimum"][1]
        y_max = printer["toolhead"]["axis_maximum"][1]
        bed_avg = ((x_max - x_min) + (y_max - y_min)) / 2.0

        if bed_avg >= 400:
            move_speed_mmps = float(vars["chamber_move_speed_fast"])
            bed_margin = 40
        elif bed_avg >= 300:
            move_speed_mmps = float(vars["chamber_move_speed_medium"])
            bed_margin = 30
        else:
            move_speed_mmps = float(vars["chamber_move_speed_slow"])
            bed_margin = 20

        move_speed = int(move_speed_mmps * 60)
        safe_x_min = x_min + bed_margin
        safe_x_max = x_max - bed_margin
        safe_y_min = y_min + bed_margin
        safe_y_max = y_max - bed_margin
        cx = (x_min + x_max) / 2.0
        cy = (y_min + y_max) / 2.0

        z_req = float(vars["chamber_printhead_height"])
        z_lo = printer["toolhead"]["axis_minimum"][2] + 2
        z_hi = printer["toolhead"]["axis_maximum"][2] - 2
        mix_z = max(z_lo, min(z_hi, z_req))

        emit("G90")
        emit(f"G1 Z{mix_z} F{move_speed}")

        if pattern == "grid":
            gx = [safe_x_min, (safe_x_min + safe_x_max) / 2, safe_x_max]
            gy = [safe_y_min, (safe_y_min + safe_y_max) / 2, safe_y_max]
            for y in gy:
                for x in gx:
                    emit(f"G1 X{x} Y{y} F{move_speed}")
                    emit("G4 P200")
        elif pattern == "corners":
            for x, y in [(safe_x_min, safe_y_min), (safe_x_max, safe_y_min),
                          (safe_x_max, safe_y_max), (safe_x_min, safe_y_max)]:
                emit(f"G1 X{x} Y{y} F{move_speed}")
                emit("G4 P350")
            emit(f"G1 X{cx} Y{cy} F{move_speed}")
            emit("G4 P250")
        elif pattern == "vortex":
            max_r = min(safe_x_max - cx, safe_y_max - cy)
            for s in [1.0, 0.75, 0.5, 0.25]:
                R = s * max_r
                for angle_deg in range(0, 360, 45):
                    rad = math.radians(angle_deg)
                    emit(f"G1 X{cx + R * math.cos(rad)} Y{cy + R * math.sin(rad)} F{move_speed}")
        else:
            emit(f"G1 X{safe_x_min} Y{safe_y_min} F{move_speed}")
            emit(f"G1 X{safe_x_max} Y{safe_y_min} F{move_speed}")
            emit(f"G1 X{safe_x_max} Y{safe_y_max} F{move_speed}")
            emit(f"G1 X{safe_x_min} Y{safe_y_max} F{move_speed}")
            emit(f"G1 X{safe_x_min} Y{safe_y_min} F{move_speed}")
            emit(f"G1 X{cx} Y{safe_y_min} F{move_speed}")
            emit(f"G1 X{cx} Y{safe_y_max} F{move_speed}")
            emit(f"G1 X{cx} Y{cy} F{move_speed}")
            emit(f"G1 X{safe_x_min} Y{cy} F{move_speed}")
            emit(f"G1 X{safe_x_max} Y{cy} F{move_speed}")
            emit(f"G1 X{cx} Y{cy} F{move_speed}")
            emit(f"G1 X{cx} Y{safe_y_min} F{move_speed}")

        wait_moves()
        sleep(interval_s)

    if not reached and cycle == max_cycles - 1:
        emit("TURN_PART_COOLING_FAN_OFF")
        respond_info(f"Chamber heating exceeded {max_cycles} cycles without reaching {chamber_target}C - continuing with print")
