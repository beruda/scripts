#
# Other
#
# see LidoOracle's proxy appId()
ORACLE_APP_ID = "0x8b47ba2a8454ec799cd91646e7ec47168e91fd139b23f017455f3e5898aaba93"
# see Lido's proxy appId()
LIDO_APP_ID = "0x3ca7c3e38968823ccb4c78ea688df41356f182ae1d159e4ee608d30d68cef320"
# see NodeOperatorsRegistry's proxy appId()
NODE_OPERATORS_REGISTRY_APP_ID = "0x7071f283424072341f856ac9e947e7ec0eb68719f757a7e785979b6b8717579d"

# 0x01...withdrawal_vault or Lido.getWithdrawalCredentials()
WITHDRAWAL_CREDENTIALS = "0x010000000000000000000000b9d7934878b5fb9610b3fe8a5e441e8fad7e293f"

# Existed values from chain
oracle_committee = (
    "0x140Bd8FbDc884f48dA7cb1c09bE8A2fAdfea776E",
    "0x1d0813bf088BE3047d827D98524fBf779Bc25F00",
    "0x404335BcE530400a5814375E7Ec1FB55fAff3eA2",
    "0x946D3b081ed19173dC83Cd974fC69e1e760B7d78",
    "0x007DE4a5F7bc37E2F26c0cb2E8A95006EE9B89b5",
    "0xEC4BfbAF681eb505B94E4a7849877DC6c600Ca3A",
    "0x61c91ECd902EB56e314bB2D5c5C07785444Ea1c8",
    "0x1Ca0fEC59b86F549e1F1184d97cb47794C8Af58d",
    "0xA7410857ABbf75043d61ea54e07D57A6EB6EF186",
)

deposit_security_module_guardians = [
    "0x5fd0dDbC3351d009eb3f88DE7Cd081a614C519F1",
    "0x7912Fa976BcDe9c2cf728e213e892AD7588E6AaF",
    "0x14D5d5B71E048d2D75a39FfC5B407e3a3AB6F314",
    "0xf82D88217C249297C6037BA77CE34b3d8a90ab43",
    "0xa56b128Ea2Ea237052b0fA2a96a387C0E43157d8",
    "0xd4EF84b638B334699bcf5AF4B0410B8CCD71943f",
]
ORACLE_QUORUM = 5
DSM_GUARDIAN_QUORUM = 4
LIDO_MAX_STAKE_LIMIT_ETH = 150_000
CURATED_NODE_OPERATORS_COUNT = 30
CURATED_NODE_OPERATORS_ACTIVE_COUNT = 30

# Ethereum Chain parameters
CHAIN_SLOTS_PER_EPOCH = 32
CHAIN_SECONDS_PER_SLOT = 12
CHAIN_GENESIS_TIME = 1606824023
# NodeOperatorsRegistry
STUCK_PENALTY_DELAY = 432000
# OracleDaemonConfig
NORMALIZED_CL_REWARD_PER_EPOCH = 64
NORMALIZED_CL_REWARD_MISTAKE_RATE_BP = 1000
REBASE_CHECK_NEAREST_EPOCH_DISTANCE = 1
REBASE_CHECK_DISTANT_EPOCH_DISTANCE = 23
VALIDATOR_DELAYED_TIMEOUT_IN_SLOTS = 7200
VALIDATOR_DELINQUENT_TIMEOUT_IN_SLOTS = 28800
PREDICTION_DURATION_IN_SLOTS = 50400
FINALIZATION_MAX_NEGATIVE_REBASE_EPOCH_SHIFT = 1350
NODE_OPERATOR_NETWORK_PENETRATION_THRESHOLD_BP = 100
# OracleReportSanityChecker
CHURN_VALIDATORS_PER_DAY_LIMIT = 40000
ONE_OFF_CL_BALANCE_DECREASE_BP_LIMIT = 500
ANNUAL_BALANCE_INCREASE_BP_LIMIT = 1000
SIMULATED_SHARE_RATE_DEVIATION_BP_LIMIT = 50
MAX_VALIDATOR_EXIT_REQUESTS_PER_REPORT = 500
MAX_ACCOUNTING_EXTRA_DATA_LIST_ITEMS_COUNT = 500
MAX_NODE_OPERATORS_PER_EXTRA_DATA_ITEM_COUNT = 100
REQUEST_TIMESTAMP_MARGIN = 7680
MAX_POSITIVE_TOKEN_REBASE = 750000
# Burner
TOTAL_NON_COVER_SHARES_BURNT = 32145684728326685744
TOTAL_COVER_SHARES_BURNT = 0
# DepositSecurityModule
DSM_MAX_DEPOSITS_PER_BLOCK = 150
DSM_MIN_DEPOSIT_BLOCK_DISTANCE = 25
DSM_PAUSE_INTENT_VALIDITY_PERIOD_BLOCKS = 6646
# StakingRouter and StakingModules
STAKING_MODULE_NOR_ID = 1
STAKING_MODULE_NOR_NAME = "curated-onchain-v1"
STAKING_MODULE_NOR_TYPE = (
    "0x637572617465642d6f6e636861696e2d76310000000000000000000000000000"  # bytes32("curated-onchain-v1");
)
STAKING_MODULE_NOR_MODULE_FEE = 500
STAKING_MODULE_NOR_TREASURY_FEE = 500
STAKING_MODULES_FEE_E4 = STAKING_MODULE_NOR_MODULE_FEE
STAKING_MODULES_TREASURY_FEE_E4 = STAKING_MODULE_NOR_TREASURY_FEE
STAKING_MODULES_FEE_E20 = 5 * 10**18
STAKING_MODULES_TREASURY_FEE_E20 = 5 * 10**18
# AccountingOracle
ACCOUNTING_ORACLE_EPOCHS_PER_FRAME = 225
# ValidatorsExitBusOracle
VALIDATORS_EXIT_BUS_ORACLE_EPOCHS_PER_FRAME = 75
# AccountingOracle and ValidatorsExitBusOracle
FAST_LANE_LENGTH_SLOTS = 10
# WithdrawalQueueERC721
WITHDRAWAL_QUEUE_ERC721_NAME = "stETH Withdrawal NFT"
WITHDRAWAL_QUEUE_ERC721_SYMBOL = "unstETH"
WITHDRAWAL_QUEUE_ERC721_BASE_URI = ""
# GateSeal
GATE_SEAL_PAUSE_DURATION_SECONDS = 6 * 24 * 60 * 60  # 6 days
GATE_SEAL_EXPIRY_TIMESTAMP = 1713139200  # 2024-04-15 00:00GMT