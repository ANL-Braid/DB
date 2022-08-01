#!/bin/env python3
import hashlib
import json
import sys
import time
from argparse import ArgumentParser
from os.path import expanduser
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple

from funcx.sdk.client import FuncXClient
from funcx.sdk.executor import FuncXExecutor
from funcx.serialize import FuncXSerializer

_MY_ENDPOINT_ID = "834dd614-adc1-4ed1-a620-d67c4e90a165"

_ADD_RECORD_FUNCX_UUID = "76093527-1c17-459e-ace8-d9ff10235807"

_FUNCTION_REGISTRATION_CACHE = expanduser(
    "~/.funcx_registered_functions_cache.json"
)


class CachedFunction(NamedTuple):
    funcx_uuid: str
    impl_hash: str


def load_registered_funcx_functions() -> Dict[str, CachedFunction]:
    ret_entries = {}
    try:
        with open(_FUNCTION_REGISTRATION_CACHE) as f:
            entries = json.load(f)
            for entry_name, cached_val in entries.items():
                ret_entries[entry_name] = CachedFunction(
                    funcx_uuid=cached_val[0], impl_hash=cached_val[1]
                )
            return ret_entries
    except FileNotFoundError:
        return {}


def store_registered_funcx_functions(
    funcx_functions: Dict[str, CachedFunction]
):
    try:
        with open(_FUNCTION_REGISTRATION_CACHE, "w") as f:
            json.dump(funcx_functions, f)
    except Exception as e:
        print(f"Saving function cached failed due to {e}")


def add_transfer_request(
    previous_step_record_id=None,
    transfer_input={},
    transfer_result={},
    *args,
    **kwargs,
):
    import os

    from braid_db import BraidDB, BraidRecord

    DEFAULT_DB_FILE = "~/funcx-braid.db"

    db_file = os.getenv("BRAID_DB_FILE", os.path.expanduser(DEFAULT_DB_FILE))

    DB = BraidDB(db_file)
    DB.create()
    session = DB.get_session()

    transfer_items = transfer_input.get("transfer_items", [])
    src_endpoint = transfer_input.get("source_endpoint_id")
    dest_endpoint = transfer_input.get("destination_endpoint_id")
    transfer_status = transfer_result.get("status")
    transfer_details = transfer_result.get("details", {})
    transfer_task_id = transfer_details.get("task_id")
    transfer_uri = (
        f"https://app.globus.org/activity/{transfer_task_id}/overview"
    )
    source_records = []
    dest_records = []

    transfer_record = BraidRecord(
        db=DB, name=f"Globus Transfer task {transfer_task_id}"
    )
    transfer_record.add_uri(transfer_uri)
    transfer_record.add_tag("status", transfer_status)

    if previous_step_record_id is not None:
        pred_model = DB.get_record_model_by_id(
            int(previous_step_record_id), session=session
        )
        if pred_model is not None:
            pred_rec = BraidRecord.from_orm(pred_model, db=DB)
            pred_rec.add_derivation(transfer_record)

    for transfer_item in transfer_items:
        src_path = transfer_item.get("source_path", "Unknown")
        src_name = f"Globus transfer source {src_endpoint}:{src_path}"
        src_record = BraidRecord(db=DB, name=src_path)
        src_uri = f"globustransfer://{src_endpoint}/{src_path}"
        src_record = BraidRecord(db=DB, name=src_name)
        src_record.add_uri(src_uri)
        source_records.append(src_record)
        src_record.add_derivation(transfer_record)

        dest_path = transfer_item.get("destination_path", "Unknown")
        dest_name = f"Globus transfer source {dest_endpoint}:{dest_path}"
        dest_uri = f"globustransfer://{dest_endpoint}/{dest_path}"
        dest_record = BraidRecord(db=DB, name=dest_name)
        dest_record.add_uri(dest_uri)
        dest_records.append(dest_record)
        transfer_record.add_derivation(dest_record)

    return {
        "flow_state_record_id": transfer_record.record_id,
        "input_record_ids": [s.record_id for s in source_records],
        "output_record_ids": [d.record_id for d in dest_records],
    }


def sha256_function(function: Callable) -> str:
    """
    Get the SHA256 checksum of a funcx function
    :return: sha256 hex string of a given funcx function
    """
    fxs = FuncXSerializer()
    serialized_func = fxs.serialize(function).encode()
    return hashlib.sha256(serialized_func).hexdigest()


