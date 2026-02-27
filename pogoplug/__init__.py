import functools
import json
import os
from configparser import ConfigParser
from optparse import OptionParser
from typing import Any

import requests


class PogoplugError(IOError):
    pass


class Connection:
    base_url = "http://service.pogoplug.com/svc/api/json/"

    def __init__(self, email_or_valtoken: str, password: str | None = None):
        self.valtoken: str | None = None
        self._drives: list[Directory] | None = None
        if password:
            result = self.invoke("loginUser", {"email": email_or_valtoken, "password": password})
            if isinstance(result, dict):
                self.valtoken = result.get("valtoken")
        else:
            self.valtoken = email_or_valtoken
        self.user = self.getUser()

    def __getattr__(self, attname: str) -> Any:
        # Avoid recursion for methods/attributes that exist or are dunder methods
        if attname.startswith("__"):
            raise AttributeError(attname)

        if attname in self.__class__.__dict__:
            return self.__class__.__dict__[attname]
        return functools.partial(self.invoke, attname)

    def invoke(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        if not params:
            params = {}
        if self.valtoken:
            params["valtoken"] = self.valtoken

        # Replacement for restclient.rest_invoke
        try:
            # Pogoplug API likely used GET or POST.
            # Assuming GET for simplicity or trying to match legacy behavior
            resp = requests.get(self.base_url + fn, params=params)
            resp.raise_for_status()
            response_text = resp.text
        except requests.RequestException as e:
            raise PogoplugError(f"Network error: {e}") from e

        # The original code handled single quotes in JSON manually?
        response_text = response_text.replace("'", '"')

        try:
            response = json.loads(response_text)
        except json.JSONDecodeError:
            return response_text  # return raw string if not json?

        if isinstance(response, dict) and "HB-EXCEPTION" in response:
            raise PogoplugError((
                response["HB-EXCEPTION"]["ecode"],
                response["HB-EXCEPTION"]["message"]
            ))
        return response

    @property
    def drives(self) -> list["Directory"]:
        if not self._drives:
            services_resp = self.listServices()
            if isinstance(services_resp, dict) and "services" in services_resp:
                self._drives = [
                    Directory(self, service["deviceid"], service["serviceid"], service)
                    for service in services_resp["services"]
                ]
            else:
                self._drives = []
        return self._drives


class PogoObject(dict):
    def __init__(self, connection: Connection, json_dict: dict[str, Any]):
        super().__init__(json_dict)
        self.connection = connection
        self.flush()

    def __getattr__(self, attname: str) -> Any:
        if attname.startswith("__"):
            raise AttributeError(attname)
        return functools.partial(self.invoke, attname)

    def invoke(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        # Base implementation just calls connection invoke?
        return self.connection.invoke(fn, params)

    def flush(self) -> None:
        pass


class BaseFile(PogoObject):
    def __init__(self, connection: Connection, deviceid: str, serviceid: str, json_dict: dict[str, Any]):
        super().__init__(connection, json_dict)
        self.deviceid = deviceid
        self.serviceid = serviceid
        self.fileid = self.get("fileid")
        self.flush()

    def invoke(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        if not params:
            params = {}
        params["deviceid"] = self.deviceid
        params["serviceid"] = self.serviceid
        if self.fileid:
            params["fileid"] = self.fileid
        return self.connection.invoke(fn, params)


class File(BaseFile):
    def update(self, fd_or_filename: Any) -> None:
        pass


class Directory(BaseFile):
    def __init__(self, connection: Connection, deviceid: str, serviceid: str, json_dict: dict[str, Any]):
        json_dict.setdefault("fileid", None)
        super().__init__(connection, deviceid, serviceid, json_dict)
        self._files: dict[str, BaseFile] | None = None

    def new_file(self) -> None:
        pass

    @property
    def files(self) -> dict[str, BaseFile]:
        if not self._files:
            self._files = {}
            # listFiles might fail or return structure that needs checking
            list_resp = self.listFiles({"parentid": self.fileid} if self.fileid else {})
            if isinstance(list_resp, dict) and "files" in list_resp:
                for file_json in list_resp["files"]:
                    # FileTypes keys are strings '0', '1'
                    ftype = str(file_json.get("type"))
                    if ftype in FileTypes:
                        klass = FileTypes[ftype]
                        file_obj = klass(self.connection, self.deviceid, self.serviceid, file_json)
                        self._files[file_json["filename"]] = file_obj
        return self._files

    def flush(self) -> None:
        self._files = None


FileTypes: dict[str, type[BaseFile]] = {"0": File, "1": Directory}


def main() -> None:
    parser = OptionParser()
    parser.add_option("--user", dest="user", help="logon as USER", metavar="USER")
    parser.add_option("-p", "--password", dest="password", help="use password PASSWORD", metavar="PASSWORD")
    parser.add_option(
        "-i",
        "--info",
        action="store_true",
        dest="print_info",
        default=False,
        help="print connection information, particularly the valtoken",
    )
    parser.add_option(
        "-u", "--update", action="store_true", dest="update", default=False, help="update stored connection information"
    )

    (options, args) = parser.parse_args()
    config = ConfigParser()
    filename = os.path.join(os.path.expanduser("~"), ".pogoplug")
    config.read(filename)
    if not config.has_section("auth"):
        config.add_section("auth")
    c = None
    if options.user and options.password:
        c = Connection(options.user, options.password)
    elif config.has_option("auth", "valtoken"):
        c = Connection(config.get("auth", "valtoken"))

    if not c or not c.user:
        print("Unable to connect to pogoplug service.")
        return

    if options.print_info:
        print(f"Valtoken {c.valtoken}")

    if options.update:
        if c.valtoken:
            config.set("auth", "valtoken", c.valtoken)
        with open(filename, "w") as f:
            config.write(f)


if __name__ == "__main__":
    main()
