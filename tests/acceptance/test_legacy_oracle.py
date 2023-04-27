import pytest
from brownie import interface, chain  # type: ignore

from utils.config import (
    contracts,
    lido_dao_legacy_oracle,
    lido_dao_legacy_oracle_implementation,
    ORACLE_APP_ID,
    lido_dao_evm_script_registry,
    CHAIN_SLOTS_PER_EPOCH,
    CHAIN_SECONDS_PER_SLOT,
    CHAIN_GENESIS_TIME,
    ACCOUNTING_ORACLE_EPOCHS_PER_FRAME,
)

lastSeenTotalPooledEther = 5879742251110033487920093


@pytest.fixture(scope="module")
def contract() -> interface.LegacyOracle:
    return interface.LegacyOracle(lido_dao_legacy_oracle)


def test_links(contract):
    assert contract.getLido() == contracts.lido
    assert contract.getAccountingOracle() == contracts.accounting_oracle
    assert contract.getEVMScriptRegistry() == lido_dao_evm_script_registry


def test_aragon(contract):
    proxy = interface.AppProxyUpgradeable(contract)
    assert proxy.implementation() == lido_dao_legacy_oracle_implementation
    assert contract.kernel() == contracts.kernel
    assert contract.appId() == ORACLE_APP_ID
    assert contract.hasInitialized() == True
    assert contract.isPetrified() == False


def test_versioned(contract):
    assert contract.getContractVersion() == 4


def test_recoverability(contract):
    assert contract.getRecoveryVault() == contracts.agent
    assert contract.allowRecoverability(contracts.ldo_token) == True


def test_legacy_oracle_state(contract):
    reported_delta = contract.getLastCompletedReportDelta()
    assert reported_delta["postTotalPooledEther"] > lastSeenTotalPooledEther
    assert reported_delta["preTotalPooledEther"] >= lastSeenTotalPooledEther
    assert reported_delta["timeElapsed"] == 86400

    current_frame = contract.getCurrentFrame()
    assert current_frame["frameEpochId"] > 0
    assert current_frame["frameStartTime"] > 0
    assert current_frame["frameEndTime"] > 0

    assert contract.getLastCompletedEpochId() > 0

    assert contract.getInitializationBlock() > 0
    assert contract.getInitializationBlock() <= chain.height

    oracle_beacon_spec = contracts.legacy_oracle.getBeaconSpec()

    assert oracle_beacon_spec["epochsPerFrame"] == ACCOUNTING_ORACLE_EPOCHS_PER_FRAME
    assert oracle_beacon_spec["slotsPerEpoch"] == CHAIN_SLOTS_PER_EPOCH
    assert oracle_beacon_spec["secondsPerSlot"] == CHAIN_SECONDS_PER_SLOT
    assert oracle_beacon_spec["genesisTime"] == CHAIN_GENESIS_TIME