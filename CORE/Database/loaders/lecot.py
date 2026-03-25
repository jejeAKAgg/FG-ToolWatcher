# CORE/Database/loaders/lecot.py
from CORE.Database.LOADERengine import LoaderEngine


class LECOTloader(LoaderEngine):
    def __init__(self):
        super().__init__("LECOT")


if __name__ == "__main__":
    LECOTloader().run()
