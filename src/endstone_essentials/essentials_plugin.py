from endstone import Player
from endstone.command import Command, CommandSender
from endstone.event import EventPriority, ServerLoadEvent, event_handler
from endstone.plugin import Plugin


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
        }
    }

    permissions = {
        "essentials.command": {
            "description": "Allow users to use all commands provided by this plugin.",
            "default": True,
            "children": {
                "essentials.command.fly": True,
                "essentials.command.broadcast": True
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
    }

    def on_load(self) -> None:
        self.logger.info("Essentials plugin is loaded!")

    def on_enable(self) -> None:
        self.logger.info("Essentials plugin is enabled!")

    def on_disable(self) -> None:
        self.logger.info("Essentials plugin is disabled!")

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
        return True
