[![codecov](https://codecov.io/gh/lbryio/txupnp/branch/master/graph/badge.svg)](https://codecov.io/gh/lbryio/txupnp)

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



## License

This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Contact

The primary contact for this project is [@jackrobison](mailto:jack@lbry.io)

