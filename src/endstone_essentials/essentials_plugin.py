import datetime

from endstone.command import Command, CommandSender
from endstone.event import EventPriority, ServerLoadEvent, event_handler
from endstone.plugin import Plugin


class EssentialsPlugin(Plugin):
    name = "EssentialsPlugin"
    api_version = "0.4"

    commands = {}

    permissions = {}

    def on_load(self) -> None:
        self.logger.info("essentials plugin is loaded!")

    def on_enable(self) -> None:
        self.logger.info("essentials plugin is enabled!")

    def on_disable(self) -> None:
        self.logger.info("essentials plugin is disabled!")

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        return True
