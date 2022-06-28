from brownie import network, Contract, Lottery
from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy
from scripts.deploy_governance import deployGovernanceToken, deployGovernance, transferOwnership
from scripts.governance_control import delegateVotes, createProposal, vote
from scripts.helpful_scripts import get_account, wait, LOCKAL_BLOCKCHAIN_NETWORKS, MAINNET_FORKED_NETWORKS, VOTING_DELAY, VOTING_PERIOD, TIMELOCK_DELAY, PRIORITY_FEE, proposeState
from web3 import Web3
import time


def test_delegate_votes():
    # Arrange
    governanceToken = deployGovernanceToken()
    account = get_account()
    # Act
    delegateVotes(governanceToken)
    # Assert
    print(f"Account {account} has {governanceToken.getVotes(account)} votes")
    assert governanceToken.getVotes(account) != 0


def test_create_proposal():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    governanceToken, timeLock, governance = deployGovernance(redeploy)

    DESCRIPTION = "Propose: Start lottery"
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyLottery.startLottery.encode_input()

    # Act
    proposalId, transaction = createProposal(
        governance, DESCRIPTION, proxyLottery, encryptedCalldata)

    # Assert
    assert proposalId != 0
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")
    assert governance.state(proposalId) == 0

    delay = VOTING_DELAY + 2
    wait(delay, transaction)
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")
    assert governance.state(proposalId) == 1


def test_voting_process_succeeded():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    governanceToken, timeLock, governance = deployGovernance(redeploy)
    delegateVotes(governanceToken)
    DESCRIPTION = "Propose: Start lottery"
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyLottery.startLottery.encode_input()

    proposalId, transaction = createProposal(
        governance, DESCRIPTION, proxyLottery, encryptedCalldata)
    delay = VOTING_DELAY + 2
    wait(delay, transaction)
    # Act
    # voting
    _vote = 1  # 1 = For
    transaction = vote(governance, proposalId, _vote)
    # wait voting to finish
    delay = VOTING_PERIOD + 2
    wait(delay, transaction)

    # Assert
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")
    assert governance.state(proposalId) == 4


def test_voting_process_defeated():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    governanceToken, timeLock, governance = deployGovernance(redeploy)
    delegateVotes(governanceToken)
    DESCRIPTION = "Propose: Start lottery"
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyLottery.startLottery.encode_input()

    proposalId, transaction = createProposal(
        governance, DESCRIPTION, proxyLottery, encryptedCalldata)
    delay = VOTING_DELAY + 2
    wait(delay, transaction)
    # Act
    # voting
    _vote = 0  # 0 = Against
    transaction = vote(governance, proposalId, _vote)
    # wait voting to finish
    delay = VOTING_PERIOD + 2
    wait(delay, transaction)

    # Assert
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")
    assert governance.state(proposalId) == 3


def test_queue_and_execute_proposal():
    # Arrange
    redeploy = True
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(redeploy)
    proxyLottery = Contract.from_abi("Lottery", proxy.address, Lottery.abi)

    governanceToken, timeLock, governance = deployGovernance(redeploy)
    delegateVotes(governanceToken)
    DESCRIPTION = "Propose: Start lottery"
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyLottery.startLottery.encode_input()

    proposalId, transaction = createProposal(
        governance, DESCRIPTION, proxyLottery, encryptedCalldata)
    delay = VOTING_DELAY + 2
    wait(delay, transaction)

    # voting
    _vote = 1  # 1 = For
    transaction = vote(governance, proposalId, _vote)
    # wait voting to finish
    delay = VOTING_PERIOD + 2
    wait(delay, transaction)

    # Act
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

    if governance.state(proposalId) == 4:
        descriptionHash = Web3.keccak(text=DESCRIPTION).hex()
        if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
            tx = governance.queue([proxyLottery.address], [0], [
                encryptedCalldata], descriptionHash, {"from": get_account()})
        else:
            tx = governance.queue([proxyLottery.address], [0], [
                encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
        tx.wait(1)

        delay = TIMELOCK_DELAY + 3
        print(f"Sleeping for {delay} seconds")
        time.sleep(delay)

        assert governance.state(proposalId) == 5

        wait(TIMELOCK_DELAY + 1, tx)

        print(
            f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")

        if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
            transaction = governance.execute([proxyLottery.address], [0], [
                encryptedCalldata], descriptionHash, {"from": get_account()})
        else:
            transaction = governance.execute([proxyLottery.address], [0], [
                encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
        transaction.wait(1)
        # to pass transaction and have ability took info from events
        return transaction
    else:
        print("Proposal is not in Succeeded state")
        print(
            f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")

    # Assert
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")
    assert governance.state(proposalId) == 7
