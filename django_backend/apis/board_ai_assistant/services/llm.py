from openai import OpenAI


def get_openrouter_client(base_url: str, api_key: str):
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


def get_llm_stream(*, base_url, api_key, model_name, messages, tools=None):
    client = get_openrouter_client(base_url, api_key)

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta

        result = {}

        if delta.content:
            result["content"] = delta.content

        if delta.tool_calls:
            result["tool_calls"] = [
                {
                    "index": tc.index,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in delta.tool_calls
            ]

        yield result