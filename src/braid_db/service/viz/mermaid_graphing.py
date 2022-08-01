from __future__ import annotations

from typing import Any, Set
from uuid import UUID

from braid_db import BraidDB, BraidRecord
from braid_db.models import (
    BraidInvalidationAction,
    BraidInvalidationModel,
    BraidRecordModel,
)

_html_header = """
<html>
    <body>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js">
        </script>
        <script>
            mermaid.initialize({ startOnLoad: true });
        </script>

        <div class="mermaid">

"""

_html_footer = """
        </div>
    </body>
</html>
"""


def quote_str(s: Any) -> str:
    return '"' + str(s) + '"'


def node_name_for_record(record: BraidRecord) -> str:
    return f"record{record.record_id}"


def node_name_for_invalidation_action(
    invalidation_action: BraidInvalidationAction,
) -> str:
    return f"invalidation_action{str(invalidation_action.id)[:5]}"


def node_name_for_invalidation(
    invalidation: BraidInvalidationModel | UUID,
) -> str:
    if isinstance(invalidation, BraidInvalidationModel):
        the_id = invalidation.id
    else:
        the_id = invalidation
    return f"invalidation{str(the_id)[:5]}"


def truncate_val(val: Any, max_len: int, from_right=False) -> str:
    str_val = str(val)
    # return str_val

    if len(str_val) > max_len:
        if from_right:
            str_val = "..." + str_val[-max_len:]
        else:
            str_val = str_val[0:max_len] + "..."
    return str_val


def record_to_mermaid_shape(record: BraidRecordModel) -> str:
    node_name = node_name_for_record(record)
    rows = [record.name]
    if len(record.uris) > 0:
        rows.extend("<hr>")
        rows.extend(
            "<br>".join([truncate_val(u.uri, 90) for u in record.uris])
        )
    if len(record.tags) > 0:
        rows.extend("<hr>")
        rows.extend(
            "<br>".join(
                [
                    (
                        f"{truncate_val(t.key, 25, from_right=True)} "
                        f"= {truncate_val(t.value, 32)}"
                    )
                    for t in record.tags
                ]
            )
        )
    shape = f"{node_name}({quote_str(''.join(rows))})"
    if record.invalidation is None:
        color = "LightGoldenRodYellow"
    else:
        color = "LightPink"
    style = f"style {node_name} fill:{color}"
    return shape + "\n" + style


def invalidation_action_to_mermaid_shape(
    invalidation_action: BraidInvalidationAction,
) -> str:
    node_name = node_name_for_invalidation_action(invalidation_action)
    return (
        f"{node_name}"
        "{{"
        f"{invalidation_action.name} <br> "
        f"{invalidation_action.cmd}"
        "}}\n"
        # f"{quote_str(invalidation_action.params)}]\n"
        f"style {node_name} fill:MediumSpringGreen\n"
    )


def invalidation_to_mermaid_shape(invalidation: BraidInvalidationModel) -> str:
    node_name = node_name_for_invalidation(invalidation)
    to_root = ""
    if invalidation.root_invalidation is not None:
        root_node_name = node_name_for_invalidation(
            invalidation.root_invalidation
        )
        to_root = f"{root_node_name} ==>|Causes| " f"{node_name}\n"
    return (
        f"{node_name}"
        f"[/{quote_str(invalidation.cause)}/]\n"
        f"{to_root}"
        f"style {node_name} fill:Violet"
    )


def to_mermaid(root_record_id: int, DB: BraidDB) -> str:
    visited: Set[int] = set()
    graph_def = "graph TD\n"
    session = DB.get_session()

    record = DB.get_record_model_by_id(root_record_id, session=session)
    to_visit = [record]
    while len(to_visit) > 0:
        record = to_visit.pop()
        rec_node_name = node_name_for_record(record)
        graph_def += record_to_mermaid_shape(record) + "\n"
        visited.add(record.record_id)

        if record.invalidation_action is not None:
            graph_def += (
                invalidation_action_to_mermaid_shape(
                    record.invalidation_action
                )
                + "\n"
            )
            action_node_name = node_name_for_invalidation_action(
                record.invalidation_action
            )
            graph_def += f"{action_node_name} -.-> {rec_node_name}\n"

        if record.invalidation is not None:
            graph_def += (
                invalidation_to_mermaid_shape(record.invalidation) + "\n"
            )
            invalidation_node_name = node_name_for_invalidation(
                record.invalidation
            )
            graph_def += (
                f"{invalidation_node_name} -.-o|Invalidates| {rec_node_name}\n"
            )

        derivatives = DB.get_derivations(record.record_id, session)

        for derivative in derivatives:
            deriv_node_name = node_name_for_record(derivative)
            graph_def += f"{rec_node_name}-->{deriv_node_name}\n"
            if (
                derivative.record_id not in visited
                and derivative not in to_visit
            ):
                to_visit.append(derivative)

        predecessors = DB.get_predecessors(record.record_id, session)
        for pred in predecessors:
            if pred.record_id not in visited and pred not in to_visit:
                to_visit.append(pred)
    session.close()
    return graph_def


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("record_id", type=int)
    parser.add_argument("--db-file", type=str, required=True)
    parser.add_argument("--raw-mermaid", action="store_true")

    args = parser.parse_args()

    DB = BraidDB(args.db_file)

    mermaid_graph = to_mermaid(args.record_id, DB)

    if args.raw_mermaid:
        sys.stdout.write(mermaid_graph)
    else:
        html = _html_header + mermaid_graph + _html_footer
        sys.stdout.write(html)
