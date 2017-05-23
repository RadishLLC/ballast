import unittest
from ballast import LoadBalancer
from ballast.discovery.static import StaticServerList
from ballast.rule import RoundRobinRule
from ballast.ping import Ping, DummyPing
from ballast.exception import BallastException


class _MockPing(Ping):

    def __init__(self, is_alive):
        super(_MockPing, self).__init__()
        self._is_alive = is_alive

    def is_alive(self, server):
        return self._is_alive


class RoundRobinRuleTest(unittest.TestCase):

    def test_choose_without_setting_balancer(self):
        rule = RoundRobinRule()
        self.assertRaises(BallastException, rule.choose)

    def test_equal_choice(self):

        servers = StaticServerList(['127.0.0.1', '127.0.0.2', '127.0.0.3'])
        load_balancer = LoadBalancer(servers, ping=DummyPing(), ping_on_start=False)

        # ping our servers once to set them available
        load_balancer.ping()

        rule = RoundRobinRule()
        rule.load_balancer = load_balancer

        stats = dict()

        expected_iterations = 1000

        # each should be chosen an equal number of times
        # loop a bunch to get some stats
        for i in range(expected_iterations):
            server1 = rule.choose()
            if server1 in stats:
                stats[server1] += 1
            else:
                stats[server1] = 1

            server2 = rule.choose()
            if server2 in stats:
                stats[server2] += 1
            else:
                stats[server2] = 1

            server3 = rule.choose()
            if server3 in stats:
                stats[server3] += 1
            else:
                stats[server3] = 1

        # all 3 should have been chosen the same number of times
        self.assertEqual(3, len(stats))
        for server in stats:
            self.assertEqual(expected_iterations, stats[server])

    def test_no_servers_reachable(self):

        servers = StaticServerList(['127.0.0.1', '127.0.0.2', '127.0.0.3'])
        load_balancer = LoadBalancer(servers, ping=_MockPing(False), ping_on_start=False)

        rule = RoundRobinRule()
        rule.load_balancer = load_balancer

        self.assertRaises(BallastException, rule.choose)
