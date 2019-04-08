from mcstatus import MinecraftServer
from mcstatus.pinger import ServerPinger, PingResponse
from mcstatus.querier import ServerQuerier, QueryResponse
from mcstatus.protocol.connection import TCPSocketConnection, UDPSocketConnection
import dns.resolver


class OGMinecraftServer(MinecraftServer):
    def __init__(self, host, port):
        super().__init__(host, port)

    def status(self, retries=3, **kwargs):
        connection = TCPSocketConnection((self.host, self.port))
        exception = None
        for attempt in range(retries):
            try:
                pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
                pinger.handshake()
                result = pinger.read_status()
                result.latency = pinger.test_ping()
                return result
            except Exception as e:
                exception = e
        else:
            raise exception

    def query(self, retries=3):
        exception = None
        host = self.host
        try:
            answers = dns.resolver.query(host, "A")
            if len(answers):
                answer = answers[0]
                host = str(answer).rstrip(".")
        except Exception as e:
            pass
        for attempt in range(retries):
            try:
                connection = UDPSocketConnection((host, self.port))
                querier = ServerQuerier(connection)
                querier.handshake()
                q = querier.read_query()
                qq = OGQueryResponse(q.raw, q.players.names)

            except Exception as e:
                exception = e
        else:
            raise exception


class OGQueryResponse(QueryResponse):
    class Players(QueryResponse.Players):
        def __init__(self, online, max, names):
            super().__init__(online, max, names)

        def __repr__(self):
            return {'online': self.online, 'max': self.max, 'names': self.names}

        def __str__(self):
            return ", ".join(self.names)

    class Software(QueryResponse.Software):
        def __init__(self, version, plugins):
            super().__init__(version, plugins)

        def __repr__(self):
            return {'version': self.version, 'brand': self.brand, 'plugins': self.plugins}

        def __str__(self):
            return self.brand + self.version

    def __init__(self, raw, players):
        super().__init__(raw, players)

    def __repr__(self):
        return {}

    def __str__(self):
        return ''
