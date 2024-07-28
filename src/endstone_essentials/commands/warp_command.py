import json
from pathlib import Path
from typing import TYPE_CHECKING

from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender
from endstone.form import ModalForm, Dropdown, TextInput
from endstone.level import Location

from endstone_essentials.commands.command_executor_base import CommandExecutorBase

if TYPE_CHECKING:
    from endstone_essentials import EssentialsPlugin


class WarpCommandExecutors(CommandExecutorBase):
    def __init__(self, plugin: "EssentialsPlugin"):
        super().__init__(plugin)
        self.warps = {}
        self.load_warps()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return False

        match command.name:
            case "warp":
                if len(self.warps) == 0:
                    sender.send_error_message("No warp exists.")
                    return False

                def on_submit(player: Player, json_str: str) -> None:
                    index = int(json.loads(json_str)[0])
                    warp, location = list(self.warps.items())[index]
                    self.plugin.teleport_to_location(player, location)
                    player.send_message(ColorFormat.GREEN + f"You have been teleport to warp {warp}")

                sender.send_form(
                    ModalForm(
                        title="Teleport to warp",
                        controls=[
                            Dropdown(label="Name", options=list(self.warps)),
                        ],
                        submit_button=ColorFormat.DARK_AQUA + ColorFormat.BOLD + "Go warp",
                        on_submit=on_submit,
                    )
                )

            case "addwarp":

                def on_submit(player: Player, json_str: str) -> None:
                    warp = str(json.loads(json_str)[0]).strip()
                    if len(warp) == 0:
                        sender.send_error_message("Invalid warp name")
                        return

                    if warp in self.warps:
                        sender.send_error_message(f"Warp {warp} already exists.")
                        return

                    location = player.location
                    self.warps[warp] = location
                    self.save_warps()
                    sender.send_message(
                        ColorFormat.GREEN + f"Successfully create warp {warp} at "
                        f"{location.dimension.type.name}, {location.x:.2f}, {location.y:.2f}, {location.z:.2f}"
                    )

                sender.send_form(
                    ModalForm(
                        title="Add a new warp",
                        controls=[
                            TextInput(label="Name", placeholder="Warp"),
                        ],
                        submit_button=ColorFormat.DARK_GREEN + ColorFormat.BOLD + "Add",
                        on_submit=on_submit,
                    )
                )

            case "delwarp":
                if len(self.warps) == 0:
                    sender.send_error_message("No warp exists.")
                    return False

                def on_submit(player: Player, json_str: str) -> None:
                    index = int(json.loads(json_str)[0])
                    warp = list(self.warps)[index]
                    del self.warps[warp]
                    self.save_warps()
                    player.send_message(ColorFormat.RED + f"You have deleted warp {warp}")

                sender.send_form(
                    ModalForm(
                        title="Delete a home",
                        controls=[
                            Dropdown(label="Name", options=list(self.warps)),
                        ],
                        submit_button=ColorFormat.RED + ColorFormat.BOLD + "Delete",
                        on_submit=on_submit,
                    )
                )

            case "listwarp":
                if len(self.warps) == 0:
                    sender.send_error_message("No warp exists.")
                    return False

                sender.send_message(f"There are {len(self.warps)} warps:")
                for name, location in self.warps.items():
                    sender.send_message(
                        f" - {name}: {location.dimension.type.name}, {location.x:.2f}, {location.y:.2f}, {location.z:.2f}"
                    )

        return True

    def load_warps(self) -> None:
        path = Path(self.plugin.data_folder) / "warps.json"
        if not path.exists():
            return

        with path.open("r") as f:
            data = json.load(f)

        level = self.plugin.server.levels[0]
        for warp_name, warp_location in data.items():
            self.warps[warp_name] = Location(
                level.get_dimension(warp_location[0]),
                float(warp_location[1]),
                float(warp_location[2]),
                float(warp_location[3]),
            )

    def save_warps(self) -> None:
        data = {}
        for warp_name, warp_location in self.warps.items():
            data[warp_name] = [
                warp_location.dimension.type.name,
                warp_location.x,
                warp_location.y,
                warp_location.z,
            ]

        path = Path(self.plugin.data_folder) / "warps.json"
        with path.open("w") as f:
            json.dump(data, f, indent=4)
