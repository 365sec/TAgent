from bson import BSON, InvalidBSON
from bson.codec_options import CodecOptions
from bson.binary import STANDARD
from uuid import UUID
from __init__ import __version__

from TAgentEnums import SessionTypeEnum
    
class Command(object):

    def __init__(self):
        pass

    def to_string(self):
        pass

    def to_bson(self):
        pass

    def is_idm_event(self):
        return False


class AgentDateCommand(Command):

    def __init__(self, tzone, agent_date):
        super(AgentDateCommand, self).__init__()
        self.tzone = tzone
        self.agent_date = agent_date

    def to_bson(self):
        data = {'agent-date': {'timestamp': float(self.agent_date),
                        'tzone': float(self.tzone)}}
        return BSON.encode(data)

    def to_string(self):
        return 'agent-date agent_date="%s" tzone="%s"\n' % (self.agent_date, self.tzone)
    
    
class AgentServerConnectionMessage(Command):
    MSG = 'connect id="{0}" type="sensor" version="' + __version__ + '" sensor_id="{1}"\n'

    def __init__(self, sequence_id, sensor_id):
        super(AgentServerConnectionMessage, self).__init__()
        self.sequence_id = sequence_id
        self.sensor_id = sensor_id

    def to_bson(self):
        print self.sensor_id
        return BSON.encode({'connect': {'version': __version__,
                     'id': int(self.sequence_id),
                     'sensor_id': self.sensor_id,
                     'type': int(SessionTypeEnum.SESSION_TYPE_SENSOR)}}, codec_options=CodecOptions(uuid_representation=STANDARD))

    def to_string(self):
        return AgentServerConnectionMessage.MSG.format(self.sequence_id, self.sensor_id)
    

class AgentFrameworkConnectionMessage(Command):
    MSG = 'control id="{0}" action="connect" version="' + __version__ + ' sensor_id="{1}" \n'

    def __init__(self, connection_id, sensor_id):
        super(AgentFrameworkConnectionMessage, self).__init__()
        self.connection_id = connection_id
        self.sensor_id = sensor_id

    def to_bson(self):
        return self.to_string()

    def to_string(self):
        return AgentFrameworkConnectionMessage.MSG.format(self.connection_id, self.sensor_id)
    
    
class AgentServerCommandPong(Command):

    def __init__(self, timestamp = None):
        super(AgentServerCommandPong, self).__init__()
        self.timestamp = timestamp

    def to_bson(self):
        return BSON.encode({'pong': {'timestamp': self.timestamp}})

    def to_string(self):
        return 'pong\n'

class AgentServerCommandExc(Command):

    def __init__(self, timestamp = None):
        super(AgentServerCommandExc, self).__init__()
        self.timestamp = timestamp

    def to_bson(self):
        return BSON.encode({'exc_cmd_ok': {'info': "self.timestamp"}})

    def to_string(self):
        return 'pong\n'

class AgentFrameworkCommandPong(Command):

    def __init__(self):
        super(AgentFrameworkCommandPong, self).__init__()

    def to_bson(self):
        return self.to_string()

    def to_string(self):
        return 'pong\n'
    

class AgentFrameworkCommand(Command):

    def __init__(self, command):
        super(AgentFrameworkCommand, self).__init__()
        self.command = command

    def to_bson(self):
        return self.to_string()

    def to_string(self):
        return self.command