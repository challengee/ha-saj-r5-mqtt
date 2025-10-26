# SAJ R5 solar inverter (MQTT)

Home Assistant integration for SAJ R5 solar inverters. \
This custom integration provides MQTT integration for SAJ R5 solar inverters (Sununo Plus and Suntrio Plus series). \
**DISCLAIMER:** I won't be responsible for any kind of loss during its usage, the integration is provided AS-IS.

## Supported Models

This integration supports SAJ R5 series inverters:
- **Sununo Plus** (single-phase, 1-2 MPPT): Device types 0x0011, 0x0012
- **Suntrio Plus** (three-phase): Device type 0x0021

**Note:** This integration is specifically for R5 series (on-grid solar inverters). If you have an H1 series (hybrid storage inverter with battery), please use the separate `saj_h1_mqtt` integration.

## Configure Home Assistant MQTT broker

This integration uses the MQTT services already configured in Home Assistant to communicate with the inverter and retrieve the data. \
For this reason you need to first setup a broker and configure Home Assistant to talk to using the standard MQTT integration. \
Of course, if you already have MQTT configured, you don't need to do this again.

## Configure the inverter

The last step is to configure the inverter (actually the Wifi communication module AIO3 attached to the inverter) to talk with the local MQTT broker and not directly with the SAJ broker. \
To do that, you have 3 options:
- Change the MQTT broker using the SAJ [eSolar O&M](https://play.google.com/store/apps/details?id=com.saj.operation) app to your local MQTT broker.
- Poison your local DNS to redirect the MQTT messages to your broker. This consists in telling your home router to point to your broker IP when domain **mqtt.saj-solar.com** is queried by the inverter. Refer to your router capabilities to handle this. This may require some time for the inverter to discover that the broker IP changed, so you may want to remove and reinstall the Wifi AIO3 module to restart it.
- Setup a bridge on your local MQTT broker to the SAJ mqtt broker if you still want to use the SAJ [Home](https://play.google.com/store/apps/details?id=com.saj.home) app. For instructions, see [here](https://github.com/paolosabatino/saj-mqtt-ha/discussions/4).

## Install the integration

### Option 1: via HACS

- Add a custom integration repository to HACS: https://github.com/challengee/ha-saj-r5-mqtt
- Once the repository is added, use the search bar and type "SAJ R5 solar inverter (MQTT)"
- Download the integration by using the `Download` button
- Restart Home Assistant
- Setup the integration as described below (see: Setting up the integration)

### Option 2: manual installation

- In the `custom_components` directory of your home assistant system create a directory called `saj_r5_mqtt`.
- Download all the files from `/custom_components/saj_r5_mqtt/` directory in this repository and place them in the `saj_r5_mqtt` directory you created before.
- Restart Home Assistant
- Setup the integration as described below (see: Setting up the integration)

## Setting up the integration

- Go to Configuration -> Integrations and add "SAJ R5 solar inverter (MQTT)" integration
- Provide the serial number of your inverter
- Specify the realtime data scan interval
- Optionally, if you would have multiple inverters, you can include the serial number in the sensor names
- Click submit to enable the integration
- Optionally, you can configure the integration again to:
    - include additional data:
        - inverter data (device info, serial number, versions)
        - config data (power limit, inverter time)
    - enable accurate realtime power data
    - enable mqtt debugging (for debugging purposes)

## Features

### Real-time Monitoring
- **PV Data**: Voltage, current, and power for PV1, PV2, and PV3 (for multi-MPPT models)
- **Grid Data**:
  - Single-phase models: L1 voltage, current, frequency, DCI, power, power factor
  - Three-phase models (Suntrio): L1, L2, L3 voltage, current, frequency, DCI, power, power factor
- **Power Metrics**: Total power, reactive power, power factor
- **Inverter Status**: Working mode, temperature, bus voltage, GFCI
- **Isolation**: ISO1, ISO2, ISO3, ISO4 sensors
- **Energy Statistics**: Today, month, year, and total energy generation
- **Operating Hours**: Today and total operating hours
- **Error Tracking**: Error count sensor
- **Time Sync**: Inverter time sensor

### Device Information
- Device type (auto-detected)
- Serial number
- Product code
- Protocol version
- Software versions (display, master controller, slave controller)
- Hardware versions (display, controller, power)

### Configuration
- Power limit percentage
- Scan interval configuration for different data types

## HA Services

This integration also exposes a few services that can be used from within home assistant. \
The following services are available:
- `saj_r5_mqtt.read_register`, to read a value of any register
- `saj_r5_mqtt.write_register`, to write a value to any register (USE AT OWN RISK AS THIS CAN DAMAGE YOUR INVERTER!)
- `saj_r5_mqtt.refresh_inverter_data`, to refresh the inverter data sensors
- `saj_r5_mqtt.refresh_config_data`, to refresh the config data sensors

## Register Mapping

The R5 series uses different register addresses compared to the H1 series:
- **Realtime data**: 0x0100-0x0137 (56 registers)
- **Inverter info**: 0x8F00-0x8F1C (29 registers)
- **Config data**: 0x801F-0x8023 (5 registers)

See the [changes.md](changes.md) file for detailed register mapping information.

## Three-Phase Support

The integration automatically detects three-phase Suntrio Plus models (device type 0x0021) and enables L2 and L3 phase sensors accordingly. Single-phase models will only show L1 sensors.

## Differences from H1 Integration

The R5 series is an **on-grid solar inverter** without battery storage capabilities. Key differences:
- ❌ No battery sensors or controls
- ❌ No hybrid operation modes (self-use, time-of-use, backup, passive)
- ❌ No grid import/export energy tracking
- ❌ No backup load monitoring
- ✅ Simpler register structure (56 vs 256 registers)
- ✅ Three-phase support (Suntrio Plus)
- ✅ PV3 support for multi-MPPT models
- ✅ Reactive power and power factor sensors
- ✅ Operating hours tracking

## Troubleshooting

### No data received
- Verify MQTT broker is configured correctly
- Check that the inverter is sending data to your local MQTT broker
- Enable MQTT debugging in the integration options
- Check Home Assistant logs for errors

### Three-phase sensors not showing
- Verify your model is Suntrio Plus (device type should show 0x0021)
- Check the inverter data coordinator is enabled
- Restart Home Assistant after configuration changes

## Credits

Based on the original SAJ H1 MQTT integration by h3llrais3r and paolosabatino, adapted for R5 series inverters.

## License

This integration is provided AS-IS without any warranty. Use at your own risk.
