# Yale Access Bluetooth Activity for Home Assistant

[![HACS](https://img.shields.io/badge/custom-grey?logo=homeassistantcommunitystore&logoColor=white)][hacs-repo]
[![HACS installs](https://img.shields.io/github/downloads/wbyoung/yalexs-ble-activity/latest/total?label=installs&color=blue)][hacs-repo]
[![Version](https://img.shields.io/github/v/release/wbyoung/yalexs-ble-activity)][releases]
![Downloads](https://img.shields.io/github/downloads/wbyoung/yalexs-ble-activity/total)
![Build](https://img.shields.io/github/actions/workflow/status/wbyoung/yalexs-ble-activity/pytest.yml)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-grey?&logo=GitHub-Sponsors&logoColor=EA4AAA)][gh-sponsors]

Activity history sensor for Yale Access Bluetooth.

## Installation

### HACS

Installation through [HACS][hacs] is the preferred installation method.

1. Go to the HACS dashboard.
1. Click the ellipsis menu (three dots) in the top right &rarr; choose _Custom repositories_.
1. Enter the URL of this GitHub repository,
   `https://github.com/wbyoung/yalexs-ble-activity`, in the _Repository_ field.
1. Select _Integration_ as the category.
1. Click _Add_.
1. Search for "Yale Access Bluetooth Activity" &rarr; select it &rarr; press _DOWNLOAD_.
1. Press _DOWNLOAD_.
1. Select the version (it will auto select the latest) &rarr; press _DOWNLOAD_.
1. Restart Home Assistant then continue to [the setup section](#setup).

### Manual Download

1. Go to the [release page][releases] and download the `yalexs_ble_activity.zip` attached
   to the latest release.
1. Unpack the zip file and move `custom_components/yalexs_ble_activity` to the following
   directory of your Home Assistant configuration: `/config/custom_components/`.
1. Restart Home Assistant then continue to [the setup section](#setup).

## Setup

Open your Home Assistant instance and start setting up by following these steps:

1. Navigate to "Settings" &rarr; "Devices & Services"
1. Click "+ Add Integration"
1. Search for and select &rarr; "Yale Access Bluetooth Activity"

Or you can use the My Home Assistant Button below.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)][config-flow-start]

Follow the instructions to configure the integration.

## Entities

One _sensor_ entity is created for for selected lock:

### `sensor.<lock_name>_operation`

The last operation of the door or lock. One of:

- `door_unknown`
- `door_closed`
- `door_ajar`
- `door_opened`
- `lock_unknown`
- `lock_unlocking`
- `lock_unlocked`
- `lock_locking`
- `lock_locked`

The sensor value will only change to the most recent value obtained and will skip over activity to avoid rapid state changes. To create automations that trigger on any activity, use the [`yalexs_ble_activity` event](#yalexs_ble_activity)

#### Attributes

- `timestamp`: The time of the activity.
- `source`: The source of a lock operation. Possible values: `remote`, `manual`, `auto_lock`, `pin` or `unknown`. Not present for door related activity.
- `remote_type`: The type of remote operation performed. Not present for door related activity.
- `slot`: This is a unique integer representing the code used. Only present for unlock activity with `source=pin`.

## Events

### `yalexs_ble_activity`

An event emitted immediately when new activity is received.

This will be triggered for all activity that is received from the lock regardless of how old it is. Even for the most recent activity, however, the state of the [`sensor.<lock_name>_operation`](#sensorlock_name_operation) sensor entity will not yet be updated at the time this event is fired. (State updates are deferred for a short period to ensure all activity has been read from the lock.)

#### Event Data

- `state`: The state of the activity which mirrors that of [`sensor.<lock_name>_operation`](#sensorlock_name_operation).
- `attributes`: The attributes for the activity which mirrors that of the [`sensor.<lock_name>_operation`](#sensorlock_name_operation) attributes.

[config-flow-start]: https://my.home-assistant.io/redirect/config_flow_start/?domain=yalexs_ble_activity
[hacs]: https://hacs.xyz/
[hacs-repo]: https://github.com/hacs/integration
[hacs-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-open]: https://my.home-assistant.io/redirect/hacs_repository/?owner=wbyoung&repository=yalexs-ble-activity&category=integration
[releases]: https://github.com/wbyoung/yalexs-ble-activity/releases
[gh-sponsors]: https://github.com/sponsors/wbyoung
