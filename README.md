# Purpose

Systemd service or timer monitor with alerting to:
 - Opsgenie

# Deployment

## Docker

* Set environment variables:
    export OPSGENIE_APIKEY=......
    export OPSGENIE_SERVER=......

* Create config file to be mounted by the container, see config/systemd-monitor.yaml

* Run the systemd-monitor in a Docker container, mounting d-bus file system and config file like this:
    ```
    docker run --name systemd_monitor \
            -v /var/run/dbus:/var/run/dbus \
            -e OPSGENIE_APIKEY -e OPSGENIE_SERVER \
            -v /some/path/config.yaml:/etc/systemd-monitor.yaml:ro \
            ekaparulin/systemd-monitor

    ````
    Or with any other Docker orchestration tools.

* Environment varibles may be omitted if the correspondign values are set in the yaml file

## Ansible

### Requirements

- ansible 2.9.9
- SSH config to reach the hosts per IP address
- Centos VMs (yum based)

### Depoyment

- edit yaml files in inventory directory specifiying the hosts and systemd units on them to monitor
- export OpsGenie related environment variables 
- run the playbook with:

    ```
    export OPSGENIE_APIKEY=......
    export OPSGENIE_SERVER=......
    ansible-playbook -i inventory site.yaml
    ```
