#!/bin/env python3
import sys
import time
from argparse import ArgumentParser
from typing import Any

from funcx.sdk.client import FuncXClient
from funcx.sdk.executor import FuncXExecutor

_MY_ENDPOINT_ID = "4877c629-0671-4bc9-8146-9ffa813d1ec3"

_ADD_RECORD_FUNCX_UUID = "76093527-1c17-459e-ace8-d9ff10235807"


def add_func(a: int, b: int) -> int:
    print("add me")
    return a + b


def add_braid_records(*args, **kwargs):
    import os

    from braid_db import BraidDB, BraidRecord

    DB_FILE = "~/funcx-braid.db"

    DB = BraidDB(os.path.expanduser(DB_FILE))
    DB.create()
    record_params = {}
    if len(args) > 0:
        if isinstance(args[0], dict):
            record_params = args[0]
        else:
            print(f"Got unexpected input argument: {args[0]}")
    record_params.update(kwargs)
    if "name" not in record_params:
        raise ValueError("Input must contain a name")
    rec = BraidRecord(DB, name=record_params["name"])
    record_id = rec.record_id
    if uris := record_params.get("uris") is not None:
        if isinstance(uris, list):
            for uri in uris:
                if isinstance(uri, str):
                    rec.add_uri(uri)
    return record_id


def _run_and_wait_funcx(
    fxc: FuncXClient, *args, function_id: str, endpoint_id: str, **kwargs
) -> Any:
    task_id = fxc.run(
        *args, function_id=function_id, endpoint_id=endpoint_id, **kwargs
    )
    task_status = fxc.get_task(task_id)
    while task_status.get("pending", False):
        time.sleep(1.0)
        task_status = fxc.get_task(task_id)
    if task_status.get("status") == "failed":
        exception = task_status.get("exception")
        if exception is not None:
            exception.reraise()
    return task_status.get("result")


def register_functions():
    fxc = FuncXClient()
    functions = [add_braid_records]
    now = int(time.time())
    for function in functions:
        funcx_uuid = fxc.register_function(
            function,
            f"braid_db_{function.__name__}_v{now}",
            searchable=True,
        )
        print(
            f"Added function {function.__name__} as "
            f"braid_db_{function.__name__}_v{now} with uuid {funcx_uuid}"
        )


def funcx_add_record():
    parser = ArgumentParser()
    parser.add_argument("--endpoint-id", default=_MY_ENDPOINT_ID, type=str)
    parser.add_argument(
        "--function-id", default=_ADD_RECORD_FUNCX_UUID, type=str
    )
    parser.add_argument("record_name")
    args = parser.parse_args()

    fxc = FuncXClient()
    result = _run_and_wait_funcx(
        fxc,
        name=args.record_name,
        function_id=args.function_id,
        endpoint_id=args.endpoint_id,
    )
    print(f"Added record with id {result}")


def main():
    register_functions()
    fxc = FuncXClient()
    fx = FuncXExecutor(fxc)
    # search_result = fxc.search_endpoint("default")
    # print(f"DEBUG {(search_result)=}")

    """
    func_uuid = fxc.register_function(add_func)
    result = _run_and_wait_funcx(
        fxc, 1, 2, function_id=func_uuid, endpoint_id=_MY_ENDPOINT_ID
    )
    print(f"Add Result: {result}")
    """

    """
    braid_fn_uuid = fxc.register_function(add_braid_records)
    result = _run_and_wait_funcx(
        fxc,
        function_id=braid_fn_uuid,
        endpoint_id=_MY_ENDPOINT_ID,
        name="funcx_record",
    )
"""
    future = fx.submit(
        add_braid_records, name="funcx_record", endpoint_id=_MY_ENDPOINT_ID
    )
    result = future.result()
    print(f"Add Record Result: {result}")
    print("Are we done???")
    sys.exit(0)


if __name__ == "__main__":
    main()


"""
from funcx.sdk.client import FuncXClient


def double(x):
    return x * 2

count = 10

futures = []
for i in range(count):
    future = fx.submit(double, i, endpoint_id=tutorial_endpoint)
    futures.append(future)

for fu in futures:
    print(fu.result())
"""
