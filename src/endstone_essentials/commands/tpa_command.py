from typing import TYPE_CHECKING

from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender
from endstone.form import *

from endstone_essentials.commands.command_executor_base import CommandExecutorBase

if TYPE_CHECKING:
    from endstone_essentials import EssentialsPlugin


class TpaCommandExecutor(CommandExecutorBase):

    def __init__(self, plugin: "EssentialsPlugin"):
        super().__init__(plugin)
        self.teleport_requests = {}

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return False

        match [command.name] + args:
            case ["tpa", player_name]:
                player_name = player_name.strip('"')  # remove the leading and trailing quotes
                if player_name == "@s" or player_name == sender.name:
                    sender.send_error_message("You can only teleport to a player other than yourself")
                    return True
                else:
                    target = self.plugin.server.get_player(player_name)

                if target is None:
                    sender.send_error_message(f"Player {player_name} not found.")
                    return True

                self.handle_teleport_request(sender, target)

            case ["tpaccept"]:
                self.accept_teleport_request(sender)

            case ["tpdeny"]:
                self.deny_teleport_request(sender)

        return True

    def handle_teleport_request(self, player: Player, target: Player) -> None:
        if target.unique_id in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "This player already has a pending teleport request.")
            return

        self.teleport_requests[target.unique_id] = player.unique_id
        player.send_message(ColorFormat.GREEN + f"Teleport request sent to {target.name}.")

        def on_submit(tgt: Player, selection: int) -> None:
            if selection == 0:
                self.accept_teleport_request(tgt)
            else:
                self.deny_teleport_request(tgt)

        player_name = player.name
        target.send_form(
            MessageForm(
                title="Teleport request",
                content=f"{ColorFormat.GREEN}{player_name}{ColorFormat.RESET} has sent you a teleport request.",
                button1=f"{ColorFormat.DARK_GREEN}{ColorFormat.BOLD}Accept",
                button2=f"{ColorFormat.RED}{ColorFormat.BOLD}Deny",
                on_submit=on_submit,
                on_close=lambda tgt: tgt.send_message(
                    f"{ColorFormat.GREEN}{player_name}{ColorFormat.RESET} has sent you a teleport request. "
                    f"Use /tpaccept to accept or /tpdeny to deny."
                ),
            )
        )

    def accept_teleport_request(self, player: Player) -> None:
        if player.unique_id not in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "You have no pending teleport requests.")
            return

        source = self.plugin.server.get_player(self.teleport_requests[player.unique_id])
        if source is None:
            player.send_message(ColorFormat.YELLOW + "The player who sent the teleport request is no longer online.")
        else:
            self.plugin.teleport_to_player(source, player)
            source.send_message(ColorFormat.GREEN + f"You have been teleported to {player.name}.")
            player.send_message(ColorFormat.GREEN + "Teleport request accepted.")

        del self.teleport_requests[player.unique_id]

    def deny_teleport_request(self, player: Player) -> None:
        if player.unique_id not in self.teleport_requests:
            player.send_message(ColorFormat.YELLOW + "You have no pending teleport requests.")
            return

        source = self.plugin.server.get_player(self.teleport_requests[player.unique_id])
        if source is not None:
            source.send_message(ColorFormat.RED + f"{player.name} has denied your teleport request.")

        player.send_message(ColorFormat.DARK_PURPLE + "Teleport request denied.")
        del self.teleport_requests[player.unique_id]
