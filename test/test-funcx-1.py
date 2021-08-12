
# TEST FUNCX 1

import time

from funcx.sdk.client   import FuncXClient
from funcx.utils.errors import TaskPending


# TUTOR = '4b116d3c-1703-4f8f-9f6f-39921e5864df'
DUNEDIN = '9ea962c1-059e-49e4-a605-bcb82d76dde8'

F_id = "353e37a8-56c6-4b74-8d4c-356bcf51dc1d"

fxc = FuncXClient()

handle = fxc.run(endpoint_id=DUNEDIN, function_id=F_id)  # TUTOR
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
