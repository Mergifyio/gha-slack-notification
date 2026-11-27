import os
import subprocess
import json
import sys

EMOJIS = {
    "success": "🦾",
    "cancelled": "✋",
    "failure": "💥",
}

GITHUB_OUTPUT = os.environ["GITHUB_OUTPUT"]

repository = os.environ["REPOSITORY"]

project = os.environ["PROJECT"] or repository.split("/")[-1]

run_id = os.environ["GITHUB_RUN_ID"]
run_url = f"{os.environ['GITHUB_SERVER_URL']}/{repository}/actions/runs/{run_id}"
if os.environ["JOB_ID"]:
    job_id = os.environ["JOB_ID"]
    job_url = f"{run_url}/job/{job_id}"
else:
    # No job.check_run_id (GitHub Enterprise Server): name and link the run.
    job_id = run_id
    job_url = run_url
ref_name = os.environ["REF_NAME"]

notif_type = os.environ["NOTIF_TYPE"]

extra_message = os.environ["EXTRA_MESSAGE"]

job_status = os.environ["OVERRIDE_JOB_STATUS"] or os.environ["JOB_STATUS"]

emoji = EMOJIS.get(job_status, "❔")

if notif_type == "message":
    slack_text_message = (
        f"*{os.environ['SLACK_TEXT_MESSAGE']} :{emoji}*\nConclusion: {job_status}"
    )

elif notif_type == "release-start":
    slack_text_message = f"*Starting release ({job_id}) of {project} {ref_name}*"

elif notif_type == "release-finish":
    slack_text_message = f"*Release ({job_id}) of {project} {ref_name} finished {emoji}*\n Conclusion: {job_status}\n {extra_message}"

elif notif_type == "deploy-start":
    slack_text_message = f"*Starting deployment ({job_id}) of {project}*"

elif notif_type == "deploy-finish":
    if os.path.isdir(".git"):
        p = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"], capture_output=True, check=True
        )
        commit = p.stdout.decode()
        escaped_commit = f"```\n{commit.replace('```', '~~~')}```"
        extra_message = f"{escaped_commit}\n{extra_message}"

    slack_text_message = f"*Deployment ({job_id}) of {project} finished {emoji}*\nConclusion: {job_status}\n{extra_message}"
else:
    print(f"Unsupported notification type: {notif_type}")
    sys.exit(1)


slack_payload = {
    "blocks": [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": slack_text_message},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Job log", "emoji": True},
                "url": job_url,
            },
        }
    ]
}

compacted_slack_payload = json.dumps(slack_payload, separators=(",", ":"))

with open(GITHUB_OUTPUT, "w") as f:
    f.write(f"SLACK_PAYLOAD={compacted_slack_payload}\n")
