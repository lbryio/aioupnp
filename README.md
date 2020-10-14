[![Build Status](https://travis-ci.org/lbryio/aioupnp.svg?branch=master)](https://travis-ci.org/lbryio/aioupnp)
[![codecov](https://codecov.io/gh/lbryio/aioupnp/branch/master/graph/badge.svg)](https://codecov.io/gh/lbryio/aioupnp)
[![PyPI version](https://badge.fury.io/py/aioupnp.svg)](https://badge.fury.io/py/aioupnp)
[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)

# UPnP for asyncio

`aioupnp` is a python 3.6-8 library and command line tool to interact with UPnP gateways using asyncio. `aioupnp` requires the `netifaces` and `defusedxml` modules.

## Supported devices
![img](https://i.imgur.com/JtO4glP.png)

## Installation

Verify python is version 3.6-8
```
python --version
```

Installation for normal usage
```
pip install aioupnp
```

Installation for development
```
git clone https://github.com/lbryio/aioupnp.git
cd aioupnp
pip install -e .
```


## Usage

```
aioupnp [-h] [--debug_logging] [--interface=<interface>] [--gateway_address=<gateway_address>]
        [--lan_address=<lan_address>] [--timeout=<timeout>]
        [(--<case sensitive m-search header>=<value>)...]
        command [--<arg name>=<arg>]...
```


#### Commands
* `help`
* `get_external_ip`
* `m_search`
* `add_port_mapping`
* `get_port_mapping_by_index`
* `get_redirects`
* `get_specific_port_mapping`
* `delete_port_mapping`
* `get_next_mapping`
* `gather_debug_info`

#### To get the documentation for a command

    aioupnp help get_external_ip

#### To get the external ip address

    aioupnp get_external_ip

#### To list the active port mappings on the gateway

    aioupnp get_redirects

#### To set up a TCP port mapping
    
    aioupnp add_port_mapping --external_port=1234 --internal_port=1234 --lan_address=<lan_addr> --description=test --protocol=TCP

#### To delete a TCP port mapping

    aioupnp delete_port_mapping --external_port=1234 --protocol=TCP

#### M-Search headers
UPnP uses a multicast protocol (SSDP) to locate the gateway. Gateway discovery is automatic by default, but you may provide specific headers for the search to use to override automatic discovery.

If m-search headers are provided as keyword arguments then all of the headers to be used must be provided, in the order they are to be used. For example:

    aioupnp --HOST=239.255.255.250:1900 --MAN=\"ssdp:discover\" --MX=1 --ST=upnp:rootdevice m_search

#### Using non-default network interfaces
By default, the network device will be automatically discovered. The interface may instead be specified with the `--interface`, provided before the command to be run. The gateway used on the interface network may be specified with the `--gateway_address` argument.

    aioupnp --interface=wlp4s0 --gateway_address=192.168.1.6 m_search


#### Example usage from python

    from aioupnp.upnp import UPnP

    async def main():
        upnp = await UPnP.discover()
        print(await upnp.get_external_ip())
        print(await upnp.get_redirects())

        print("adding a port mapping")
        await upnp.add_port_mapping(1234, 'TCP', 1234, upnp.lan_address, 'test mapping')
        print(await upnp.get_redirects())

        print("deleting the port mapping")
        await upnp.delete_port_mapping(1234, 'TCP')
        print(await upnp.get_redirects())


    asyncio.run(main())


## Troubleshooting

#### Debug logging
To enable verbose debug logging, add the `--debug_logging` argument before the command

    aioupnp --debug_logging m_search

#### It really doesn't work
If aioupnp doesn't work with a device, a debugging report can be collected with `aioupnp gather_debug_info`.

This will attempt to discover the UPnP gateway, and then perform a functionality check where it will request the external address and existing port mappings before attempting to make and remove a port mapping. The final result is the zipped packet dump of these attempts, which allows writing tests replaying it.

## License

This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Contact

The primary contact for this project is [@jackrobison](mailto:jackrobison@lbry.com)
