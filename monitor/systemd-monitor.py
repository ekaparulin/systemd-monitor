#!/usr/bin/env python3
from pydbus import SystemBus
from gi.repository import GLib
import yaml
import sys
import os

class Unit:
    def __init__(self, name):
        self.bus = SystemBus()
        self.systemd = SystemBus().get('.systemd1')
        self.name = name
        self.unit = self.bus.get('.systemd1', self.systemd.GetUnit(self.name))
        self.connection = self.unit['org.freedesktop.DBus.Properties'].PropertiesChanged.connect(self.callback)
        self.prevState = self.unit.ActiveState
        self.notify(True)

    def active_state(self):
        return self.unit.ActiveState

    def callback(self, interface_name, changed_properties, invalidated_properties):
        if interface_name != 'org.freedesktop.systemd1.Unit':
            return
        if self.prevState == self.unit.ActiveState:
            return

        self.notify()
        self.prevState == self.unit.ActiveState

    def name(self):
        return self.name
    
    def disconnect(self):
        self.connection.disconnect()

    def notify(self, suppress_active=False):
        if self.unit.ActiveState == 'active' and suppress_active:
            return

        print ('Systemd unit: "%s": (Prev state=%s Active state=%s Sub State=%s)' % ( self.name, self.prevState, self.unit.ActiveState, self.unit.SubState)) 


if __name__ == '__main__':

    # Parse config
    if len(sys.argv) < 2:
        sys.exit('Usage: %s /path/to/config.yaml' % sys.argv[0])

    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Config file %s was not found!' % sys.argv[1])

    config_file = open(sys.argv[1])
    config = yaml.load(config_file)
    
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

