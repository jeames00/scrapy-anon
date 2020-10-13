from __future__ import print_function
from stem.control import Controller
import logging, grpc, launchtor_pb2, launchtor_pb2_grpc
import stem.control
import stem.process
import stem.descriptor.remote
import random
from random import shuffle
import sys
import os
from twisted.internet import threads, defer
from twisted.internet.defer import Deferred, ensureDeferred
import socket

class TorController:

    @property
    def socks_port(self):
        return self._socks_port

    @property
    def control_port(self):
        return self._control_port

    @property
    def custom_circuit(self):
        return self._custom_circuit
    
    @property
    def http_port(self):
        try:
            _http_port = self.controller.get_listeners("HTTPTUNNEL", "there was an error...")[0][1] 
        except:
            e = sys.exc_info()[0]
            print("unable to get HTTPTunnelPort for tor process with socks port {0}. Error: {1}".format(str(self._socks_port), e))
            sys.exit() 

        return str(_http_port)

    @property
    def exit_ip(self):
        if self._custom_circuit != None:
            circuit = self.controller.get_circuit(self._custom_circuit)
            if circuit.status == 'BUILT':
                print("get_exit_ip: circuit.path is: %s" % str(circuit.path))
                exit_fingerprint = circuit.path[-1][0]
                exit_relay = self.controller.get_network_status(exit_fingerprint)
                return exit_relay.address

    def __init__(self, tor_number):
        self.tor_ctrl_pwd = os.environ["TOR_CONTROL_PASSWORD"]
        self.tor_grpc_port = os.environ["TOR_GRPC_PORT"]
     #   self.hashed_tor_ctrl_pwd = os.environ["HASHED_TOR_CONTROL_PASSWORD"] 
        self.tor_number = tor_number
        self.controller = None
        self._custom_circuit = None

        # Set socks and control port according to controller number
        self._socks_port = 9250 + (tor_number * 100)
        self._control_port = 9251 + (tor_number * 100)

        self.init_tor_process()
        # Don't auto-attach incoming streams to circuits
        try:
            self.controller.set_conf('__LeaveStreamsUnattached', '1')
        except:
            print("""SpiderController: launch_spiders: couldn't set conf
                  __LeaveStreamsUnattached""")
            sys.exit()

    def init_tor_process(self): 

        # Try to make controller from existing tor process, otherwise launch new one
        try:
            self.controller = Controller.from_port(
                address=socket.gethostbyname('tor'),
                port=self._control_port
            )
        except:
            self.launch_tor(self._socks_port, self.__control_port)

        ## Authenicate to the tor controller
        try:
            self.controller.authenticate(password = self.tor_ctrl_pwd)
        except stem.connection.MissingPassword:
            print("can't authenticate to tor controller (" +
                  str(_control_port) +
                  "), password incorrect")
        except stem.SocketError:
            print("unable to re-establish socket to tor controller") 
            sys.exit()
        except stem.connection.AuthenticationFailure:
            print("unable to authenticate to tor controller")
            sys.exit()

        # Listen for new circuit and stream events
        self.controller.add_event_listener(self.custom_circuit_launched, 'CIRC')
        self.controller.add_event_listener(self.new_stream, 'STREAM')

    def launch_tor(self, _socks_port, _control_port):
        ## Launch the tor process with appropriate settings
        with grpc.insecure_channel(socket.gethostbyname('tor') + ':' + self.tor_grpc_port) as channel:
            stub = launchtor_pb2_grpc.TorRequesterStub(channel)
            response = stub.RequestLaunch(
                launchtor_pb2.ConfigPorts(
                    socksPort = _socks_port,
                    controlPort = _control_port
                )
            )
            if response.success is False:
                print("""couldn't create a tor process with control
                      '"""+str(_control_port)+"' and socks '"+str(_socks_port)+"'")
                sys.exit()

        ## Initialise the tor controller object from new tor process
        try:
            self.controller = Controller.from_port(
                socket.gethostbyname('tor'),
                _control_port
            )
        except stem.SocketError:
            print("unable to establish a connection to tor instance on control \
                  port '"+str(_control_port)+"'")
            sys.exit()


    def get_http_port(self):
        try:
            http_port = self.controller.get_listeners("HTTPTUNNEL", "there was an error...")[0][1] 
        except:
            e = sys.exc_info()[0]
            print("unable to get HTTPTunnelPort for tor process with socks port {0}. Error: {1}".format(str(self._socks_port), e))
            sys.exit() 

        return str(http_port)

    def get_exit_ip(self):
        if self.custom_circuit != None:
            circuit = self.controller.get_circuit(self.custom_circuit)
            if circuit.status == 'BUILT':
                print("get_exit_ip: circuit.path is: %s" % str(circuit.path))
                exit_fingerprint = circuit.path[-1][0]
                exit_relay = self.controller.get_network_status(exit_fingerprint)
                return exit_relay.address

    def get_exit_fingerprint(self):
        exit_fingerprints = []
        try:
            #for desc in self.controller.get_network_statuses():
            for desc in stem.descriptor.remote.get_consensus():
                if all(x in desc.flags for x in ['Exit', 'Stable']):
                    print("%s" % desc.flags)
                    exit_fingerprints.append(desc.fingerprint)
                    print("found exit relay %s (%s)" % (desc.nickname, desc.fingerprint))
            print("checking %i tor exit relays..." % len(exit_fingerprints))
            return random.sample(exit_fingerprints, 1)
        except Exception as exc:
            print("Unable to retrieve the consensus: %s" % exc)
            sys.exit()
            
      #  relays = [(desc.flags, desc.fingerprint) for desc in self.controller.get_network_statuses()]
      #  for flags, fingerprint in relays:
      #      if 'Exit' and 'Stable' in flags:
      #          exit_fingerprints.append(fingerprint)
      #  return exit_fingerprints[:4]

    @defer.inlineCallbacks
    def custom_circuit_launched(self, circuit):
        if self._custom_circuit == circuit.id:
            logging.debug("** trying to get circuit %s" % circuit)
            circuit = self.controller.get_circuit(self._custom_circuit)
            if circuit.status == 'FAILED':
                print("** BUILD FAILED!")
                yield threads.deferToThread(self.create_circuit())
                return
            if circuit.status == 'BUILT':
                return
            else:
                print("circuit status not caught, is: " + circuit.status)
                return

    def new_stream(self, stream):
        if stream.status == 'NEW':
            print("new stream detected")
            if self._custom_circuit != None:
                try:
                    circuit = self.controller.get_circuit(self._custom_circuit)
                except:
                    print("Circuit %s is CLOSED, unable to attach stream %s" % self._custom_circuit, stream.id)
                if circuit.status == 'BUILT':
                    try:
                        self.controller.attach_stream(stream.id, circuit.id)
                        print("connecting stream with circuit %s" % circuit.id)
                    except:
                        print("couldn't attach stream to circuit %s" % circuit.id)

    def create_circuit(self):
        if self._custom_circuit != None:
            try:
                circuit = self.controller.get_circuit(self._custom_circuit)
                if circuit.status == 'BUILT':
                    return
            except:
                pass

        circuits = self.controller.get_circuits()
        relays = [(desc.flags, desc.fingerprint) for desc in self.controller.get_network_statuses()]
        exit_fingerprints = []
        entry_fingerprints = []
        exits_in_use = []
        for flags, fingerprint in relays:
        #    print(flags)
            if 'Exit' in flags:
                exit_fingerprints.append(fingerprint)
            if 'Guard' in flags:
                entry_fingerprints.append(fingerprint)
        exit_fingerprint = random.choice(exit_fingerprints)

        if len(circuits) > 0:
            for i, circuit in enumerate(circuits):
                print("circuit path length: " + str(len(circuit.path)))
                if len(circuit.path) < 1:
                    continue
                print("circuit path[-1] length: " + str(len(circuit.path[-1])))
                exit = circuit.path[-1][0]
                exits_in_use.append(exit)
            while exit_fingerprint in exits_in_use:
                exit_fingerprint = random.choice(exit_fingerprints)

            exits_in_use.append(exit_fingerprint)
            
        entry_fingerprint = random.choice(entry_fingerprints)
        while entry_fingerprint is exit_fingerprint:
            entry_fingerprint = random.choice(entry_fingerprints)
        
        print("create_circuit: fingerprints are %s, %s" % (entry_fingerprint,
                                                           exit_fingerprint))
      #  self.controller.add_event_listener(self.custom_circuit_launched, 'CIRC')
        try:
            new_circuit = self.controller.extend_circuit(
                '0', 
                [entry_fingerprint, exit_fingerprint],
                purpose = 'general',
                await_build = False
            )
            logging.debug("** created new circuit: %s" % new_circuit)
            self._custom_circuit = new_circuit 
        except:
            raise CircuitCreationError()
        print("Created circuit %s" % self._custom_circuit)
        circuit_exit = exit_fingerprint
        print("exits in use: %s" % circuit_exit if len(exits_in_use) == 0
            else "exits in use: %s" % exits_in_use)
        

class CircuitCreationError(Exception):
    
    def __init__(self, message="Failed to create new circuit"):
        self.message = message
        super().__init__(self.message)

if __name__ == "__main__":
    tor_controller = TorController(3)

