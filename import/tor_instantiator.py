import logging

from scrapyanon.ObserveNotify import Subject, Observer

class TorInstantiator:

    def __init__(self, connectors_observers):
        self._connectors_observers = connectors_observers

    def get_proxies(self):
        for (conn,obsvr) in self._connectors_observers:
            conn.attach(obsvr)
            conn.create_circuit()

        while not all(item in ['BUILT'] for item in \
                [conn_obsvr[0].custom_circuit_status for conn_obsvr in self._connectors_observers]):
            continue

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
            ) for x in self._connectors_observers]


        return tor_nodes



