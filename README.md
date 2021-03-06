
# Husqvarna automower node server

This is the Husqvarna automower node server for the [Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2)
(c) 2018 Robert Paauwe
MIT license.

This node server is intended to interact with Husqvarna Automowers. It can track the mowers status and send commands to control the mower.[Husqvarna](http://www.husqvarnagroup.com/en/automower-435x-awd) You will need account access to your mower(s) via the Automower API. 

Currently, only one mower is supported.

## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. Configure the node server with your account username and password.

### Node Settings
The settings for this node are:

#### Short Poll
   * Query mower status.
#### Long Poll
   * Not used

#### Username
   * Your Husqvarna account username

#### Password
   * Your Husqvarna account password


## Requirements

1. Polyglot V2 itself should be run on Raspian Stretch.
  To check your version, ```cat /etc/os-release``` and the first line should look like
  ```PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"```. It is possible to upgrade from Jessie to
  Stretch, but I would recommend just re-imaging the SD card.  Some helpful links:
   * https://www.raspberrypi.org/blog/raspbian-stretch/
   * https://linuxconfig.org/raspbian-gnu-linux-upgrade-from-jessie-to-raspbian-stretch-9
2. This has only been tested with ISY 5.0.13 so it is not guaranteed to work with any other version.

# Upgrading

Open the Polyglot web page, go to nodeserver store and click "Update" for "Husqvarna automower".

For Polyglot 2.0.35, hit "Cancel" in the update window so the profile will not be updated and ISY rebooted.  The install procedure will properly handle this for you.  This will change with 2.0.36, for that version you will always say "No" and let the install procedure handle it for you as well.

Then restart the Husqvarna automower nodeserver by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

The Husqvarna automower nodeserver keeps track of the version number and when a profile rebuild is necessary.  The profile/version.txt will contain the Husqvarna automower profile_version which is updated in server.json when the profile should be rebuilt.

# Release Notes

- 1.0.4 08/05/2020
   - fix syntax error
- 1.0.3 08/05/2020
   - re-authenticate if get status fails.
- 1.0.2 10/21/2019
   - handle max retry errors properly.
- 1.0.1 07/23/2019
   - Change mower mode to mowing mode to better reflect what's being reported
   - Fix connection status reporting
- 1.0.0 07/16/2019
   - First public release
- 0.0.2 07/02/2019
   - Updated profile files to add pause command, set the start override period, and added additional status info.
- 0.0.1 05/03/2019
   - Initial version published to github
