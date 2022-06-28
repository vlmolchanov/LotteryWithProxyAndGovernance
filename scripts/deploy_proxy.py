from brownie import network, config, TransparentUpgradeableProxy, ProxyAdmin
from scripts.helpful_scripts import (
    get_account,
    get_contract,
    encode_function_data,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE,
    proposeState,
)

from scripts.governance_control import governanceProcess


def deployProxyContract(lottery, proxyAdmin):
    priceFeedAddress = get_contract("ethUsdPriceFeed")
    vrfCoordinator = get_contract("vrfCoordinator")
    aavePoolAddress = get_contract("aavePoolAddress")
    wethContractAddress = get_contract("aaveWethAddress")
    # subscriptionId
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS:
        subscriptionId = 1
    else:
        subscriptionId = 3156

    keyHash = config["networks"][network.show_active()].get("keyHash")
    encoded_initializer = encode_function_data(
        lottery.initialize, priceFeedAddress, vrfCoordinator, aavePoolAddress, wethContractAddress, subscriptionId, keyHash)
    proxy = deployProxy(lottery, proxyAdmin, encoded_initializer)
    return proxy


def deployProxy(contract, proxyAdmin, encoded_initializer):
    print("Deploying Proxy contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        proxy = TransparentUpgradeableProxy.deploy(contract.address, proxyAdmin.address, encoded_initializer,
                                                   {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        proxy = TransparentUpgradeableProxy.deploy(contract.address, proxyAdmin.address, encoded_initializer,
                                                   {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return proxy


def deployProxyAdmin():
    print("Deploying Proxy Admin contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        proxyAdmin = ProxyAdmin.deploy(
            {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        proxyAdmin = ProxyAdmin.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))

    return proxyAdmin


def upgradeProxy(proxy, proxyAdmin, contract):
    print("Upgrading to new lottery")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        transaction = proxyAdmin.upgrade(
            proxy, contract.address, {"from": get_account()})
    else:
        transaction = proxyAdmin.upgrade(proxy, contract.address, {
                                         "from": get_account(), "priority_fee": PRIORITY_FEE})
    transaction.wait(1)


def upgradeProxyViaGovernance(governanceToken, governance, proxyAdmin, proxy, newContract):
    # proposing
    DESCRIPTION = "Propose: Change proxy to new implementation"
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyAdmin.upgrade.encode_input(
        proxy, newContract.address,)
    # process via Governance
    governanceProcess(governanceToken, governance, proxyAdmin,
                      DESCRIPTION, encryptedCalldata)