def add_record_for_action_step(
    step_name=None,
    tags=None,
    step_result=None,
    previous_step_output=None,
    other_predecessor_record_ids=None,
    input_record_ids=None,
    inputs_from_referenced_outputs=False,
    output_record_ids=None,
    outputs_from_referenced_inputs=False,
    input_record_defs=None,
    output_record_defs=None,
    uris=None,
    **kwargs,
):
    assert tags is None or isinstance(
        tags, dict
    ), f"Value for 'tags' must be a dictionary not {tags}"
    assert uris is None or isinstance(
        uris, (str, list)
    ), f"Value for uris must be a string or a list of strings not {uris}"
    assert step_name is None or isinstance(
        step_name, str
    ), f"Got unexpected value for step_name {step_name}"

    import logging
    import os

    from braid_db import BraidDB, BraidRecord
    from braid_db.models import BraidDerivationModel

    DEFAULT_LOG_FILE = "~/funcx-braid.log"

    log_file = os.getenv(
        "BRAID_LOG_FILE", os.path.expanduser(DEFAULT_LOG_FILE)
    )

    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )

    logging.info("**************START*************")
    logging.info("Request to add record for step ")

    if kwargs:
        logging.info(f"***** Unexpected arguments: {kwargs}")

    DEFAULT_DB_FILE = "~/funcx-braid.db"

    db_file = os.getenv("BRAID_DB_FILE", os.path.expanduser(DEFAULT_DB_FILE))

    DB = BraidDB(db_file)
    DB.create()
    session = DB.get_session()

    ############################
    def extract_record_ids_from_other_provenance_step(
        previous_step_output, previous_step_field_name="flow_state_record_id"
    ):
        logging.info(
            f"Looking for record_id in field {previous_step_field_name} in "
            f"{previous_step_output}"
        )
        return_record_ids = []
        if previous_step_output is None:
            return return_record_ids
        if isinstance(previous_step_output, list):
            previous_steps = previous_step_output
        else:
            previous_steps = [previous_step_output]

        for previous_step in previous_steps:
            logging.info(f"Searching in step output {previous_step}")
            # If the input is a dict, we will assume we were provided the
            # result from a previous invocation of this same funcx-based
            # provenance recording operation. So, we navigate into the result
            # to the point where the previous step would place the record id
            if isinstance(previous_step, dict):
                previous_step = (
                    previous_step.get("details", {})
                    .get("result", [dict()])[0]
                    .get(previous_step_field_name, [])
                )
            if isinstance(previous_step, (str, int)):
                previous_step = [previous_step]
            if isinstance(previous_step, list):
                return_record_ids.extend([int(p) for p in previous_step])
        logging.info(f"Previous step lookup found records {return_record_ids}")
        return return_record_ids

    ###########################

    ###########################
    def add_record(
        name: str, uris, tags, predecessor_record_ids, derivative_record_ids
    ):
        logging.info(f"Adding record {(name, uris, predecessor_record_ids)=}")
        record = BraidRecord(db=DB, name=name)
        record_id = record.record_id
        if isinstance(uris, str):
            uris = [uris]
            if isinstance(uris, list):
                for uri in uris:
                    record.add_uri(uri, session=session)

        # If we have tags, we recurse through the values building dotted key
        # names.
        if isinstance(tags, dict):
            to_traverse = [(tags, "")]
            while to_traverse:
                vals, prefix = to_traverse.pop()
                for k, v in vals.items():
                    if isinstance(v, dict):
                        to_traverse.append((v, k + "."))
                    else:
                        record.add_tag(prefix + k, str(v), session=session)

        if isinstance(predecessor_record_ids, (int, str)):
            predecessor_record_ids = [predecessor_record_ids]

        if predecessor_record_ids is None:
            predecessor_record_ids = []

        for predecessor_record_id in set(predecessor_record_ids):
            if isinstance(predecessor_record_id, str):
                predecessor_record_id = int(predecessor_record_id)
            predecessor_record = DB.get_record_model_by_id(
                predecessor_record_id, session=session
            )
            logging.info(
                f"Adding (pred) derivation from {predecessor_record_id} "
                f"to {record_id}"
            )
            if predecessor_record is not None:
                derivation_model = BraidDerivationModel(
                    record_id=predecessor_record_id,
                    derivation=record_id,
                )
                DB.add_model(derivation_model, session=session)
            else:
                ...  # TODO: Raise some sort of exception

        if isinstance(derivative_record_ids, (int, str)):
            derivative_record_ids = [derivative_record_ids]

        if derivative_record_ids is None:
            derivative_record_ids = []

        for derivative_record_id in set(derivative_record_ids):
            if isinstance(derivative_record_id, str):
                derivative_record_id = int(derivative_record_id)
            derivative_record = DB.get_record_model_by_id(
                derivative_record_id, session=session
            )
            logging.info(
                f"Adding (dep) derivation from {record_id} to "
                f"{derivative_record_id}"
            )
            if derivative_record is not None:
                derivation_model = BraidDerivationModel(
                    record_id=record_id,
                    derivation=derivative_record_id,
                )
                DB.add_model(derivation_model, session=session)
            else:
                ...  # TODO: Raise some sort of exception

        logging.info(f"Created record with id {record.record_id}")
        return record

    ###########################

    if tags is None:
        tags = {}
    exception_str = None
    if step_result is None:
        step_result = "Not Provided"
    elif isinstance(step_result, dict):
        step_result = step_result.get("status", "Not Present in Step Results")
    tags["status"] = str(step_result)

    predecessor_record_ids = []

    if previous_step_output is not None:
        previous_step_record_ids = (
            extract_record_ids_from_other_provenance_step(previous_step_output)
        )
        predecessor_record_ids.extend(previous_step_record_ids)

    if isinstance(other_predecessor_record_ids, list):
        predecessor_record_ids.extend(other_predecessor_record_ids)

    if input_record_ids is None:
        input_record_ids = []

    if not isinstance(input_record_ids, list):
        input_record_ids = [input_record_ids]

    return_input_record_ids = []
    logging.debug(f"{(input_record_ids)=}")
    for input_record_id in input_record_ids:
        if isinstance(input_record_id, dict):
            if inputs_from_referenced_outputs:
                field = "output_record_ids"
            else:
                field = "input_record_ids"
            found_input_record_id = (
                extract_record_ids_from_other_provenance_step(
                    input_record_id, previous_step_field_name=field
                )
            )
            return_input_record_ids.extend(found_input_record_id)
        else:
            return_input_record_ids.append(input_record_id)
    logging.debug(f"{(return_input_record_ids)=}")

    if isinstance(input_record_defs, dict):
        input_record_defs = [input_record_defs]

    if isinstance(input_record_defs, list):
        for input_record_def in input_record_defs:
            input_rec = add_record(
                input_record_def.get("name", "NoNameGiven"),
                input_record_def.get("uris"),
                input_record_def.get("tags"),
                None,
                None,
            )
            return_input_record_ids.append(input_rec.record_id)

    if output_record_ids is None:
        output_record_ids = []

    if not isinstance(output_record_ids, list):
        output_record_ids = [output_record_ids]

    return_output_record_ids = []
    for output_record_id in output_record_ids:
        if isinstance(output_record_id, dict):
            if outputs_from_referenced_inputs:
                field = "input_record_ids"
            else:
                field = "output_record_ids"
            found_output_record_ids = (
                extract_record_ids_from_other_provenance_step(
                    output_record_id, previous_step_field_name=field
                )
            )
            return_output_record_ids.extend(found_output_record_ids)
        else:
            return_output_record_ids.append(output_record_id)

    if isinstance(output_record_defs, dict):
        output_record_defs = [output_record_defs]

    if isinstance(output_record_defs, list):
        for output_record_def in output_record_defs:
            output_rec = add_record(
                output_record_def.get("name", "NoNameGiven"),
                output_record_def.get("uris"),
                output_record_def.get("tags"),
                None,
                None,
            )
            return_output_record_ids.append(output_rec.record_id)

    predecessor_record_ids.extend(return_input_record_ids)
    step_record = add_record(
        name=f"Action Step {step_name}",
        uris=uris,
        tags=tags,
        predecessor_record_ids=predecessor_record_ids,
        derivative_record_ids=return_output_record_ids,
    )

    session.commit()

    logging.info("************** END *************")

    return {
        "flow_state_record_id": step_record.record_id,
        "input_record_ids": return_input_record_ids,
        "output_record_ids": return_output_record_ids,
        "exception_str": exception_str,
    }


