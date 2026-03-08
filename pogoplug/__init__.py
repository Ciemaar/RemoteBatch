import functools
import json
import os
from configparser import ConfigParser
from optparse import OptionParser
from typing import Any

import requests


class PogoplugError(IOError):
    """Exception raised for Pogoplug API errors."""
    pass


class Connection:
    """Represents a connection to the Pogoplug API service."""

    base_url = "http://service.pogoplug.com/svc/api/json/"

    def __init__(self, email_or_valtoken: str, password: str | None = None):
        """Initialize the connection to the Pogoplug service.

        Args:
            email_or_valtoken (str): Either the user's email address or an existing validation token.
            password (str | None, optional): The user's password. Defaults to None.
        """
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
        """Dynamically invoke API methods.

        Args:
            attname (str): The name of the API method to call.

        Returns:
            Any: A partial function ready to be called with parameters.
        """
        # Avoid recursion for methods/attributes that exist or are dunder methods
        if attname.startswith("__"):
            raise AttributeError(attname)

        if attname in self.__class__.__dict__:
            return self.__class__.__dict__[attname]
        return functools.partial(self.invoke, attname)

    def invoke(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        """Invoke a specific Pogoplug API function.

        Args:
            fn (str): The API function name.
            params (dict[str, Any] | None, optional): The parameters to pass to the function. Defaults to None.

        Raises:
            PogoplugError: If a network error occurs or the API returns an exception block.

        Returns:
            Any: The JSON-decoded response from the API, or the raw text if parsing fails.
        """
        if not params:
            params = {}
        if self.valtoken:
            params["valtoken"] = self.valtoken

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
        """Retrieve the list of drives associated with the user.

        Returns:
            list[Directory]: A list of Directory objects representing the root drives.
        """
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
    """Base class for objects returned by the Pogoplug API, acting as a dictionary."""

    def __init__(self, connection: Connection, json_dict: dict[str, Any]):
        """Initialize the PogoObject.

        Args:
            connection (Connection): The associated Pogoplug connection.
            json_dict (dict[str, Any]): The initial dictionary data.
        """
        super().__init__(json_dict)
        self.connection = connection
        self.flush()

    def __getattr__(self, attname: str) -> Any:
        """Dynamically invoke API methods associated with this object.

        Args:
            attname (str): The name of the API method.

        Returns:
            Any: A partial function to invoke the method.
        """
        if attname.startswith("__"):
            raise AttributeError(attname)
        return functools.partial(self.invoke, attname)

    def invoke(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        """Invoke an API function using the object's connection context.

        Args:
            fn (str): The API function name.
            params (dict[str, Any] | None, optional): The API parameters. Defaults to None.

        Returns:
            Any: The API response.
        """
        return self.connection.invoke(fn, params)

    def flush(self) -> None:
        """Clear any cached data for the object."""
        pass


class BaseFile(PogoObject):
    """Represents a file or directory on a Pogoplug device."""

    def __init__(self, connection: Connection, deviceid: str, serviceid: str, json_dict: dict[str, Any]):
        """Initialize the BaseFile object.

        Args:
            connection (Connection): The associated API connection.
            deviceid (str): The device ID where the file resides.
            serviceid (str): The service ID providing access to the file.
            json_dict (dict[str, Any]): The dictionary containing file data.
        """
        super().__init__(connection, json_dict)
        self.deviceid = deviceid
        self.serviceid = serviceid
        self.fileid = self.get("fileid")
        self.flush()

    def invoke(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        """Invoke an API function with contextual parameters specific to the file.

        Args:
            fn (str): The API function name.
            params (dict[str, Any] | None, optional): Additional parameters. Defaults to None.

        Returns:
            Any: The API response.
        """
        if not params:
            params = {}
        params["deviceid"] = self.deviceid
        params["serviceid"] = self.serviceid
        if self.fileid:
            params["fileid"] = self.fileid
        return self.connection.invoke(fn, params)


class File(BaseFile):
    """Represents a standard file on a Pogoplug device."""

    def update(self, fd_or_filename: Any) -> None:
        """Update the file contents.

        Args:
            fd_or_filename (Any): The file descriptor or filename containing new data.
        """
        pass


class Directory(BaseFile):
    """Represents a directory on a Pogoplug device."""

    def __init__(self, connection: Connection, deviceid: str, serviceid: str, json_dict: dict[str, Any]):
        """Initialize the Directory object.

        Args:
            connection (Connection): The associated API connection.
            deviceid (str): The device ID.
            serviceid (str): The service ID.
            json_dict (dict[str, Any]): Dictionary data for the directory.
        """
        json_dict.setdefault("fileid", None)
        super().__init__(connection, deviceid, serviceid, json_dict)
        self._files: dict[str, BaseFile] | None = None

    def new_file(self) -> None:
        """Create a new file within the directory."""
        pass

    @property
    def files(self) -> dict[str, BaseFile]:
        """List files contained within this directory.

        Returns:
            dict[str, BaseFile]: A dictionary mapping filenames to file objects.
        """
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
        """Clear the cached list of files."""
        self._files = None


FileTypes: dict[str, type[BaseFile]] = {"0": File, "1": Directory}


def main() -> None:
    """Command-line entry point for Pogoplug utilities."""
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
