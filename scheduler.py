import json
import time
import pandas as pd
import requests

from datetime import datetime
import pytz


def log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    line = f"[{timestamp}] {message}"

    print(line)

    with open(
        "scheduler.log",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(line + "\n")


with open("config.json", "r") as f:
    config = json.load(f)

WEBHOOK_URL = config["webhook_url"]
TIMEZONE = config["timezone"]

log("====================================")
log("Scheduler started")
log(f"Timezone: {TIMEZONE}")
log("====================================")


def process_schedule():

    df = pd.read_csv(
        "schedule.csv",
        dtype=str
    ).fillna("")

    tz = pytz.timezone(TIMEZONE)

    now = datetime.now(tz)

    changed = False

    for idx, row in df.iterrows():

        status = row["Status"].strip()

        if status == "SENT":
            continue

        try:

            post_time = datetime.strptime(
                row["Post Time"],
                "%Y-%m-%d %H:%M"
            )

            post_time = tz.localize(post_time)

        except Exception as e:

            log(
                f"ERROR | Invalid date format: "
                f"{row['Post Time']} | {e}"
            )

            continue

        log(
            f"CHECKING | "
            f"Message='{row['Message']}' | "
            f"Scheduled='{post_time}' | "
            f"Status='{status}'"
        )

        if post_time <= now:

            try:

                role_ping = ""

                if "Role Ping" in row and str(
                    row["Role Ping"]
                ).strip():

                    role_ids = [
                        role.strip()
                        for role in str(
                            row["Role Ping"]
                        ).split(",")
                    ]

                    role_ping = " ".join(
                        [
                            f"<@&{role}>"
                            for role in role_ids
                        ]
                    )

                content = row["Message"]

                if role_ping:

                    content = (
                        f"{role_ping}\n\n"
                        f"{row['Message']}"
                    )

                response = requests.post(
                    WEBHOOK_URL,
                    json={
                        "content": content,
                        "allowed_mentions": {
                            "parse": ["roles", "everyone"]
                        }
                    },
                    timeout=10
                )

                if response.status_code in [
                    200,
                    204
                ]:

                    log(
                        f"SUCCESS | "
                        f"Sent message: "
                        f"{row['Message']}"
                    )

                    df.at[
                        idx,
                        "Status"
                    ] = "SENT"

                    changed = True

                else:

                    log(
                        f"FAILED | "
                        f"Status Code: "
                        f"{response.status_code} | "
                        f"Response: "
                        f"{response.text}"
                    )

            except Exception as e:

                log(
                    f"ERROR | "
                    f"Failed to send "
                    f"message | {e}"
                )

    if changed:

        df.to_csv(
            "schedule.csv",
            index=False
        )

        log(
            "schedule.csv updated successfully"
        )


while True:

    try:

        process_schedule()

    except Exception as e:

        log(
            f"CRITICAL ERROR | {e}"
        )

    time.sleep(60)