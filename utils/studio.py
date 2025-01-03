import httpx
from openai import AsyncOpenAI
from setting import settings

openai_api_key = settings.openai_api_key


async def llm_chat(prompt, query):
    client = AsyncOpenAI(
        api_key=openai_api_key,
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


async def send_inference_request(
    user_id: str, agent_id: str, session_id: str, message: str, api_key: str
) -> dict:
    """
    Sends an asynchronous POST request to the inference chat endpoint.

    Args:
        user_id (str): The user ID for the request.
        agent_id (str): The agent ID for the session.
        session_id (str): The session ID for the request.
        message (str): The message content.
        api_key (str): The API key for authentication.

    Returns:
        dict: The JSON response from the server.
    """
    url = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    payload = {
        "user_id": user_id,
        "agent_id": agent_id,
        "session_id": session_id,
        "message": message,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
            print("RESPONSE", response.text)
            return response.json()
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url}: {e}||||")
            return None
        except httpx.HTTPStatusError as e:
            print(
                f"Error response {e.response.status_code} while requesting {e.request.url}: {e.response.text}"
            )
            return None
        except Exception as e:
            print("Something went wrong: ", str(e))
            return None
