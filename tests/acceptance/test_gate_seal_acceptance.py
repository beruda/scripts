import pytest
from brownie import Contract, interface, web3  # type: ignore
from brownie.network.account import Account

from utils.config import GATE_SEAL_EXPIRY_TIMESTAMP, GATE_SEAL_PAUSE_DURATION_SECONDS, contracts, gate_seal_address


@pytest.fixture(scope="module")
def gate_seal_committee() -> Account:
    ...


@pytest.fixture(scope="module")
def contract() -> Contract:
    return interface.GateSeal(gate_seal_address)


@pytest.mark.skip(reason="No actual committee multisig yet")
def test_gate_seal(contract: Contract, gate_seal_committee: Account):
    assert contract.get_sealing_committee() == gate_seal_committee

    sealables = contract.get_sealables()
    assert len(sealables) == 2
    assert contracts.validators_exit_bus_oracle.address in sealables
    assert contracts.withdrawal_queue.address in sealables

    _check_role(contracts.validators_exit_bus_oracle, "PAUSE_ROLE", contract.address)
    _check_role(contracts.withdrawal_queue, "PAUSE_ROLE", contract.address)

    assert contract.get_seal_duration_seconds() == GATE_SEAL_PAUSE_DURATION_SECONDS
    assert contract.get_expiry_timestamp() == GATE_SEAL_EXPIRY_TIMESTAMP
    assert not contract.is_expired()


def _check_role(contract: Contract, role: str, holder: str):
    role_bytes = web3.keccak(text=role).hex()
    assert contract.getRoleMemberCount(role_bytes) == 1, f"Role {role} on {contract} should have exactly one holder"
    assert contract.getRoleMember(role_bytes, 0) == holder, f"Role {role} holder on {contract} should be {holder}"