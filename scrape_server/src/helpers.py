from . import exceptions

def is_string_price_valid(price_string: str):
    return price_string.startswith("$") and \
        (price_string.isnumeric() or
            all([letter in "0123456789." for letter in price_string])
        )


def are_conditions_good(conditions: dict):
    avaliable_conditions = ('drop-percent', 'up-percent', 'sell-percent')
    for name, value in conditions.items():
        if name not in avaliable_conditions:
            raise exceptions.CustomYamlException(
                "Error while scraping config file. \
                allowed conditions 'drop-percent'/'up-percent'/'sell-percent' \
                See pattern in samples folder in project root"
            )
        if not (isinstance(value, int) or is_string_price_valid(value)):
            raise exceptions.CustomYamlException(
                "Error while scraping config file. \n\
Stock quantity must be integer (numeric quantity) or \n\
string starting with '$' sign preceding actual floating point or integer price value. \n\
See pattern in samples folder in project root"
            )
        if not (0 <= value <= 100):
            raise exceptions.CustomYamlException(
                "Error while scraping config file. \
                condition value must be in range 0-100 \
                See pattern in samples folder in project root"
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
