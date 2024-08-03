import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender
from endstone.form import ModalForm, Dropdown, TextInput
from endstone.level import Location

from endstone_essentials.commands.command_executor_base import CommandExecutorBase

if TYPE_CHECKING:
    from endstone_essentials import EssentialsPlugin


class HomeCommandExecutors(CommandExecutorBase):

    def __init__(self, plugin: "EssentialsPlugin"):
        super().__init__(plugin)
        self.homes: dict[uuid.UUID, dict[str, Location]] = {}
        self.load_homes()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("This command can only be executed by a player")
            return False

        match command.name:
            case "home":
                player_homes = self.homes.get(sender.unique_id, {})
                if len(player_homes) == 0:
                    sender.send_error_message("You don't have any home. Use /addhome to add a home.")
                    return False

                def on_submit(player: Player, json_str: str) -> None:
                    index = int(json.loads(json_str)[0])
                    home, location = list(player_homes.items())[index]
                    self.plugin.teleport_to_location(player, location)
                    player.send_message(ColorFormat.GREEN + f"You have been teleport to home {home}")

                sender.send_form(
                    ModalForm(
                        title="Back to home",
                        controls=[
                            Dropdown(label="Name", options=list(player_homes)),
                        ],
                        submit_button=ColorFormat.DARK_AQUA + ColorFormat.BOLD + "Go home",
                        on_submit=on_submit,
                    )
                )

            case "addhome":

                def on_submit(player: Player, json_str: str) -> None:
                    home = str(json.loads(json_str)[0]).strip()
                    if len(home) == 0:
                        sender.send_error_message("Invalid home name")
                        return

                    location = player.location
                    player_homes = self.homes.get(sender.unique_id, {})
                    if home in player_homes:
                        sender.send_error_message(f"Home {home} already exists.")
                        return

                    player_homes[home] = location
                    self.homes[sender.unique_id] = player_homes
                    self.save_homes()
                    sender.send_message(
                        ColorFormat.GREEN + f"Successfully create home {home} at "
                        f"{location.dimension.type.name}, {location.x:.2f}, {location.y:.2f}, {location.z:.2f}"
                    )

                sender.send_form(
                    ModalForm(
                        title="Add a new home",
                        controls=[
                            TextInput(label="Name", placeholder="Home"),
                        ],
                        submit_button=ColorFormat.DARK_GREEN + ColorFormat.BOLD + "Add",
                        on_submit=on_submit,
                    )
                )

            case "delhome":
                player_homes = self.homes.get(sender.unique_id, {})
                if len(player_homes) == 0:
                    sender.send_error_message("You don't have any home. Use /addhome to add a home.")
                    return False

                def on_submit(player: Player, json_str: str) -> None:
                    index = int(json.loads(json_str)[0])
                    home = list(player_homes)[index]
                    del self.homes[player.unique_id][home]
                    self.save_homes()
                    player.send_message(ColorFormat.RED + f"You have deleted home {home}")

                sender.send_form(
                    ModalForm(
                        title="Delete a home",
                        controls=[
                            Dropdown(label="Name", options=list(player_homes)),
                        ],
                        submit_button=ColorFormat.RED + ColorFormat.BOLD + "Delete",
                        on_submit=on_submit,
                    )
                )

            case "listhome":
                player_homes = self.homes.get(sender.unique_id, {})
                if len(player_homes) == 0:
                    sender.send_error_message("You don't have any home. Use /addhome to add a home.")
                    return False

                sender.send_message(f"You have {len(player_homes)} homes:")
                for name, location in player_homes.items():
                    sender.send_message(
                        f" - {name}: {location.dimension.type.name}, {location.x:.2f}, {location.y:.2f}, {location.z:.2f}"
                    )

        return True

    def load_homes(self) -> None:
        path = Path(self.plugin.data_folder) / "homes.json"
        if not path.exists():
            return

        with path.open("r") as f:
            data = json.load(f)

        level = self.plugin.server.level
        for player_uuid, homes in data.items():
            player_homes = {}
            for home_name, home_location in homes.items():
                player_homes[home_name] = Location(
                    level.get_dimension(home_location[0]),
                    float(home_location[1]),
                    float(home_location[2]),
                    float(home_location[3]),
                )
            self.homes[uuid.UUID(player_uuid)] = player_homes

    def save_homes(self) -> None:
        data = {}
        for player_uuid, player_homes in self.homes.items():
            data_homes = {}
            for home_name, home_location in player_homes.items():
                data_homes[home_name] = [
                    home_location.dimension.type.name,
                    home_location.x,
                    home_location.y,
                    home_location.z,
                ]
            data[str(player_uuid)] = data_homes

        path = Path(self.plugin.data_folder) / "homes.json"
        with path.open("w") as f:
            json.dump(data, f, indent=4)
