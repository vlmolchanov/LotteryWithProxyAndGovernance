from brownie import Contract, Lottery, LotteryNew, exceptions, network
from scripts.deploy_proxy import upgradeProxy, upgradeProxyViaGovernance
from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy, deploy_upgraded_lottery
from scripts.play_lottery import playLottery, addPlayersToLottery, endLottery
from scripts.deploy_governance import deployGovernance, transferOwnership
from scripts.helpful_scripts import get_account
import pytest


def test_upgrade_proxy():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)
    lottery = deploy_upgraded_lottery(redeploy)
    # Act
    upgradeProxy(proxy, proxyAdmin, lottery)
    proxyLottery = Contract.from_abi(
        "Lottery", proxy.address, LotteryNew.abi)
    # Assert
    # Check new functionality
    proxyLottery.increaseCounter({"from": get_account()})
    assert proxyLottery.lotteryCounter != 0


def test_upgrade_proxy_via_governance():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)
    governanceToken, timeLock, governance = deployGovernance(redeploy)
    # Transfer ownership of ProxyAdmin contract to Time Lock contract if needed
    if proxyAdmin.owner() != timeLock.address:
        if proxyAdmin.owner() == get_account():
            transferOwnership(proxyAdmin, timeLock)
        else:
            print(
                f"ProxyAdmin is controlled by {proxyAdmin.owner}. Not able to transfer ownership")
            quit()
    else:
        print(f"Proxy Admin is controlled by Governance Time Lock")

    lottery = deploy_upgraded_lottery(redeploy)
    # Act
    proxyLottery = Contract.from_abi(
        "Lottery", proxy.address, LotteryNew.abi)

    # Check that variable doesn't exist
    with pytest.raises(ValueError):
        print(f"New counter is {proxyLottery.lotteryCounter()}")

    upgradeProxyViaGovernance(
        governanceToken, governance, proxyAdmin, proxy, lottery)

    # Assert
    # Check new functionality
    proxyLottery.increaseCounter({"from": get_account()})
    print(f"New counter is {proxyLottery.lotteryCounter()}")
    assert proxyLottery.lotteryCounter() != 0


def test_upgrade_proxy_with_started_lottery():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)
    lottery = deploy_upgraded_lottery(redeploy)
    # play lottery once but don't finish it
    proxyLottery = Contract.from_abi(
        "Lottery", proxy.address, Lottery.abi)
    playLottery(proxyLottery)
    numberOfPlayers = 2
    addPlayersToLottery(proxyLottery, numberOfPlayers)

    # Act
    assert proxyLottery.lottery_state() == 0
    assert proxyLottery.getPlayersNumber() == numberOfPlayers
    prizePool = proxyLottery.prizePool()
    upgradeProxy(proxy, proxyAdmin, lottery)
    proxyLottery = Contract.from_abi(
        "Lottery", proxy.address, LotteryNew.abi)
    # Assert
    # Lottery is still open and has same players
    assert proxyLottery.lottery_state() == 0
    assert proxyLottery.getPlayersNumber() == numberOfPlayers
    assert proxyLottery.prizePool() == prizePool

    # Now end lottery
    endLottery(proxyLottery)
    assert proxyLottery.lottery_state() == 1


def test_upgrade_proxy_via_governance_with_started_lottery():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)

    governanceToken, timeLock, governance = deployGovernance(redeploy)
    # Transfer ownership of ProxyAdmin contract to Time Lock contract if needed
    if proxyAdmin.owner() != timeLock.address:
        if proxyAdmin.owner() == get_account():
            transferOwnership(proxyAdmin, timeLock)
        else:
            print(
                f"ProxyAdmin is controlled by {proxyAdmin.owner}. Not able to transfer ownership")
            quit()
    else:
        print(f"Proxy Admin is controlled by Governance Time Lock")

    lottery = deploy_upgraded_lottery(redeploy)
    # play lottery once but don't finish it
    proxyLottery = Contract.from_abi(
        "Lottery", proxy.address, Lottery.abi)
    playLottery(proxyLottery)
    numberOfPlayers = 2
    addPlayersToLottery(proxyLottery, numberOfPlayers)

    # Act
    assert proxyLottery.lottery_state() == 0
    assert proxyLottery.getPlayersNumber() == numberOfPlayers
    prizePool = proxyLottery.prizePool()
    upgradeProxyViaGovernance(
        governanceToken, governance, proxyAdmin, proxy, lottery)
    proxyLottery = Contract.from_abi(
        "Lottery", proxy.address, LotteryNew.abi)
    # Assert
    # Lottery is still open and has same players
    assert proxyLottery.lottery_state() == 0
    assert proxyLottery.getPlayersNumber() == numberOfPlayers
    assert proxyLottery.prizePool() == prizePool

    # Now end lottery
    endLottery(proxyLottery)
    assert proxyLottery.lottery_state() == 1
