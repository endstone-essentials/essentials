import uuid

from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender
from endstone.event import EventPriority, PlayerDeathEvent, event_handler
from endstone.plugin import Plugin
from endstone.level import Location


class EssentialsPlugin(Plugin):
    name = "EssentialsPlugin"
    api_version = "0.4"

    commands = {
        "fly": {
            "description": "Switch flying mode",
            "usages": ["/fly"],
            "permissions": ["essentials.command.fly"]
        },
        "broadcast": {
            "description": "Broadcast a message",
            "usages": ["/broadcast <message: message>"],
            "aliases": ["bd"],
            "permissions": ["essentials.command.broadcast"]
        },
        "tpa": {
            "description": "Send a teleport request to another player.",
            "usages": ["/tpa <target: player>"],
            "permissions": ["essentials.command.tpa"],
        },
        "tpaccept": {
            "description": "Accept a teleport request.",
            "usages": ["/tpaccept"],
            "aliases": ["tpac"],
            "permissions": ["essentials.command.tpaccept"],
        },
        "tpdeny": {
            "description": "Deny a teleport request.",
            "usages": ["/tpdeny"],
            "aliases": ["tpd"],
            "permissions": ["essentials.command.tpdeny"],
        },
        "back": {
            "description": "Back to the place where you last died.",
            "usages": ["/back"],
            "permissions": ["essentials.command.back"],
        },
    }

    permissions = {
        "essentials.command": {
            "description": "Allow users to use all commands provided by this plugin.",
            "default": True,
            "children": {
                "essentials.command.fly": True,
                "essentials.command.broadcast": True,
                "essentials.command.tpa": True,
                "essentials.command.tpaccept": True,
                "essentials.command.tpdeny": True,
                "essentials.command.back": True
            }
        },
        "essentials.command.fly": {
            "description": "Allow users to use the /fly command.",
            "default": True,
        },
        "essentials.command.broadcast": {
            "description": "Allow users to use the /broadcast command.",
            "default": True,
        },
        "essentials.command.tpa": {
            "description": "Allow users to use the /tpa command.",
            "default": True,
        },
        "essentials.command.tpaccept": {
            "description": "Allow users to use the /tpaccept command.",
            "default": True,
        },
        "essentials.command.tpdeny": {
            "description": "Allow users to use the /tpdeny command.",
            "default": True,
        },
        "essentials.command.back": {
            "description": "Allow users to use the /back command.",
            "default": True,
        }
    }

    teleport_requests: dict[uuid.UUID, uuid.UUID] = {}
    last_death_locations: dict[uuid.UUID, Location] = {}

    def __init__(self):
        super().__init__()

    def on_load(self) -> None:
        self.logger.info("Essentials plugin is loaded!")

    def on_enable(self) -> None:
        self.register_events(self)
        self.logger.info("Essentials plugin is enabled!")

    def on_disable(self) -> None:
        self.logger.info("Essentials plugin is disabled!")

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
                if len(args) != 0:
                    sender.send_error_message("Usage: /fly")
                    return False

                if sender.allow_flight:
                    sender.allow_flight = False
                    sender.send_message("Turn off flying mode")
                else:
                    sender.allow_flight = True
                    sender.send_message("You can now fly")

            case "bd", "broadcast":
                if len(args) == 0:
                    sender.send_error_message("You have to send something")
                    return False

                self.server.broadcast_message(" ".join(args))

            case "tpa":
                if len(args) != 1:
                    sender.send_error_message("Usage: /tpa <player>")
                    return True

                player_name = args[0].strip('\"')
                target = self.server.get_player(player_name)
                if target is None:
                    sender.send_message(f"Player {player_name} not found.")
                    return True

                self.handle_teleport_request(sender, target)

            case "tpaccept":
                self.accept_teleport_request(sender)

            case "tpdeny":
                self.deny_teleport_request(sender)

            case "back":
                if len(args) != 0:
                    sender.send_error_message("Usage: /back")
                    return False

                if sender.unique_id not in self.last_death_locations:
                    sender.send_error_message("You haven't died yet")
                    return False

                location = self.last_death_locations[sender.unique_id]
                # TODO(api): replace with player.teleport
                self.server.dispatch_command(self.server.command_sender, f'execute as "{sender.name}" in {location.dimension.type.name.lower()} run tp @s {location.x} {location.y} {location.z}')
                sender.send_message("You have been teleported to the last place of death")

        return True

    def handle_teleport_request(self, player: Player, target: Player) -> None:
        if target.unique_id in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "This player already has a pending teleport request.")
            return

        self.teleport_requests[target.unique_id] = player.unique_id
        player.send_message(ColorFormat.GREEN + f"Teleport request sent to {target.name}.")
        target.send_message(ColorFormat.GREEN + f"{player.name} has sent you a teleport request. "
                                                f"Use /tpaccept or /tpdeny.")

    def accept_teleport_request(self, player: Player) -> None:
        if player.unique_id not in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "You have no pending teleport requests.")
            return

        source = self.server.get_player(self.teleport_requests[player.unique_id])
        if source is None:
            player.send_message(ColorFormat.YELLOW + "The player who sent the teleport request is no longer online.")
        else:
            # TODO(api): replace with player.teleport
            self.server.dispatch_command(self.server.command_sender, f'tp "{source.name}" "{player.name}"')
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
