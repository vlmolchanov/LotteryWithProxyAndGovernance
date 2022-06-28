from brownie import Lottery, MockVRFCoordinatorV2, network, Contract, chain
from scripts.helpful_scripts import (
    get_account,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE
)

from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy
from scripts.governance_control import governanceProcess

import time


def main():

    # deploy initial Lottery contract with proxy
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)

    # upgradeable lottery
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    # play lottery
    proxyLottery.startLottery({"from": get_account()})

    print(proxyLottery.getEntranceFee())

    numberOfPlayers = 3
    addPlayersToLottery(proxyLottery, numberOfPlayers)

    playLottery(proxyLottery)
    endLottery(proxyLottery)


def endLottery(lottery):
    account = get_account()
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        transaction = lottery.endLottery({"from": account})
    else:
        transaction = lottery.endLottery(
            {"from": account, "priority_fee": PRIORITY_FEE})
    transaction.wait(1)

    print(f"Number of participants is {lottery.getPlayersNumber()}")
    print("Selecting winner ......")

    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS:
        contract = MockVRFCoordinatorV2[-1]
        requestId = transaction.events["RandomRequestSent"]["requestId"]
        tx = contract.fulfillRandomWords(
            requestId, lottery, {"from": account})
        tx.wait(1)
    else:
        delay = 180
        print(f"Waiting {delay} seconds")
        time.sleep(delay)

    if lottery.lottery_state() == 3:
        print("Lottery is finished")
        print(f"Winner is {lottery.recentWinner()}")
        print("Sending money to winner")

        if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
            transaction = lottery.transferFundsToWinner({"from": account})
        else:
            transaction = lottery.transferFundsToWinner(
                {"from": account, "priority_fee": PRIORITY_FEE})
        transaction.wait(1)
        print("Money sent to winner")
    else:
        print("Winner is not specified yet. Wait a bit")
        quit()


def playLottery(lottery):
    account = get_account()
    if lottery.lottery_state() == 2:
        print("Lottery is calculating winner. Come later")
        quit()
    if lottery.lottery_state() == 3:
        print("Lottery is finished")
        print(f"Winner is {lottery.recentWinner()}")
        print("Sending money to winner")
        lottery.transferFundsToWinner({"from": account})
        quit()
    if lottery.lottery_state() == 1:
        lottery.startLottery({"from": account})
    print("Lottery is started")
    print(f"Money can be sent to {lottery} contract")
    print(
        f"Entrance fee is {lottery.entranceFeeUSD()} USD / {lottery.getEntranceFee()} wei"
    )


def addPlayersToLottery(lottery, numberOfPlayers):
    account = get_account()
    if lottery.getPlayersNumber() < numberOfPlayers:
        # Enter lottery with requested people
        playersToEnter = numberOfPlayers - lottery.getPlayersNumber()
        ethVal = lottery.getEntranceFee() + 1000
        for i in range(0, playersToEnter, 1):
            if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
                transaction = lottery.enter({"from": account, "value": ethVal})
            else:
                transaction = lottery.enter(
                    {"from": account, "value": ethVal, "priority_fee": PRIORITY_FEE})
            transaction.wait(1)
            print(f"Player № {lottery.getPlayersNumber()} entered lottery")
            if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
                delay = 1
            else:
                delay = 20
            time.sleep(delay)
    else:
        print(
            f"Lottery already has {lottery.getPlayersNumber()} players. It's enough to proceed.")

# Functions via governance


def playLotteryViaGovernance(governanceToken, governance, lottery):
    account = get_account()
    if lottery.lottery_state() == 2:
        print("Lottery is calculating winner. Come later")
        quit()
    if lottery.lottery_state() == 3:
        print("Lottery is finished")
        print(f"Winner is {lottery.recentWinner()}")
        print("Sending money to winner")
        if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
            transaction = lottery.transferFundsToWinner({"from": account})
        else:
            transaction = lottery.transferFundsToWinner(
                {"from": account, "priority_fee": PRIORITY_FEE})
        transaction.wait(1)
        quit()
    if lottery.lottery_state() == 1:
        startLotteryViaGovernance(governanceToken, governance, lottery)
    print("Lottery is started")
    print(f"Money can be sent to {lottery} contract")
    print(
        f"Entrance fee is {lottery.entranceFeeUSD()} USD / {lottery.getEntranceFee()} wei"
    )


