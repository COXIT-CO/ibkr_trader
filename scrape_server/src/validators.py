from . import exceptions
from . import helpers


def validate_yaml_data(data_to_validate: dict):
    try:
        are_values_provided(data_to_validate)
        is_fill_flag_valid(data_to_validate)
        is_order_present(data_to_validate)
        is_stock_set_present(data_to_validate)
        are_conditions_valid(data_to_validate)
    except exceptions.CustomYamlException as exc:
        return str(exc)


def are_values_provided(data_to_validate: dict):
    """
    check if all keys in yaml file have values provided
    """
    if isinstance(data_to_validate, dict):
        for _, value in data_to_validate.items():
            if value is None:
                raise exceptions.CustomYamlException(
                    "Error while scraping config file. \n\
You didn't provide value for some key \n\
See pattern in samples folder in project root"
                )
            are_values_provided(value)
    elif isinstance(data_to_validate, list):
        for elem in data_to_validate:
            if elem is None:
                raise exceptions.CustomYamlException(
                    "Error while scraping config file. \n\
Key values can't be empty \n\
See pattern in samples folder in project root"
                )
            if not isinstance(elem, dict):
                raise exceptions.CustomYamlException(
                    "Invalid format of config file detected \n\
You didn't provide value for some key \n\
See pattern in samples folder in project root"
                )
            are_values_provided(elem)
    else:
        if data_to_validate is None:
            raise exceptions.CustomYamlException(
                    "Error while scraping config file. \n\
File can't be empty \n\
See pattern in samples folder in project root"
            )


def is_fill_flag_valid(data_to_validate: dict):
    """
    check if 'fill' flag is present in yaml file and it's value equals to 'on' or 'off'
    """
    if not ('fill' in data_to_validate and data_to_validate['fill'] in ("on", "off")):
        raise exceptions.CustomYamlException(
            "Error while scraping config file. \n\
'fill' keyword must be present on top of config file with value 'on'/'off'. \n\
See pattern in samples folder in project root"
        )


def is_order_present(data_to_validate: dict):
    """
    check if 'order' keyword is present in yaml file and it's value is dictionary
    """
    if not ('order' in data_to_validate and type(data_to_validate['order']) == dict):
        raise exceptions.CustomYamlException(
            "Error while scraping config file. \n\
'order' key must be under 'fill' one or the value assigned to it is invalid. \n\
See pattern in samples folder in project root"
        )


def is_stock_set_present(data_to_validate: dict):
    """
    check if 'stock-set' keyword is present in yaml file and it's value is list
    """
    if not ('stock-set' in data_to_validate['order'] and type(data_to_validate['order']['stock-set']) == list):
        raise exceptions.CustomYamlException(
            "Error while scraping config file. \n\
'stock-set' key must be one level below 'order' one or the value assigned to it is invalid. \n\
See pattern in samples folder in project root"
        )


def are_conditions_valid(data_to_validate: dict):
    """
    check if 'common-conditions' keyword is present in yaml file, it's value is dictionary, conditions are valid and 
    remaining conditions are provided for each stock separately or if it's not present check if all 3 conditions are 
    provided for each stock separately
    """
    common_conditions = ()
    if 'common-conditions' in data_to_validate['order']:
        helpers.are_conditions_good(data_to_validate['order']['common-conditions'])

        for condition in data_to_validate['order']['common-conditions']:
            common_conditions += (condition,)
        if len(common_conditions) == 3:
            # all conditions are provided in common ones, so we don't need to worry
            # if user has provided remaining ones for each stock individually
            pass
        else:
            separate_conditions = []
            # determine separate conditions need to be provided
            for cond in ('drop-percent', 'up-percent', 'sell-percent'):
                if cond not in common_conditions:
                    separate_conditions.append(cond)
            for stock_data in data_to_validate['order']['stock-set']:
                if 'conditions' not in stock_data:
                    raise exceptions.CustomYamlException(
                        "Error while scraping config file. \n\
You have provided common conditions, but not all 3 of them, \n\
so it's required to provide each of remaining for stock separately \n\
See pattern in samples folder in project root"
                    )
                helpers.are_conditions_good(stock_data['conditions'])
                for cond in separate_conditions:
                    if cond not in stock_data['conditions']:
                        raise exceptions.CustomYamlException(
                            f"Error while scraping config file. \n\
You didn't provided '{cond}' condition neither in common conditions nor in separate one for some stock \n\
See pattern in samples folder in project root"
                        )
    elif 'common-conditions' not in data_to_validate['order']:
        separate_conditions = ('drop-percent', 'up-percent', 'sell-percent')
        for stock_data in data_to_validate['order']['stock-set']:
            if 'conditions' not in stock_data:
                raise exceptions.CustomYamlException(
                    "Error while scraping config file. \
You didn't provided common conditions, so have to provide them for each stock separately \
See pattern in samples folder in project root"
                )
            helpers.are_conditions_good(stock_data['conditions'])
            for cond in ('drop-percent', 'up-percent', 'sell-percent'):
                if cond not in stock_data['conditions']:
                    raise exceptions.CustomYamlException(
                        f"Error while scraping config file. \
You didn't provided {cond} condition neither in separate stock conditions nor in common ones \
See pattern in samples folder in project root"
                    )
