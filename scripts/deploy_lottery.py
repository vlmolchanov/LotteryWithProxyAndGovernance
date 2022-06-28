from brownie import TransparentUpgradeableProxy, ProxyAdmin, Lottery, LotteryNew, config, network
from scripts.helpful_scripts import (
    get_account,
    get_contract,
    encode_function_data,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE
)

from scripts.deploy_proxy import deployProxyAdmin, deployProxyContract


def main():
    # redeploy all contacts
    redeploy = False

    # deploy initial Lottery contract with proxy
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)


def deploy_initial_Lottery_with_proxy(redeploy):

    # deploy lottery
    if len(Lottery) <= 0 or redeploy:
        lottery = deployLottery()
    else:
        lottery = Lottery[-1]
    print(f"Lottery contract deployed at {lottery.address}")

    # deploy proxy admin
    if len(Lottery) <= 0 or redeploy:
        proxyAdmin = deployProxyAdmin()
    else:
        proxyAdmin = ProxyAdmin[-1]
    print(f"ProxyAdmin contract deployed at {proxyAdmin.address}")

    # deploy proxy contract
    if len(TransparentUpgradeableProxy) <= 0 or redeploy:
        proxy = deployProxyContract(lottery, proxyAdmin)
    else:
        proxy = TransparentUpgradeableProxy[-1]
    print(f"Proxy contract deployed at {proxy.address}. !!!Fund me!!!")

    return lottery, proxyAdmin, proxy


def deployLottery():
    print("Deploying new lottery")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        lottery_conract = Lottery.deploy({"from": get_account()},
                                         publish_source=config["networks"][network.show_active()].get(
            "verify", False))
    else:
        lottery_conract = Lottery.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False))
    return lottery_conract


def deploy_upgraded_lottery(redeploy):
    # deploy lottery
    if len(LotteryNew) <= 0 or redeploy:
        lottery = deployLotteryNew()
    else:
        lottery = LotteryNew[-1]
    print(f"Lottery contract deployed at {lottery.address}")
    return lottery


def deployLotteryNew():
    print("Deploying upgraded lottery")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        lottery_conract = LotteryNew.deploy({"from": get_account()},
                                            publish_source=config["networks"][network.show_active()].get(
            "verify", False))
    else:
        lottery_conract = LotteryNew.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False))
    return lottery_conract
