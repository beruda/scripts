import pytest

from brownie import reverts, accounts, chain  # type: ignore
from utils.test.oracle_report_helpers import oracle_report, ZERO_BYTES32

from utils.test.helpers import almostEqEth, ETH
from utils.config import (
    contracts,
    deployer_eoa,
    lido_dao_withdrawal_queue,
    lido_dao_validators_exit_bus_oracle,
    gate_seal_address,
    GATE_SEAL_PAUSE_DURATION_SECONDS,
    GATE_SEAL_EXPIRY_TIMESTAMP,
    CHAIN_SLOTS_PER_EPOCH,
    CHAIN_SECONDS_PER_SLOT,
    ACCOUNTING_ORACLE_EPOCHS_PER_FRAME,
)


@pytest.fixture(autouse=True)
def shared_setup(fn_isolation):
    pass


def test_gate_seal_expiration():
    assert not contracts.gate_seal.is_expired()
    time = chain.time()
    chain.sleep(GATE_SEAL_EXPIRY_TIMESTAMP - time)
    chain.mine(1)
    assert contracts.gate_seal.is_expired()
    with reverts("gate seal: expired"):
        contracts.gate_seal.seal(
            [lido_dao_withdrawal_queue, lido_dao_validators_exit_bus_oracle], {"from": deployer_eoa}
        )


