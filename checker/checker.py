#!/usr/bin/env python3
"""Checker script for mars-express."""
import os
import random
import time
from pathlib import Path

os.environ["TERM"] = "linux"
os.environ["TERMINFO"] = "/etc/terminfo"

import pwn # pylint: disable=wrong-import-position
import pyte # pylint: disable=wrong-import-position

import utils # pylint: disable=wrong-import-position

from ctf_gameserver import checkerlib # pylint: disable=wrong-import-position


pwn.context.log_level = "warn"
pwn.context.timeout = 10


class Wagon():
    """This class represents one wagon of a train."""

    WIDTH = 46

    def __init__(self, content: str = "", symbol: str = " ", content_length: int = None) -> None:
        """Initializes a new wagon."""
        self.content = content
        self.symbol = symbol
        self._content_length = content_length

    @property
    def content_length(self) -> str:
        """Returns content length. This might differ from len(self.content).

        This is necessary for ascii_art when parsing an unknown train. We know
        the length of the content first, then we can read each byte of the
        content from the animation.
        """
        if self._content_length:
            return self._content_length
        return len(self.content)

    @content_length.setter
    def content_length(self, new_length: int) -> None:
        """Sets the expected length."""
        self._content_length = new_length

    @property
    def ascii_art(self) -> list:
        """Returns the Wagon as ascii art."""
        before = (Wagon.WIDTH - 4 - self.content_length) // 2
        after = Wagon.WIDTH - 4 - before - self.content_length
        content = self.content.ljust(self.content_length, " ")

        return [
            " " + "_"*(Wagon.WIDTH-2) + " ",
            "|" + self.symbol*(Wagon.WIDTH-2) + "|",
            "|" + before*self.symbol +  " " + content + " " + after*self.symbol + "|",
            "|" + "-"*(Wagon.WIDTH-2) + "|",
            "`-----(o)~~~~(o)--------------(o)~~~~(o)-----'",
        ]

    def __eq__(self, other: object) -> bool:
        """Returns True if content and symbol equal."""
        if not isinstance(other, Wagon):
            return False
        if self.content != other.content:
            return False
        if self.symbol != other.symbol:
            return False
        return True

    def __str__(self) -> str:
        """Returns the string representation."""
        return f"Wagon({self.content}, {self.symbol})"


class Train():
    """This class represents a train, which can contain multiple wagons."""

    LOCO = ["         _____________________________ ",
            "    _,-'/| #### | |          ####     |",
            " _-'            | |                   |",
            "(------------------mars-express-------|",
            " \\----(o)~~~~(o)----------(o)~~~~(o)--'"]

    def __init__(self, name=None) -> None:
        """Initializes the train."""
        self.name = name
        self.wagons = []

    def check_duplicate_wagon_names(self) -> bool:
        """Returns true if wagons in the train have the same name."""
        return len([w.content for w in self.wagons]) != len({w.content for w in self.wagons})

    def add_wagon(self, wagon: Wagon) -> None:
        """Appends wagon to the list of wagons."""
        self.wagons.append(wagon)

    def get_frame(self, i: int) -> list:
        """Returns a single frame of the train ascii art."""
        train = self._get_whole_train()
        train = [" "*36 + line + " "*40 for line in train]
        return [line[i:i+39] + " " for line in train]

    def _get_whole_train(self) -> list:
        """Returns the entire train as ascii art."""
        train = self.LOCO
        for wagon in self.wagons:
            train = list(map(lambda x: x[0] + x[1], zip(train, wagon.ascii_art)))

        for line in train:
            assert len(line) == len(train[0])

        return train

    def __eq__(self, other: object) -> bool:
        """Returns True if name and all wagons equal."""
        if not isinstance(other, Train):
            return False
        if self.name != other.name:
            return False
        if self.wagons != other.wagons:
            return False
        return True

    def __str__(self) -> str:
        """Returns the string representation."""
        return f"Train({self.name}, [" + ", ".join(map(str, self.wagons)) + "])"


