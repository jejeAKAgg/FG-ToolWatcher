# CORE/Watchers/lecot.py
from CORE.Search.WATCHERengine import WatcherEngine
from CORE.Services.user import UserService
from typing import List


class LECOTwatcher(WatcherEngine):
    def __init__(self, items: List[dict], config: UserService):
        super().__init__("LECOT", items, config)
