"""
#pylint: disable=too-many-locals
Inits for the Plugins
"""
#pylint: disable=too-many-locals
import sys
from application.helpers.get_account import get_account_by_name
from application.modules.checkmk.cmk2 import CMK2, CmkException
from application.modules.debug import ColorCodes
from application.models.host import Host
from application.modules.checkmk.config_sync import SyncConfiguration
from application.modules.checkmk.rules import CheckmkRulesetRule, DefaultRule
from application.modules.checkmk.models import CheckmkRuleMngmt, CheckmkBiRule
from application.plugins.checkmk import _load_rules

#   .-- Export BI Rules
def export_bi_rules(account):
    """
    Export BI Rules to Checkmk
    """
    try:
        target_config = get_account_by_name(account)
        if target_config:
            syncer = SyncConfiguration()
            syncer.account_id = str(target_config['_id'])
            syncer.account_name = target_config['name']
            syncer.config = target_config
            actions = DefaultRule()
            actions.rules = CheckmkBiRule.objects(enabled=True)
            syncer.actions = actions
            syncer.export_bi_rules()
        else:
            print(f"{ColorCodes.FAIL} Config not found {ColorCodes.ENDC}")
    except CmkException as error_obj:
        print(f'C{ColorCodes.FAIL}MK Connection Error: {error_obj} {ColorCodes.ENDC}')
#.
#   .-- Inventorize Hosts
def inventorize_hosts(account):
    """
    Inventorize information from Checkmk Installation
    """
    inventory_target = [
        'site', 'inventory_failed','is_offline',
    ]
    config = get_account_by_name(account)
    cmk = CMK2()
    cmk.config = config

    print(f"{ColorCodes.OKBLUE}Started {ColorCodes.ENDC} with account "\
          f"{ColorCodes.UNDERLINE}{account}{ColorCodes.ENDC}")


    print(f"{ColorCodes.OKBLUE} *{ColorCodes.ENDC} Collecting Config Data")
    url = "domain-types/host_config/collections/all?effective_attributes=true"
    api_hosts = cmk.request(url, method="GET")
    config_inventory = {}
    for host in api_hosts[0]['value']:
        hostname = host['id']
        attributes = host['extensions']['effective_attributes']
        host_inventory = {}
        for attribute in attributes:
            if attribute in inventory_target or attribute.startswith('tag_'):
                host_inventory[f"cmk_{attribute}"] = attributes[attribute]

        config_inventory[hostname] = host_inventory


    # Inventory for Status Information
    url = "domain-types/service/collections/all"
    params={
        "query":
           '{"op": "or", "expr": ['\
           '{ "op": "=", "left": "description", "right": "Check_MK"}, '\
           '{ "op": "=", "left": "description", "right": "Check_MK Agent"},'\
           '{ "op": "=", "left": "description", "right": "Check_MK Discovery"}'\
           '] }',
        "columns":
           ['host_name', 'description', 'state', 'plugin_output'],
    }
    print(f"{ColorCodes.OKBLUE} *{ColorCodes.ENDC} Collecting Status Data")
    api_response = cmk.request(url, data=params, method="GET")
    status_inventory = {}
    for service in api_response[0]['value']:
        host_name = service['extensions']['host_name']
        service_description = service['extensions']['description'].lower().replace(' ', '_')
        service_state = service['extensions']['state']
        service_output = service['extensions']['plugin_output']
        status_inventory.setdefault(host_name, {})
        status_inventory[host_name][f"cmk_svc_{service_description}_state"] = service_state
        status_inventory[host_name][f"cmk_svc_{service_description}_output"] = service_output

    print(f"{ColorCodes.UNDERLINE}Write to DB{ColorCodes.ENDC}")


    # pylint: disable=consider-using-dict-items
    for hostname in config_inventory:
        db_host = Host.get_host(hostname, False)
        if db_host:
            db_host.update_inventory('cmk_', config_inventory[hostname])
            db_host.update_inventory('cmk_svc)', status_inventory.get(hostname, {}))
            db_host.save()
            print(f" {ColorCodes.OKGREEN}* {ColorCodes.ENDC} Updated {hostname}")
        else:
            print(f" {ColorCodes.FAIL}* {ColorCodes.ENDC} Not in Syncer: {hostname}")
