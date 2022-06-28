from brownie import MockV3Aggregator, MockVRFCoordinatorV2, MockAavePool, MockWeth,  accounts, network, config, chain

LOCKAL_BLOCKCHAIN_NETWORKS = ["development", "ganache-local"]
MAINNET_FORKED_NETWORKS = ["mainnet-fork"]

DECIMALS = 8
ETHPRICE = 120077777777

# Priority fee
PRIORITY_FEE = 2000000000

# Voting params
VOTING_DELAY = 1
VOTING_PERIOD = 10
QUORUM_PERCENTAGE = 4

# Time Lock params
TIMELOCK_DELAY = 1  # delay in seconds

# Propose state description
proposeState = {
    '0': "Pending",
    '1': "Active",
    '2': "Canceled",
    '3': "Defeated",
    '4': "Succeeded",
    '5': "Queued",
    '6': "Expired",
    '7': "Executed"
}


def get_account(index=0):
    if (
        network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS
        or network.show_active()
        # in mainnet we also need account with eth, so brownie provide it to us
        in MAINNET_FORKED_NETWORKS
    ):
        return accounts[index]  # use first account in account array
    else:
        return accounts.add(
            config["wallets"]["from_key"]
        )  # accounts.add(private_key) create account with specified pKey.


contractNameToType = {
    "ethUsdPriceFeed": MockV3Aggregator,
    "vrfCoordinator": MockVRFCoordinatorV2,
    "aavePoolAddress": MockAavePool,
    "aaveWethAddress": MockWeth,
}


def deployMocks():
    print(f"Deploy Mocks")
    MockV3Aggregator.deploy(DECIMALS, ETHPRICE, {"from": get_account()})
    contract = MockVRFCoordinatorV2.deploy(1, 1, {"from": get_account()})
    transaction = contract.createSubscription({"from": get_account()})
    subId = transaction.events["SubscriptionCreated"]["subId"]
    contract.fundSubscription(subId, 100000000000000, {"from": get_account()})
    MockAavePool.deploy({"from": get_account()})
    MockWeth.deploy({"from": get_account()})
    print("Mock is deployed")


def get_contract(contract_name):
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS:
        contractType = contractNameToType[contract_name]
        if len(MockVRFCoordinatorV2) <= 0:
            deployMocks()
        return contractType[-1]
    else:
        return config["networks"][network.show_active()][contract_name]


def encode_function_data(initializer=None, *args):
    """Encodes the function call so we can work with an initializer.
    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: `box.store`.
        Defaults to None.
        args (Any, optional):
        The arguments to pass to the initializer function
    Returns:
        [bytes]: Return the encoded bytes.
    """
    if not len(args):
        args = b''

    if initializer:
        return initializer.encode_input(*args)

    return b''


def wait(numberOfBlocks, transaction):
    print(f"Waiting {numberOfBlocks} blocks")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        for block in range(numberOfBlocks):
            get_account().transfer(get_account(), "0 ether")
            print(chain.height)
    else:
        transaction.wait(numberOfBlocks)
