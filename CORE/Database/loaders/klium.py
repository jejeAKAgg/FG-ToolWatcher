# CORE/Database/loaders/klium.py
from CORE.Database.LOADERengine import LoaderEngine


class KLIUMloader(LoaderEngine):
    def __init__(self):
        super().__init__("KLIUM")


if __name__ == "__main__":
    KLIUMloader().run()
