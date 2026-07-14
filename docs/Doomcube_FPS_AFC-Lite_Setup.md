# Doomcube FPS + AFC-Lite Setup Guide

> **Status (2026-07-07):** This is the original bring-up guide (2026-05), kept for re-flash/rebuild reference. What has changed since it was written:
>
> - Both the FPS and the MMU board now run the **Katapult** bootloader — routine reflashes go through `katapult-helper` (`~/git/katapult-helper`, inventory on the Pi), not the DFU procedures below. DFU is only needed to recover a bricked bootloader.
> - The original AFC-Lite (STM32G0B1, as described in Part 5) was **damaged and replaced**. The current board enumerates as `stm32h723xx` (serial in `mmu/base/mmu.cfg`) — Part 5's build settings do not apply to it; check the katapult-helper inventory for the correct STM32H723 profile.
> - Klipper config moved from the AFC plugin to **Happy Hare**: the board is `[mcu mmu]` in `mmu/base/mmu.cfg`. Part 6's `AFC/AFC_Turtle_1.cfg` / `[mcu BoxTurtle]` instructions are obsolete. FPS MCU config lives in `custom/mcus/fps.cfg` (canbus_uuid `0e8ab784e48c`); EBB36 in `custom/mcus/ebb36.cfg` (canbus_uuid `1586f2c37eaf`).

## System Topology

```
                          ┌─────────────────┐
                          │   Raspberry Pi   │
                          └────────┬─────────┘
                                   │ USB-C
                          ┌────────▼─────────┐
                    24V──►│     FPS Board     │◄── Hall effect sensor (built-in)
                          │  (CAN Bridge +   │
                          │  Pressure Sensor) │
                          ├──────────┬────────┤
                  USB OUT │          │ CAN H/L
                          │          │
               ┌──────────▼──┐  ┌───▼──────────┐
         24V──►│  AFC-Lite    │  │   EBB36      │◄── 120R termination ON
               │ (Boxturtle)  │  │  (Toolhead)  │
               └──────────────┘  └──────────────┘
```

Three MCUs in Klipper, two physical USB connections through one cable to the Pi.


---

## Part 1: Remove the U2C

1. Power down the printer completely
2. Disconnect the U2C USB cable from the Pi
3. Disconnect CAN H/L wires from the U2C going to the EBB36
4. Disconnect 24V power from the U2C
5. Remove the U2C from the printer — it's no longer needed


---

## Part 2: Wire the FPS Board

### Power

- **PSU +24V IN** → 24V from printer PSU
- **PSU GND IN** → PSU ground

> **Warning:** The FPS has a crowbar over-voltage protection circuit. If input exceeds ~27V, it blows the onboard fuse to protect the board. Make sure your PSU is outputting clean 24V.

### Data (USB to Pi)

- **USB-C IN** → Raspberry Pi USB port
- Use a data-capable USB-C cable (not power-only)

### CAN Bus (to EBB36 toolhead)

- **FPS CAN H terminal** → EBB36 CAN H (same wires that were on the U2C)
- **FPS CAN L terminal** → EBB36 CAN L

### Jumpers

- **120R termination jumper** → **OFF** (because CAN toolhead output is in use; termination stays on the EBB36 as the last device in the chain)
- **BOOT jumper** → OFF for normal operation (ON only during DFU flashing)

### FPS USB OUT (for AFC-Lite)

- Leave this port open for now — the AFC-Lite will plug in here after it's flashed


---

## Part 3: Flash the FPS Board

### Build Klipper firmware for the FPS

```bash
cd ~/klipper
make menuconfig
```

Settings:

```
[*] Enable extra low-level configuration options
    Micro-controller Architecture: STMicroelectronics STM32
    Processor model: STM32G0B1
    Bootloader offset: No bootloader
    Clock Reference: 8 MHz crystal
    Communication interface: USB to CAN bus bridge (USB on PA11/PA12)
    CAN bus interface: CAN bus (on PB0/PB1)
    CAN bus speed: 1000000
```

```bash
make clean
make
```

### Flash via DFU

1. Place jumper on **BOOT** pins
2. Connect USB-C IN to the Pi
3. Verify DFU device is visible:

```bash
lsusb
```

Look for `STMicroelectronics STM Device in DFU Mode` (0483:df11).

4. Flash:

```bash
sudo dfu-util -d 0483:df11 -a 0 -R -D ~/klipper/out/klipper.bin -s0x08000000:leave
```

5. Disconnect USB-C IN
6. Remove BOOT jumper
7. Reconnect USB-C IN

### Verify

```bash
lsusb
```

You should see two new devices:
- **OpenMoko, Inc. Geschwister Schneider CAN adapter** (the CAN bridge)
- **QinHeng Electronics USB HUB** (the built-in USB hub)

If the QinHeng hub doesn't appear, check your USB cable — it may be power-only.


---

## Part 4: Configure CAN Bus on the Pi

If CAN was already working with the U2C, this should come up automatically. Verify:

```bash
sudo ip link set can0 up type can bitrate 1000000
ip -s link show can0
```

If `can0` doesn't exist, follow the Klipper CAN bus docs or Esoterical's guide to set up the interface file:

```bash
# /etc/network/interfaces.d/can0
auto can0
iface can0 can static
    bitrate 1000000
    up ip link set $IFACE txqueuelen 1024
```

Then:

```bash
sudo systemctl restart networking
```

### Query for UUIDs

```bash
~/klippy-env/bin/python ~/klipper/scripts/canbus_query.py can0
```

