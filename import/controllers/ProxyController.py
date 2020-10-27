import logging, ast, json
from time import sleep
from contextlib import contextmanager

from pymemcache.client.base import Client
from pymemcache import serde

from scrapyanon.controllers.TorController import TorController
from scrapyanon.controllers.DatabaseController import DatabaseController

class ProxyController:

    @contextmanager
    def memcclient(self, host):
        c = Client(host)
        lock = c.get('lock')
        while lock:
            sleep(.25)
            lock = c.get('lock')
        c.set('lock', 'true')
        try:
            yield c
        finally:
            c.delete('lock')

    def setup_tor_circuits(self, number_to_create, active_proxies):
        tor_controllers = []
        # Create a tor controller and custom circuit for each proxy required
        i = 0
        while i < number_to_create:
            torc = TorController(i)
            try:
                prev_circuit =\
                    [x['tor_custom_circuit'] for x in active_proxies\
                    if x['socks_port'] == torc.socks_port][0]
                torc.custom_circuit = prev_circuit
            except:
                pass
            
            try:
                torc.create_circuit()
            except Exception as e:
                logging.debug(e)
                logging.debug("trying again to create circuit...")
                continue

            i += 1
            tor_controllers.append(torc)

        # Keep checking custom circuits in tor controllers until they've all been built
        custom_circuit_ids = [x.custom_circuit for x in tor_controllers]
        num_built_circuits = 0
        while num_built_circuits < number_to_create:
            for x in tor_controllers:
                for y in custom_circuit_ids:
                    if (y, 'BUILT') in [(z.id, z.status) for z in x.controller.get_circuits()]:
                        num_built_circuits += 1
                        # This circuit is built, remove it from checking on next loop
                        custom_circuit_ids.remove(y)
        
        tor_nodes = \
            [(
                # Gets the SOCKS port for each tor controller
                x.socks_port,
                # Gets IP address of exit node for each tor controller's custom circuit
                x.exit_ip,
                # Gets fingerprint of exit node for each tor controller's custom circuit
                x.controller.get_circuit(x.custom_circuit).path[-1][0],
                # Gets nickname of exit node for each tor controller's custom circuit
                x.controller.get_circuit(x.custom_circuit).path[-1][1],
                #Gets the control port for each tor controller
                x.control_port,

                x.custom_circuit,

                # Gets the HTTPTunnelPort for each tor controller
                x.http_port
            ) for x in tor_controllers]

        db = DatabaseController()
        db.upsert_tor_nodes(
            [(x[1],x[2],x[3]) for x in tor_nodes]
        )

        return tor_nodes

    def get_proxies(self, number_required, regions = "any", **kwargs):
        for key, value in kwargs.items():
            if key == 'spider':
                self.spider = value

        with self.memcclient('localhost') as c:
            active_proxies = [] if not c.get('active_proxies') \
                else ast.literal_eval(c.get('active_proxies').decode("utf-8"))
         #       else c.get('active_proxies')
            tor_nodes = self.setup_tor_circuits(number_required, active_proxies)
            active_proxies = [
                {
                    'socks_port': x[0],
                    'is_tor': True,
                    'control_port': x[4],
                    'tor_custom_circuit': x[5]
                } for x in tor_nodes
            ]
                    
            c.set('active_proxies', active_proxies)
            logging.debug([(str(x[0]), x[1]) for x in tor_nodes])
            return [('socks5://tor:'+str(x[0]), x[1]) for x in tor_nodes]
