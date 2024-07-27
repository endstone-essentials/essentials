from endstone import ColorFormat
from endstone.command import Command, CommandSender

from endstone_essentials.commands.command_executor_base import CommandExecutorBase


class BackCommandExecutors(CommandExecutorBase):

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if sender.unique_id not in self.plugin.last_death_locations:
            sender.send_error_message(ColorFormat.DARK_RED + "It seems you haven't died yet.")
            return False

        location = self.plugin.last_death_locations[sender.unique_id]
        self.plugin.teleport_to_location(sender, location)
        sender.send_message(ColorFormat.GREEN + "You have been teleported to the last place of death")
        del self.plugin.last_death_locations[sender.unique_id]  # remove the last death location
        return True
