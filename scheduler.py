import os
import pandas as pd
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Read webhook from GitHub Secret
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Load schedule
df = pd.read_csv("schedule.csv")

# Current Melbourne time
now = datetime.now(
    ZoneInfo("Australia/Melbourne")
)

changed = False

for idx, row in df.iterrows():

    status = str(
        row.get("Status", "")
    ).strip().upper()

    # Skip already sent rows
    if status == "SENT":
        continue

    # Skip empty rows
    if pd.isna(row["Post Time"]) or pd.isna(row["Message"]):
        continue

    # Parse scheduled time
    post_time = datetime.strptime(
        str(row["Post Time"]),
        "%Y-%m-%d %H:%M"
    )

    post_time = post_time.replace(
        tzinfo=ZoneInfo("Australia/Melbourne")
    )

    # Is it time to send?
    if post_time <= now:

        try:

            response = requests.post(
                WEBHOOK_URL,
                json={
                    "content": str(row["Message"])
                },
                timeout=30
            )

            if response.status_code in [200, 204]:

                print(
                    f"Sent: {row['Message']}"
                )

                df.at[idx, "Status"] = "SENT"
                changed = True

            else:

                print(
                    f"Failed: {response.status_code}"
                )

                print(response.text)

        except Exception as e:

            print(
                f"Error sending row {idx}: {e}"
            )

# Save updated statuses
if changed:
    df.to_csv(
        "schedule.csv",
        index=False
    )
