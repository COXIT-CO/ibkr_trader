from . import exceptions
from . import helpers


def validate_yaml_data(raw_data: dict):
    try:
        are_values_provided(raw_data)
        is_stock_set_present(raw_data)
        are_stocks_provided(raw_data)
        are_conditions_valid(raw_data)
        is_quantity_valid(raw_data)
    except exceptions.CustomYamlException as exc:
        return str(exc)


def are_values_provided(raw_data: dict):
    """
    check if all keys in yaml file have values provided
    """
    if isinstance(raw_data, dict):
        for key, value in raw_data.items():
            if key is None:
                raise exceptions.CustomYamlException(
                    f"""Rejected
Empty keys are forbidden
Take a look at pattern"""
                )
            if value is None:
                raise exceptions.CustomYamlException(
                    f"""Rejected
No value provided for '{key}' key
Take a look at pattern"""
                )
            are_values_provided(value)
    elif isinstance(raw_data, list):
        if not len(raw_data):
            raise exceptions.CustomYamlException(
                    """Rejected
Value for 'stock-set' key is empty
Take a look at pattern"""
                )
        for elem in raw_data:
            if elem is None:
                raise exceptions.CustomYamlException(
                    """Rejected
No data provided for 'stock-set'
Take a look at pattern"""
                )
            if not isinstance(elem, dict):
                raise exceptions.CustomYamlException(
                    """Rejected
'stock-key' value is invalid
Take a look at pattern"""
                )
            are_values_provided(elem)
    else:
        if raw_data is None:
            raise exceptions.CustomYamlException(
                    """Error while scraping config file.
File can't be empty
Take a look at pattern"""
            )


def is_stock_set_present(raw_data: dict):
    """
    check if 'stock-set' keyword is present in yaml file and it's value is list
    """
    if not ('stock-set' in raw_data and type(raw_data['stock-set']) == list):
        raise exceptions.CustomYamlException(
            "Error while scraping config file. \n\
'stock-set' key must be one level below 'order' one or the value assigned to it is invalid. \n\
Take a look at pattern"
        )


def are_stocks_provided(raw_data: dict):
    """
    check if 'stocks' keywords is present
    """
    for stock_data in raw_data['stock-set']:
        if 'stocks' not in stock_data:
            raise exceptions.CustomYamlException(
                """Error while scraping config file.
No stocks are provided.
Take a look at pattern"""
            )


def are_conditions_valid(raw_data: dict):
    """
    check if 'common-conditions' keyword is present in yaml file, it's value is dictionary, conditions are valid and 
    remaining conditions are provided for each stock separately or if it's not present check if all 3 conditions are 
    provided for each stock separately
    """
    common_conditions = ()
    if 'common-conditions' in raw_data:
        helpers.are_conditions_good(raw_data['common-conditions'])

        for condition in raw_data['common-conditions']:
            common_conditions += (condition,)
        if len(common_conditions) == 3:
            # all conditions are provided in common ones, so we don't need to worry
            # if user has provided remaining ones for each stock individually
            return

        separate_conditions = []
        # determine separate conditions need to be provided
        for cond in ('drop-percent', 'up-percent', 'sell-percent'):
            if cond not in common_conditions:
                separate_conditions.append(cond)
        for stock_data in raw_data['stock-set']:
            if 'conditions' not in stock_data:
                raise exceptions.CustomYamlException(
                    """Error while scraping config file.
You have provided common conditions, but not all 3 of them,
so it's required to provide each of remaining for every stock separately
Take a look at pattern"""
                )
            helpers.are_conditions_good(stock_data['conditions'])
            # check if missing conditions provided for separate stock
            for cond in separate_conditions:
                if cond not in stock_data['conditions']:
                    raise exceptions.CustomYamlException(
                        f"""Error while scraping config file.
You didn't provided '{cond}' condition neither in common conditions nor in separate one for some stock
Take a look at pattern"""
                    )
    elif 'common-conditions' not in raw_data:
        for stock_data in raw_data['stock-set']:
            if 'conditions' not in stock_data:
                raise exceptions.CustomYamlException(
                    """Error while scraping config file.
You didn't provided common conditions, so have to provide them for each stock separately
Take a look at pattern"""
                )
            helpers.are_conditions_good(stock_data['conditions'])
            for cond in ('drop-percent', 'up-percent', 'sell-percent'):
                if cond not in stock_data['conditions']:
                    raise exceptions.CustomYamlException(
                        f"""Error while scraping config file.
You didn't provided {cond} condition neither in separate stock conditions nor in common ones
Take a look at pattern"""
                    )


def is_quantity_valid(raw_data: dict):
    for stock_data in raw_data['stock-set']:
        for _, quant in stock_data['stocks'].items():
            if not helpers.is_quantity_valid(quant):
                raise exceptions.CustomYamlException(
                    """Error while scraping config file.
Stock quantity must be integer (numeric quantity) or
string starting with '$' sign preceding actual floating point or integer price value.
Take a look at pattern"""
                )
