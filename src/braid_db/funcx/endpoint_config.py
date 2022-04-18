import os

from funcx_endpoint.endpoint.utils.config import Config
from funcx_endpoint.executors import HighThroughputExecutor
from parsl.providers import LocalProvider

path_to_activate = os.path.abspath(venv_activate)  # noqa: F821

config = Config(
    executors=[
        HighThroughputExecutor(
            provider=LocalProvider(
                init_blocks=1,
                min_blocks=0,
                max_blocks=1,
                worker_init=f"source {path_to_activate}",
            ),
        )
    ],
    funcx_service_address="https://api2.funcx.org/v2",
)

# For now, visible_to must be a list of URNs for globus auth users or groups,
# e.g.: urn:globus:auth:identity:{user_uuid} urn:globus:groups:id:{group_uuid}
meta = {
    "name": "default",
    "description": "",
    "organization": "",
    "department": "",
    "public": False,
    "visible_to": [],
}
