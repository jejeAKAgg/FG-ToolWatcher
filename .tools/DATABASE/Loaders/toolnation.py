# CORE/Database/loaders/toolnation.py
from Database.LOADERengine import LoaderEngine


class TOOLNATIONloader(LoaderEngine):
    def __init__(self):
        super().__init__("TOOLNATION")


if __name__ == "__main__":
    TOOLNATIONloader().run()
