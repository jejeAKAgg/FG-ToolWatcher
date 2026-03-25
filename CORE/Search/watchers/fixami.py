# CORE/Watchers/fixami.py
from CORE.Search.WATCHERengine import WatcherEngine
from CORE.Services.user import UserService
from typing import List


class FIXAMIwatcher(WatcherEngine):
    def __init__(self, items: List[dict], config: UserService):
        super().__init__("FIXAMI", items, config)
