# CORE/Database/loaders/CLABOTS.py
from CORE.Database.LOADERengine import LoaderEngine


class CLABOTSloader(LoaderEngine):
    def __init__(self):
        super().__init__("CLABOTS")


if __name__ == "__main__":
    CLABOTSloader().run()
