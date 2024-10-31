# Readme

![icon](https://github.com/user-attachments/assets/8be7ce6d-c8d2-4e99-9ca8-609846483845)

This is a custom component to control your SimpleEVSE-WiFi car charger controller made by SmartWB in Home Assistant (https://github.com/CurtRod/SimpleEVSE-WiFi) (https://www.smartwb.de/)

# What is working:
 - Turn on and off switch
 - Current amp slider with dynamic reading of max amp setting
 - All available sensors from the charger controller
 - Loging of all error messages sent by the controller
 - Icon change reflecting current vehicle state
 - You can use the switch or amp settings in automations

![839832dd098fef8a1b070222866d5daa618d7142](https://github.com/user-attachments/assets/20f7635d-5273-453c-b573-0691ead9fedd)


# Install with HACS recomended:
It is possible to add it as a custom repository.

If you are using HACS, go to HACS -> Integrations and click on the 3 dots (top righ corner).
Then choose custom repositories, and add this repository url (https://github.com/DominikWrobel/SmartWB), choosing the Integration category.

That's it, and you will be notified by HACS on every release.
Just click on upgrade.

# Manual install:
To use the SmartWB custom component, place the file `SmartWB` directory from the root of
the repository in to the folder `~/.homeassistant/custom_components/` where
you have your home assistant installation

The custom components directory is inside your Home Assistant configuration directory.

This is how your custom_components directory should be:
```bash
custom_components
├── SmartWB
│   ├── __init__.py
│   ├── manifest.json
│   ├── number.py
│   ├── config_flow.py
│   ├── const.py
│   ├── strings.json
│   ├── sensor.py
│   ├── switch.py
│   ├── translations
│   │   └── en.json
```

# Configuration Example:
Search for SmartWB in Settings -> devices and services:

![Przechwytywanie](https://github.com/user-attachments/assets/c7d62fad-6c0f-4c96-9bb8-d36b66ecf452)


# Support

If you like my work you can support me via:

<figure class="wp-block-image size-large"><a href="https://www.buymeacoffee.com/dominikjwrc"><img src="https://homeassistantwithoutaplan.files.wordpress.com/2023/07/coffe-3.png?w=182" alt="" class="wp-image-64"/></a></figure>

# Special thanks to:
@kodacy for motivating me to make this integration and for the great icons.
