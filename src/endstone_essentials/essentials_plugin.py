from pathlib import Path
from typing import Union

import yaml
from endstone import Player
from endstone.command import Command, CommandExecutor, CommandSender
from endstone.event import PlayerDeathEvent, event_handler
from endstone.level import Location
from endstone.plugin import Plugin

from endstone_essentials.commands import (
    BackCommandExecutors,
    BroadcastCommandExecutor,
    FlyCommandExecutor,
    HomeCommandExecutors,
    WarpCommandExecutors,
    TpaCommandExecutor,
    NoticeCommandExecutors,
)


# NOTE(Vincent): maybe we can consider making this part of endstone api?
def plugin_metadata(filename):
    def decorator(cls):
        with (Path(__file__).parent / filename).open("r") as file:
            data = yaml.safe_load(file)
        for key, value in data.items():
            setattr(cls, key, value)
        return cls

    return decorator


@plugin_metadata("plugin.yml")
class EssentialsPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.last_death_locations = {}

    def on_enable(self) -> None:
        self.save_default_config()
        self.register_events(self)
        self.register_command("back", BackCommandExecutors(self))
        self.register_command("broadcast", BroadcastCommandExecutor(self))
        self.register_command("fly", FlyCommandExecutor(self))
        self.register_command(["home", "addhome", "delhome", "listhome"], HomeCommandExecutors(self))
        self.register_command(["warp", "addwarp", "delwarp", "listwarp"], WarpCommandExecutors(self))
        self.register_command(["tpa", "tpaccept", "tpdeny"], TpaCommandExecutor(self))
        self.register_command(["notice", "setnotice"], NoticeCommandExecutors(self))

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not self.is_command_enabled(command.name):
            sender.send_error_message("This command is not enabled")
            return True

        sender.send_error_message(f"Unhandled command /{command.name} {' '.join(args)}")

    @event_handler()
    def on_player_death(self, event: PlayerDeathEvent):
        self.last_death_locations[event.player.unique_id] = event.player.location
        event.player.send_message("You can use the /back command to return to the place of death")
        return

    def register_command(self, names: Union[str, list[str]], executor: CommandExecutor) -> None:
        if not isinstance(names, list):
            names = [names]

        if not self.is_command_enabled(names[0]):
            return

        for name in names:
            command = self.get_command(name)
            if command is None:
                raise ValueError(f"Unknown command '{name}'")
            command.executor = executor

    def is_command_enabled(self, command: str) -> bool:
        return self.config.get("commands", {}).get(command)

    def teleport_to_player(self, source: Player, player: Player):
        # TODO(api): replace with player.teleport
        self.server.dispatch_command(self.server.command_sender, f'tp "{source.name}" "{player.name}"')

    def teleport_to_location(self, player: Player, location: Location):
        # TODO(api): replace with player.teleport
        self.server.dispatch_command(
            self.server.command_sender,
            f'execute as "{player.name}" in {location.dimension.type.name.lower()} run tp @s {location.x} {location.y} {location.z}',
        )
