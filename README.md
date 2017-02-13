# VDSM Networks

## Schema

```yaml
networks:
    required: false
    default: {}
    description: >
        Dictionary in format `{name: attrs}`, where `attrs` has the same
        values and `state: present|absent`.
bondings:
    required: false
    default: {}
    description: >
        Dictionary in format `{name: attrs}`, where `attrs` has the same
        values and `state: present|absent`.
options:
    required: false
    default: {'force': False, 'connectivity_check': False, 'connectivity_timeout': 10}
    description:
        - When `force` is set to True, setupNetworks will be called no
          matter if current running config already fits the request.
          `connectivity_check` and `connectivity_timeout` are mapped to 
          setupNetworks `ConnectivityCheck` and `ConnectivityTimeout`.
```

## Example

```yaml
- vdsm_networks:
    networks:
        net1:
            bonding: bond1
            status: present
        net2:
            status: absent
    bondings:
        bond1:
            nics:
                - eth0
                - eth1
            status: present
    options:
        connectivity_check: true
```
