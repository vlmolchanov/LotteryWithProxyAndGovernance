from brownie import GovernanceToken, TimeLock, Governance, network, config
from scripts.helpful_scripts import get_account, LOCKAL_BLOCKCHAIN_NETWORKS, MAINNET_FORKED_NETWORKS, PRIORITY_FEE, VOTING_DELAY, VOTING_PERIOD, QUORUM_PERCENTAGE, TIMELOCK_DELAY
from web3 import constants


def main():
    redeploy = False
    # create Governance and delegate all control functionality to TimeLock
    governanceToken, timeLock, governance = deployGovernance(redeploy)


def deployGovernance(redeploy):

    # deploy Governance Token
    if len(GovernanceToken) <= 0 or redeploy:
        governanceToken = deployGovernanceToken()
    else:
        governanceToken = GovernanceToken[-1]
    print(f"Governance token contract deployed at {governanceToken.address}")

    # deploy Time Lock contract
    if len(TimeLock) <= 0 or redeploy:
        timeLock = deployTimeLock()
    else:
        timeLock = TimeLock[-1]
    print(f"TimeLock contract deployed at {timeLock.address}")

    # deploy Governance Token
    if len(Governance) <= 0 or redeploy:
        governance = deployGovernanceContract(
            governanceToken, timeLock, VOTING_DELAY, VOTING_PERIOD, QUORUM_PERCENTAGE)
        # Set up Time Lock roles
        setUpTimeLockContract(timeLock, governance)
    else:
        governance = Governance[-1]
    print(f"Governance contract deployed at {governance.address}")

    return governanceToken, timeLock, governance


def transferOwnership(contract, newAdmin):
    print("Transfering Contract ownership to TimeLock")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        transaction = contract.transferOwnership(
            newAdmin, {"from": get_account()})
    else:
        transaction = contract.transferOwnership(
            newAdmin, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    transaction.wait(1)


def deployGovernanceToken():
    print("Deploying Governance Token contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        governanceToken = GovernanceToken.deploy(
            {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        governanceToken = GovernanceToken.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return governanceToken


def deployTimeLock():
    print("Deploying TimeLock contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        timeLock = TimeLock.deploy(TIMELOCK_DELAY, [], [], {"from": get_account(
        )}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        timeLock = TimeLock.deploy(TIMELOCK_DELAY, [], [], {"from": get_account(
        ), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return timeLock


def deployGovernanceContract(token, timeLock, votingDelay, votingPeriod, quorumPercentage):
    print("Deploying Governance contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        governance = Governance.deploy(token, timeLock, votingDelay, votingPeriod, quorumPercentage,  {
            "from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        governance = Governance.deploy(token, timeLock, votingDelay, votingPeriod, quorumPercentage,  {
            "from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return governance


def setUpTimeLockContract(timeLockContract, governanceContract):
    # SetUp roles for proposer, executor, timelock_admin
    print(
        f"Setting proposer to Governance contract({governanceContract.address})")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = timeLockContract.grantRole(
            timeLockContract.PROPOSER_ROLE(), governanceContract.address, {"from": get_account()})
    else:
        tx = timeLockContract.grantRole(
            timeLockContract.PROPOSER_ROLE(), governanceContract.address, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    print(f"Setting executor to anyone")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = timeLockContract.grantRole(timeLockContract.EXECUTOR_ROLE(),
                                        constants.ADDRESS_ZERO, {"from": get_account()})
    else:
        tx = timeLockContract.grantRole(timeLockContract.EXECUTOR_ROLE(),
                                        constants.ADDRESS_ZERO, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    print(f"Deleting our account from Time Lock admins. No we can do nothing")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = timeLockContract.revokeRole(
            timeLockContract.TIMELOCK_ADMIN_ROLE(), get_account(), {
                "from": get_account()}
        )
    else:
        tx = timeLockContract.revokeRole(
            timeLockContract.TIMELOCK_ADMIN_ROLE(), get_account(), {
                "from": get_account(), "priority_fee": PRIORITY_FEE}
        )
    tx.wait(1)
