
"""
Ansible Inventory Modul
"""
#pylint: disable=too-many-arguments
import json
from pprint import pprint
import click
from mongoengine.errors import DoesNotExist

from application import app
from application.models.host import Host
from application.helpers.get_ansible_action import GetAnsibleCustomVars, GetAnsibleCustomVarsRule
from application.helpers.get_label import GetLabel
from application.helpers.debug import ColorCodes

@app.cli.group(name='ansible')
def cli_ansible():
    """Ansible related commands"""


def clean_vars(special_vars, inventory):
    """
    Cleanup Inventory based on rule output
    """
    if 'ignore_vars' in special_vars:
        for var in special_vars['ignore_vars']:
            try:
                del inventory[var]
            except KeyError:
                continue
    del inventory['ignore_vars']
    return inventory


@cli_ansible.command('debug_host')
@click.argument("host")
def debug_ansible_rules(host):
    """
    Print matching rules and Inventory Outcome for Host
    """
    custom_variable_helper = GetAnsibleCustomVars(debug=True)
    custom_var_var_helper = GetAnsibleCustomVarsRule(debug=True)
    label_helper = GetLabel()
    try:
        #pylint: disable=no-member
        db_host = Host.objects.get(hostname=host)
    except DoesNotExist:
        print("Host not found")
        return
    if not db_host.available:
        print("Host not  marked as available")
        return
    labels, _ = label_helper.filter_labels(db_host.get_labels())
    inventory = {}
    inventory.update(db_host.get_inventory())
    labels.update(inventory)
    custom_vars = custom_variable_helper.get_action(db_host, labels)
    special_vars = custom_var_var_helper.get_action(db_host, custom_vars)
    inventory.update(custom_vars)
    inventory.update(special_vars)


    print()
    print(f"{ColorCodes.HEADER} ***** Final Outcomes ***** {ColorCodes.ENDC}")
    print(f"{ColorCodes.UNDERLINE}Custom Variables{ColorCodes.ENDC}")
    pprint(custom_vars)
    if custom_vars.get('ignore_host'):
        print("!! This System would be ignored")
    print(f"{ColorCodes.UNDERLINE}Custom Vars based on Custom Vars{ColorCodes.ENDC}")
    pprint(special_vars)
    if special_vars.get('ignore_host'):
        print("!! This System would be ignored")
    print(f"{ColorCodes.UNDERLINE}Complete Ansible Inventory Variables{ColorCodes.ENDC}")
    pprint(inventory)
    print(f"{ColorCodes.UNDERLINE}Ansible Inventory Variables after Filter{ColorCodes.ENDC}")
    inventory = clean_vars(special_vars, inventory)
    pprint(inventory)

def get_full_inventory():
    """
    Get information for ansible
    """
    label_helper = GetLabel()
    custom_label_helper = GetAnsibleCustomVars()
    custom_var_var_helper = GetAnsibleCustomVarsRule()
    data = {
        '_meta': {
            'hostvars' : {}
        },
        'all': {
            'hosts' : []
        },
    }
    #pylint: disable=no-member
    for db_host in Host.objects(available=True):
        hostname = db_host.hostname
        labels, _ = label_helper.filter_labels(db_host.get_labels())
        inventory = {}
        inventory.update(db_host.get_inventory())
        labels.update(inventory)
        custom_vars = custom_label_helper.get_action(db_host, labels)
        if custom_vars.get('ignore_host'):
            continue
        special_vars = custom_var_var_helper.get_action(db_host, custom_vars)
        if special_vars.get('ignore_host'):
            continue
        inventory.update(custom_vars)
        inventory.update(special_vars)
        inventory = clean_vars(special_vars, inventory)
        data['_meta']['hostvars'][hostname] = inventory
        data['all']['hosts'].append(hostname)
    return data

def get_host_inventory(hostname):
    """
    Get Inventory for single host
    """
    label_helper = GetLabel()
    try:
        #pylint: disable=no-member
        db_host = Host.objects.get(hostname=hostname, available=True)
    except DoesNotExist:
        return False
    labels, _ = label_helper.filter_labels(db_host.get_labels())
    custom_label_helper = GetAnsibleCustomVars()
    custom_var_var_helper = GetAnsibleCustomVarsRule()
    inventory = db_host.get_inventory()
    labels.update(inventory)
    custom_vars = custom_label_helper.get_action(db_host, labels)
    if custom_vars.get('ignore_host'):
        return {}
    inventory.update(custom_vars)
    special_vars = custom_var_var_helper.get_action(db_host, custom_vars)
    if special_vars.get('ignore_host'):
        return {}
    inventory.update(custom_vars)
    return inventory

@cli_ansible.command('source')
@click.option("--list", is_flag=True)
@click.option("--host")
def source(list, host): #pylint: disable=redefined-builtin
    """Inventory Source for Ansible"""
    #pylint: disable=no-else-return
    if list:
        print(json.dumps(get_full_inventory()))
        return True
    elif host:
        print(json.dumps(get_host_inventory(host)))
        return True
    print("Params missing")
    return False
