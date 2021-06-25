import logging

from dependency_injector import providers, containers
from scrapyanon.tor_instantiator import TorInstantiator
from scrapyanon.tor_connector_observer import TorConnectorObserver
from scrapyanon.tor_connector import TorConnector

def tor_connectors_observers(config=None):
    _num_tor_proxies = config
    #_tor_connectors = [] 
    #for tor_num in range(0, _num_tor_proxies-1):
    #    _tor_connectors.append(providers.Factory(TorConnector, tor_num))

    _tor_connectors_observers = \
            [(TorConnector(tor_num),TorConnectorObserver())\
            for tor_num in range(0, _num_tor_proxies)]

    return _tor_connectors_observers

#class Configs(containers.DeclarativeContainer):
#    instantiator_config = providers.Configuration()
#    config = providers.Configuration()
#
#class Observers(containers.DeclarativeContainer):
#    #tor_connector_observer = providers.Factory(TorConnectorObserver)
#
#    def tor_connector_observers(self):
#        _num_tc_observers = Configs.instantiator_config.num_proxies_required
#        _tc_observers = []
#        for tc_obs in range(1, _num_tc_observers):
#            _tc_observers.append(providers.Factory(TorConnectorObserver))
#
#        return _tc_observers

class Connectors(containers.DeclarativeContainer):
    pass
   # proxy_connector = providers.Factory(ProxyConnector, Configs.config)
   # tor_connector = providers.Factory(TorConnector, Configs.config)

#    config = providers.Configuration()
#    
#    tor_connectors = providers.Resource(tor_connector_loop, config=config.awk)

    #def tor_connectors(self):
    #    _num_tor_proxies = Configs.instantiator_config.'num_proxies_required'
    #    _tor_connectors = [] 
    #    for tor_num in range(0, _num_tor_proxies-1):
    #        _tor_connectors.append(providers.Factory(TorConnector, tor_num, Configs.config))

    #    return _tor_connectors


class Instantiators(containers.DeclarativeContainer):
   # proxy_instantiator = providers.Singleton(
   #         ProxyInstantiator, connector=Connectors.proxy_connector, config=Configs.instantiator_config,
   # )
   
    config = providers.Configuration()
   # tor_instantiator = providers.Singleton(TorInstantiator, 
   #         connectors=Connectors.tor_connectors, observers=Observers.tor_connector_observers, config=config
   # )
    connectors_observers = providers.Factory(tor_connectors_observers, 
            config=config.num_proxies_required)

    tor_instantiator = providers.Singleton(TorInstantiator, connectors_observers)
    

