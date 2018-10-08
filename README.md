[![codecov](https://codecov.io/gh/lbryio/aioupnp/branch/master/graph/badge.svg)](https://codecov.io/gh/lbryio/aioupnp)

# UPnP for asyncio

`aioupnp` is a python 3 library and command line tool to interact with UPnP gateways using asyncio. `aioupnp` requires the `netifaces` module.

## Installation

```
pip install --upgrade aioupnp
```

## Usage

```
aioupnp [-h] [--debug_logging=<debug_logging>] [--interface=<interface>]
        [--gateway_address=<gateway_address>]
        [--lan_address=<lan_address>] [--timeout=<timeout>]
        [--service=<service>]
        command [--<arg name>=<arg>]...
```

### Commands
    add_port_mapping | delete_port_mapping | get_external_ip | get_next_mapping | get_port_mapping_by_index | get_redirects | get_soap_commands | get_specific_port_mapping | m_search


### Examples

To get the external ip address from the UPnP gateway
    
    aioupnp get_external_ip
    
To list the active port mappings on the gateway

    aioupnp get_redirects
   
To debug the default gateway

    aioupnp --debug_logging=1 m_search

To debug a gateway on a non default network interface

    aioupnp --interface=vmnet1 --debug_logging=1 m_search

To debug a gateway on a non default network interface that isn't the router

    aioupnp --interface=vmnet1 --gateway_address=192.168.1.106 --debug_logging=1 m_search
    
## License

This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Contact

The primary contact for this project is [@jackrobison](mailto:jack@lbry.io)
