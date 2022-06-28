
from scripts.deploy_governance import deployGovernance, transferOwnership
from scripts.deploy_lottery import deploy_initial_Lottery_with_proxy
from scripts.helpful_scripts import get_account, VOTING_DELAY, VOTING_PERIOD, TIMELOCK_DELAY


def test_deploy_governance_func():
    # Arrange
    redeploy = True
    # Act
    governanceToken, timeLock, governance = deployGovernance(redeploy)
    # Assert
    assert governanceToken.totalSupply() == 1000000000000000000000000  # 1 mln of Tokens
    assert timeLock.getMinDelay() == TIMELOCK_DELAY
    assert governance.votingDelay() == VOTING_DELAY
    assert governance.votingPeriod() == VOTING_PERIOD


def test_transfer_ownership():
    # Arrange
    redeploy = True
    governanceToken, timeLock, governance = deployGovernance(redeploy)
    lottery, proxyAdmin, proxy = deploy_initial_Lottery_with_proxy(
        redeploy)

    # Act
    # Transfer ownership of ProxyAdmin contract to Time Lock contract if needed
    if proxyAdmin.owner() != timeLock.address:
        if proxyAdmin.owner() == get_account():
            transferOwnership(proxyAdmin, timeLock)
        else:
            print(
                f"ProxyAdmin is controlled by {proxyAdmin.owner}. Not able to transfer ownership")
            quit()
    else:
        print(f"Proxy Admin is controlled by Governance Time Lock already")
    # Assert
    assert proxyAdmin.owner() == timeLock.address
