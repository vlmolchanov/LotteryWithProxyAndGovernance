from brownie import network
from scripts.helpful_scripts import (
    get_account,
    wait,
    LOCKAL_BLOCKCHAIN_NETWORKS,
    MAINNET_FORKED_NETWORKS,
    PRIORITY_FEE,
    VOTING_DELAY,
    VOTING_PERIOD,
    TIMELOCK_DELAY,
    proposeState,
)
from web3 import Web3
import time


def main():
    pass


def governanceProcess(governanceToken, governance, contract, description, encryptedCalldata):
    # before proposal we want to delegate all votes to account
    delegateVotes(governanceToken)

    proposalId, transaction = createProposal(
        governance, description, contract, encryptedCalldata)
    # **********************************

    votingProcess(governance, proposalId, transaction)

    # check state of proposal
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")

    # queue and execute proposal
    transaction = queueAndExecuteProposal(governance, contract,
                                          description, encryptedCalldata, proposalId)
    return transaction


def queueAndExecuteProposal(governance, contract, description, encryptedCalldata, proposalId):

    descriptionHash = Web3.keccak(text=description).hex()
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governance.queue([contract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account()})
    else:
        tx = governance.queue([contract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)

    delay = TIMELOCK_DELAY + 3
    print(f"Sleeping for {delay} seconds")
    time.sleep(delay)

    wait(TIMELOCK_DELAY + 1, tx)

    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")

    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        transaction = governance.execute([contract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account()})
    else:
        transaction = governance.execute([contract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    transaction.wait(1)
    # to pass transaction and have ability took info from events
    return transaction


def createProposal(governance, description, contract, encryptedCalldata):
    print(description)
    # function propose(address[] memory targets,uint256[] memory values,bytes[] memory calldatas,string memory description)
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governance.propose([contract.address], [
            0], [encryptedCalldata], description, {"from": get_account()})
    else:
        tx = governance.propose([contract.address], [
            0], [encryptedCalldata], description, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    # Read proposal ID from emited event
    proposalId = tx.events["ProposalCreated"]["proposalId"]
    print(f"Proposal {proposalId} is created")
    print(description)
    return proposalId, tx


def votingProcess(governance, proposalId, transaction):
    # wait before voting
    delay = VOTING_DELAY + 2
    wait(delay, transaction)

    # voting
    _vote = 1  # For
    transaction = vote(governance, proposalId, _vote)

    # wait voting to finish
    delay = VOTING_PERIOD + 2
    wait(delay, transaction)


def delegateVotes(governanceToken):
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        governanceToken.delegate(
            get_account(), {"from": get_account()})
    else:
        governanceToken.delegate(
            get_account(), {"from": get_account(), "priority_fee": PRIORITY_FEE})
    # delegating if moving some voting power - creates checkPoint
    print(f"Checkpoints: {governanceToken.numCheckpoints(get_account())}")

# 0 = Against
# 1 = For
# 2 = Abstain


def vote(governanceContract, proposalId, _vote):
    vote = int(_vote)
    reason = "I want so"
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.castVoteWithReason(
            proposalId, vote, reason, {"from": get_account()})
    else:
        tx = governanceContract.castVoteWithReason(
            proposalId, vote, reason, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    voteReason = tx.events["VoteCast"]["reason"]
    voteSupport = tx.events["VoteCast"]["support"]
    voteWeight = tx.events["VoteCast"]["weight"]
    # 0 = Against, 1 = For, 2 = Abstain
    voteDesc = {
        '0': "Against",
        '1': "For",
        '2': "Abstain"
    }
    print(
        f"You voted {voteDesc.get(str(voteSupport), -1)}, having weight = {voteWeight}, reason = {voteReason}")
    # return transaction receipt to use wait on it (istead of time)
    return tx
