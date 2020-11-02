[![Build Status](https://github.com/lbryio/aioupnp/workflows/CI/badge.svg)
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

#### Installation for normal usage
```
pip install aioupnp
```

#### Installation for development
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
If `aioupnp` is failing with m-search timeouts this means the UPnP gateway (the router) isn't being found at all. To see if this error is expected try running m_search with debug logging, which will print out the packets sent and received:

    aioupnp --debug_logging m_search

If you only see packets being sent or the replies are only from devices that aren't your router (smart devices, speakers, etc), then there are three options:
* your router does not support UPnP (this is unlikely)
* UPnP is turned off in the web gui for your router (more likely)
* `aioupnp` has a bug (very likely if you don't see your router manufacturer doing well in the supported devices table)

If you see replies from the router but it still fails, then it's likely a bug in aioupnp.

If there are no replies and UPnP is certainly turned on, then a local firewall is the likely culprit.


## Sending a bug report

If it still doesn't work, you can send a bug report using an included script. This script will try finding the UPnP gateway using `aioupnp` as well as `miniupnpc` and then try add and remove a port mapping using each library. The script does this while capturing the packets sent/received, which makes figuring out what went wrong possible. The script will create a file with this packet capture (`aioupnp-bug-report.json`) and automatically send it.

Note: the bug report script currently does not work on MacOS
```
git clone https://github.com/lbryio/aioupnp.git
cd aioupnp
python3 -m pip install -e .

python3 -m pip install --user certifi aiohttp miniupnpc
sudo -E python3 generate_bug_report.py
```

## License

This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Contact

The primary contact for this project is [@jackrobison](mailto:jackrobison@lbry.com)
