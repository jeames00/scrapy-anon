import logging, ast, json
from time import sleep
from contextlib import contextmanager

from pymemcache.client.base import Client
from pymemcache import serde

from scrapyanon.controllers.TorController import TorController
from scrapyanon.controllers.DatabaseController import DatabaseController
from scrapyanon.ObserveNotify import Observer, Subject

from scrapyanon.containers import Instantiators

class TorControllerObserver(Observer):

    def __init__(self):
        self.custom_circuit_status = None

    def update(self, subject: Subject) -> None:
        self.custom_circuit_status = subject.custom_circuit_status
        logging.debug("observer detected circuit change to: {}".format(subject.custom_circuit_status))

    @property
    def custom_circuit_status(self):
        return self._custom_circuit_status

    @custom_circuit_status.setter
    def custom_circuit_status(self, value):
        self._custom_circuit_status = value

class ProxyController():

    def __init__(self, proxy_type='tor', num_proxies_required=0):
        self.proxy_type = proxy_type
        self.num_proxies_required = num_proxies_required
        #configs_container = Configs()
        #configs_container.config.from_ini('config.ini')
        #configs_container.instantiator_config.from_dict(
        #        {'num_proxies_required': num_proxies_required},
        #)
        #Configs.instantiator_config.override({
        #    "num_proxies_required": num_proxies_required
        #    })

        if self.proxy_type == 'tor':
            container = Instantiators()
            container.config.from_dict(
                    {'num_proxies_required': self.num_proxies_required},
            )
            self.tor_instantiator = container.tor_instantiator()


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
            tcObserver = TorControllerObserver()
            torc.attach(tcObserver)
#            try:
#                prev_circuit =\
#                    [x['tor_custom_circuit'] for x in active_proxies\
#                    if x['socks_port'] == torc.socks_port][0]
#
#                prev_circuit_status = torc.get_circuit_status(prev_circuit)
#                if prev_circuit_status:
#                    torc.custom_circuit = prev_circuit
#                    torc.custom_circuit_status = prev_circuit_status
#                    tcObserver.custom_circuit_status = prev_circuit_status
#                    logging.debug("Set custom circuit to previous circuit ({}) from active_proxies".format(prev_circuit))
#                except:
#                    pass
#            except:
#                pass
            
            try:
                torc.create_circuit()
            except Exception as e:
                logging.debug(e)
                logging.debug("trying again to create circuit...")
                continue

            i += 1
            tor_controllers.append((torc,tcObserver))


    ### NEW
        # Keep checking custom circuits in tor controllers until they've all been built
        while not all(item in ['BUILT'] for item in \
                [x[1].custom_circuit_status for x in tor_controllers]):
            continue

       #     logging.debug("{}".format([x[1].custom_circuit_status for x in tor_controllers]))
       #     sleep(.1)
#            for y in tor_controllers:
#                if y[1].custom_circuit_status == 'FAILED':
#                    y[0].create_circuit()
                    
    ### END NEW

    ### OLD
 #       # Keep checking custom circuits in tor controllers until they've all been built
 #       custom_circuit_ids = [x[0].custom_circuit for x in tor_controllers]
 #       num_built_circuits = 0
 #       while num_built_circuits < number_to_create:
 #           for x in tor_controllers:
 #               for y in custom_circuit_ids:
 #                   if (y, 'BUILT') in [(z.id, z.status) for z in x.controller.get_circuits()]:
 #                       num_built_circuits += 1
 #                       # This circuit is built, remove it from checking on next loop
 #                       custom_circuit_ids.remove(y)
    ### END OLD
        
        tor_nodes = \
            [(
                # Gets the SOCKS port for each tor controller
                x[0].socks_port,
                # Gets IP address of exit node for each tor controller's custom circuit
                x[0].exit_ip,
                # Gets fingerprint of exit node for each tor controller's custom circuit
                x[0].controller.get_circuit(x[0].custom_circuit).path[-1][0],
                # Gets nickname of exit node for each tor controller's custom circuit
                x[0].controller.get_circuit(x[0].custom_circuit).path[-1][1],
                #Gets the control port for each tor controller
                x[0].control_port,

                x[0].custom_circuit,

                # Gets the HTTPTunnelPort for each tor controller
                x[0].http_port
            ) for x in tor_controllers]

        db = DatabaseController()
        db.upsert_tor_nodes(
            [(x[1],x[2],x[3]) for x in tor_nodes]
        )

        return tor_nodes

    def get_proxies(self):
        self._tor_nodes = self.tor_instantiator.get_proxies()

        db = DatabaseController()
        db.upsert_tor_nodes(
            [(x[1],x[2],x[3]) for x in self._tor_nodes]
        )
    #def get_proxies(self, number_required, regions = "any", **kwargs):
        
#        self.circuit_status = None
#
#
#
#
#        for key, value in kwargs.items():
#            if key == 'spider':
#                self.spider = value
#
#        with self.memcclient('localhost') as c:
#            active_proxies = [] if not c.get('active_proxies') \
#                else ast.literal_eval(c.get('active_proxies').decode("utf-8"))
#         #       else c.get('active_proxies')
#            tor_nodes = self.setup_tor_circuits(number_required, active_proxies)
#            active_proxies = [
#                {
#                    'socks_port': x[0],
#                    'is_tor': True,
#                    'control_port': x[4],
#                    'tor_custom_circuit': x[5]
#                } for x in tor_nodes
#            ]
#                    
#            c.set('active_proxies', active_proxies)
#            logging.debug([(str(x[0]), x[1]) for x in tor_nodes])
#            return [('socks5://tor:'+str(x[0]), x[1]) for x in tor_nodes]


        #logging.debug([(str(x[0]), x[1]) for x in tor_nodes])
        return [('socks5://tor:'+str(x[0]), x[1]) for x in self._tor_nodes]
