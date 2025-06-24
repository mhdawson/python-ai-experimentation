import asyncio
import logging

from llama_stack_client import LlamaStackClient

logging.getLogger("httpx").setLevel(logging.WARNING)

model_id = "meta-llama/Llama-3.1-8B-Instruct"

client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)

verbose = False


def log(message):
    if verbose:
        print(message)


#############################
# TOOL info for the LLM
available_tools = [
    {
        "tool_name": "favorite_color_tool",
        "description": "returns the favorite color for person given their City and Country",
        "parameters": {
            "city": {
                "param_type": "string",
                "description": "the city for the person",
                "required": True,
            },
            "country": {
                "param_type": "string",
                "description": "the country for the person",
                "required": True,
            },
        },
    },
    {
        "tool_name": "favorite_hockey_tool",
        "description": "returns the favorite hockey team for a person given their City and Country",
        "parameters": {
            "city": {
                "param_type": "string",
                "description": "the city for the person",
                "required": True,
            },
            "country": {
                "param_type": "string",
                "description": "the country for the person",
                "required": True,
            },
        },
    },
]


#############################
# FUNCTION IMPLEMENTATIONS
def get_favorite_color(args):
    city = args.get("city")
    country = args.get("country")
    if city == "Ottawa" and country == "Canada":
        return "the favoriteColorTool returned that the favorite color for Ottawa Canada is black"
    if city == "Montreal" and country == "Canada":
        return "the favoriteColorTool returned that the favorite color for Montreal Canada is red"
    return (
        "the favoriteColorTool returned The city or country "
        "was not valid, assistant please ask the user for them"
    )


def get_favorite_hockey_team(args):
    city = args.get("city")
    country = args.get("country")
    if city == "Ottawa" and country == "Canada":
        return "the favoriteHocketTool returned that the favorite hockey team for Ottawa Canada is The Ottawa Senators"
    if city == "Montreal" and country == "Canada":
        return "the favoriteHockeyTool returned that the favorite hockey team for Montreal Canada is the Montreal Canadians"
    return (
        "the favoriteHockeyTool returned The city or country "
        "was not valid, please ask the user for them"
    )


funcs = {
    "favorite_color_tool": get_favorite_color,
    "favorite_hockey_tool": get_favorite_hockey_team,
}


#############################
# FUNCTION IMPLEMENTATIONS
# Handle responses which may include a request to run a function
def handle_response(messages, response):
    # push the models response to the chat
    messages.append(response.completion_message)

    if response.completion_message.tool_calls and len(response.completion_message.tool_calls) != 0:

        for tool in response.completion_message.tool_calls:
            # log the function calls so that we see when they are called
            log(f"  FUNCTION CALLED WITH: {tool}")
            print(f"  CALLED: {tool.tool_name}")

            func = funcs.get(tool.tool_name)
            if func:
                func_response = func(tool.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "content": func_response,
                        "call_id": tool.call_id,
                        "tool_name": tool.tool_name,
                    }
                )
            else:
                messages.append(
                    {
                        "role": "tool",
                        "call_id": tool.call_id,
                        "tool_name": tool.tool_name,
                        "content": "invalid tool called",
                    }
                )

        # call the model again so that it can process the data returned by the
        # function calls
        return handle_response(
            messages,
            client.inference.chat_completion(
                messages=messages,
                model_id=model_id,
                tools=available_tools,
            ),
        )
    # no function calls just return the response
    return response.completion_message.content


#############################
# ASK QUESTIONS

questions = [
    "What is my favorite color?",
    "My city is Ottawa",
    "My country is Canada",
    "I moved to Montreal. What is my favorite color now?",
    "My city is Montreal and my country is Canada",
    "What is the fastest car in the world?",
    "My city is Ottawa and my country is Canada, what is my favorite color?",
    "What is my favorite hockey team ?",
    "My city is Montreal and my country is Canada",
    "Who was the first president of the United States?",
]


async def main():
    for j in range(1):
        # maintains chat history
        messages = [
            {
                "role": "system",
                "content": (
                    "only answer questions about a favorite color by using the response from the favorite_color_tool "
                    "only answer questions about a favorite hockey team by using the response from the favorite_hockey_tool "
                    "when asked for a favorite color if you have not called the favorite_color_tool, call it "
                    "Never guess a favorite color "
                    "Do not be chatty "
                    "Give short answers when possible"
                ),
            },
        ]

        print(f"Iteration {j} ------------------------------------------------------------")

        for _i, question in enumerate(questions):
            print(f"QUESTION: {question}")
            messages.append({"role": "user", "content": question})

            response = client.inference.chat_completion(
                messages=messages,
                model_id=model_id,
                tools=available_tools,
            )

            result = handle_response(messages, response)
            print(f"  RESPONSE: {result}")


if __name__ == "__main__":
    asyncio.run(main())
