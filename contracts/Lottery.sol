//SPDX-License-Identifier: MIT

pragma solidity ^0.8.7;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@proxy/contracts/access/OwnableUpgradeable.sol";
import "@proxy/contracts/proxy/utils/Initializable.sol";
import "./random/VRFConsumerBaseV2Upgradable.sol";
import "../interfaces/IPool.sol";
import "../interfaces/IWeth.sol";

contract Lottery is
    Initializable,
    VRFConsumerBaseV2Upgradable,
    OwnableUpgradeable
{
    uint256 public entranceFeeUSD;
    uint256 public prizePool;

    address beneficiary;

    address payable[] public players;
    address payable public recentWinner;

    mapping(address => uint256) public playerDeposit;

    enum LOTTERY_STATE {
        OPEN,
        CLOSE,
        CALCULATING_WINNER,
        WINNER_SELECTED
    }
    LOTTERY_STATE public lottery_state;

    //****Random number params
    //Our subscription ID.
    uint64 subscriptionId;
    bytes32 keyHash;
    uint32 callbackGasLimit;
    uint16 requestConfirmations;
    uint32 numWords;
    //*****

    uint256[] public randomWords;

    AggregatorV3Interface priceFeed;
    VRFCoordinatorV2Interface vrfCoordinator;
    IPool public aavePool;
    IWeth public wethContract;

    event NewPlayer(
        uint256 date,
        address player,
        uint256 amount,
        uint256 prizePool
    );
    event RandomRequestSent(uint256 date, uint256 requestId);
    event RandomNumberReceived(
        uint256 date,
        uint256 randomNumber,
        uint256 recentWinnerIndex,
        address recentWinner
    );
    event EthReceived(uint256 date, address player, uint256 amount);
    event MoneySentToWinner(uint256 date, address player, uint256 amount);

    receive() external payable {
        emit EthReceived(block.timestamp, msg.sender, msg.value);
    }

    fallback() external payable {}

    function initialize(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _aavePoolAddress,
        address _wethContractAddress,
        uint64 _subscriptionId,
        bytes32 _keyHash
    ) public virtual initializer {
        __Lottery_init(
            _priceFeedAddress,
            _vrfCoordinator,
            _aavePoolAddress,
            _wethContractAddress,
            _subscriptionId,
            _keyHash
        );
    }

    function __Lottery_init(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _aavePoolAddress,
        address _wethContractAddress,
        uint64 _subscriptionId,
        bytes32 _keyHash
    ) internal onlyInitializing {
        __Ownable_init();
        __VRFConsumerBaseV2_init_unchained(_vrfCoordinator);
        __Lottery_init_unchained(
            _priceFeedAddress,
            _vrfCoordinator,
            _aavePoolAddress,
            _wethContractAddress,
            _subscriptionId,
            _keyHash
        );
    }

    function __Lottery_init_unchained(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _aavePoolAddress,
        address _wethContractAddress,
        uint64 _subscriptionId,
        bytes32 _keyHash
    ) internal onlyInitializing {
        lottery_state = LOTTERY_STATE.CLOSE;
        beneficiary = msg.sender;
        priceFeed = AggregatorV3Interface(_priceFeedAddress);
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        aavePool = IPool(_aavePoolAddress);
        wethContract = IWeth(_wethContractAddress);
        subscriptionId = _subscriptionId;
        keyHash = _keyHash;
        entranceFeeUSD = 50;
        callbackGasLimit = 100000;
        requestConfirmations = 3;
        numWords = 1;
    }

    //Show actual entrance fee in wei
    function getEntranceFee() public view returns (uint256) {
        //50*10^(8+18)/3000*10^8 to have answer in wei
        (, int256 conversionRate, , , ) = priceFeed.latestRoundData();
        return (entranceFeeUSD * 10**26) / uint256(conversionRate);
    }

    //Show number of participants
    function getPlayersNumber() public view returns (uint256) {
        return players.length;
    }

    //Enter lottery
    function enter() public payable lotteryOpen {
        require(msg.value >= getEntranceFee(), "Not enough ETH to enter!");
        players.push(payable(msg.sender));
        playerDeposit[msg.sender] += msg.value;
        wethContract.deposit{value: msg.value}();
        supplyFundsAave(msg.value);
        prizePool += msg.value;
        emit NewPlayer(block.timestamp, msg.sender, msg.value, prizePool);
    }

    //Transfer funds to selected winner
    function transferFundsToWinner() public lotteryWinnerSelected {
        withdrawAaveFunds(prizePool);
        transferWeth(recentWinner, prizePool);
        lottery_state = LOTTERY_STATE.CLOSE;
        emit MoneySentToWinner(block.timestamp, recentWinner, prizePool);
    }

    //*****Admin functions *********************************
    function startLottery() public lotteryClose onlyOwner {
        for (uint256 i = 1; i < players.length; i++) {
            address player = players[i];
            playerDeposit[player] = 0;
        }
        players = new address payable[](0);
        recentWinner = payable(address(0));
        prizePool = 0;
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public lotteryOpen onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        requestRandomWords();
    }

    function setEntranceFee(uint256 _entranceFeeUSD)
        public
        lotteryClose
        onlyOwner
    {
        require(_entranceFeeUSD >= 10, "Not enough USD value!");
        entranceFeeUSD = _entranceFeeUSD;
    }

    function setBeneficiary(address _beneficiary)
        public
        lotteryClose
        onlyOwner
    {
        require(
            _beneficiary != address(0),
            "Beneficiary address shouldn't be ZERO"
        );
        beneficiary = _beneficiary;
    }

    function emrgStopLottery() public onlyOwner {
        uint256 bigValue = 100 * 10**18;
        withdrawAaveFunds(bigValue);
        //Send all WETH to beneficiary
        uint256 value = wethContract.balanceOf(address(this));
        transferWeth(beneficiary, value);
        //Send all Eth to beneficiary
        payable(beneficiary).transfer(address(this).balance);
        lottery_state = LOTTERY_STATE.CLOSE;
    }

    function checkAaveBalance()
        public
        view
        onlyOwner
        returns (uint256, uint256)
    {
        (
            uint256 total_collateral_base,
            uint256 total_debt_base,
            ,
            ,
            ,

        ) = aavePool.getUserAccountData(address(this));
        return (total_collateral_base, total_debt_base);
    }

    function transferFundsToAdmin() public lotteryClose onlyOwner {
        //Try big value
        uint256 bigNumber = 10**18;
        withdrawAaveFunds(bigNumber);
        //Send all WETH to beneficiary
        uint256 value = wethContract.balanceOf(address(this));
        transferWeth(beneficiary, value);
        //Send all Eth to beneficiary
        payable(beneficiary).transfer(address(this).balance);
    }

    //***********Internal functions ********************
    // Assumes the subscription is funded sufficiently.
    function requestRandomWords() internal onlyOwner {
        // Will revert if subscription is not set and funded.

        uint256 requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        emit RandomRequestSent(block.timestamp, requestId);
    }

    function fulfillRandomWords(
        uint256, /* requestId */
        uint256[] memory _randomWords
    ) internal override {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Lottery is not in correct state"
        );
        randomWords = _randomWords;
        require(randomWords[0] > 0, "Random number should be > 0");
        uint256 recentWinnerIndex = randomWords[0] % players.length;
        recentWinner = players[recentWinnerIndex];
        lottery_state = LOTTERY_STATE.WINNER_SELECTED;
        emit RandomNumberReceived(
            block.timestamp,
            randomWords[0],
            recentWinnerIndex,
            recentWinner
        );
    }

    function supplyFundsAave(uint256 amount) internal {
        wethContract.approve(address(aavePool), amount);
        aavePool.supply(address(wethContract), amount, address(this), 0);
    }

    function withdrawAaveFunds(uint256 amount) internal {
        wethContract.approve(address(aavePool), amount);
        aavePool.withdraw(address(wethContract), amount, address(this));
    }

    function transferWeth(address _to, uint256 _value) internal {
        wethContract.approve(address(this), _value);
        wethContract.transfer(_to, _value);
    }

    //********************Modifiers****************

    modifier lotteryOpen() {
        require(
            lottery_state == LOTTERY_STATE.OPEN,
            "Lottery should be started"
        );
        _;
    }

    modifier lotteryClose() {
        require(
            lottery_state == LOTTERY_STATE.CLOSE,
            "Lottery should be finished"
        );
        _;
    }

    modifier lotteryCalculatingWinner() {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Lottery should selecting winner"
        );
        _;
    }

    modifier lotteryWinnerSelected() {
        require(
            lottery_state == LOTTERY_STATE.WINNER_SELECTED,
            "Lottery should select winner"
        );
        _;
    }
}
