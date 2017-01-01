import restclient

try:
    import json
except ImportError:
    import anyjson as json
import functools


class PogoplugError(IOError): pass


class Connection(object):
    base_url = "http://service.pogoplug.com/svc/api/json/"

    def __init__(self, email_or_valtoken, password=None):
        self.valtoken = None
        self._drives = None
        if password:
            self.valtoken = self.invoke("loginUser", {"email": email_or_valtoken, "password": password})['valtoken']
        else:
            self.valtoken = email_or_valtoken
        self.user = self.getUser()

    def __getattr__(self, attname):
        if attname in self.__class__.__dict__:
            return self.__class__.__dict__[attname]
        return functools.partial(self.invoke, attname)

    def invoke(self, fn, params=None):
        if not params:
            params = {}
        if self.valtoken:
            params["valtoken"] = self.valtoken
        response = restclient.rest_invoke(self.base_url + fn, params=params)
        response = response.replace("\'",
                                    '"')  # anyjson can't handle this probably should get a different json library
        if isinstance(response, str):
            response = json.loads(response)
            if 'HB-EXCEPTION' in response:
                raise PogoplugError((response['HB-EXCEPTION']['ecode'], response['HB-EXCEPTION']['message']))
            return response

    @property
    def drives(self):
        if not self._drives:
            self._drives = [Directory(self, service['deviceid'], service['serviceid'], service) for service in
                            self.listServices()['services']]
        return self._drives
        # @drives.setter
        # def setdrives(self,value):
        #    raise Exception


class PogoObject(dict):
    def __init__(self, connection, json_dict):
        super(PogoObject, self).__init__(json_dict)
        self.connection = connection
        self.flush()

    def __getattr__(self, attname):
        return functools.partial(self.invoke, attname)

    def flush(self):
        pass


class BaseFile(PogoObject):
    def __init__(self, connection, deviceid, serviceid, json_dict):
        super(BaseFile, self).__init__(connection, json_dict)
        self.deviceid = deviceid
        self.serviceid = serviceid
        self.fileid = self['fileid']
        self.flush()

    def invoke(self, fn, params=None):
        if not params:
            params = {}
        params["deviceid"] = self.deviceid
        params["serviceid"] = self.serviceid
        if self.fileid:
            params["fileid"] = self.fileid
        return self.connection.invoke(fn, params)


class File(BaseFile):
    def update(self, fd_or_filename):
        pass


class Directory(BaseFile):
    def __init__(self, connection, deviceid, serviceid, json_dict):
        json_dict.setdefault('fileid', None)
        super(Directory, self).__init__(connection, deviceid, serviceid, json_dict)

    def new_file(self):
        pass

    @property
    def files(self):
        if not self._files:
            self._files = {}
            for file_json in self.listFiles({'parentid': self.fileid} if self.fileid else {})['files']:
                if file_json['type'] in FileTypes:
                    klass = FileTypes[file_json['type']]
                    file = klass(self.connection, self.deviceid, self.serviceid, file_json)
                    self._files[file_json['filename']] = file
        return self._files

    def flush(self):
        self._files = None


FileTypes = {'0': File, '1': Directory}


def main():
    import os.path
    from optparse import OptionParser
    from ConfigParser import ConfigParser

    parser = OptionParser()
    parser.add_option("--user", dest="user",
                      help="logon as USER", metavar="USER")
    parser.add_option("-p", "--password", dest="password",
                      help="use password PASSWORD", metavar="PASSWORD")
    parser.add_option("-i", "--info",
                      action="store_true", dest="print_info", default=False,
                      help="print connection information, particularly the valtoken")
    parser.add_option("-u", "--update",
                      action="store_true", dest="update", default=False,
                      help="update stored connection information")

    (options, args) = parser.parse_args()
    config = ConfigParser()
    filename = os.path.join(os.path.expanduser("~"), ".pogoplug")
    config.read(filename)
    if not config.has_section("auth"):
        config.add_section("auth")
    c = None
    if options.user and options.password:
        c = Connection(options.user, options.password)
    elif config.has_option('auth', 'valtoken'):
        c = Connection(config.get('valtoken', 'auth'))

    if not c or not c.user:
        print "Unable to connect to pogoplug service."
        return

    if options.print_info:
        print "Valtoken {0}".format(c.valtoken)

    if options.update:
        config.set('auth', 'valtoken', c.valtoken)
        config.write(open(filename, "w"))


if __name__ == "__main__":
    main()
