IBKR trader
=========================

<h3>To run the code do following (! make sure docker service is running on your machine):</h3>

```
git clone https://github.com/COXIT-CO/ibkr_trader.git
cd ibkr_trader
./run.sh
```

Wait for some time for containers to build, after what you can start making orders. To do so create file with following pattern:
```
stock-set:
- stocks:
    PSTG: 4
    TSLA: 6 
 conditions:
    drop-percent: 15
    up-percent: 2
- stocks:
    AAPL: 6
    MSFT: 2
 conditions:
    drop-percent: 10
    up-percent: 2
common-conditions:
  sell-percent: 20
```
Explanation:
- ```stock-set``` keyword needs to be present as it is. It stores the list of stock-subsets as shown above
- ```stocks``` keyword means that after it there will be pairs: ```stock symbol: quantity```
  - **note!** ```quantity``` can be integer corresponding real number of stocks or price taking form ```$X``` where X is actual floating point/integer price value
- right after stocks keyword stands **optional** ```conditions``` one that will hold conditions. Possible conditions are:
  - ```drop-percent``` corresponds to percent stock can drop. Can take integer/floating point value more than 0
  - ```up-percent``` corresponds to percent stock need to rise to after drop to buy it. Can take integer/floating point value more than 0.
  - ```sell-percent```. We have purchased stock and want to provide risk-avoidance, for this purpose such condition exists. It corresponds to percent losing which stock will be immediately sold. Can take integer/floating point value more than 0.
- you can also notice that **optional** ```common-conditions``` keyword is used. It applies conditions to all above stocks (e.g. I provided ```drop-percent``` and ```up-percent``` conditions individually for every stock-subset and carried ```sell-percent``` one to common conditions to apply it to all stocks)
- **Important**. As I said ```conditions``` and ```common-conditions``` keywords are optional, but at least one of them must be provided. The main rule you should keep in head that all 3 conditions listed above must be found for every stock-subset.
  - if you don't set ```common-conditions``` you must point all 3 conditions for every stock-subset in ```conditions```
  - if you don't provide ```conditions``` for one or many stock-subsets you must provide ```common-conditions``` with all 3 conditions
  - if you provide both ```conditions``` and ```common-conditions``` all 3 conditions must be found in ```conditions``` and ```common-conditions``` as if they were joined. 
  - **note!** if you provide one condition both in ```conditions``` and ```common-conditions``` that one in ```conditions``` will take precedence over common


<h3>More examples for better understanding:</h3>

-   Example 1 (all variants of stock quantity used):
    <pre>
    stock-set:
    - stocks:
        PSTG: <b>4    # integer as quantity used</b>
        TSLA: <b>$1234.56    # price in dollars</b>
      conditions:
        drop-percent: <b>$1234    # price in dollars as well</b>
        up-percent: 2
    - stocks:
        AAPL: 6
        MSFT: 2
      conditions:
        drop-percent: 10
        up-percent: 2
    common-conditions:
      sell-percent: 20
    </pre>
    
-   Example 2 (only ```common-conditions``` used):
    ```
    stock-set:
    - stocks:
        PSTG: 4
        TSLA: 6 
        AAPL: 6
        MSFT: 2
    common-conditions:
      drop-percent: 5
      up-percent: 10
      sell-percent: 20
    ```
    
-   Example 3 (only ```conditions``` used):
    ```
    stock-set:
    - stocks:
        PSTG: 4
        TSLA: 6 
     conditions:
        drop-percent: 15
        up-percent: 2
        sell-percent: 20
    - stocks:
        AAPL: 6
        MSFT: 2
     conditions:
        drop-percent: 10
        up-percent: 2
        sell-percent: 20
    ```
    
-   Example 4 (both ```conditions``` and ```common-conditions``` used).Here some conditions are overlaping:
    - ```drop-percent``` from first subset encounters in ```conditions``` and in ```common-conditions```. Variant from ```conditions``` takes precedence and value 15
    - the same situation with ```sell-percent``` from second subset. Variant in ```conditions``` takes precedence and value 20
    <pre>
    stock-set:
    - stocks:
        PSTG: 4
        TSLA: 6 
     conditions:<b>
        drop-percent: 15</b>
        up-percent: 3
    - stocks:
        AAPL: 6
        MSFT: 2
     conditions:<b>
        sell-percent: 20</b>
        up-percent: 4
    common-conditions:<b>
      drop-percent: 5
      sell-percent: 11</b>
    </pre>

<h3>How to pass file with order? Use suggested variant or use yours one</h3>

<pre>
curl -X POST --upload-file <b>your_file</b> http://<b>ip</b>:8000
</pre>

where:

  - **you_file** - file with order
  - **ip** - ip adress used to host the application
