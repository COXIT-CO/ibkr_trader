import sys
import collections
import oyaml as yaml
from ib_insync import Stock


def contractForName(sym, exchange="SMART", currency="USD"):
    """Convert a single text symbol into an ib_insync contract."""
    
    return Stock(sym, exchange, currency)



def tickFieldsForContract(contract) -> str:
    extraFields = []
    if isinstance(contract, Stock):
        # 104:
        # "The 30-day historical volatility (currently for stocks)."
        # 106:
        # "The IB 30-day volatility is the at-market volatility estimated
        #  for a maturity thirty calendar days forward of the current trading
        #  day, and is based on option prices from two consecutive expiration
        #  months."
        # 236:
        # "Number of shares available to short"
        # "Shortable: < 1.5, not availabe
        #             > 1.5, if shares can be located
        #             > 2.5, enough shares are available (>= 1k)"
        extraFields += [104, 106, 236]

    # yeah, the API wants a CSV for the tick list. sigh.
    tickFields = ",".join([str(x) for x in extraFields])

    # logger.info("[{}] Sending fields: {}", contract, tickFields)
    return tickFields



def extract_data_from_yaml_file(path_to_file):
    with open(path_to_file, "r") as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            logger.info(exc)
            sys.exit()



def extract_data_from_yaml_file(path: str) -> dict:
    """function to extact content to dictionary 
    from yaml file residing on privided path
        Parameters:
            path (str): path to the file to extact data from"""
    stream = open(path, 'r')
    try:
        scraped_data = yaml.safe_load(stream)

        if "fill" not in scraped_data or scraped_data["fill"] != "on":
            return None
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

    return scraped_data



def replace_stocks_being_processed(
    stocks_data, 
    file_path, 
    stocks_cost=0, 
    balance_cash=0, 
    are_stocks_accepted: bool = False
):
    patterns_dump_to_file = [collections.OrderedDict([
        ('fill', 'off'), 
        ('warning', 
    "previous stocks are being processed, please, don't put other ones until this title dissapears"),
        ('order', {
            'buy': [
                {"stocks": ""}, 
                {"conditions": ""}
            ], 
            'sell': [
                {"stocks": ""}, 
                {"conditions": ""}
            ]
            }
        )
    ]), collections.OrderedDict([
        ('fill', 'off'), 
        ('order', {
            'buy': [
                {"stocks": ""}, 
                {"conditions": ""}
            ], 
            'sell': [
                {"stocks": ""}, 
                {"conditions": ""}
            ]
            }
        )
    ]), collections.OrderedDict([
        ('fill', 'off'), 
        ('warning', 
    f"stocks haven't been processes cause their price exceeds balance cash, \nstocks averall price - {stocks_cost}, balance cash -{balance_cash}, \nif you still want to proceed these stocks, please, consider their quantity"),
    ])]

    if are_stocks_accepted:
        data_to_dump = patterns_dump_to_file[1]
    elif stocks_cost and balance_cash:
        stocks_data_copy = stocks_data.copy()
        del stocks_data_copy['fill']
        patterns_dump_to_file[2].update(OrderedDict(stocks_data_copy))
        data_to_dump = patterns_dump_to_file[2]
    else:
        data_to_dump = patterns_dump_to_file[0]

    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if line.startswith("\n") or line.strip("\n").startswith("#"):
                file.write(line)
        
        file.write(yaml.dump(data_to_dump))



def delete_processed_stocks_from_file(data_to_replace: dict, file_path: str) -> dict:
    if data_to_replace is None or "fill" not in data_to_replace or data_to_replace["fill"] != "on":
        return None
    data_to_replace = collections.OrderedDict([
        ('fill', 'off'), 
        ('warning', 
    "previous stocks are being processed, please, don't put other ones untill this title dissapears"),
        ('order', {
            'buy': [
                {"stocks": ""}, 
                {"conditions": ""}
            ], 
            'sell': [
                {"stocks": ""}, 
                {"conditions": ""}
            ]
            }
        )
    ])

    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if line.startswith("\n") or line.strip("\n").startswith("#"):
                file.write(line)
        
        file.write(yaml.dump(data_to_replace))



def write_orders_to_file(stocks_data: dict, file_path: str) -> None:
    yaml_representation = yaml.dump(stocks_data)
    with open(file_path, "w") as file:
        file.write(yaml_representation)



def process_scraped_stock_data(data_to_process):
    processed_data = []

    for item in data_to_process['order']['buy']:
        # print(item['stocks'])
        for stock in item['stocks']:
            stock_symbol = list(stock.keys())[0]
            stock_info = {stock_symbol: {}}
            try:
                stock_info[stock_symbol]["quantity"] = int(list(stock.values())[0])
            except:
                stock_info[stock_symbol]["quantity"] = str(list(stock.values())[0])
            stock_info[stock_symbol]["drop_percent"] = float(item['conditions'][1]['trailing-drop-percent'])
            stock_info[stock_symbol]["rise_percent"] = float(item['conditions'][2]['trailing-up-percent'])
            stock_info[stock_symbol]["risk_avoidance_percent"] = float(data_to_process['order']['sell'][1]['trailing-drop-percent'])
            processed_data.append(stock_info)

    return processed_data



def process_suspended_stocks(data):
    processed_data = []

    for item in data:
        symbol = list(item.keys())[0]
        conditions = list(item.values())[0][0]
        processed_data.append(
            {symbol: conditions},
        )

    return processed_data
