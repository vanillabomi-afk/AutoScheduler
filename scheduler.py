import pandas as pd
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

WEBHOOK_URL = "https://discord.com/api/webhooks/1511640772431057038/DNj4WlJv0sF27qAlFT4KQlvfKromuOSGrFUmynOqTkYhaATfsFxlxdmwiFW0ONALAzvq"

df = pd.read_csv("schedule.csv")

now = datetime.now(
    ZoneInfo("Australia/Melbourne")
)

changed = False

for idx, row in df.iterrows():

    status = str(row.get("Status", "")).strip()

    if status == "SENT":
        continue

    post_time = datetime.strptime(
        str(row["Post Time"]),
        "%Y-%m-%d %H:%M"
    )

    post_time = post_time.replace(
        tzinfo=ZoneInfo("Australia/Melbourne")
    )

    if post_time <= now:

        response = requests.post(
            WEBHOOK_URL,
            json={
                "content": row["Message"]
            }
        )

        if response.status_code in [200, 204]:
            df.at[idx, "Status"] = "SENT"
            changed = True

if changed:
    df.to_csv("schedule.csv", index=False)
