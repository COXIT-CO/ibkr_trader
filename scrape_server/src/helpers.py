import yaml
from tokenize import single_quoted
from . import exceptions


def is_quantity_valid(price_string):
    return isinstance(price_string, int) or price_string.startswith("$") and \
        (price_string.isnumeric() or
            all([letter in "0123456789." for letter in price_string])
        )


def are_conditions_good(conditions: dict):
    """
    check if stock condition values good
    """
    avaliable_conditions = ('drop-percent', 'up-percent', 'sell-percent')
    for name, value in conditions.items():
        if name not in avaliable_conditions:
            raise exceptions.CustomYamlException(
                """Error while scraping config file.
Allowed conditions 'drop-percent'/'up-percent'/'sell-percent'
Take a look at pattern"""
            )
        if not (0 <= value <= 100):
            raise exceptions.CustomYamlException(
                """Error while scraping config file.
Condition value must be in range 0-100.
Take a look at pattern"""
            )


def create_config_file(stock_data):
    """
    created config file with stocks and their conditions 
    in convenient way to work with them in taras_trader
    """
    transformed_data = []
    for stock_data in stock_data['order']['stock-set']:
        for stock, quantity in stock_data['stocks']:
            pass
        pass



def beautify_stock_data(row_data):
    """"
    given row stock data provided by user make it easy to use 
    by taras_trader by transforming in appropriate form
    """
    pretty_data = []
    for stock_data in row_data['stock-set']:
        for stock, quant in stock_data['stocks'].items():
            single_stock = {
                "stock": stock, 
                "quantity": quant,
            }
            for cond, value in row_data['common-conditions'].items():
                single_stock[cond] = value
            # overriding common conditions as stock ones have more precedence
            # or filling left ones not provided in common
            for cond, value in stock_data['conditions'].items():
                single_stock[cond] = value
            pretty_data.append(single_stock)
    
    return pretty_data


def generate_yaml_file(data_to_dump, file_path):
    """
    given stock data dump it into file by provided file path
    """
    yaml_data = yaml.dump(data_to_dump)
    with open(file_path, "w") as f:
        f.write(yaml_data)