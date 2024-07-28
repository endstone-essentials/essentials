from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender

from endstone_essentials.commands.command_executor_base import CommandExecutorBase


class PingCommandExecutor(CommandExecutorBase):
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if len(args) == 0:
            if not isinstance(sender, Player):
                sender.send_error_message("This command can only be executed by a player")
                return False

            target = sender
        else:
            player_name = args[0].strip('"')  # remove the leading and trailing quotes
            if player_name == "@s":
                target = sender
            else:
                target = self.plugin.server.get_player(player_name)
                if target is None:
                    sender.send_error_message(f"Player {player_name} not found.")
                    return True

        sender.send_message(f"The ping of {target.name} is {ColorFormat.GREEN}{target.ping}{ColorFormat.RESET}ms")
        return True
