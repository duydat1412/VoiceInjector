import pytest

from src.core.queue_manager import QueueManager, QueueState


class TestQueueManager:
    @pytest.fixture
    def queue(self):
        return QueueManager()

    def test_initial_state(self, queue):
        assert queue.state == QueueState.IDLE
        assert queue.total == 0
        assert queue.current_index == -1
        assert queue.current_item is None

    def test_add_item(self, queue):
        queue.add_item("Hello")
        assert queue.total == 1
        assert queue.items[0].text == "Hello"
        assert queue.items[0].index == 0

    def test_add_items(self, queue):
        queue.add_items(["Hello", "World", "Test"])
        assert queue.total == 3

    def test_clear(self, queue):
        queue.add_items(["A", "B", "C"])
        queue.clear()
        assert queue.total == 0
        assert queue.state == QueueState.IDLE

    def test_skip_current(self, queue):
        queue.add_items(["A", "B"])
        queue._current_index = 0
        queue.skip_current()
        assert queue.items[0].skipped is True

    def test_state_change_callback(self, queue):
        states = []
        queue.set_on_state_change(lambda s: states.append(s))
        queue.clear()
        assert QueueState.IDLE in states
