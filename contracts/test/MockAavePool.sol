//SPDX-License-Identifier: MIT

pragma solidity ^0.8.8;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockAavePool {
    mapping(address => uint256) public balanceOf;

    //getUserAccountData
    function getUserAccountData(address user)
        external
        view
        returns (
            uint256 totalCollateralBase,
            uint256 totalDebtBase,
            uint256 availableBorrowsBase,
            uint256 currentLiquidationThreshold,
            uint256 ltv,
            uint256 healthFactor
        )
    {
        return (balanceOf[user], 0, 0, 0, 0, 0);
    }

    //supply
    function supply(
        address asset,
        uint256 amount,
        address onBehalfOf,
        uint16 referralCode
    ) external {
        ERC20 token = ERC20(asset);
        //transferFrom(sender, recipient, amount)
        token.transferFrom(msg.sender, address(this), amount);
        balanceOf[onBehalfOf] += amount;
    }

    //withdraw (can be big value)
    function withdraw(
        address asset,
        uint256 amount,
        address to
    ) external returns (uint256) {
        ERC20 token = ERC20(asset);

        if (amount > balanceOf[msg.sender]) {
            amount = balanceOf[msg.sender];
        }
        balanceOf[to] -= amount;
        token.approve(address(this), amount);
        token.transfer(to, amount);
        return 0;
    }
}
