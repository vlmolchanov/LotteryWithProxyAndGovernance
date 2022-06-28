'''
1. Deploy lottery contract with proxy and proxy admin
2. Playing on a real network, don't forget to add proxy contract to VRF Subscription
3. Make sure that lottery is working properly (play it once)
4. Start playing lottery and add players, but don't finish it
5. Deploy upgraded lottery
6. Upgrade proxy to a new implementation
7. Check new variables and functions (they are added in new Lottery version)
8. Finish lottery (to check if all variables and states are correctly transferred to updated Lottery version)
'''

from brownie import Lottery, LotteryNew, Contract, network
from scripts.helpful_scripts import (
    get_account,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE
)

from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy, deploy_upgraded_lottery
from scripts.play_lottery import playLottery, addPlayersToLottery, endLottery
from scripts.deploy_proxy import upgradeProxy


def test_upgrade_proxy():
    # # deploy initial Lottery contract with proxy
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

    # Upgrade to new contract
    upgradeToNew = True
    if upgradeToNew:
        # start playing lottery but don't finish it
        playLottery(proxyLottery)
        numberOfPlayers = 3
        addPlayersToLottery(proxyLottery, numberOfPlayers)

        # upgrade to new functionality
        lottery = deploy_upgraded_lottery(redeploy)
        upgradeProxy(proxy, proxyAdmin, lottery)

        proxyLottery = Contract.from_abi(
            "Lottery", proxy.address, LotteryNew.abi)

        # check new function and new variable
        proxyLottery.increaseCounter({"from": get_account()})
        print(f"New counter is {proxyLottery.lotteryCounter()}")
        # end lottery
        endLottery(proxyLottery)
