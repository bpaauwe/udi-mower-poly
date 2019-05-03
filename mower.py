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
import requests

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    id = 'husqvarna'
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'mower'
        self.address = 'mower'
        self.primary = self.address
        self.configured = False
        self.myConfig = {}
        self.username = ''
        self.password = ''
        self.base_url="https://iam-api.dss.husqvarnagroup.net/api/v3/"
        self.track_url="https://amc-api.dss.husqvarnagroup.net/v1/"
        self.expires_in = ''
        self.connected = False
        self.session = None

        self.poly.onConfig(self.process_config)

    # Process changes to customParameters
    def process_config(self, config):
        if 'customParams' in config:
            # Check if anything we care about was changed...
            if config['customParams'] != self.myConfig:
                changed = False

                self.myConfig = config['customParams']
                if changed:
                    self.removeNoticesAll()

    def start(self):
        LOGGER.info('Starting node server')
        self.check_params()
        self.authenticate()
        self.discover()
        LOGGER.info('Node server started')

    def longPoll(self):
        pass

    def shortPoll(self):
        for node in self.nodes:
            if self.nodes[node].id == 'mower':
                self.nodes[node].get_status

    def authenticate(self):
        LOGGER.info('Authenticate with Husqvarna API')

        if not self.configured:
            return

        self.session = requests.Sessions()

        response = self.session.post(self.base_url + 'token',
                headers = {'Accept' : 'application/json', 'Content-type': 'application/json'},
                json = {
                    'data': {
                        'attributes': {
                            'password': self.password,
                            'username': self.username
                            },
                        'type': 'token'
                        }
                    })
        response.raise_for_status()

        json = response.json()
        LOGGER.info (json)

        # update session headers with token and provider from login
        # response

        self.session.headers.update({
            'Authorization': 'Bearer ' + json['data']['id'],
            'Autorization-Provider': json['data']['attributes']['provider']
            })

        self.expires_in = json['data']['attributes']['expires_in']
        self.connected = True

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

        response = self.session.get(self.track_url + 'mowers',
                headers = {
                    'Accept' : 'application/json',
                    'Content-type': 'application/json'})
        response.raise_for_status()

        for mower in response.json():
            LOGGER.info('Adding node for:')
            LOGGER.info('  Mower : ' + mower['name'])
            LOGGER.info('     ID : ' + mower['id'])

            mower_node = mowerNode(self, self.address, mower['id'], mower['name'])
            mower_node.internal_id = mower['id']
            mower_node.token = self.token
            mower_node.provider = self.provider
            mower_node.api_url = self.track_url
            self.addNode(mower_node)
            

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

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
    token = ''
    provider = ''
    api_url = ''
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 25},   # status
            ]

    def get_status(self):
        headers = {
                'Accept' : 'application/json',
                'Content-type': 'application/json',
                'Authorization' : 'Bearer ' + self.token,
                'Autorization-Provider': self.provider
                }
        r = requests.get(self.api_url + 'mowers/%s/status' % self.internal_id,
                headers = headers)
        r.raise_for_status()

        jdata = r.json()
        LOGGER.debug(jdata)

        # TODO: What does the response look like?  We need to translate
        # whatever we get into the numeric value that the node can
        # use here.  Then do a 
        #     setDriver to set the node status value.

    def send_command(self, command):
        if command not in ['PARK', 'STOP', 'START']:
            LOGGER.error("Unknown command %s" % command)
            return

        headers = {
                'Accept' : 'application/json',
                'Content-type': 'application/json',
                'Authorization' : 'Bearer ' + self.token,
                'Autorization-Provider': self.provider
                }
        LOGGER.info('Sending command %s to mower %s' % (command, self.internal_id)
        r = requests.post(self.api_url + 'mowers/%s/control/' % self.internal_id,
                headers = headers,
                json ={
                    'action': command
                    })
        r.raise_for_status()

    def park(self):
        send_command("PARK")

    def start(self):
        send_command("START")

    def stop(self):
        send_command("STOP")

    commands = {
            'PARK': park,
            'START': start,
            'STOP': stop,
            }

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('HusqvarnaMower')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