def create_invalidation_action(
    name="Not Provided",
    action_type="shell",
    command=None,
    params=None,
    **kwargs,
):
    if command is None:
        raise ValueError("A value for parameter 'command' must be provided")
    if params is not None and not isinstance(params, list):
        raise ValueError(
            "If parameter 'params' is provided it must be a list of strings "
            f"not a {type(params)}"
        )

    import os

    from braid_db import BraidDB
    from braid_db.models import BraidInvalidationAction

    DEFAULT_DB_FILE = "~/funcx-braid.db"

    db_file = os.getenv("BRAID_DB_FILE", os.path.expanduser(DEFAULT_DB_FILE))

    DB = BraidDB(db_file)
    DB.create()
    session = DB.get_session()

    if params is not None:
        ia_params = {"args": params}
    else:
        ia_params = None
    ia = BraidInvalidationAction(
        name=name, action_type=action_type, cmd=command, params=ia_params
    )
    DB.add_model(ia, session=session)
    session.commit()

    return {"invalidation_action_id": str(ia.id)}


def add_invalidation_action_to_record(
    record_id=None, invalidation_action_id=None, **kwargs
):
    if not isinstance(record_id, (dict, str, int)) or not isinstance(
        invalidation_action_id, (dict, str)
    ):
        raise ValueError(
            "Both 'record_id' and 'invalidation_action_id' "
            "must be provided as values or as the output of "
            "previous steps which created these structures"
        )

    import os

    from braid_db import BraidDB, BraidRecord

    DB_FILE = "~/funcx-braid.db"

    DB = BraidDB(os.path.expanduser(DB_FILE))
    session = DB.get_session()

    # If the input is a dict, we will assume we were provided the
    # result from a previous invocation of this same funcx-based
    # provenance recording operation. So, we navigate into the result
    # to the point where the previous step would place the record id
    if isinstance(record_id, dict):
        record_id = (
            record_id.get("details", {})
            .get("result", [dict()])[0]
            .get("flow_state_record_id", -1)
        )
    if isinstance(record_id, str):
        record_id = int(record_id)

    record_model = DB.get_record_model_by_id(record_id, session=session)

    if record_model is None:
        raise ValueError(f"Cannot find a DB entry for record id {record_id}")

    if isinstance(invalidation_action_id, dict):
        invalidation_action_id = (
            invalidation_action_id.get("details", {})
            .get("result", [dict()])[0]
            .get("invalidation_action_id", "")
        )

    braid_record = BraidRecord.from_orm(record_model, DB)

    ia = braid_record.set_invalidation_action(
        invalidation_action_id, session=session
    )
    session.commit()

    return {
        "invalidation_action_id": str(ia.id),
        "flow_state_record_id": record_id,
    }


