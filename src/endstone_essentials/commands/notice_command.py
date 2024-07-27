from pathlib import Path

from endstone import Player, ColorFormat
from endstone.command import *
from endstone.form import *
from typing import TYPE_CHECKING

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
                        controls=[
                            Label(text=self.notice_body)
                        ],
                        submit_button=self.notice_button
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
        path = Path(self.plugin.data_folder) / "notice.txt"
        if not path.exists():
            return

        with path.open("r") as f:
            self.notice_title = f.readline().replace("\n", "")
            self.notice_button = f.readline().replace("\n", "")
            self.notice_body = f.read()

    def save_notice(self) -> None:
        path = Path(self.plugin.data_folder) / "notice.txt"
        with path.open("w") as f:
            f.write(self.notice_title)
            f.write("\n")
            f.write(self.notice_button)
            f.write("\n")
            f.write(self.notice_body)
