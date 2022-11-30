class CustomYamlException(Exception):
    __message: str

    def __init__(self, message=None):
        if not message is None:
            self.__message = message

    def __str__(self):
        return self.__message