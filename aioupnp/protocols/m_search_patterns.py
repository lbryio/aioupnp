M_SEARCH_ARG_PATTERNS = [
    #
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('ST', lambda s: s),
        ('MAN', lambda s: '"%s"' % s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('ST', lambda s: s),
        ('Man', lambda s: '"%s"' % s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('Host', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('ST', lambda s: s),
        ('Man', lambda s: '"%s"' % s),
        ('MX', lambda n: int(n)),
    ],

    # swap st and man
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('MAN', lambda s: '"%s"' % s),
        ('ST', lambda s: s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('Man', lambda s: '"%s"' % s),
        ('ST', lambda s: s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('Host', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('Man', lambda s: '"%s"' % s),
        ('ST', lambda s: s),
        ('MX', lambda n: int(n)),
    ],

    # repeat above but with no quotes on man
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('ST', lambda s: s),
        ('MAN', lambda s: s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('ST', lambda s: s),
        ('Man', lambda s: s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('Host', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('ST', lambda s: s),
        ('Man', lambda s: s),
        ('MX', lambda n: int(n)),
    ],

    # swap st and man
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('MAN', lambda s: s),
        ('ST', lambda s: s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('HOST', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('Man', lambda s: s),
        ('ST', lambda s: s),
        ('MX', lambda n: int(n)),
    ],
    [
        ('Host', lambda ssdp_ip: "{}:{}".format(ssdp_ip, 1900)),
        ('Man', lambda s: s),
        ('ST', lambda s: str(s)),
        ('MX', lambda n: int(n)),
    ],
]