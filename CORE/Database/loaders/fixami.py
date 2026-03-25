# CORE/Database/loaders/FIXAMI.py
from CORE.Database.LOADERengine import LoaderEngine


class FIXAMIloader(LoaderEngine):
    def __init__(self):
        super().__init__("FIXAMI")


if __name__ == "__main__":
    FIXAMIloader().run()
