from typing import Dict

import pytest

from brownie import accounts, chain, MockCallTarget, Contract, interface

from utils.test.snapshot_helpers import ValueChanged, dict_zip, dict_diff, assert_no_diffs, assert_expected_diffs

from utils.voting import create_vote, bake_vote_items
from utils.config import ldo_vote_executors_for_tests, ldo_holder_address_for_tests, contracts
from utils.import_current_votes import is_there_any_vote_scripts, start_and_execute_votes


@pytest.fixture(scope="module")
def vote_time():
    return contracts.voting.voteTime()


@pytest.fixture(scope="module", autouse=True)
def call_target():
    return MockCallTarget.deploy({"from": accounts[0]})


@pytest.fixture(scope="module")
def old_voting():
    return Contract.from_explorer(
        address=contracts.voting, as_proxy_for=interface.AppProxyUpgradeable(contracts.voting).implementation()
    )


def snapshot(voting, vote_id):
    length = voting.votesLength()
    vote = voting.getVote(vote_id)

    return {
        "address": voting.address,
        "voteTime": voting.voteTime(),
        "CREATE_VOTES_ROLE": voting.CREATE_VOTES_ROLE(),
        "MODIFY_SUPPORT_ROLE": voting.MODIFY_SUPPORT_ROLE(),
        "MODIFY_QUORUM_ROLE": voting.MODIFY_QUORUM_ROLE(),
        "minAcceptQuorumPct": voting.minAcceptQuorumPct(),
        "supportRequiredPct": voting.supportRequiredPct(),
        "votesLength": length,
        "vote_open": vote[0],
        "vote_executed": vote[1],
        "vote_supportRequired": vote[4],
        "vote_minAcceptQuorum": vote[5],
        "vote_yea": vote[6],
        "vote_nay": vote[7],
        "vote_votingPower": vote[8],
        "vote_script": vote[9],
        "vote_canExecute": voting.canExecute(vote_id),
        "vote_voter1_state": voting.getVoterState(vote_id, ldo_vote_executors_for_tests[0]),
        "vote_voter2_state": voting.getVoterState(vote_id, ldo_vote_executors_for_tests[1]),
        "vote_voter3_state": voting.getVoterState(vote_id, ldo_vote_executors_for_tests[2]),
    }


def steps(voting, call_target, vote_time) -> Dict[str, Dict[str, ValueChanged]]:
    result = {}

    params = {"from": ldo_holder_address_for_tests}
    vote_items = [(call_target.address, call_target.perform_call.encode_input())]
    vote_id = create_vote(bake_vote_items(["Test voting"], vote_items), params)[0]
    result["create"] = snapshot(voting, vote_id)

    for indx, voter in enumerate(ldo_vote_executors_for_tests):
        account = accounts.at(voter, force=True)
        voting.vote(vote_id, True, False, {"from": account})
        result[f"vote_#{indx}"] = snapshot(voting, vote_id)

    chain.sleep(vote_time + 100)
    chain.mine()
    result["wait"] = snapshot(voting, vote_id)

    assert not call_target.called()

    voting.executeVote(vote_id, {"from": ldo_holder_address_for_tests})

    assert call_target.called()

    result["enact"] = snapshot(voting, vote_id)
    return result


@pytest.mark.skipif(condition=not is_there_any_vote_scripts(), reason="No votes")
def test_create_wait_enact(old_voting, helpers, vote_time, call_target):
    """
    Run a smoke test before upgrade, then after upgrade, and compare snapshots at each step
    """
    votesLength = old_voting.votesLength()
    before: Dict[str, Dict[str, any]] = steps(old_voting, call_target, vote_time)
    chain.revert()
    start_and_execute_votes(contracts.voting, helpers)
    after: Dict[str, Dict[str, any]] = steps(contracts.voting, call_target, vote_time)

    step_diffs: Dict[str, Dict[str, ValueChanged]] = {}

    for step, pair_of_snapshots in dict_zip(before, after).items():
        (before, after) = pair_of_snapshots
        step_diffs[step] = dict_diff(before, after)

    for step_name, diff in step_diffs.items():
        assert_expected_diffs(
            step_name, diff, {"votesLength": ValueChanged(from_val=votesLength + 1, to_val=votesLength + 3)}
        )
        assert_no_diffs(step_name, diff)
