import aiohttp
import asyncio
import json

async def invoke_chute():
	api_token = "$cpk_8638a1bafb40499ca77ca399a289776d.a8e23eadbcbb5017a2e9b95e810f4af4.OlmyG2C9AszlGQqLA0HUT37woQNyMZbO"  # Replace with your actual API token

	headers = {
		"Authorization": "Bearer " + api_token,
		"Content-Type": "application/json"
	}
	
	body =     {
      "model": "deepseek-ai/DeepSeek-V3.1",
      "messages": [
        {
          "role": "user",
          "content": "Tell me a 250 word story."
        }
      ],
      "stream": True,
      "max_tokens": 1024,
      "temperature": 0.7
    }

	async with aiohttp.ClientSession() as session:
		async with session.post(
			"https://llm.chutes.ai/v1/chat/completions", 
			headers=headers,
			json=body
		) as response:
			async for line in response.content:
				line = line.decode("utf-8").strip()
				if line.startswith("data: "):
					data = line[6:]
					if data == "[DONE]":
						break
					try:
						chunk = data.strip()
						if chunk:
							print(chunk)
					except Exception as e:
						print(f"Error parsing chunk: {e}")

asyncio.run(invoke_chute())