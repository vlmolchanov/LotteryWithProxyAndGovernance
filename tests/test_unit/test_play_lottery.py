from brownie import Contract, Lottery, exceptions, network, interface
from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy
from scripts.helpful_scripts import get_account, LOCKAL_BLOCKCHAIN_NETWORKS, MAINNET_FORKED_NETWORKS, PRIORITY_FEE
from scripts.play_lottery import addPlayersToLottery, playLottery, endLottery
import pytest
import time

# Basic lottery contracts are already checked, so proceed with new ones


def test_set_entrance_fee():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
    # Act
    newVal = 70
    proxyLottery.setEntranceFee(newVal, {"from": get_account()})
    # Arrange
    assert proxyLottery.entranceFeeUSD() == newVal


def test_start_lottery_by_owner():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    assert proxyLottery.lottery_state() == 1
    # Act
    proxyLottery.startLottery({"from": get_account(index=0)})

    # Assert
    assert proxyLottery.lottery_state() == 0

# Assert starting lottery by stranger is resticted


def test_start_lottery_by_stranger():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
    # Act

    # Assert
    assert proxyLottery.lottery_state() == 1

    if (
        network.show_active() == "development"
    ):
        with pytest.raises(exceptions.VirtualMachineError):
            proxyLottery.startLottery({"from": get_account(index=1)})


def test_add_players_to_lottery():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
    proxyLottery.startLottery({"from": get_account()})
    # Act

    # Assert
    assert proxyLottery.getPlayersNumber() == 0
    numberOfPlayers = 3
    addPlayersToLottery(proxyLottery, numberOfPlayers)
    assert proxyLottery.getPlayersNumber() == numberOfPlayers

# to troubleshoot some pi


# def test_transfer_funds_to_winner():

#     # Arrange
#     redeploy = True
#     lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
#     proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
#     playLottery(proxyLottery)
#     numberOfPlayers = 3
#     addPlayersToLottery(proxyLottery, numberOfPlayers)

#     # divide endLottery script in pieces
#     account = get_account()
#     lottery = proxyLottery
#     if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
#         transaction = lottery.endLottery({"from": account})
#     else:
#         transaction = lottery.endLottery(
#             {"from": account, "priority_fee": PRIORITY_FEE})
#     transaction.wait(1)

#     print(f"Number of participants is {lottery.getPlayersNumber()}")
#     print("Selecting winner ......")

#     if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS:
#         contract = MockVRFCoordinatorV2[-1]
#         requestId = transaction.events["RandomRequestSent"]["requestId"]
#         tx = contract.fulfillRandomWords(
#             requestId, lottery, {"from": account})
#         tx.wait(1)
#     else:
#         delay = 180
#         print(f"Waiting {delay} seconds")
#         time.sleep(delay)

#     if lottery.lottery_state() == 3:
#         print("Lottery is finished")
#         print(f"Winner is {lottery.recentWinner()}")
#         print("Sending money to winner")

#         amount = lottery.prizePool()
#         print(f"Prize pool equal {amount}")
#         # let's check what we have in Aave
#         pool = Contract.from_abi(
#             "Aave pool", lottery.aavePool(), MockAavePool.abi)
#         print(
#             f"In aave we have {pool.getUserAccountData(lottery)}")
#         # let's check balance of Aave in Weth contract
#         weth = Contract.from_abi(
#             "Weth token", lottery.wethContract(), MockWeth.abi)
#         print(f"Weth balance of aave is {weth.balanceOf(lottery.aavePool())}")

#         tx = lottery.withdrawAaveFunds(amount, {"from": account})

#         tx.wait(1)
#         print(f"Weth balance of lottery is {weth.balanceOf(lottery.address)}")

#         print(
#             f"Recent winner is {lottery.recentWinner()}. Prize pool is {lottery.prizePool()}")

#         # Act
#         balanceBeforeTransfer = weth.balanceOf(lottery.recentWinner())
#         prizePool = lottery.prizePool()
#         tx = lottery.transferWeth(
#             lottery.recentWinner(), lottery.prizePool(), {"from": account})
#         tx.wait(1)

#         # Assert
#         assert weth.balanceOf(lottery.recentWinner()
#                               ) == balanceBeforeTransfer + prizePool


def test_end_lottery_by_owner():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
    playLottery(proxyLottery)
    numberOfPlayers = 3
    addPlayersToLottery(proxyLottery, numberOfPlayers)
    # Act
    prizePool = proxyLottery.prizePool()
    weth = interface.IWeth(proxyLottery.wethContract())
    account = get_account()
    balanceBeforeTransfer = weth.balanceOf(account)

    assert proxyLottery.lottery_state() == 0

    endLottery(proxyLottery)

    # Assert
    assert proxyLottery.lottery_state() == 1

    # we have only one player so we know him
    assert proxyLottery.recentWinner() == account

    # we know winner, so we know whose balance should change
    assert weth.balanceOf(account) == balanceBeforeTransfer + prizePool


def test_emrg_stop_lottery():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
    playLottery(proxyLottery)
    numberOfPlayers = 3
    addPlayersToLottery(proxyLottery, numberOfPlayers)

    prizePool = proxyLottery.prizePool()
    weth = interface.IWeth(proxyLottery.wethContract())
    account = get_account()

    assert prizePool != 0
    total_collater, total_debt = proxyLottery.checkAaveBalance()
    assert total_collater != 0

    # Act
    tx = proxyLottery.emrgStopLottery({"from": account})
    tx.wait(1)

    # Asset
    total_collater, total_debt = proxyLottery.checkAaveBalance()
    weth = interface.IWeth(proxyLottery.wethContract())
    assert total_collater == 0
    assert weth.balanceOf(proxyLottery) == 0
    assert proxyLottery.balance() == 0


def test_set_beneficiary():
    if (
        network.show_active() == "development"
    ):
        # Arrange
        redeploy = True
        lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
            redeploy)
        proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)
        adminAccount = get_account()

        # Need to change beneficiary when lottery is closed
        newBeneficiary = get_account(index=2)
        tx = proxyLottery.setBeneficiary(
            newBeneficiary, {"from": adminAccount})

        playLottery(proxyLottery)
        numberOfPlayers = 3
        addPlayersToLottery(proxyLottery, numberOfPlayers)

        prizePool = proxyLottery.prizePool()
        weth = interface.IWeth(proxyLottery.wethContract())

        assert prizePool != 0
        total_collater, total_debt = proxyLottery.checkAaveBalance()
        assert total_collater != 0

        # Act

        initialBalance = weth.balanceOf(newBeneficiary)
        adminBalance = weth.balanceOf(adminAccount)
        tx = proxyLottery.emrgStopLottery({"from": adminAccount})
        tx.wait(1)

        # Asset
        total_collater, total_debt = proxyLottery.checkAaveBalance()
        assert weth.balanceOf(newBeneficiary) == initialBalance + prizePool
        assert weth.balanceOf(adminAccount) == adminBalance
        assert total_collater == 0
        assert weth.balanceOf(proxyLottery) == 0
        assert proxyLottery.balance() == 0

    else:
        pytest.skip("Just for development network")
