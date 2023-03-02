"""
TODO description
Voting ??/??/2023.

Shapella Protocol Upgrade

1. Publishing new implementation (0x47EbaB13B806773ec2A2d16873e2dF770D130b50) in Lido app APM repo
2. Updating implementation of Lido app with the new one
3. Publishing new implementation (0x5d39ABaa161e622B99D45616afC8B837E9F19a25) in Node Operators Registry app APM repo
4. Updating implementation of Node Operators Registry app with the new one
5. Publishing new implementation (0x1430194905301504e8830ce4B0b0df7187E84AbD) in Oracle app APM repo
6. Updating implementation of Oracle app with new one

# 7. Call Oracle's finalizeUpgrade_v3() to update internal version counter.
# 8. Create permission for SET_EL_REWARDS_VAULT_ROLE of Lido app assigning it to Voting

"""

import time
import json
from pprint import pprint

from typing import Dict, Tuple, Optional

from brownie.network.transaction import TransactionReceipt
from brownie import ShapellaUpgradeTemplate

from utils.voting import bake_vote_items, confirm_vote_script, create_vote
from utils.evm_script import encode_call_script
from utils.repo import (
    add_implementation_to_lido_app_repo,
    add_implementation_to_nos_app_repo,
    add_implementation_to_oracle_app_repo,
)
from utils.kernel import update_app_implementation
from utils.config import (
    get_deployer_account,
    get_is_live,
    contracts,
    network_name,
    lido_dao_voting_address,
)
from utils.permissions import encode_permission_create, encode_permission_revoke

# noinspection PyUnresolvedReferences
from utils.brownie_prelude import *


def load_shapella_deploy_config():
    with open("scripts/deployed-mainnet-fork-shapella-upgrade.json") as fp:
        return json.load(fp)


# TODO: set content_uri
update_lido_app = {
    "new_address": load_shapella_deploy_config()["app:lido"]["implementation"],
    "content_uri": "0x697066733a516d516b4a4d7476753474794a76577250584a666a4c667954576e393539696179794e6a703759714e7a58377053",
    "id": "0x3ca7c3e38968823ccb4c78ea688df41356f182ae1d159e4ee608d30d68cef320",
    "version": (4, 0, 0),
}

update_nos_app = {
    "new_address": load_shapella_deploy_config()["app:node-operators-registry"]["implementation"],
    "content_uri": "0x697066733a516d61375058486d456a346a7332676a4d3976744850747176754b3832695335455950694a6d7a4b4c7a55353847",
    "id": "0x7071f283424072341f856ac9e947e7ec0eb68719f757a7e785979b6b8717579d",
    "version": (4, 0, 0),
}

update_oracle_app = {
    "new_address": load_shapella_deploy_config()["app:oracle"]["implementation"],
    "content_uri": "0x697066733a516d554d506669454b71354d786d387932475951504c756a47614a69577a31747665703557374564414767435238",
    "id": "0x8b47ba2a8454ec799cd91646e7ec47168e91fd139b23f017455f3e5898aaba93",
    "version": (4, 0, 0),
}


def encode_template_start_upgrade(template_address: str) -> Tuple[str, str]:
    template = ShapellaUpgradeTemplate.at(template_address)
    return template.address, template.startUpgrade.encode_input()


def encode_template_finish_upgrade(template_address: str) -> Tuple[str, str]:
    template = ShapellaUpgradeTemplate.at(template_address)
    return template.address, template.finishUpgrade.encode_input()


def encode_template_proxy_upgrade(proxy_address, implementation) -> Tuple[str, str]:
    proxy = interface.OssifiableProxy(proxy_address)
    return proxy.address, proxy.proxy__upgradeTo.encode_input(implementation)


def encode_template_proxy_ossify(proxy_address) -> Tuple[str, str]:
    proxy = interface.OssifiableProxy(proxy_address)
    return proxy.address, proxy.proxy__ossify.encode_input()


