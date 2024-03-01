"""Simple version control system that can be used in application versioning"""

__author__ = "Ivo Žitník"


class VersionControl:
    """
    Class for handling version control of the application

    Parameters:
        version_file (str): Custom path and name of the version file
    """

    def __init__(self, version_file: str = ".version") -> None:
        self.version_file: str = version_file
        self.ver_content: dict[str, str]

        self._get_version_file()

    def _get_version_file(self) -> None:
        """
        Gets content of .version file that is used for storing version info

        ** Beware that it erases current ver_content **
        """
        self.ver_content = {}
        key: str
        value: str
        try:
            with open(".version", "r", encoding="utf-8") as f:
                keypairs_str: list[str] = f.read().split(";")
                # Loads keys from .version content
                for keypair in keypairs_str:
                    if keypair == "":
                        continue
                    if "=" not in keypair:
                        print(
                            f"Invalid keypair '{keypair}' in .version file, skipping..."
                        )
                        continue
                    key, value = keypair.split("=")
                    self.ver_content[key] = value
        except FileNotFoundError:
            self._set_version_file({})

    def _set_version_file(self, new_content: dict[str, str]) -> None:
        """
        Sets content of .version file that is used for storing version info

        Parameters:
            new_content (dict[str, str]): New content to set
        """
        with open(".version", "w", encoding="utf-8") as f:
            f.write("")
            for key, value in new_content.items():
                f.write(f"{key}={value};")

    def update(self, key: str, new_value: str | None) -> None:
        """
        Updates the version file with a new key/value pair

        Parameters:
            key (str): Key to update, if set to None removes the key
            new_value (str): New value to set
        """
        if new_value is None:
            self.ver_content.pop(key)
        else:
            self.ver_content[key] = new_value

    def get(self, key: str) -> str | None:
        """
        Gets the value of the given key

        Parameters:
            key (str): Key to get value of

        Returns:
            str | None: Value of the given key or None if it doesn't exist
        """
        return self.ver_content.get(key, None)

    def save(self) -> None:
        """
        Saves the version file
        """
        self._set_version_file(self.ver_content)

    def compare(self, key: str, value: str) -> bool:
        """
        Compares the given key and value to the version file

        Parameters:
            key (str): Key to compare
            value (str): Value to compare

        Returns:
            bool: True if the key and value match, False if not
        """
        return self.ver_content.get(key, None) == value


verControl = VersionControl()
