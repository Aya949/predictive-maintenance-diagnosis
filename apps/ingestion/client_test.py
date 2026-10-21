import asyncio
from asyncua import Client

CHANNEL_NAMES = ['tachometer', 'underhang_axial', 'underhang_radial', 'underhang_tangential',
                  'overhang_axial', 'overhang_radial', 'overhang_tangential', 'microphone']


async def main():
    url = "opc.tcp://localhost:4840/freeopcua/server/"
    async with Client(url=url) as client:
        print("Connected to OPC-UA server")

        # find the namespace index
        uri = "http://jesa.machine1"
        idx = await client.get_namespace_index(uri)

        # browse to Machine1 object
        root = client.nodes.objects
        machine_obj = await root.get_child([f"{idx}:Machine1"])

        for _ in range(10):  # read 10 snapshots
            values = {}
            for ch in CHANNEL_NAMES:
                node = await machine_obj.get_child([f"{idx}:{ch}"])
                values[ch] = await node.read_value()
            print(values)
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())