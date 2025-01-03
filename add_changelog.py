import os
import json
from datetime import datetime
import asyncio
import httpx
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI

load_dotenv()

# Constants
GITHUB_API_BASE = "https://api.github.com"


PR_TO_RELEASE_LOG_PROMPT = """You are a PR ANALYZER. Your task is to ANALYZE the GIVEN PR INFORMATION BELOW and EXTRACT the LIST OF DETAILS GIVEN BELOW: 
Jira/ Notion link(field name: `jira_notion_link`): Link to a notion page that will be avaialable in the PR BODY
Description in Details(field name: `description`): COMPLETE DETAIL about the CHANGES made by the PR
Breaking Changes(field name: `breaking_changed`): THE BREAKING CHANGES SHOULD BE EXPLAINED IN DETAIL
Test Cases(field name: test_cases): THE VARIOUS TEST CASE SCENARIOS THE peron MAKING the PR HAS TESTED with.

If you can not extract the values for the above fields from the give BODY of the PR then store `N/A` in those fields.

YOUR RESPONSE SHOULD ONLY BE A VALID JSON OBJECT STRING WITH THE FOLLWING FIELDS GIVEN IN THE EXAMPLE BELOW:

`{
  "jira_notion_link": "",
  "description": "",
  "breaking_changes": "",
  "test_cases": ""
}`
DO NOT ADD ```json{response}``` around the object just send the actual response only
"""


async def llm_chat(prompt, query):
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
        temperature=0.5,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    response = response.choices[0].message.content
    return response


async def process_pr(repo, pr_number, github_token, service_changed, prolog_url):
    async with httpx.AsyncClient() as client:
        # Fetch PR details from GitHub API
        headers = {"Authorization": f"token {github_token}"}
        pr_url = f"{GITHUB_API_BASE}/repos/{repo}/pulls/{pr_number}"
        response = await client.get(pr_url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch PR details: {response.status_code} - {response.text}"
            )

        pr_data = response.json()

        # Extract basic data
        deployment_data = {
            "deployment_date": datetime.now().strftime(
                "%Y-%m-%d"
            ),  # Assuming deployment happens on PR merge
            "service_changed": service_changed,
            "pr_link": pr_data.get("html_url", ""),
            "pr_raised_by": pr_data.get("user", {}).get("login", ""),
            "pr_reviewed_by": ", ".join(
                reviewer["user"]["login"]
                for reviewer in pr_data.get("requested_reviewers", [])
            ),
            "pr_merged_by": pr_data.get("merged_by", {}).get("login", ""),
        }

        # Pass PR description to LLM for additional fields
        llm_response = await llm_chat(
            prompt=PR_TO_RELEASE_LOG_PROMPT,
            query="BODY OF THE PR: \n" + pr_data.get("body", ""),
        )
        print("LLM", llm_response)
        llm_data = json.loads(llm_response)  # Simulate LLM response as dictionary

        deployment_data.update(llm_data)

        # Call Flask service to add the deployment
        flask_response = await client.post(prolog_url, json=deployment_data)
        if flask_response.status_code != 201:
            raise Exception(
                f"Failed to add deployment: {flask_response.status_code} - {flask_response.text}"
            )

        print(f"Deployment data successfully added: {flask_response.json()}")


if __name__ == "__main__":
    # Get inputs from environment variables
    from dotenv import load_dotenv

    load_dotenv()

    REPO = os.getenv("GITHUB_REPOSITORY")  # e.g., "username/repo"
    PR_NUMBER = os.getenv("PR_NUMBER")  # PR number
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub token for API access
    SERVICE_NAME = os.getenv("SERVICE_NAME")  # GitHub token for API access
    PROLOG_URL = os.getenv("PROLOG_URL")

    if not all([REPO, PR_NUMBER, GITHUB_TOKEN, SERVICE_NAME, PROLOG_URL]):
        raise ValueError(
            "Missing required environment variables: REPO, PR_NUMBER, SERVICE_NAME, PROLOG_URL or GITHUB_TOKEN.",
            REPO,
            PR_NUMBER,
            SERVICE_NAME,
            PROLOG_URL,
            GITHUB_TOKEN,
        )

    # Process the PR
    asyncio.run(process_pr(REPO, PR_NUMBER, GITHUB_TOKEN, SERVICE_NAME, PROLOG_URL))
