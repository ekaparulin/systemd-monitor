#!/usr/bin/python3
from pydbus import SystemBus
from gi.repository import GLib
import yaml
import sys
import os
import urllib.request
import urllib.error
import json
import time
import platform

class OpsGenieApi:
    def __init__(self):
        self.genie_key = os.environ.get('OPSGENIE_APIKEY')
        self.base_url = 'https://api.%s/v2/alerts' % os.environ.get('OPSGENIE_SERVER', 'opsgenie.com')
        self.alerts = []

        assert self.genie_key != None

    def create_alert(self, message='', description='', priority='P5', tags=[]):
        # Suppress duplicates
        if len(self.alerts) > 0:
            return

        print('Create alert: "%s"' % (message))
        
        payload = {}
        payload['message'] = message
        payload['description'] = description
        payload['priority'] = priority
        payload['tags'] = tags

        headers = {}
        headers['Content-Type'] = 'application/json'

        req_data = json.loads(self.__request(url=self.base_url, data=payload, headers=headers)) 
        tries = 0
        while tries < 3: 
            try:
                alert_data = json.loads(self.__request(self.base_url + '/requests/' + req_data['requestId'] ))
                self.alerts.append(alert_data['data']['alertId'])
                break
            except urllib.error.HTTPError:
                tries += 1
                time.sleep(1)


    def close_alerts(self, note=None):
        while len(self.alerts) != 0:
            self.close_alert(alert_id=self.alerts.pop(), note=note)

    def close_alert(self, alert_id, note=None):
        print('Close alert: %s, reason: "%s"' % (alert_id, note))
        payload = {}
        if note != None:
            payload['note'] = note

        headers = {}
        headers['Content-Type'] = 'application/json'

        self.__request(url=self.base_url + '/%s/close?identifierType=id' % alert_id, data=payload, headers=headers)

    def __request(self, url, data=None, headers={}):
        if data != None:
            data = json.dumps(data).encode('utf8')

        req = urllib.request.Request(url, data)
        for k,v in headers.items():
            req.add_header(k, v)
        req.add_header('Authorization', 'GenieKey %s' % self.genie_key)
        resp = urllib.request.urlopen(req)
        data = resp.read()
        return(data.decode(resp.info().get_content_charset('utf-8')))

class Unit:
    def __init__(self, name):
        self.bus = SystemBus()
        self.systemd = SystemBus().get('.systemd1')
        self.name = name
        self.unit = self.bus.get('.systemd1', self.systemd.GetUnit(self.name))
        self.connection = self.unit['org.freedesktop.DBus.Properties'].PropertiesChanged.connect(self.callback)

        self.og = OpsGenieApi()
        self.notify(True)

    def active_state(self):
        return self.unit.ActiveState

    def callback(self, interface_name, changed_properties, invalidated_properties):
        if interface_name != 'org.freedesktop.systemd1.Unit':
            return

        self.notify()

    def name(self):
        return self.name
    
    def disconnect(self):
        self.connection.disconnect()

    def notify(self, suppress_active=False):
        if self.unit.ActiveState == 'active':
            if suppress_active:
                return
        
            self.og.close_alerts(note='%s: systemd %s state is %s (sub state=%s)' % (platform.node(), self.name, self.unit.ActiveState, self.unit.SubState))
            return

        if self.unit.ActiveState == 'inactive':
            self.og.create_alert(
               message='%s: systemd %s is %s' % ( platform.node(), self.name, self.unit.ActiveState), 
               description='%s: systemd %s (state=%s, sub state=%s)' % ( platform.node(), self.name, self.unit.ActiveState, self.unit.SubState), 
               priority='P5', tags=['Moi'])

if __name__ == '__main__':

    # Parse config
    if len(sys.argv) < 2:
        sys.exit('Usage: %s /path/to/config.yaml' % sys.argv[0])

    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Config file %s was not found!' % sys.argv[1])

    config_file = open(sys.argv[1])
    config = yaml.load(config_file, Loader=yaml.FullLoader)

    # Set env vars
    if 'opsgenie' in config.keys():
        if 'server' in config['opsgenie'].keys():
            os.environ['OPSGENIE_SERVER'] = os.environ.get('OPSGENIE_SERVER', config['opsgenie']['server'])
        if 'apikey' in config['opsgenie'].keys():
            os.environ['OPSGENIE_APIKEY'] = os.environ.get('OPSGENIE_APIKEY', config['opsgenie']['apikey'])
    
    # Build watchers
    units = []
    for unit in config['watch']:
        units.append(Unit(unit))

    # Enter the main loop
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        for unit in units:
           unit.disconnect()