class Interaction():
    """This class encapsulates the interaction with the binary."""

    PORT = 8888

    HEADER = ["Welcome to mars-express!                ",
              "Your friends need some tools at the     ",
              "outpost? Just send them a train - We    ",
              "deliver everything.                     ",
              "                                        ",
              "Do you want to send a new train or      ",
              "show a previous?                        ",
              "                                        ",
              "1: Create and send new train            ",
              "2: Show a previous train                ",
              ">                                       "]

    MENU = ["Current train: %s                         ",
            "                                        ",
            "What do you want to do?                 ",
            "                                        ",
            "1: Append new wagon                     ",
            "2: Unqueue a wagon                      ",
            "3: Show current train                   ",
            "4: Send the train!                      ",
            ">                                       "]

    def __init__(self, ip: str) -> None:
        """Sets the ip for the new interaction."""
        self.ip = ip # pylint: disable=invalid-name
        self.proc = None
        self.screen = None
        self.stream = None

    def _init_connection(self) -> None:
        """Opens a connection and intializes variables."""
        try:
            self.proc = pwn.remote(self.ip, self.PORT)
        except pwn.pwnlib.exception.PwnlibException:
            # Raising a ConnectionRefusedError here is not necessarily correct.
            # Anyway, this error is handled by the checkerlib.
            raise ConnectionRefusedError("Cannot connect to target")

        self.screen = pyte.Screen(40, 20)
        self.stream = pyte.Stream(self.screen, True)


    @staticmethod
    def _get_menues(name: str) -> tuple:
        """Returns the expected menues of the binary."""
        menu = Interaction.MENU.copy()
        menu[0] = (menu[0] % name)[:40]

        menu_added = menu.copy()
        menu_added.append(" "*40)
        menu_added.append("Wagon inserted!".ljust(40, " "))

        menu_deleted = menu.copy()
        menu_deleted.append(" "*40)
        menu_deleted.append("Wagon inserted!".ljust(40, " "))

        return menu, menu_added, menu_deleted

    def _recv_until(self, state: list = []) -> None: # pylint: disable=dangerous-default-value
        """Receives bytes from the target until state is reached.

        Raises:
            EOFError: No more data available from the target
        """
        while len(state) < 20:
            state.append(" "*40)

        while state != self.screen.display:
            char = self.proc.recvn(1).decode("utf-8")
            if not char:
                # Treat this case as the end
                raise EOFError("No more data available from the target")
            self.stream.feed(char)

    def _load_frame(self) -> None:
        """Receives bytes from the target until a new unknown frame is loaded.

        This is necessary to receive enough bytes from the target to identify
        symbols and wagon contents.
        """
        self._recv_until()

        while True:
            char = self.proc.recvn(1).decode("utf-8")
            if not char:
                # Treat this case as the end
                raise EOFError("No more data available from the target")
            self.stream.feed(char)

            if char == ")" and "(o)~~~~(o)" in self.screen.display[4]:
                break

    def _parse_train(self) -> Train:
        """Parses the ascii art animation and returns the train."""
        i = 0
        train = Train()

        # Parse the locomotive
        for _ in range(37):
            self._recv_until(train.get_frame(i))
            i += 1

        # Parse all wagons
        while True:
            self._load_frame()

            if self.screen.display[1][38] != "|":
                break # There is no more wagon

            new_wagon = Wagon()
            train.add_wagon(new_wagon)

            self._recv_until(train.get_frame(i))
            i += 1

            # Identify the symbol
            self._load_frame()

            symbol = self.screen.display[1][38]
            new_wagon.symbol = symbol

            self._recv_until(train.get_frame(i))
            i += 1

            # Now we have to wait for the content
            before = 1
            while True:
                self._load_frame()

                char = self.screen.display[2][38]

                if char != new_wagon.symbol:
                    break

                self._recv_until(train.get_frame(i))
                i += 1
                before += 1

            new_wagon.content_length = Wagon.WIDTH - 4 - before*2 - 1
            self._recv_until(train.get_frame(i))
            i += 1

            # Parse the content of the wagon
            for _ in range(new_wagon.content_length):
                self._load_frame()

                new_wagon.content += self.screen.display[2][38]

                self._recv_until(train.get_frame(i))
                i += 1

            # Check if this wagon name is of even length
            self._load_frame()
            if self.screen.display[2][38] != " ":
                new_wagon.content += self.screen.display[2][38]
                new_wagon.content_length += 1

                self._recv_until(train.get_frame(i))
                i += 1

            # Wait for the end of the wagon
            after = Wagon.WIDTH - 4 - before - new_wagon.content_length
            for _ in range(2 + after):
                self._recv_until(train.get_frame(i))
                i += 1
                before += 1

            pwn.log.info(f"New {new_wagon}")

        # Just read the remaining frames
        for _ in range(39):
            self._recv_until(train.get_frame(i))
            i += 1

        return train

    def _add_wagon(self, wagon: Wagon, menu_added: str) -> None:
        pwn.log.info(f"Adding {wagon}")
        assert len(wagon.content) <= 40
        self.proc.sendline("1")
        self.proc.sendline(wagon.content)
        self.proc.sendline(wagon.symbol)

        self.proc.recvuntil("Give me the name: ")
        self.proc.recvuntil("And its symbol: ")
        self._recv_until(menu_added)

    def _delete_wagon(self, wagon: Wagon, menu_deleted: str) -> None:
        pwn.log.info(f"Deleting {wagon}")
        self.proc.sendline("2")
        self.proc.sendline(wagon.content)

        self.proc.recvuntil("Give me the name of the wagon: ")
        self._recv_until(menu_deleted)


    def create_train(self, train: Train, check_delete: bool = False) -> bool:
        """Opens a connection to the team; creates the train; returns True on success."""
        pwn.log.info(f"Creating new train ({train.name})")
        assert len(train.name) <= 32

        if not train.wagons:
            raise ValueError("Cannot create empty train.")

        self._init_connection()

        pwn.log.info("Requesting to add a new train")
        self._recv_until(Interaction.HEADER)

        self.proc.sendline("1")
        self.proc.sendline(train.name)
        self.proc.recvuntil("Give it a name:")

        menu, menu_added, menu_deleted = self._get_menues(train.name)
        self._recv_until(menu)

        for wagon in train.wagons:
            self._add_wagon(wagon, menu_added)

            if check_delete and random.randrange(10) < 4:
                self._delete_wagon(wagon, menu_deleted)
                self._add_wagon(wagon, menu_added)

        pwn.log.info(f"Saving the train")
        self.proc.sendline("4") # Save the train

        pwn.log.info(f"Parsing the train animation")
        try:
            parsed_train = self._parse_train()
        except EOFError:
            pwn.log.info("Parsing failed, probably the train already existed")
            return False

        parsed_train.name = train.name
        if parsed_train == train:
            pwn.log.info("Success")
            return True
        return False

    def get_train(self, name: str) -> Train:
        """Opens a connection to the team and trys to retrieve the train."""
        pwn.log.info(f"Trying to retrieve a train ({name})")

        self._init_connection()

        pwn.log.info("Requesting to retrieve a train")
        self._recv_until(Interaction.HEADER)

        self.proc.sendline("2")
        self.proc.recvuntil("Give me the name of the train:")
        self.proc.sendline(name)

        pwn.log.info(f"Parsing the train animation")
        try:
            parsed_train = self._parse_train()
        except EOFError:
            pwn.log.info("Parsing failed, probably the service is misbehaving")
            return None
        parsed_train.name = name
        return parsed_train