def add_records(record_dicts, *args, **kwargs) -> list:
    import os
    from typing import Optional

    from braid_db import (
        APIBraidRecordInput,
        APIBraidRecordOutput,
        BraidDB,
        BraidRecord,
    )

    DEFAULT_DB_FILE = "~/funcx-braid.db"

    db_file = os.getenv("BRAID_DB_FILE", os.path.expanduser(DEFAULT_DB_FILE))

    DB = BraidDB(db_file)
    DB.create()
    session = DB.get_session()

    # output_records: List[Union[Dict[str, Any], str]] = []
    output_records = []

    def add_record(
        api_record: APIBraidRecordInput,
        derived_from: Optional[APIBraidRecordOutput] = None,
    ) -> APIBraidRecordOutput:
        braid_rec = BraidRecord(db=DB, name=api_record.name)
        if api_record.uris:
            for uri in api_record.uris:
                braid_rec.add_uri(uri)

        if api_record.tags:
            for tag_name, tag_val in api_record.tags.items():
                braid_rec.add_tag(tag_name, tag_val.value, tag_val.typ)

        if api_record.derived_from_record_id is not None:
            parent_rec = BraidRecord.by_record_id(
                DB, api_record.derived_from_record_id, session
            )
            if parent_rec is None:
                print("UH OH!!!")
            else:
                parent_rec.add_derivation(braid_rec)

        braid_rec_output = APIBraidRecordOutput(
            record_id=braid_rec.record_id,
            name=api_record.name,
            uris=api_record.uris,
            tags=api_record.uris,
            time=braid_rec.timestamp,
        )

        if api_record.derivations is not None:
            braid_rec_output.derivations = []
            for derivative in api_record.derivations:
                output_derivative = add_record(derivative, braid_rec_output)
                braid_rec_output.derivations.append(output_derivative)

        return braid_rec_output

    # IF there's just one record in the first arg, that's ok, we'll just use
    # that
    if isinstance(record_dicts, dict):
        record_dicts = [record_dicts]
    record_dicts.extend(args)
    for record_dict in record_dicts:
        if isinstance(record_dict, dict):
            try:
                api_input_record = APIBraidRecordInput(**record_dict)
                api_output_record = add_record(api_input_record, None)
                output_records.append(api_output_record.dict())
            except Exception as ve:
                output_records.append(str(ve))

    return output_records


