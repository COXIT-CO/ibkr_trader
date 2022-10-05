import yaml
import sys
import time

def extract_data_yaml_file(path: str):
    """function to extact content to dictionary 
    from yaml file residing on privided path
        Parameters:
            path (str): path to the file to extact data from"""
    stream = open(path, 'r')
    try:
        scraped_data = yaml.safe_load(stream)
        # print(parsed_data.get("fill", True))
        # print(parsed_data["fill"] != "on")
        if "fill" not in scraped_data or scraped_data["fill"] != "on":
            """if 'fill' keyword isn't in file or
            its value isn't 'on'
            """
            return None
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

    return scraped_data
    # for key, value in dictionary.items():
    #     print(key + " : " + str(value))
