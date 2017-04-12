import unittest
import mock
import socket
import time
from balast import Server
from balast.discovery.static import StaticServerList
from balast.ping import (
    Ping,
    DummyPing,
    SocketPing,
    UrlPing,
    SerialPingStrategy,
    ThreadPoolPingStrategy,
    MultiprocessingPoolPingStrategy,
    GeventPingStrategy
)


class _MockPing(Ping):

    def __init__(self, is_alive=True, delay=0):
        super(_MockPing, self).__init__()
        self._is_alive = is_alive
        self._delay = delay

    def is_alive(self, server):
        time.sleep(self._delay)
        return self._is_alive


class DummyPingTest(unittest.TestCase):

    def test_is_dummy_alive(self):

        ping = DummyPing()
        server = Server('127.0.0.1', 80)

        # dummy ping assumes everything is alive
        self.assertTrue(ping.is_alive(server))


class SocketPingTest(unittest.TestCase):

    @mock.patch('balast.ping.socket.socket')
    def test_is_socket_alive_success(self, mock_socket):

        expected_ping_time = 3

        ping = SocketPing()
        ping.max_ping_time = expected_ping_time

        server = Server('127.0.0.1', 80)

        # ping our server via (mock) TCP socket
        self.assertTrue(ping.is_alive(server))
        mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)

        # verify the socket received the expected values
        s = mock_socket.return_value
        s.settimeout.assert_called_with(expected_ping_time)
        s.connect.assert_called_with(('127.0.0.1', 80))

    @mock.patch('balast.ping.socket.socket.connect')
    def test_is_socket_alive_fails(self, mock_connect):

        mock_connect.side_effect = Exception('mock exception')
        ping = SocketPing()

        server = Server('127.0.0.1', 80)

        # ping our server via (mock) TCP socket
        self.assertFalse(ping.is_alive(server))


class UrlPingTest(unittest.TestCase):

    @mock.patch('balast.ping.requests.get')
    def test_is_url_alive_success(self, mock_get_request):

        ping = UrlPing()
        server = Server('127.0.0.1', 80)
        expected_http_address = 'http://127.0.0.1:80'
        expected_https_address = 'https://127.0.0.1:80'

        # ping our server via (mock) HTTP request
        self.assertTrue(ping.is_alive(server))
        mock_get_request.assert_called_with(expected_http_address)

        # now do the same thing with https
        ping = UrlPing(is_secure=True)

        # ping our server via (mock) HTTP request
        self.assertTrue(ping.is_alive(server))
        mock_get_request.assert_called_with(expected_https_address)

    @mock.patch('balast.ping.requests.get')
    def test_is_url_alive_fails(self, mock_get_request):

        mock_get_request.side_effect = Exception('mock exception')
        ping = UrlPing()

        server = Server('127.0.0.1', 80)

        # ping our server via (mock) TCP socket
        self.assertFalse(ping.is_alive(server))


class SerialPingStrategyTest(unittest.TestCase):

    def test_serial_ping(self):

        servers = StaticServerList(['127.0.0.1', '127.0.0.2', '127.0.0.3'])
        ping = _MockPing(delay=0.4)
        strategy = SerialPingStrategy()

        start_time = time.time()
        results = strategy.ping(ping, servers)
        end_time = time.time() - start_time

        # with a delay of 0.4, the strategy
        # should have taken a bit more than 1 second
        self.assertGreaterEqual(end_time, 1)

        # verify the results
        self.assertEqual(3, len(results))

        for server in results:
            self.assertTrue(server.is_alive)


class ThreadPoolPingStrategyTest(unittest.TestCase):

    def test_thread_pool_ping(self):

        servers = StaticServerList([])
        for i in range(100):
            servers.add_server('127.0.0.%s' % i)

        ping = _MockPing(delay=0.4)
        strategy = ThreadPoolPingStrategy()

        start_time = time.time()
        results = strategy.ping(ping, servers)
        end_time = time.time() - start_time

        # with a delay of 0.4, and 100 threads,
        # the strategy should still not have taken
        # much more than 0.4 seconds
        self.assertGreaterEqual(end_time, 0.4)
        self.assertLessEqual(end_time, 0.6)

        # verify the results
        self.assertEqual(100, len(results))

        for server in results:
            self.assertTrue(server.is_alive)


class MultiprocessingPoolPingStrategyTest(unittest.TestCase):

    def test_multiprocessing_pool_ping(self):

        servers = StaticServerList([])
        for i in range(10):
            servers.add_server('127.0.0.%s' % i)

        ping = _MockPing(delay=0.4)
        strategy = MultiprocessingPoolPingStrategy()

        start_time = time.time()
        results = strategy.ping(ping, servers)
        end_time = time.time() - start_time

        # with a delay of 0.4, and 100 processes,
        # the strategy should still not have taken
        # much more than a second
        # a large number of processes is actually a lot
        # slower than a large number of threads
        self.assertGreaterEqual(end_time, 0.4)
        self.assertLessEqual(end_time, 1)

        # verify the results
        self.assertEqual(10, len(results))

        for server in results:
            self.assertTrue(server.is_alive)


class GeventPingStrategyTest(unittest.TestCase):

    def test_gevent_pool_ping(self):

        servers = StaticServerList([])
        for i in range(10):
            servers.add_server('127.0.0.%s' % i)

        ping = _MockPing(delay=0.1)
        strategy = GeventPingStrategy()

        start_time = time.time()
        results = strategy.ping(ping, servers)
        end_time = time.time() - start_time

        # since gevent (in our non-evented vacuum) in this
        # case ends up executing serially, the strategy
        # should take about a second
        self.assertGreaterEqual(end_time, 1)
        self.assertLessEqual(end_time, 2)

        # verify the results
        self.assertEqual(10, len(results))

        for server in results:
            self.assertTrue(server.is_alive)
