# Purpose

Systemd service or timer monitor with alerting to:
 - Opsgenie


# Deployment

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