def start_vote(
    tx_params: Dict[str, str], silent: bool, template_implementation: str
) -> Tuple[int, Optional[TransactionReceipt]]:
    """Prepare and run voting."""
    upgrade_config = load_shapella_deploy_config()

    # TODO: add upgrade_ prefix to the voting script to enabme snapshot tests

    voting: interface.Voting = contracts.voting
    lido: interface.Lido = contracts.lido
    lido_oracle: interface.LegacyOracle = contracts.legacy_oracle
    node_operators_registry: interface.NodeOperatorsRegistry = contracts.node_operators_registry
    staking_router = upgrade_config["stakingRouter"]["address"]
    template_address = upgrade_config["shapellaUpgradeTemplate"]["address"]

    call_script_items = [
        # TODO
        encode_template_proxy_upgrade(template_address, template_implementation),
        # TODO
        encode_template_start_upgrade(template_address),
        # 1. Publishing new implementation(TODO)
        #                   in Lido app APM repo 0xF5Dc67E54FC96F993CD06073f71ca732C1E654B1
        add_implementation_to_lido_app_repo(
            update_lido_app["version"], update_lido_app["new_address"], update_lido_app["content_uri"]
        ),
        # 2. Updating implementation of Lido app with the new one TODO
        update_app_implementation(update_lido_app["id"], update_lido_app["new_address"]),
        # 3. Publishing new implementation (TODO)
        #                   in Node Operators Registry app APM repo 0x0D97E876ad14DB2b183CFeEB8aa1A5C788eB1831
        add_implementation_to_nos_app_repo(
            update_nos_app["version"], update_nos_app["new_address"], update_nos_app["content_uri"]
        ),
        # 4. Updating implementation of Node Operators Registry app
        #                   with the new one TODO
        update_app_implementation(update_nos_app["id"], update_nos_app["new_address"]),
        # 5. Publishing new implementation (TODO)
        #     in Oracle app APM repo 0xF9339DE629973c60c4d2b76749c81E6F40960E3A
        add_implementation_to_oracle_app_repo(
            update_oracle_app["version"], update_oracle_app["new_address"], update_oracle_app["content_uri"]
        ),
        # 6. Updating implementation of Oracle app with new one TODO
        update_app_implementation(update_oracle_app["id"], update_oracle_app["new_address"]),
        # 7. Create permission for SET_EL_REWARDS_VAULT_ROLE of Lido app
        #    assigning it to Voting 0x2e59A20f205bB85a89C53f1936454680651E618e
        encode_permission_create(
            entity=staking_router,
            target_app=node_operators_registry,
            permission_name="STAKING_ROUTER_ROLE",
            manager=voting,
        ),
        # 8. Finalize upgrade via template
        encode_template_finish_upgrade(template_address),
        # TODO
        encode_template_proxy_ossify(template_address),
        # TODO: permissions to revoke for goerli might be different
        encode_permission_revoke(lido, "MANAGE_FEE", revoke_from=voting),
        encode_permission_revoke(lido, "MANAGE_WITHDRAWAL_KEY", revoke_from=voting),
        encode_permission_revoke(lido, "MANAGE_PROTOCOL_CONTRACTS_ROLE", revoke_from=voting),
        encode_permission_revoke(lido, "SET_EL_REWARDS_VAULT_ROLE", revoke_from=voting),
        encode_permission_revoke(lido, "SET_EL_REWARDS_WITHDRAWAL_LIMIT_ROLE", revoke_from=voting),
        encode_permission_revoke(node_operators_registry, "ADD_NODE_OPERATOR_ROLE", revoke_from=voting),
        encode_permission_revoke(node_operators_registry, "SET_NODE_OPERATOR_ACTIVE_ROLE", revoke_from=voting),
        encode_permission_revoke(node_operators_registry, "SET_NODE_OPERATOR_NAME_ROLE", revoke_from=voting),
        encode_permission_revoke(node_operators_registry, "SET_NODE_OPERATOR_ADDRESS_ROLE", revoke_from=voting),
        encode_permission_revoke(node_operators_registry, "REPORT_STOPPED_VALIDATORS_ROLE", revoke_from=voting),
        encode_permission_revoke(lido_oracle, "MANAGE_MEMBERS", revoke_from=voting),
        encode_permission_revoke(lido_oracle, "MANAGE_QUORUM", revoke_from=voting),
        encode_permission_revoke(lido_oracle, "SET_BEACON_SPEC", revoke_from=voting),
        encode_permission_revoke(lido_oracle, "SET_REPORT_BOUNDARIES", revoke_from=voting),
        encode_permission_revoke(lido_oracle, "SET_BEACON_REPORT_RECEIVER", revoke_from=voting),
    ]

    vote_desc_items = [
        "X) TODO template upgrade",
        "X) TODO startUpgrade",
        "1) Publish new implementation in Lido app APM repo",
        "2) Updating implementation of Lido app",
        "3) Publishing new implementation in Node Operators Registry app APM repo",
        "4) Updating implementation of Node Operators Registry app",
        "5) Publishing new implementation in Oracle app APM repo",
        "6) Updating implementation of Oracle app",
        "7) Create permission for STAKING_ROUTER_ROLE of NodeOperatorsRegistry assigning it to StakingRouter",
        "8) Finalize upgrade by calling finalizeUpgrade() of ShapellaUpgradeTemplate",
        "8) TODO ossify template proxy",
        "X) TODO revoke 1",
        "X) TODO revoke 2",
        "X) TODO revoke 3",
        "X) TODO revoke 4",
        "X) TODO revoke 5",
        "X) TODO revoke 6",
        "X) TODO revoke 7",
        "X) TODO revoke 8",
        "X) TODO revoke 9",
        "X) TODO revoke 10",
        "X) TODO revoke 11",
        "X) TODO revoke 12",
        "X) TODO revoke 13",
        "X) TODO revoke 14",
        "X) TODO revoke 15",
    ]

    vote_items = bake_vote_items(vote_desc_items, call_script_items)

    # TODO: remove redifinition of "silent" to True
    return confirm_vote_script(vote_items, silent) and create_vote(vote_items, tx_params)


def main():
    tx_params = {"from": get_deployer_account()}

    if get_is_live():
        tx_params["max_fee"] = "300 gwei"
        tx_params["priority_fee"] = "2 gwei"

    vote_id, _ = start_vote(tx_params=tx_params)

    vote_id >= 0 and print(f"Vote created: {vote_id}.")

    time.sleep(5)  # hack for waiting thread #2.