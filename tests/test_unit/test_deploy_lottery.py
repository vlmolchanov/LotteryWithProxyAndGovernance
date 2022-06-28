from eth_account import Account
from brownie import config, network, Contract, Lottery
from scripts.helpful_scripts import get_account, get_contract, LOCKAL_BLOCKCHAIN_NETWORKS
from scripts.deploy_lottery import deployLottery, deployProxyAdmin, encode_function_data
from scripts.deploy_proxy import deployProxy


# def test_():
#     # Arrange

#     # Act

#     # Assert

# Basic functionality of lottery without proxy is tested in Lottery program


def test_deploy_lottery_func():
    # Arrange
    account = get_account()
    # Act
    lottery = deployLottery()
    # Asser
    assert lottery.lottery_state() == 0


def test_deploy_proxy_admin():
    pass
    # Arrange
    account = get_account()
    # Act
    proxyAdmin = deployProxyAdmin()
    # Assert
    assert proxyAdmin.owner() == account


def test_deploy_proxy():
    # Arrange
    account = get_account()
    lottery = deployLottery()
    proxyAdmin = deployProxyAdmin()
    # Act
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
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
    # Assert
    # Check initializer params
    assert proxyLottery.lottery_state() == 1
    assert proxyLottery.entranceFeeUSD() == 50
