from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender

from endstone_essentials.commands.command_executor_base import CommandExecutorBase


class FlyCommandExecutor(CommandExecutorBase):
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return True

        if sender.allow_flight:
            sender.allow_flight = False
            sender.send_message(ColorFormat.DARK_RED + "You are no longer allowed to fly")
        else:
            sender.allow_flight = True
            sender.send_message(ColorFormat.GREEN + "You are now allowed to fly")

        return True
