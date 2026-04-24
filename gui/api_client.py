# Module: gui.api_client
# Description: Client for communicating with the FastAPI backend

# Built-ins
import requests
import logging
import typing

# Dataclass

# Configure logger
logger = logging.getLogger(__name__)


# Client to communicate with the server
class APIClient:

    # Constructor
    def __init__(self, base_url: str = "http://localhost:8000"):

        self.base_URL = base_url
        self.session = requests.Session()
        self.user_id: typing.Optional[str] = None
        self.project_uid: typing.Optional[str] = None
        self.last_error: typing.Optional[str] = None

    def login(self, uid: str) -> bool:
        """
        Log in a user with the server.

        Args:
            uid: The unique user ID.

        Returns:
            True if login was successful, False otherwise.
        """

        # Construct the login URL
        url = f"{self.base_URL}/lan/login"

        # Log in the user (or register if not already registered)
        try:
            response = self.session.post(
                url,
                params={"token": uid},
                timeout=10.0,
            )

            # 200 = User successfully logged in
            if response.status_code == 200:
                self.user_id = uid
                self.last_error = None
                logger.info(f"User {uid} logged in successfully")
                return True

            # 422 = User already exists (login rejected)
            elif response.status_code == 422:
                detail = response.json().get("detail", f"User {uid} already exists")
                self.last_error = detail
                logger.error(detail)
                return False

            # Other status codes are errors
            else:
                try:
                    self.last_error = response.json().get("detail", response.text)
                except ValueError:
                    self.last_error = response.text
                response.raise_for_status()
                return False

        except requests.RequestException as e:
            self.last_error = str(e)
            logger.error(f"Failed to connect to server at {self.base_URL}: {e}")
            return False

    def list_projects(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Retrieve the list of projects for the registered user.

        Returns:
            Dictionary with project information, or None if request failed.
        """
        if not self.user_id:
            logger.error("User not logged in. Call login first.")
            return None

        try:
            response = self.session.get(
                f"{self.base_URL}/projects/list",
                headers={"X-Client-ID": self.user_id},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to list projects: {e}")
            return None

    def create_project(
        self, project_uid: str
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Create a blank project by its UID.

        Args:
            project_uid: The unique identifier of the project.

        Returns:
            Dictionary with project data, or None if request failed.
        """
        if not self.user_id:
            logger.error("User not logged in. Call login first.")
            return None

        try:
            response = self.session.post(
                f"{self.base_URL}/projects/",
                json={"name": project_uid},
                headers={"X-Client-ID": self.user_id},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create project {project_uid}: {e}")
            return None

    def save_blueprint(
        self, project_uid: str
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Persist the live blueprint back into the project HDF5."""
        if not self.user_id:
            logger.error("User not logged in. Call login first.")
            return None

        try:
            response = self.session.post(
                f"{self.base_URL}/projects/{project_uid}/blueprint",
                headers={"X-Client-ID": self.user_id},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to save blueprint for {project_uid}: {e}")
            return None

    def create_instance(
        self, project_uid: str, payload: typing.Dict[str, typing.Any]
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Create a new instance in the active project."""
        if not self.user_id:
            logger.error("User not logged in. Call login first.")
            return None

        try:
            response = self.session.post(
                f"{self.base_URL}/projects/{project_uid}/instances",
                json=payload,
                headers={"X-Client-ID": self.user_id},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create instance in {project_uid}: {e}")
            return None

    def open_project(
        self, project_uid: str
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Open a project by its UID.

        Args:
            project_uid: The unique identifier of the project.

        Returns:
            Dictionary with project data, or None if request failed.
        """
        if not self.user_id:
            logger.error("User not logged in. Call login first.")
            return None

        try:
            response = self.session.post(
                f"{self.base_URL}/projects/{project_uid}/open",
                headers={"X-Client-ID": self.user_id},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to open project {project_uid}: {e}")
            return None

    def delete_project(
        self, project_uid: str
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Delete a project by its UID."""
        if not self.user_id:
            logger.error("User not logged in. Call login first.")
            return None

        try:
            response = self.session.delete(
                f"{self.base_URL}/projects/{project_uid}",
                headers={"X-Client-ID": self.user_id},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to delete project {project_uid}: {e}")
            return None

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
