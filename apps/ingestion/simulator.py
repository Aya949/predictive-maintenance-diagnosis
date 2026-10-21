import asyncio
import os
import random
import pandas as pd

from asyncua import Server


# ============================================================
# CONFIG
# ============================================================

CHANNEL_NAMES = [
    "tachometer",
    "underhang_axial",
    "underhang_radial",
    "underhang_tangential",
    "overhang_axial",
    "overhang_radial",
    "overhang_tangential",
    "microphone",
]

WINDOW_SIZE = 2048

BASE_PATH = "apps/data/raw/MAFAULDA"

FAULT_FOLDERS = {
    "normal": "normal",
    "imbalance": "imbalance",
    "horizontal_misalignment": "horizontal-misalignment",
    "vertical_misalignment": "vertical-misalignment",
    "underhang_bearing": "underhang",
    "overhang_bearing": "overhang",
}

MACHINE_NAMES = [
    "Machine1",
    "Machine2",
    "Machine3",
]


# ------------------------------------------------------------
# IMPORTANT:
# How long one recording is streamed before the simulator
# chooses another recording/state.
#
# 25,000 samples ≈ 25 seconds at 0.001 s/sample
# 50,000 samples ≈ 50 seconds
# ------------------------------------------------------------

NORMAL_DURATION = 60000
FAULT_DURATION = 15000


SAMPLE_INTERVAL = 0.01


# ============================================================
# FIND AVAILABLE FILES
# ============================================================

def list_files_for_category(category):
    folder = os.path.join(
        BASE_PATH,
        FAULT_FOLDERS[category]
    )

    if not os.path.exists(folder):
        print(
            f"WARNING: folder does not exist for "
            f"{category}: {folder}"
        )
        return []

    files = []

    for root, dirs, filenames in os.walk(folder):

        for filename in filenames:

            if filename.lower().endswith(".csv"):
                files.append(
                    os.path.join(root, filename)
                )

    return files


print("=" * 60)
print("Indexing MAFAULDA recordings")
print("=" * 60)

FILE_POOLS = {
    category: list_files_for_category(category)
    for category in FAULT_FOLDERS
}

for category, files in FILE_POOLS.items():

    print(
        f"{category:25s}: {len(files)} files"
    )

    if not files:
        print(
            f"  WARNING: no files found for {category}"
        )


# ============================================================
# MACHINE STATE
# ============================================================

class MachineState:

    def __init__(self, name):

        self.name = name

        self.current_category = "normal"

        self.data = None

        self.row_idx = 0

        self.samples_in_state = 0

        self._load_new_file("normal")


    def _load_new_file(self, category):

        files = FILE_POOLS.get(category, [])

        if not files:

            print(
                f"[{self.name}] "
                f"No files available for {category}. "
                f"Keeping current state."
            )

            return

        filepath = random.choice(files)

        print(
            f"[{self.name}] streaming "
            f"{category}: "
            f"{os.path.basename(filepath)}"
        )

        data = pd.read_csv(
            filepath,
            header=None
        ).values

        # Make sure the recording is usable
        # and has all expected channels.
        if data.shape[1] < len(CHANNEL_NAMES):

            raise ValueError(
                f"{filepath} contains "
                f"{data.shape[1]} columns but "
                f"{len(CHANNEL_NAMES)} are required."
            )

        n_clean = (
            len(data) // WINDOW_SIZE
        ) * WINDOW_SIZE

        data = data[:n_clean]

        if len(data) == 0:

            raise ValueError(
                f"{filepath} contains no usable samples."
            )

        self.data = data

        self.current_category = category

        self.row_idx = 0

        self.samples_in_state = 0


    def _choose_next_state(self):

        # ----------------------------------------------------
        # We intentionally bias the simulator toward NORMAL.
        #
        # This gives us a realistic demo distribution rather
        # than making the plant fail continuously.
        # ----------------------------------------------------

        if self.current_category == "normal":

            # 75% of transitions stay normal
            # 25% enter a fault.
            if random.random() < 0.25:

                fault_categories = [
                    category
                    for category in FAULT_FOLDERS
                    if category != "normal"
                ]

                return random.choice(
                    fault_categories
                )

            return "normal"

        else:

            # After a fault, 70% chance of returning
            # to normal, 30% chance of another fault episode.
            if random.random() < 0.70:

                return "normal"

            fault_categories = [
                category
                for category in FAULT_FOLDERS
                if category != "normal"
            ]

            return random.choice(
                fault_categories
            )


    def _maybe_transition(self):

        if self.current_category == "normal":

            duration = NORMAL_DURATION

        else:

            duration = FAULT_DURATION


        if self.samples_in_state < duration:

            return


        next_category = self._choose_next_state()

        print(
            f"[STATE CHANGE] "
            f"{self.name}: "
            f"{self.current_category} "
            f"-> "
            f"{next_category}"
        )

        self._load_new_file(
            next_category
        )


    def next_row(self):

        # ----------------------------------------------------
        # Check whether the current state should end.
        # ----------------------------------------------------

        self._maybe_transition()

        # ----------------------------------------------------
        # Read current raw sensor row.
        # ----------------------------------------------------

        row = self.data[self.row_idx]

        self.row_idx += 1

        self.samples_in_state += 1

        # Loop inside the SAME recording if needed.
        if self.row_idx >= len(self.data):

            self.row_idx = 0

        return row


# ============================================================
# OPC-UA SERVER
# ============================================================

async def main():

    server = Server()

    await server.init()

    server.set_endpoint(
        "opc.tcp://0.0.0.0:4840/freeopcua/server/"
    )

    server.set_server_name(
        "JESA Multi-Machine Simulator"
    )

    uri = "http://jesa.plant"

    idx = await server.register_namespace(uri)


    # --------------------------------------------------------
    # Create machines
    # --------------------------------------------------------

    machines = {
        machine_name:
            MachineState(machine_name)
        for machine_name in MACHINE_NAMES
    }

    machine_nodes = {}


    for machine_name in MACHINE_NAMES:

        machine_obj = (
            await server.nodes.objects.add_object(
                idx,
                machine_name
            )
        )

        nodes = {}

        for channel in CHANNEL_NAMES:

            node = await machine_obj.add_variable(
                idx,
                channel,
                0.0
            )

            await node.set_writable()

            nodes[channel] = node

        machine_nodes[machine_name] = nodes


    print()
    print("=" * 60)
    print(
        "OPC-UA server starting at "
        "opc.tcp://0.0.0.0:4840/freeopcua/server/"
    )
    print("=" * 60)
    print()


    # --------------------------------------------------------
    # Start server
    # --------------------------------------------------------

    async with server:

        tick = 0

        while True:

            for machine_name in MACHINE_NAMES:

                row = machines[
                    machine_name
                ].next_row()

                nodes = machine_nodes[
                    machine_name
                ]

                for i, channel in enumerate(
                    CHANNEL_NAMES
                ):

                    await nodes[
                        channel
                    ].write_value(
                        float(row[i])
                    )


            tick += 1

            await asyncio.sleep(
                SAMPLE_INTERVAL
            )

            if tick % 5000 == 0:

                print(
                    f"Streamed {tick} ticks..."
                )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())