def test_gate_seal_scenario(steth_holder):
    account = accounts.at(steth_holder, force=True)
    REQUESTS_COUNT = 2
    REQUEST_AMOUNT = ETH(1)
    REQUESTS_SUM = REQUESTS_COUNT * REQUEST_AMOUNT

    """ requests to be finalized """
    contracts.lido.approve(contracts.withdrawal_queue.address, REQUESTS_SUM, {"from": steth_holder})
    request_tx = contracts.withdrawal_queue.requestWithdrawals(
        [REQUEST_AMOUNT for _ in range(REQUESTS_COUNT)], steth_holder, {"from": steth_holder}
    )
    claimable_request_ids = [event["requestId"] for event in request_tx.events["WithdrawalRequested"]]

    """ finalization """
    report_tx = oracle_report(silent=True)[0]
    # on second report requests will get finalized for sure
    if not report_tx.events.count("WithdrawalsFinalized") == 1:
        report_tx = oracle_report(silent=True)[0]
    assert report_tx.events.count("WithdrawalsFinalized") == 1

    post_report_statuses = contracts.withdrawal_queue.getWithdrawalStatus(claimable_request_ids, {"from": steth_holder})
    for i, _ in enumerate(claimable_request_ids):
        (_, _, _, _, isFinalized, isClaimed) = post_report_statuses[i]
        assert isFinalized
        assert not isClaimed

    """ requests to be left pending """
    contracts.lido.approve(contracts.withdrawal_queue.address, REQUESTS_SUM, {"from": steth_holder})
    request_tx = contracts.withdrawal_queue.requestWithdrawals(
        [REQUEST_AMOUNT for _ in range(REQUESTS_COUNT)], steth_holder, {"from": steth_holder}
    )
    pending_request_ids = [event["requestId"] for event in request_tx.events["WithdrawalRequested"]]

    """ sealing """
    sealables = [lido_dao_withdrawal_queue, lido_dao_validators_exit_bus_oracle]
    seal_tx = contracts.gate_seal.seal(sealables, {"from": deployer_eoa})

    assert seal_tx.events.count("Sealed") == 2
    for i, seal_event in enumerate(seal_tx.events["Sealed"]):
        assert seal_event["gate_seal"] == gate_seal_address
        assert seal_event["sealed_for"] == GATE_SEAL_PAUSE_DURATION_SECONDS
        assert seal_event["sealed_by"] == deployer_eoa
        assert seal_event["sealable"] == sealables[i]
        assert seal_event["sealed_at"] == seal_tx.timestamp

    # brownie for some reason fails to decode second event
    # assert seal_tx.events.count("Paused") == 2
    for pause_event in seal_tx.events["Paused"]:
        assert pause_event["duration"] == GATE_SEAL_PAUSE_DURATION_SECONDS

    assert contracts.gate_seal.is_expired()
    with reverts("gate seal: expired"):
        seal_tx = contracts.gate_seal.seal(sealables, {"from": deployer_eoa})

    assert contracts.withdrawal_queue.isPaused()
    assert contracts.withdrawal_queue.getResumeSinceTimestamp() == seal_tx.timestamp + GATE_SEAL_PAUSE_DURATION_SECONDS

    assert contracts.validators_exit_bus_oracle.isPaused()
    assert (
        contracts.validators_exit_bus_oracle.getResumeSinceTimestamp()
        == seal_tx.timestamp + GATE_SEAL_PAUSE_DURATION_SECONDS
    )

    # reverts on requestWithdrawals
    contracts.lido.approve(contracts.withdrawal_queue.address, REQUESTS_SUM, {"from": steth_holder})
    with reverts("typed error: 0x14378398"):  # signature for ResumedExpected()
        contracts.withdrawal_queue.requestWithdrawals(
            [REQUEST_AMOUNT for _ in range(REQUESTS_COUNT)], steth_holder, {"from": steth_holder}
        )

    # reverts on VEBO report
    with reverts("typed error: 0x14378398"):  # signature for ResumedExpected()
        contracts.validators_exit_bus_oracle.submitReportData((1, 1, 1, 1, ZERO_BYTES32), 1, {"from": steth_holder})

    # reverts on finalization attempt
    with reverts("typed error: 0x14378398"):  # signature for ResumedExpected()
        contracts.withdrawal_queue.finalize(1, 1, {"from": steth_holder})

    """ claim """
    assert contracts.withdrawal_queue.isPaused()
    assert contracts.validators_exit_bus_oracle.isPaused()

    lastCheckpointIndex = contracts.withdrawal_queue.getLastCheckpointIndex()
    hints = contracts.withdrawal_queue.findCheckpointHints(claimable_request_ids, 1, lastCheckpointIndex)
    claim_balance_before = account.balance()
    claim_tx = contracts.withdrawal_queue.claimWithdrawals(claimable_request_ids, hints, {"from": steth_holder})
    claim_balance_after = account.balance()

    assert contracts.withdrawal_queue.isPaused()
    assert contracts.validators_exit_bus_oracle.isPaused()

    assert almostEqEth(
        claim_balance_after - claim_balance_before + claim_tx.gas_used * claim_tx.gas_price, REQUESTS_SUM
    )
    assert claim_tx.events.count("WithdrawalClaimed") == REQUESTS_COUNT

    """ accounting oracle reports until we pass pause and claim"""
    MAX_REPORTS_UNTIL_RESUME = (
        GATE_SEAL_PAUSE_DURATION_SECONDS
        // (CHAIN_SECONDS_PER_SLOT * CHAIN_SLOTS_PER_EPOCH * ACCOUNTING_ORACLE_EPOCHS_PER_FRAME)
        + 2
    )
    reports_passed = 0
    while True:
        (report_tx, _) = oracle_report(silent=True)
        reports_passed += 1
        print(
            f"Oracle report {reports_passed} at {report_tx.timestamp}/{seal_tx.timestamp + GATE_SEAL_PAUSE_DURATION_SECONDS} seconds to resume"
        )
        if report_tx.events.count("WithdrawalsFinalized") == 1:
            break
        assert reports_passed <= MAX_REPORTS_UNTIL_RESUME

    assert not contracts.withdrawal_queue.isPaused()
    assert not contracts.validators_exit_bus_oracle.isPaused()

    """ post seal claim """
    lastCheckpointIndex = contracts.withdrawal_queue.getLastCheckpointIndex()
    hints = contracts.withdrawal_queue.findCheckpointHints(pending_request_ids, 1, lastCheckpointIndex)
    claim_balance_before = account.balance()
    claim_tx = contracts.withdrawal_queue.claimWithdrawals(pending_request_ids, hints, {"from": steth_holder})
    claim_balance_after = account.balance()

    assert almostEqEth(
        claim_balance_after - claim_balance_before + claim_tx.gas_used * claim_tx.gas_price, REQUESTS_SUM
    )
    assert claim_tx.events.count("WithdrawalClaimed") == REQUESTS_COUNT