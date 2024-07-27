from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender

from endstone_essentials.commands.command_executor_base import CommandExecutorBase


class FlyCommandExecutor(CommandExecutorBase):
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return False

        if len(args) == 0:
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

        if target.allow_flight:
            target.allow_flight = False
            target.send_message(ColorFormat.DARK_RED + "You are no longer allowed to fly")
        else:
            target.allow_flight = True
            target.send_message(ColorFormat.GREEN + "You are now allowed to fly")

        return True
