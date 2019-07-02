#!/usr/bin/env python3
"""
Polyglot v2 node server experimental Husqvarna automower status/control
Copyright (C) 2019 Robert Paauwe
"""
CLOUD = False
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True
import sys
import json
import automowy
#import requests

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    id = 'husqvarna'
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'AutoMower'
        self.address = 'mower'
        self.primary = self.address
        self.configured = False
        self.myConfig = {}
        self.username = ''
        self.password = ''
        self.connected = False
        self.session = None
        self.mower = None

        self.poly.onConfig(self.process_config)

    # Process changes to customParameters
    def process_config(self, config):
        if 'customParams' in config:
            # Check if anything we care about was changed...
            if config['customParams'] != self.myConfig:
                changed = False

                if 'Username' in self.myConfig:
                    if self.myConfig['Username'] != config['customParams']['Username']:
                        changed = True
                elif 'Username' in config['customParams']:
                    if config['customParams']['Username'] != "":
                        changed = True

                if 'Password' in self.myConfig:
                    if self.myConfig['Password'] != config['customParams']['Password']:
                        changed = True
                elif 'Password' in config['customParams']:
                    if config['customParams']['Password'] != "":
                        changed = True

                self.myConfig = config['customParams']
                if changed:
                    self.username = config['customParams']['Username']
                    self.password = config['customParams']['Password']
                    self.configured = True
                    self.removeNoticesAll()
                    self.discover()

    def start(self):
        LOGGER.info('Starting node server')
        self.check_params()
        self.session = automowy.AutomowySession()
        self.discover()
        LOGGER.info('Node server started')

    def longPoll(self):
        pass

    def shortPoll(self):
        for node in self.nodes:
            if self.nodes[node].id == 'mower':
                LOGGER.info('Calling node get_status')
                self.nodes[node].get_status()
            else:
                LOGGER.info('Not getting status for node with id = ' + self.nodes[node].id)

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        # Discover the list of available mowers and create a node
        # for each.
        LOGGER.info("In Discovery...")
        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        try:
            self.mower = self.session.login(self.username, self.password).find_mower()
            LOGGER.info('mower name = ' + self.mower.name)
            LOGGER.info('mower id   = ' + self.mower.id)
            LOGGER.info(self.mower.query('status'))
            mower_node = mowerNode(self, self.address, 'automow', self.mower.name)
            mower_node.internal_id = self.mower.id
            mower_node.mower = self.mower
        except:
            LOGGER.error('Authentication failed, fake it')
            mower_node = mowerNode(self, self.address, 'automow', 'test')
            mower_node.internal_id = '100-1' 

        self.addNode(mower_node)
        self.nodes['automow'].get_status()
            

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')
        try:
            self.session.logout()
        except:
            LOGGER.debug('session logout failed')

    def update_profile(self, command):
        st = self.poly.installprofile()
        return st

    def check_params(self):
        self.configured = True

        if 'Username' in self.polyConfig['customParams']:
            self.username = self.polyConfig['customParams']['Username']

        if 'Password' in self.polyConfig['customParams']:
            self.password = self.polyConfig['customParams']['Password']

        self.addCustomParam( {
            'Username': self.username,
            'Password': self.password
            })

        if self.username == '' or self.password == '':
            self.configured = False

        self.removeNoticesAll()

    def remove_notices_all(self, command):
        self.removeNoticesAll()


    commands = {
            'DISCOVER': discover,
            'UPDATE_PROFILE': update_profile,
            'REMOVE_NOTICES_ALL': remove_notices_all
            }

    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            ]

class mowerNode(polyinterface.Node):
    id = 'mower'
    internal_id = ''
    mower = None
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},   # status
            {'driver': 'GV0', 'value': 0, 'uom': 25},   # battery
            {'driver': 'GV1', 'value': 0, 'uom': 25},   # operating mode
            {'driver': 'GV2', 'value': 0, 'uom': 25},   # last error
            {'driver': 'GV3', 'value': 0, 'uom': 25},   # start source
            {'driver': 'GV4', 'value': 0, 'uom': 56},   # start timestamp
            ]

    def operating_modes(self, modename):
        if modename == 'AUTO':
            return 0
        else:
            LOGGER.info('Unknown next start source: ' + modename)
            return 1

    def source(self, sourcename):
        if sourcename == 'COUNTDOWN_TIMER':
            return 0
        else:
            LOGGER.info('Unknown next start source: ' + sourcename)
            return 1

    def get_status(self):
        try:
            json = self.mower.query('status')
            LOGGER.info(self.json)

            status = json['connected']
            battery = json['batteryPercent']
            mode = operating_mode(json['operatingMode'])
            last_error = json['lastErrorCode']
            start_source = source(json['nextStartSource'])
            start_timestamp = json['nextStartTimestamp']

            self.setDriver('ST', status, report=True, force=False)
            self.setDriver('GV0', battery, report=True, force=False)
            self.setDriver('GV1', mode, report=True, force=False)
            self.setDriver('GV2', last_error, report=True, force=False)
            self.setDriver('GV3', start_source, report=True, force=False)
            self.setDriver('GV4', start_timestamp, report=True, force=False)

        except:
            self.setDriver('ST', 1, report=True, force=False)
            self.setDriver('GV0', 100, report=True, force=False)
            self.setDriver('GV1', 0, report=True, force=True)
            self.setDriver('GV2', 0, report=True, force=False)
            self.setDriver('GV3', 1, report=True, force=True)
            self.setDriver('GV4', 565656565, report=True, force=False)
            LOGGER.debug('Skipping status, no connection to mower')

        # TODO: What does the response look like?  We need to translate
        # whatever we get into the numeric value that the node can
        # use here.  Then do a 
        #     setDriver to set the node status value.
        #
        #   {
        #      'connected': True,
        #      'batteryPercent': 100,
        #      'lastErrorCode': 0,
        #      'nextStartTimestamp': xxxxxx,
        #      'nextStartSource': 'COUNTDOWN_TIMER',
        #      'lastErrorCodeTimestamp': xxxxxx,
        #      'valueFound': True,
        #      'storedTimestamp': xxxxxx,
        #      'cachedSettingUUID': xxxxx,
        #      'operatingMode': 'AUTO',
        #      'lastLocations': []
        #      'mowerStatus': {
        #                        'activity': 'PARKED_IN_CS',
        #                        'state': RESTRICTED',
        #                        'type': 'NOT_APPLICABLE',
        #                        'mode': 'MAIN_AREA',
        #                        'restrictedReason': 'PARK_OVERRIDE'}
        #      'errorConfirmable': False
        #   }

    def park_mower(self, junk):
        LOGGER.info(junk)
        try:
            self.mower.control('park/duration/timer')
        except:
            LOGGER.debug('Skipping control, no connection to mower')

    def start_mower(self, params):
        # looks like: {'cmd':'START', 'query': {'override.uom56': '360', }}
        LOGGER.info(params)
        period = params['query']['override.uom56']
        LOGGER.info('time period = ' + period)
        try:
            self.mower.control('start/override/period', {'period': period})
        except:
            LOGGER.debug('Skipping control, no connection to mower')

    def stop_mower(self, junk):
        LOGGER.info(junk)
        try:
            self.mower.control('stop')
        except:
            LOGGER.debug('Skipping control, no connection to mower')

    commands = {
            'PARK': park_mower,
            'START': start_mower,
            'STOP': stop_mower,
            }

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('husqvarna')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