#.
#   . -- Bake and Sign Agents
def bake_and_sign_agents(account):
    """
    Bake and Sign Agents in Checkmk
    """
    account_config = get_account_by_name(account)
    custom_config = {x['name']:x['value'] for x in account_config['custom_fields']}
    if account_config['typ'] != 'cmkv2':
        print(f"{ColorCodes.FAIL} Not a Checkmk 2.x Account {ColorCodes.ENDC}")
        sys.exit(1)
    if not "backery_key_id" in custom_config and not "bakery_passphrase" in custom_config:
        print(f"{ColorCodes.FAIL} Please set baker_key_id and "\
              f"bakery_passphrase as Custom Account Config {ColorCodes.ENDC}")
        sys.exit(1)
    cmk = CMK2()
    cmk.config = account_config
    url = "/domain-types/agent/actions/bake_and_sign/invoke"
    data = {
        'key_id': int(custom_config['bakery_key_id']),
        'passphrase': custom_config['bakery_passphrase'],
    }
    try:
        cmk.request(url, data=data, method="POST")
        print("Signed and Baked Agents")
        sys.exit(0)
    except CmkException as errors:
        print(errors)
        sys.exit(1)
#.
#   .-- Activate Changes
def activate_changes(account):
    """
    Activate Changes of Checkmk Instance
    """
    account_config = get_account_by_name(account)
    if account_config['typ'] != 'cmkv2':
        print(f"{ColorCodes.FAIL} Not a Checkmk 2.x Account {ColorCodes.ENDC}")
        sys.exit(1)
    cmk = CMK2()
    cmk.config = account_config
    url = "/domain-types/activation_run/actions/activate-changes/invoke"
    data = {
        'redirect': False,
        'force_foreign_changes': True,
    }
    try:
        cmk.request(url, data=data, method="POST")
        print("Changes activated")
        sys.exit(0)
    except CmkException as errors:
        print(errors)
        sys.exit(1)
#.
#   .-- Export Groups
def export_groups(account, test_run):
    """
    Manage Groups in Checkmk
    """
    try:
        target_config = get_account_by_name(account)
        if target_config:
            syncer = SyncConfiguration()
            syncer.account = target_config['_id']
            syncer.account_id = str(target_config['_id'])
            syncer.account_name = target_config['name']
            syncer.config = target_config
            syncer.export_cmk_groups(test_run)
        else:
            print(f"{ColorCodes.FAIL} Config not found {ColorCodes.ENDC}")
    except CmkException as error_obj:
        print(f'C{ColorCodes.FAIL}MK Connection Error: {error_obj} {ColorCodes.ENDC}')
#.
#   .-- Export Rules
def export_rules(account):
    """
    Create Rules in Checkmk
    """
    try:
        target_config = get_account_by_name(account)
        if target_config:
            rules = _load_rules()
            syncer = SyncConfiguration()
            syncer.account_id = str(target_config['_id'])
            syncer.account_name = target_config['name']
            syncer.config = target_config
            syncer.filter = rules['filter']
            syncer.rewrite = rules['rewrite']
            actions = CheckmkRulesetRule()
            actions.rules = CheckmkRuleMngmt.objects(enabled=True)
            syncer.actions = actions
            syncer.export_cmk_rules()
        else:
            print(f"{ColorCodes.FAIL} Config not found {ColorCodes.ENDC}")
    except CmkException as error_obj:
        print(f'C{ColorCodes.FAIL}MK Connection Error: {error_obj} {ColorCodes.ENDC}')
#.
