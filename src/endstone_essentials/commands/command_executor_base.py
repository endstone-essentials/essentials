from typing import TYPE_CHECKING

from endstone.command import CommandExecutor

if TYPE_CHECKING:
    from endstone_essentials import EssentialsPlugin


class CommandExecutorBase(CommandExecutor):

    def __init__(self, plugin: "EssentialsPlugin"):
        super().__init__()
        self._plugin = plugin

    @property
    def plugin(self) -> "EssentialsPlugin":
        return self._plugin
