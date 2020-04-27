import asyncio

import regex


# host = ''
# port = 22242


class SrcdsLoggingProtocol(asyncio.DatagramProtocol):

    def __init__(self, cb1, cb2):
        self.callback1 = cb1
        self.callback2 = cb2

    # noinspection PyAttributeOutsideInit
    def connection_made(self, transport):
        print("connected!")
        self.transport = transport

    def datagram_received(self, packet, addr):
        message = self.parse(packet)
        self.callback1(self.callback2(message))

    @staticmethod
    def parse(packet: bytes):
        packet_len = len(packet)

        if packet_len < 7:
            raise Exception("Packet is too short")

        for i in range(4):
            if packet[i] != int(0xFF):
                raise Exception('invalid header value')

        if packet[packet_len - 1] != int(0x00):
            raise Exception('invalid footer value')

        ptype, offset, footer = packet[4], 5, 2

        if packet[packet_len - 2] != int(0x0a):
            footer = 1

        if ptype != int(0x52):
            raise Exception('invalid packet type ' + hex(ptype))

        message = packet[offset:(packet_len - footer)]

        return message.decode('utf-8').strip()


class Crap:
    def __init__(self, log):
        self.log = log
        self.log_lock = asyncio.Lock()

    async def _log_callback(self, message):
        async with self.log_lock:
            self.log.append(message)
            # print(f"Log state: {self.log}")

    async def chat_from_server_to_discord(self):
        connections = regex.compile(
            r"""(?<=: ")([\w\s]+)(?:<\d><STEAM_0:\d:\d+><.*>") (?:((?:dis)?connected),? (?|address "(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})|(\(reason ".+"?)))""")
        chat = regex.compile(
            r"""(?<=: ")([\w\s]+)(?:<\d><(?:STEAM_0:\d:\d+|Console)><.*>") (|say|say_team) "(.*)\"""")
        while True:
            try:
                lines = []
                async with self.log_lock:
                    if self.log:
                        lines = self.log
                        self.log = []
                msgs = list()
                for line in lines:
                    raw_connectionmsg = regex.findall(connections, line)
                    raw_chatmsg = regex.findall(chat, line)

                    if raw_chatmsg:
                        msgs.append(f"{'[TEAM] ' if raw_chatmsg[0][1] == 'say_team' else ''}{raw_chatmsg[0][0]}: {raw_chatmsg[0][2]}")
                    elif raw_connectionmsg:
                        # putting this here prevents people for just typing out the connection format and faking a connection
                        msgs.append(f"`{' '.join(raw_connectionmsg[0])}`")
                    else:
                        continue
                # if msgs:
                #     x = "\n".join(msgs)
                #     await self.bot.chat_channel.send(f'{x}')
                for msg in msgs:
                    print(f"test | {msg}")
                continue
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(.75)

    async def main(self):
        print("Starting UDP server")
        # host = ''
        host = '192.168.25.184'
        port = 22242

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SrcdsLoggingProtocol(asyncio.create_task, self._log_callback),
            local_addr=(host, port))
        await loop.create_task(self.chat_from_server_to_discord())

        try:
            await asyncio.sleep(30)  # Serve for 30 seconds
        finally:
            transport.close()


c = Crap([])

asyncio.run(c.main())