def _run_and_wait_funcx(
    fxc: FuncXClient, *args, function_id: str, endpoint_id: str, **kwargs
) -> Any:
    print(f"DEBUG {(args, function_id, endpoint_id, kwargs)=}")

    task_id = fxc.run(
        *args, function_id=function_id, endpoint_id=endpoint_id, **kwargs
    )
    task_status = fxc.get_task(task_id)
    while task_status.get("pending", False):
        print(f"DEBUG {(task_status)=}")

        time.sleep(1.0)
        task_status = fxc.get_task(task_id)

    print(f"DEBUG {(task_status)=}")
    if task_status.get("status") == "failed":
        exception = task_status.get("exception")
        if exception is not None:
            exception.reraise()
    return task_status.get("result")


def register_function(
    fxc: FuncXClient, function: Callable
) -> Tuple[str, CachedFunction]:
    fn_name = function.__name__
    fn_hash = sha256_function(function)
    now = int(time.time())
    funcx_uuid = fxc.register_function(
        function,
        f"braid_db_{fn_name}_v{now}",
        searchable=True,
    )
    print(
        f"Added function {fn_name} as "
        f"braid_db_{fn_name}_v{now} with uuid {funcx_uuid}"
    )
    return fn_name, CachedFunction(funcx_uuid=funcx_uuid, impl_hash=fn_hash)


def get_funcx_id_for_function(
    fxc: FuncXClient,
    function: Callable,
    fn_map: Optional[Dict[str, CachedFunction]] = None,
) -> str:
    loaded_map = fn_map is None
    if fn_map is None:
        fn_map = load_registered_funcx_functions()
    input_fn_hash = sha256_function(function)
    for fn_name, fn_cache in fn_map.items():
        if fn_cache.impl_hash == input_fn_hash:
            return fn_cache.funcx_uuid
    name, cache_entry = register_function(fxc, function)
    fn_map[name] = cache_entry
    if loaded_map:
        store_registered_funcx_functions(fn_map)
    return cache_entry.funcx_uuid


def register_functions():
    fxc = FuncXClient(use_offprocess_checker=False)
    functions = [
        add_transfer_request,
        add_record_for_action_step,
        create_invalidation_action,
        add_invalidation_action_to_record,
    ]
    fn_map = load_registered_funcx_functions()
    now = int(time.time())
    for function in functions:
        fn_name = function.__name__
        fn_hash = sha256_function(function)
        fn_info = CachedFunction(*fn_map.get(fn_name, [None, None]))
        if fn_info is not None and fn_info.impl_hash == fn_hash and False:
            print(
                f"Function {fn_name} already registered with current hash, "
                "skipping"
            )
            continue
        funcx_uuid = fxc.register_function(
            function,
            f"braid_db_{fn_name}_v{now}",
            searchable=True,
        )
        print(
            f"Added function {fn_name} as "
            f"braid_db_{fn_name}_v{now} with uuid {funcx_uuid}"
        )
        fn_map[fn_name] = CachedFunction(
            funcx_uuid=funcx_uuid, impl_hash=fn_hash
        )
    store_registered_funcx_functions(fn_map)


def funcx_add_record():
    parser = ArgumentParser()
    parser.add_argument("--endpoint-id", default=_MY_ENDPOINT_ID, type=str)
    fn_map = load_registered_funcx_functions()
    func_id = fn_map.get(
        add_records.__name__,
        CachedFunction(funcx_uuid=_ADD_RECORD_FUNCX_UUID, impl_hash="Dummy"),
    ).funcx_uuid
    parser.add_argument("--function-id", default=func_id, type=str)
    parser.add_argument("record_name")
    args = parser.parse_args()

    fxc = FuncXClient()
    result = _run_and_wait_funcx(
        fxc,
        {"name": args.record_name},
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
        add_records, name="funcx_record", endpoint_id=_MY_ENDPOINT_ID
    )
    result = future.result()
    print(f"Add Record Result: {result}")
    print("Are we done???")
    sys.exit(0)


if __name__ == "__main__":
    main()
