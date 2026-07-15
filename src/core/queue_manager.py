import asyncio
from enum import Enum
from typing import List, Callable, Optional, Awaitable


class QueueState(Enum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"


class QueueItem:
    def __init__(self, text: str, index: int):
        self.text = text
        self.index = index
        self.skipped = False


class QueueManager:
    def __init__(self):
        self._items: List[QueueItem] = []
        self._current_index: int = -1
        self._state = QueueState.IDLE
        self._on_state_change: Optional[Callable] = None
        self._on_item_change: Optional[Callable] = None
        self._on_finished: Optional[Callable] = None

    @property
    def state(self) -> QueueState:
        return self._state

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def total(self) -> int:
        return len(self._items)

    @property
    def current_item(self) -> Optional[QueueItem]:
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    @property
    def items(self) -> List[QueueItem]:
        return self._items

    def set_on_state_change(self, callback: Callable):
        self._on_state_change = callback

    def set_on_item_change(self, callback: Callable):
        self._on_item_change = callback

    def set_on_finished(self, callback: Callable):
        self._on_finished = callback

    def add_item(self, text: str):
        self._items.append(QueueItem(text, len(self._items)))

    def add_items(self, texts: List[str]):
        for text in texts:
            self.add_item(text)

    def clear(self):
        self._items.clear()
        self._current_index = -1
        self._set_state(QueueState.IDLE)

    def skip_current(self):
        if self.current_item:
            self.current_item.skipped = True

    def _set_state(self, state: QueueState):
        self._state = state
        if self._on_state_change:
            self._on_state_change(state)

    def _notify_item_change(self):
        if self._on_item_change:
            self._on_item_change(self._current_index)

    async def process(self, speak_func: Callable[[str], Awaitable]):
        self._set_state(QueueState.PLAYING)
        self._current_index = 0
        while self._current_index < len(self._items):
            item = self._items[self._current_index]
            self._notify_item_change()
            if item.skipped:
                self._current_index += 1
                continue
            try:
                await speak_func(item.text)
            except Exception:
                pass
            self._current_index += 1
        self._set_state(QueueState.IDLE)
        self._current_index = -1
        if self._on_finished:
            self._on_finished()
