# TEST FUNCX 1

import time

from funcx.sdk.client import FuncXClient
from funcx.utils.errors import TaskPending

# TUTOR = '4b116d3c-1703-4f8f-9f6f-39921e5864df'
DUNEDIN = "9ea962c1-059e-49e4-a605-bcb82d76dde8"

F_id = "85ccbd03-de4a-4751-908c-73bfbedb70ed"

fxc = FuncXClient()

# handle = fxc.run(endpoint_id=DUNEDIN, function_id=F_id)
handle = fxc.run(
    "name1", ["uri1", "uri2"], endpoint_id=DUNEDIN, function_id=F_id
)
print("handle: " + str(handle))

delay = 1
while True:
    try:
        result = fxc.get_result(handle)
    except TaskPending:
        print("pending...")
        time.sleep(delay)
        delay += 1
        continue
    break  # success

print(result)
