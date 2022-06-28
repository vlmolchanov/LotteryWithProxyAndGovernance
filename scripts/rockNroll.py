from brownie import Lottery, LotteryNew, Contract, network
from scripts.helpful_scripts import (
    get_account,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE
)

from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy, deploy_upgraded_lottery
from scripts.play_lottery import playLottery, addPlayersToLottery, endLottery, playLotteryViaGovernance, finishLotteryViaGovernance
from scripts.deploy_governance import deployGovernance, transferOwnership
from scripts.deploy_proxy import upgradeProxyViaGovernance


def main():
    # deploy initial Lottery contract with proxy
    redeploy = False
    if network.show_active() == "development":
        redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)

    # upgradeable lottery
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    # if want to play lottery once
    playOnce = False
    if playOnce:
        playLottery(proxyLottery)
        numberOfPlayers = 3
        addPlayersToLottery(proxyLottery, numberOfPlayers)
        endLottery(proxyLottery)

    # create governance
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

    # if want to upgrade to new contract
    upgradeToNew = True
    if upgradeToNew:
        # play lottery once but don't finish it
        playLottery(proxyLottery)
        numberOfPlayers = 2
        addPlayersToLottery(proxyLottery, numberOfPlayers)
        # endLottery(proxyLottery)

        # upgrade to new functionality
        redeploy = True
        lottery = deploy_upgraded_lottery(redeploy)
        #upgradeProxy(proxy, proxyAdmin, lottery)
        upgradeProxyViaGovernance(
            governanceToken, governance, proxyAdmin, proxy, lottery)
        proxyLottery = Contract.from_abi(
            "Lottery", proxy.address, LotteryNew.abi)

        # check new function and new variable
        proxyLottery.increaseCounter({"from": get_account()})
        print(f"New counter is {proxyLottery.lotteryCounter()}")
        # end lottery
        endLottery(proxyLottery)

    # Transfering ownership of Lottery to Governance (TimeLock)
    if proxyLottery.owner() != timeLock.address:
        if proxyLottery.owner() == get_account():
            transferOwnership(proxyLottery, timeLock)
        else:
            print(
                f"Lottery is controlled by {proxyLottery.owner()}. Not able to transfer ownership")
            quit()
    else:
        print(f"Lottery is controlled by Governance Time Lock")

    # now start and end it via governance
    playLotteryViaGovernance(governanceToken, governance, proxyLottery)
    numberOfPlayers = 2
    addPlayersToLottery(proxyLottery, numberOfPlayers)
    finishLotteryViaGovernance(governanceToken, governance, proxyLottery)
