import pytest
from brownie import interface  # type: ignore

from utils.config import (
    contracts,
    lido_dao_hash_consensus_for_accounting_oracle,
    lido_dao_accounting_oracle_implementation,
    lido_dao_accounting_oracle,
    oracle_committee,
)

beacon_spec = {
    "slotsPerEpoch": 32,
    "secondsPerSlot": 12,
    "genesisTime": 1606824023,
}


@pytest.fixture(scope="module")
def contract() -> interface.AccountingOracle:
    return interface.AccountingOracle(lido_dao_accounting_oracle)


def test_proxy(contract):
    proxy = interface.OssifiableProxy(contract)
    assert proxy.proxy__getImplementation() == lido_dao_accounting_oracle_implementation
    assert proxy.proxy__getAdmin() == contracts.agent.address


def test_constants(contract):
    assert contract.LIDO() == contracts.lido
    assert contract.LOCATOR() == contracts.lido_locator
    assert contract.LEGACY_ORACLE() == contracts.legacy_oracle
    assert contract.EXTRA_DATA_FORMAT_EMPTY() == 0
    assert contract.EXTRA_DATA_FORMAT_LIST() == 1
    assert contract.EXTRA_DATA_TYPE_STUCK_VALIDATORS() == 1
    assert contract.EXTRA_DATA_TYPE_EXITED_VALIDATORS() == 2
    assert contract.SECONDS_PER_SLOT() == beacon_spec["secondsPerSlot"]
    assert contract.GENESIS_TIME() == beacon_spec["genesisTime"]


def test_versioned(contract):
    assert contract.getContractVersion() == 1


def test_consensus(contract):
    assert contract.getConsensusVersion() == 1
    assert contract.getConsensusContract() == lido_dao_hash_consensus_for_accounting_oracle


def test_processing_state(contract):
    state = contract.getProcessingState()
    assert state["currentFrameRefSlot"] > 5254400
    assert state["processingDeadlineTime"] == 0
    assert state["mainDataHash"] == "0x0000000000000000000000000000000000000000000000000000000000000000"
    assert state["mainDataSubmitted"] == False
    assert state["extraDataHash"] == "0x0000000000000000000000000000000000000000000000000000000000000000"
    assert state["extraDataFormat"] == 0
    assert state["extraDataSubmitted"] == False
    assert state["extraDataItemsCount"] == 0
    assert state["extraDataItemsSubmitted"] == 0

    assert contract.getLastProcessingRefSlot() > 5254400


def test_report(contract):
    report = contract.getConsensusReport()
    assert report["hash"] == "0x0000000000000000000000000000000000000000000000000000000000000000"
    assert report["refSlot"] > 5254400
    assert report["processingDeadlineTime"] == 0
    assert report["processingStarted"] == False


def test_accounting_hash_consensus(contract):
    # HashConsensus
    consensus = interface.HashConsensus(contract.getConsensusContract())

    current_frame = consensus.getCurrentFrame()
    assert current_frame["refSlot"] > 5254400
    assert current_frame["reportProcessingDeadlineSlot"] > 5254400

    chain_config = consensus.getChainConfig()
    assert chain_config["slotsPerEpoch"] == beacon_spec["slotsPerEpoch"]
    assert chain_config["secondsPerSlot"] == beacon_spec["secondsPerSlot"]
    assert chain_config["genesisTime"] == beacon_spec["genesisTime"]

    frame_config = consensus.getFrameConfig()
    assert frame_config["initialEpoch"] > 5254400 / 32
    assert frame_config["epochsPerFrame"] == 225
    assert frame_config["fastLaneLengthSlots"] == 10

    assert consensus.getInitialRefSlot() > 5254400

    assert consensus.getQuorum() == 5

    members = consensus.getMembers()
    assert members["addresses"] == oracle_committee
