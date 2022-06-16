from typing import Set

from braid_db import BraidDB, BraidRecord

_html_header = """
<html>
    <body>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js">
        </script>
        <script>
            mermaid.initialize({ startOnLoad: true });
        </script>

        Here is one mermaid diagram:
        <div class="mermaid">

"""

_html_footer = """
        </div>
    </body>
</html>
"""


def quote_str(s: str) -> str:
    return '"' + s + '"'


def node_name_for_record(record: BraidRecord) -> str:
    return f"record{record.record_id}"


def record_to_mermaid_shape(record: BraidRecord) -> str:
    rows = [record.name]
    if len(record.uris) > 0:
        rows.extend("<hr>")
        rows.extend("<br>".join([u.uri for u in record.uris]))
    if len(record.tags) > 0:
        rows.extend("<hr>")
        rows.extend("<br>".join([f"{t.key} = {t.value}" for t in record.tags]))
    return f"{node_name_for_record(record)}({quote_str(''.join(rows))})"


def to_mermaid(root_record_id: int, DB: BraidDB) -> str:
    visited: Set[int] = set()
    graph_def = "graph TD\n"
    session = DB.get_session()

    record = DB.get_record_model_by_id(root_record_id, session=session)
    to_visit = [record]
    while len(to_visit) > 0:
        record = to_visit.pop()
        graph_def += record_to_mermaid_shape(record) + "\n"
        visited.add(record.record_id)
        derivatives = DB.get_derivations(record.record_id, session)

        for derivative in derivatives:
            graph_def += (
                f"{node_name_for_record(record)}-->"
                f"{node_name_for_record(derivative)}\n"
            )
            if derivative.record_id not in visited:
                to_visit.append(derivative)

        predecessors = DB.get_predecessors(record.record_id, session)
        for pred in predecessors:
            if pred.record_id not in visited:
                to_visit.append(pred)
    session.close()
    return graph_def


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("record_id", type=int)
    parser.add_argument("--db-file", type=str, required=True)

    args = parser.parse_args()

    DB = BraidDB(args.db_file)

    mermaid_graph = to_mermaid(args.record_id, DB)

    html = _html_header + mermaid_graph + _html_footer

    sys.stdout.write(html)
