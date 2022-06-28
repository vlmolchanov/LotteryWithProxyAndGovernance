'''
1. Deploy lottery contract with proxy and proxy admin
2. Playing on a real network, don't forget to add proxy contract to VRF Subscription
3. Make sure that lottery is working properly (play it once)
4. Deploy governance, governance token and timelock
5. Transfer ownership of ProxyAdmin to TimeLock contract
6. Start playing lottery and add players, but don't finish it
7. Deploy upgraded lottery
8. Upgrade proxy to a new implementation via governance
9. Check new variables and functions (they are added in new Lottery version)
10. Finish lottery (to check if all variables and states are correctly transferred to updated Lottery version)
11. Transfer ownership of Lottery to Timelock (governance). Now all admin functions are available only for governance
12. Test functions of Lottery
'''

from brownie import Lottery, LotteryNew, Contract, network
from scripts.helpful_scripts import (
    get_account,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE
)

from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy, deploy_upgraded_lottery
from scripts.play_lottery import playLottery, addPlayersToLottery, endLottery, playLotteryViaGovernance, finishLotteryViaGovernance, emrgStopLotteryViaGovernance
from scripts.deploy_governance import deployGovernance, transferOwnership
from scripts.deploy_proxy import upgradeProxyViaGovernance


def test_upgrade_and_lottery_control_via_governance():
    # deploy initial Lottery contract with proxy
    redeploy = False
    if network.show_active() == "development":
        redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)

    # upgradeable lottery
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    # play lottery once
    playOnce = True
    if playOnce:
        playLottery(proxyLottery)
        numberOfPlayers = 3
        addPlayersToLottery(proxyLottery, numberOfPlayers)
        endLottery(proxyLottery)

    # create governance
    governanceToken, timeLock, governance = deployGovernance(redeploy)

    # transfer ownership of ProxyAdmin contract to Time Lock contract if needed
    if proxyAdmin.owner() != timeLock.address:
        if proxyAdmin.owner() == get_account():
            transferOwnership(proxyAdmin, timeLock)
        else:
            print(
                f"ProxyAdmin is controlled by {proxyAdmin.owner}. Not able to transfer ownership")
            quit()
    else:
        print(f"Proxy Admin is controlled by Governance Time Lock")

    # upgrade to new contract
    upgradeToNew = True
    if upgradeToNew:
        # play lottery once but don't finish it
        playLottery(proxyLottery)
        numberOfPlayers = 3
        addPlayersToLottery(proxyLottery, numberOfPlayers)

        # upgrade to new functionality
        redeploy = True
        lottery = deploy_upgraded_lottery(redeploy)

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
    numberOfPlayers = 3
    addPlayersToLottery(proxyLottery, numberOfPlayers)
    finishLotteryViaGovernance(governanceToken, governance, proxyLottery)

    # emergency stop lottery
    playLotteryViaGovernance(governanceToken, governance, proxyLottery)
    numberOfPlayers = 3
    addPlayersToLottery(proxyLottery, numberOfPlayers)
    emrgStopLotteryViaGovernance(governanceToken, governance, proxyLottery)
