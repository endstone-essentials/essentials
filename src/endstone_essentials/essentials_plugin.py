import json
import os
import uuid
from pathlib import Path

import yaml
from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender
from endstone.event import PlayerDeathEvent, event_handler
from endstone.level import Location, Level
from endstone.plugin import Plugin


# TODO(endstone): consider making this part of endstone api?
def load_from_yaml(filename):
    def decorator(cls):
        with (Path(__file__).parent / filename).open("r") as file:
            data = yaml.safe_load(file)
        for key, value in data.items():
            setattr(cls, key, value)
        return cls

    return decorator


@load_from_yaml("plugin.yml")
class EssentialsPlugin(Plugin):
    teleport_requests: dict[uuid.UUID, uuid.UUID] = {}
    last_death_locations: dict[uuid.UUID, Location] = {}
    homes: dict[uuid.UUID, dict[str, Location]] = {}

    def on_enable(self) -> None:
        self.save_default_config()
        self.load_homes()
        self.register_events(self)

    def on_disable(self) -> None:
        self.save_homes()

    def is_command_enabled(self, command: str) -> bool:
        return self.config.get("commands", {}).get(command)

    def load_homes(self) -> None:
        path = Path(self.data_folder) / "homes.json"
        if not path.exists():
            os.mknod(path)
            return

        data: dict[str, dict[str, list]]
        with open(path, "r") as i:
            data = json.load(i)
        for player, data_homes in data.items():
            player_homes: dict[str, Location] = {}
            for home_name, home_location in data_homes.items():
                player_homes[home_name] = Location(
                    Level.get_dimension(home_location[0]),
                    float(home_location[1]),
                    float(home_location[2]),
                    float(home_location[3]),
                )
            self.homes[uuid.UUID(player)] = player_homes
        return

    def save_homes(self) -> None:
        data: [str, dict[str, list[str]]] = {}
        for player, player_homes in self.homes.items():
            data_homes: dict[str, list[str]] = {}
            for home_name, home_location in player_homes.items():
                data_homes[home_name] = [
                    home_location.dimension.type.name,
                    str(home_location.x),
                    str(home_location.y),
                    str(home_location.z),
                ]
            data[str(player)] = data_homes
        with open(Path(self.data_folder) / "homes.json", "w") as o:
            json.dump(data, o, indent=4, ensure_ascii=False)
        return

    @event_handler()
    def on_player_death(self, event: PlayerDeathEvent):
        self.last_death_locations[event.player.unique_id] = event.player.location
        event.player.send_message("You can use the /back command to return to the place of death")
        return

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return False

        match command.name:
            case "fly":
                if not self.is_command_enabled("fly"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 0:
                    sender.send_error_message("Usage: /fly")
                    return False

                if sender.allow_flight:
                    sender.allow_flight = False
                    sender.send_message(ColorFormat.GREEN + "Turn off flying mode")
                else:
                    sender.allow_flight = True
                    sender.send_message(ColorFormat.GREEN + "You can now fly")

            case "broadcast":
                if not self.is_command_enabled("broadcast"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) == 0:
                    sender.send_error_message("You have to send something")
                    return False

                self.server.broadcast_message(args[0])

            case "tpa":
                if not self.is_command_enabled("tpa"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 1:
                    sender.send_error_message("Usage: /tpa <player>")
                    return True

                player_name = args[0].strip('"')
                target = self.server.get_player(player_name)
                if target is None:
                    sender.send_message(f"Player {player_name} not found.")
                    return True

                self.handle_teleport_request(sender, target)

            case "tpaccept":
                if not self.is_command_enabled("tpa"):
                    sender.send_error_message("This command is not enabled")
                    return False

                self.accept_teleport_request(sender)

            case "tpdeny":
                if not self.is_command_enabled("tpa"):
                    sender.send_error_message("This command is not enabled")
                    return False

                self.deny_teleport_request(sender)

            case "back":
                if not self.is_command_enabled("back"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 0:
                    sender.send_error_message("Usage: /back")
                    return False

                if sender.unique_id not in self.last_death_locations:
                    sender.send_error_message("You haven't died yet")
                    return False

                location = self.last_death_locations[sender.unique_id]
                self.teleport_to_location(sender, location)
                sender.send_message(ColorFormat.GREEN + "You have been teleported to the last place of death")

            case "addhome":
                if not self.is_command_enabled("home"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 1:
                    sender.send_error_message("Usage: /addhome <name: string>")
                    return False

                player_homes = self.homes.get(sender.unique_id, {})
                player_homes[args[0]] = sender.location
                self.homes[sender.unique_id] = player_homes
                sender.send_message(
                    ColorFormat.GREEN
                    + f"Successfully create home {args[0]} at location {sender.location.dimension.type.name}, {sender.location.x}, {sender.location.y}, {sender.location.z}"
                )

            case "home":
                if not self.is_command_enabled("home"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 1:
                    sender.send_error_message("Usage: /home <name: string>")
                    return False

                if sender.unique_id not in self.homes or args[0] not in self.homes[sender.unique_id]:
                    sender.send_error_message("This home doesn't exist")
                    return False

                location = self.homes[sender.unique_id][args[0]]
                self.teleport_to_location(sender, location)
                sender.send_message(ColorFormat.GREEN + f"You have been teleport to home {args[0]}")

            case "listhome":
                if not self.is_command_enabled("home"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 0:
                    sender.send_error_message("Usage: /listhome")
                    return False

                if sender.unique_id not in self.homes or len(self.homes[sender.unique_id]) == 0:
                    sender.send_error_message("You don't have any home")
                    return True

                player_homes = self.homes[sender.unique_id]
                sender.send_message(f"You have {len(player_homes)} homes:")
                for name, location in player_homes.items():
                    sender.send_message(
                        f" - {name}: {location.dimension.type.name}, {location.x}, {location.y}, {location.z}"
                    )

            case "delhome":
                if not self.is_command_enabled("home"):
                    sender.send_error_message("This command is not enabled")
                    return False

                if len(args) != 1:
                    sender.send_error_message("Usage: /delhome <name: string>")
                    return False

                if sender.unique_id not in self.homes or args[0] not in self.homes[sender.unique_id]:
                    sender.send_error_message("This home doesn't exist")
                    return False

                del self.homes[sender.unique_id][args[0]]
                sender.send_message(ColorFormat.GREEN + f"You have deleted home {args[0]}")
        return True

    def handle_teleport_request(self, player: Player, target: Player) -> None:
        if target.unique_id in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "This player already has a pending teleport request.")
            return

        self.teleport_requests[target.unique_id] = player.unique_id
        player.send_message(ColorFormat.GREEN + f"Teleport request sent to {target.name}.")
        target.send_message(
            ColorFormat.GREEN + f"{player.name} has sent you a teleport request. " f"Use /tpaccept or /tpdeny."
        )

    def accept_teleport_request(self, player: Player) -> None:
        if player.unique_id not in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "You have no pending teleport requests.")
            return

        source = self.server.get_player(self.teleport_requests[player.unique_id])
        if source is None:
            player.send_message(ColorFormat.YELLOW + "The player who sent the teleport request is no longer online.")
        else:
            self.teleport_to_player(source, player)
            source.send_message(ColorFormat.GREEN + f"You have been teleported to {player.name}.")
            player.send_message(ColorFormat.GREEN + "Teleport request accepted.")

        del self.teleport_requests[player.unique_id]

    def deny_teleport_request(self, player: Player) -> None:
        if player.unique_id not in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "You have no pending teleport requests.")
            return

        source = self.server.get_player(self.teleport_requests[player.unique_id])
        if source is not None:
            source.send_message(ColorFormat.RED + f"{player.name} has denied your teleport request.")

        player.send_message(ColorFormat.DARK_PURPLE + "Teleport request denied.")
        del self.teleport_requests[player.unique_id]

    def teleport_to_player(self, source: Player, player: Player):
        # TODO(api): replace with player.teleport
        self.server.dispatch_command(self.server.command_sender, f'tp "{source.name}" "{player.name}"')

    def teleport_to_location(self, player: Player, location: Location):
        # TODO(api): replace with player.teleport
        self.server.dispatch_command(
            self.server.command_sender,
            f'execute as "{player.name}" in {location.dimension.type.name.lower()} run tp @s {location.x} {location.y} {location.z}',
        )