class MarsexpressChecker(checkerlib.BaseChecker):
    """This is for checking the mars-express."""

    def __init__(self, ip: str, team: int) -> None: # pylint: disable=invalid-name
        """Initializes the MarsexpressChecker with a list of sample words."""
        super().__init__(ip, team)
        with open(Path(__file__).parent / "words.txt", "r") as filed:
            words = filed.read().split("\n")
        self._words = [x.strip() for x in words if len(x.strip()) >= 6]


    @staticmethod
    def _get_key_for_flag(flag: str) -> str:
        """Returns a key for the given flag. If flag is new, a fresh key is generated."""
        flag_keys = checkerlib.load_state("flag_keys")
        if not flag_keys:
            flag_keys = {}

        if flag in flag_keys.keys():
            return flag_keys[flag]

        def _new_flag_key():
            """Returns a new random key for flag trains."""
            return str(random.randrange(10**10, 10**11))

        new_key = _new_flag_key()
        while new_key in flag_keys.values():
            new_key = _new_flag_key()

        flag_keys[flag] = new_key
        checkerlib.store_state("flag_keys", flag_keys)

        return new_key

    def _get_new_key(self) -> str:
        """Returns a new key for general purpose."""
        used_keys = checkerlib.load_state("used_keys")
        if not used_keys:
            used_keys = []

        def _init_new_key():
            """Returns a new random key."""
            separator = random.choice([" ", "_", "-", ""])
            return random.choice(self._words) + separator + str(random.randrange(10**3, 10**6))

        def _valid_key(key):
            """Returns true, if key is a valid key."""
            return key not in used_keys and len(key) <= 24

        new_key = _init_new_key()
        while not _valid_key(new_key):
            new_key = _init_new_key()

        used_keys.append(new_key)
        checkerlib.store_state("used_keys", used_keys)

        return new_key

    def _get_new_wagon(self, check_delete: bool) -> Wagon:
        """Returns a randomly generated wagon."""
        def get_new_name():
            """Returns a new random key."""
            if random.randrange(4) < 1:
                return utils.generate_suspicious_message()
            return random.choice(self._words)
        content = get_new_name()

        if check_delete:
            while len(content)%2 == 0:
                content = get_new_name()

        symbol = None
        while not symbol or symbol in content:
            symbol = chr(random.randrange(48, 123))

        return Wagon(content=content, symbol=symbol)

    @staticmethod
    def _save_train(train: Train) -> None:
        """Saves the train in the state."""
        saved_trains = checkerlib.load_state("saved_trains")
        if not saved_trains:
            saved_trains = []

        saved_trains.insert(0, train)
        saved_trains = saved_trains[:2]

        checkerlib.store_state("saved_trains", saved_trains)

    @staticmethod
    def _get_random_train(max_length: int = 15) -> Train:
        """Returns a random train from the state."""
        saved_trains = checkerlib.load_state("saved_trains")
        if not saved_trains:
            return None

        trains = [train for train in saved_trains if train and len(train.wagons) <= max_length]
        return random.choice(trains) if trains else None


    def place_flag(self, tick: int) -> checkerlib.CheckResult:
        """Places a flag at the target team."""
        start_time = time.time()
        interaction = Interaction(self.ip)

        flag = checkerlib.get_flag(tick)
        key = self._get_key_for_flag(flag)

        train = Train(key)
        train.add_wagon(Wagon(content=flag, symbol=chr(random.randrange(48, 123))))
        if not interaction.create_train(train):
            return checkerlib.CheckResult.DOWN

        pwn.log.info(f"Overall duration for place_flag: {int(time.time() - start_time)}s")
        return checkerlib.CheckResult.OK

    def check_service(self) -> checkerlib.CheckResult:
        """Checks if the service is working as expected."""
        start_time = time.time()
        interaction = Interaction(self.ip)

        # Do we want to check deletion or even length wagon names?
        check_delete = random.randrange(2) < 1

        # Generate a new train
        new_train = Train(self._get_new_key())
        num_wagons = random.choice(list(range(1, 7)) + list(range(1, 5)))
        for _ in range(num_wagons):
            new_train.add_wagon(self._get_new_wagon(check_delete))

        # Disable check_delete if necessary
        if new_train.check_duplicate_wagon_names():
            pwn.log.info("Disabling check_delete since train contains wagons with the same name.")
            check_delete = False

        # Add the train
        if not interaction.create_train(new_train, check_delete=check_delete):
            pwn.log.info("Creating train failed")

            self._save_train(None) # Just to push one train out of the saved state

            pwn.log.info(f"Overall duration for check_service: {int(time.time() - start_time)}s")
            return checkerlib.CheckResult.DOWN

        # Save the submitted train
        self._save_train(new_train)

        # Retrieve and check some other train
        train = self._get_random_train(7 - len(new_train.wagons))
        if not train and 2*len(new_train.wagons) <= 7: # Fallback to the current train
            train = new_train
        if not train:
            pwn.log.info("Not trying to retrieve other train")
            pwn.log.info(f"Overall duration for check_service: {int(time.time() - start_time)}s")
            return checkerlib.CheckResult.OK

        pwn.log.info("Trying to retrieve other train")
        actual_train = interaction.get_train(train.name)

        if actual_train != train:
            pwn.log.info(f"Overall duration for check_service: {int(time.time() - start_time)}s")
            return checkerlib.CheckResult.FAULTY

        pwn.log.info(f"Overall duration for check_service: {int(time.time() - start_time)}s")
        return checkerlib.CheckResult.OK

    def check_flag(self, tick: int) -> checkerlib.CheckResult:
        """Tries to retrieve a flag."""
        start_time = time.time()
        interaction = Interaction(self.ip)

        flag = checkerlib.get_flag(tick)
        key = self._get_key_for_flag(flag)

        train = interaction.get_train(key)

        pwn.log.info(f"Overall duration for check_flag: {int(time.time() - start_time)}s")
        if not train:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        if len(train.wagons) != 1:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        if train.wagons[0].content != flag:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        return checkerlib.CheckResult.OK

if __name__ == "__main__":
    checkerlib.run_check(MarsexpressChecker)