You should see **two UUIDs**: the FPS board itself (bridge MCU) and the EBB36.

**Write both UUIDs down.** The FPS UUID goes in the oams/FPS config section; the EBB36 UUID goes in your toolhead MCU config (same as before, it shouldn't change).


---

## Part 5: Flash the AFC-Lite Board

The AFC-Lite runs over USB serial, connected through the FPS board's USB OUT port.

### Build Klipper firmware for the AFC-Lite

```bash
cd ~/klipper
make clean
make menuconfig
```

Settings:

```
[*] Enable extra low-level configuration options
    Micro-controller Architecture: STMicroelectronics STM32
    Processor model: STM32G0B1
    Bootloader offset: No bootloader
    Clock Reference: 8 MHz crystal
    Communication interface: USB (on PA11/PA12)
```

```bash
make
```

### Flash via DFU

1. Connect the AFC-Lite directly to the Pi via USB-C (use a Pi USB port for initial flash, not the FPS hub)
2. Put the AFC-Lite into DFU mode: hold **BOOT**, press and release **RESET**, count to 5, release **BOOT**
3. Verify:

```bash
lsusb
```

Look for the STM32 DFU device (0483:df11).

4. Flash:

```bash
sudo dfu-util -d 0483:df11 -a 0 -R -D ~/klipper/out/klipper.bin -s0x08000000:leave
```

5. Disconnect from Pi, reconnect to the **FPS USB OUT** port

### Wire 24V to the AFC-Lite

Even though data runs over USB, the AFC-Lite needs 24V for the stepper drivers. Run **24V+ and GND** to the AFC-Lite CAN bus connector — leave the CAN H/L pins unpopulated.

### Get the serial path

```bash
ls /dev/serial/by-id/*
```

Look for a path like `/dev/serial/by-id/usb-Klipper_stm32g0b1xx_XXXX-if00`. This is the AFC-Lite's serial address for Klipper config.


---

## Part 6: Klipper Configuration

### FPS MCU section

Add to your printer config (or oams.cfg):

```ini
[mcu fps]
canbus_uuid: <FPS_UUID_FROM_STEP_4>
```

### EBB36 MCU section

Same as before, just confirm UUID hasn't changed:

```ini
[mcu EBBCan]
canbus_uuid: <EBB36_UUID>
```

### AFC-Lite MCU section

In your AFC config (e.g., `AFC/AFC_Turtle_1.cfg`):

```ini
[mcu BoxTurtle]
serial: /dev/serial/by-id/usb-Klipper_stm32g0b1xx_XXXX-if00
```

Make sure the `canbus_uuid` line is commented out since you're using USB serial.

### AFC-Lite stepper sense resistor

In the AFC stepper config, make sure:

```ini
sense_resistor: 0.110
```

This is the correct value for the TMC2209 drivers on the AFC-Lite.


---

## Part 7: Verification Checklist

After restarting Klipper:

- [ ] `lsusb` shows CAN bridge adapter + QinHeng USB hub
- [ ] `can0` interface is up (`ip link show can0`)
- [ ] FPS UUID responds on CAN bus query
- [ ] EBB36 UUID responds on CAN bus query
- [ ] AFC-Lite serial path exists in `/dev/serial/by-id/`
- [ ] Klipper starts without MCU connection errors
- [ ] FPS LED is on (if LED is off, check the fuse)
- [ ] FPS Hall sensor readings change when slide is moved
- [ ] AFC-Lite steppers respond to manual movement commands
- [ ] EBB36 toolhead functions normally (heater, fan, probe, etc.)


---

## Troubleshooting

**FPS not showing up in lsusb:**
Check USB cable (must be data-capable). Try a different Pi USB port. Verify BOOT jumper is removed.

**QinHeng USB HUB missing:**
The hub should always appear when the FPS is powered and USB is connected, regardless of firmware state. If missing, possible board fault.

**AFC-Lite serial not found after moving to FPS USB OUT:**
The FPS hub is a standard USB hub — the serial path should be the same. If not found, try plugging the AFC-Lite back into the Pi directly to confirm it works, then try the FPS USB OUT again. Power cycle the FPS.

**CAN UUID query returns nothing:**
Check 24V power to FPS. Verify `can0` is up. Confirm Klipper firmware was built with correct CAN bridge settings.

**Katapult bootloader issues:**
If using Katapult and the bootloader won't enter, use the known-good commit:
```bash
cd ~/katapult
git checkout 081918ad769d1f1104ca253a4a8ace02147c345d
make clean && make
```

**FPS fuse blown (LED off, no response):**
Likely over-voltage event (PSU > ~27V). Check PSU output with a multimeter. The fuse is a sacrificial protection — board needs the fuse replaced.

**Grounding / static issues with AFC-Lite:**
In dry environments, static from PTFE tubing can cause intermittent errors. Run a ground wire from the stepper motor screws to a common GND pin on the AFC-Lite board.


---

## Reference Links

- OpenAMS Documentation: https://openams.si-forge.com
- FPS GitHub: https://github.com/OpenAMSOrg/filament-buffer
- AFC-Lite Manual: https://github.com/xbst/AFC-Lite
- Armored Turtle Docs: https://www.armoredturtle.xyz
- Esoterical USB Flashing: https://usb.esoterical.online
- Klipper CAN Bus: https://www.klipper3d.org/CANBUS.html
- OpenAMS Discord: https://discord.gg/Ab8TrGarpu