def finishLotteryViaGovernance(governanceToken, governance, lottery):
    account = get_account()
    transaction = endLotteryViaGovernance(governanceToken, governance, lottery)

    print(f"Number of participants is {lottery.getPlayersNumber()}")
    print("Selecting winner ......")

    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS:
        contract = MockVRFCoordinatorV2[-1]
        requestId = transaction.events["RandomRequestSent"]["requestId"]
        tx = contract.fulfillRandomWords(
            requestId, lottery, {"from": account})
        tx.wait(1)
    else:
        delay = 180
        print(f"Waiting {delay} seconds")
        time.sleep(delay)

    if lottery.lottery_state() == 3:
        print("Lottery is finished")
        print(f"Winner is {lottery.recentWinner()}")
        print("Sending money to winner")

        if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
            transaction = lottery.transferFundsToWinner({"from": account})
        else:
            transaction = lottery.transferFundsToWinner(
                {"from": account, "priority_fee": PRIORITY_FEE})
        transaction.wait(1)

    else:
        print("Winner is not specified yet. Wait a bit")
        quit()


def setBeneficiaryViaGovernance(governanceToken, governance, lottery, beneficiary):
    # proposing
    DESCRIPTION = "Propose: Set new beneficiary " + str(chain.height)
    # encrypt function name and args to bytes array
    encryptedCalldata = lottery.setBeneficiary.encode_input(beneficiary,)
    # process via Governance
    governanceProcess(governanceToken, governance, lottery,
                      DESCRIPTION, encryptedCalldata)


def emrgStopLotteryViaGovernance(governanceToken, governance, lottery):
    # proposing
    DESCRIPTION = "Propose: Emergency stop lottery " + str(chain.height)
    # encrypt function name and args to bytes array
    encryptedCalldata = lottery.emrgStopLottery.encode_input()
    # process via Governance
    governanceProcess(governanceToken, governance, lottery,
                      DESCRIPTION, encryptedCalldata)


def transferFundsToAdminViaGovernance(governanceToken, governance, lottery):
    # proposing
    DESCRIPTION = "Propose: Transfer funds to admin " + str(chain.height)
    # encrypt function name and args to bytes array
    encryptedCalldata = lottery.transferFundsToAdmin.encode_input()
    # process via Governance
    governanceProcess(governanceToken, governance, lottery,
                      DESCRIPTION, encryptedCalldata)


def startLotteryViaGovernance(governanceToken, governance, lottery):
    # proposing
    DESCRIPTION = "Propose: Start lottery " + str(chain.height)
    # encrypt function name and args to bytes array
    encryptedCalldata = lottery.startLottery.encode_input()
    # process via Governance
    governanceProcess(governanceToken, governance, lottery,
                      DESCRIPTION, encryptedCalldata)


def endLotteryViaGovernance(governanceToken, governance, lottery):
    # proposing
    DESCRIPTION = "Propose: End lottery " + str(chain.height)
    # encrypt function name and args to bytes array
    encryptedCalldata = lottery.endLottery.encode_input()
    # process via Governance
    transaction = governanceProcess(governanceToken, governance, lottery,
                                    DESCRIPTION, encryptedCalldata)
    return transaction


def setEntranceFeeViaGovernance(governanceToken, governance, lottery, newFee):
    # proposing
    DESCRIPTION = "Propose: End lottery " + str(chain.height)
    # encrypt function name and args to bytes array
    encryptedCalldata = lottery.setEntranceFee.encode_input(newFee)
    # process via Governance
    governanceProcess(governanceToken, governance, lottery,
                      DESCRIPTION, encryptedCalldata)
