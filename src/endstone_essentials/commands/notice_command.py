from typing import TYPE_CHECKING

from endstone import Player, ColorFormat
from endstone.command import Command, CommandSender
from endstone.form import ModalForm, Label

from endstone_essentials.commands.command_executor_base import CommandExecutorBase

if TYPE_CHECKING:
    from endstone_essentials import EssentialsPlugin


class NoticeCommandExecutors(CommandExecutorBase):

    def __init__(self, plugin: "EssentialsPlugin"):
        super().__init__(plugin)
        self.notice_title = "Notice"
        self.notice_button = "OK"
        self.notice_body = ""
        self.load_notice()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return False

        match command.name:
            case "notice":
                if self.notice_body == "":
                    sender.send_message("There is no notice.")
                    return True

                sender.send_form(
                    ModalForm(
                        title=self.notice_title,
                        controls=[Label(text=self.notice_body)],
                        submit_button=self.notice_button,
                    )
                )

            case "setnotice":
                if len(args) != 3:
                    return False

                self.notice_title = args[0]
                self.notice_button = args[1]
                self.notice_body = args[2].replace("\\n", "\n")
                self.save_notice()
                sender.send_message(ColorFormat.GREEN + "Notice has been updated!")

        return True

    def load_notice(self) -> None:
        self.notice_title = self.plugin.config["notice"]["title"]
        self.notice_button = self.plugin.config["notice"]["button"]
        self.notice_body = self.plugin.config["notice"]["body"]

    def save_notice(self) -> None:
        self.plugin.config["notice"]["title"] = self.notice_title
        self.plugin.config["notice"]["body"] = self.notice_body
        self.plugin.config["notice"]["button"] = self.notice_button
        self.plugin.save_config()
