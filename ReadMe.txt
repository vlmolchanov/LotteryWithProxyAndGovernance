1. We have a usual Lottery at the begining
    - we are able to start/end/play and all other functions
2. Then we create proxy and make it upgradeable
    - for this we change prizes in Eth to WETH to handle Istanbul update ("transfer" doesnt' work from WETH withdraw)
3. After we are testing Lottery functionality via proxy address
4. Next step is to create governance. And delegate proxyAdmin ownership to it (Only governance is able to change Proxy)
    -Other functions are done by admin, can be delegated to TimeLock too if needed
5. After we delegate admin functions to governance and test lottery functions


Key Features:
1. Aggregator V3 Interface - to receive actual ETH price
2. VRF Coordinator V2 - to receive random number
3. Aave Pool interface - to deposit funds and earn money for beneficiar
4. Transparent Uprgradeable proxy, ProxyAdmin, Initializable and other upgradeable contracts - to use proxy
5. Governance, Governance Token, TimeLock - to use governance




