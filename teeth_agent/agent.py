"""
Copyright 2013 Rackspace, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import uuid

import pkg_resources
import simplejson as json
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
from twisted.python import log

from teeth_agent.protocol import TeethAgentProtocol

AGENT_VERSION = '0.1-dev'


class AgentClientHandler(TeethAgentProtocol):
    def __init__(self):
        TeethAgentProtocol.__init__(self, json.JSONEncoder())

    def connectionMade(self):
        def _response(result):
            log.msg('Handshake successful', connection_id=result['id'])

        self.send_command('handshake', 'a:b:c:d', AGENT_VERSION).addCallback(_response)


class AgentClientFactory(ReconnectingClientFactory):
    protocol = AgentClientHandler
    initialDelay = 1.0
    maxDelay = 120


    def buildProtocol(self, addr):
        self.resetDelay()
        return self.protocol()

    def clientConnectionFailed(self, connector, reason):
        log.err('Failed to connect, re-trying', delay=self.delay)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        log.err('Lost connection, re-connecting', delay=self.delay)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)


class TeethAgent(object):
    client_factory = AgentClientFactory()

    def start(self, host, port):
        reactor.connectTCP(host, port, self.client_factory)