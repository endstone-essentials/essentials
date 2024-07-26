from endstone.command import Command, CommandSender

from endstone_essentials.commands.command_executor_base import CommandExecutorBase


class BroadcastCommandExecutor(CommandExecutorBase):

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if len(args) == 0:
            return False  # return false to send usage

        self.plugin.server.broadcast_message(str(args[0]))
        return True
