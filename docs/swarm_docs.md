# Instructions
For this project, we use an Azure OpenAI instance. 
Consider this when coding.

# Swarm (Experimental, Educational)

An educational framework exploring ergonomic, lightweight multi-agent orchestration.

## ⚠️ Warning

Swarm is currently an **experimental sample framework** intended to explore ergonomic interfaces for multi-agent systems. It is **not intended for production use**, and therefore has **no official support**. 

> **Note**: We will not be reviewing pull requests (PRs) or issues for this repository.

The primary goal of Swarm is to showcase the **handoff** and **routines** patterns explored in the [Orchestrating Agents: Handoffs & Routines cookbook](https://github.com/openai/swarm#:~:text=Orchestrating%20Agents%3A%20Handoffs%20%26%20Routines). 

Swarm is **not meant as a standalone library** and is intended primarily for **educational purposes**.


## Install
```pip install git+ssh://git@github.com/openai/swarm.git```
or
```pip install git+https://github.com/openai/swarm.git```

## Usage

```python
from swarm import Swarm, Agent

client = Swarm()

def transfer_to_agent_b():
    return agent_b


agent_a = Agent(
    name="Agent A",
    instructions="You are a helpful agent.",
    functions=[transfer_to_agent_b],
)

agent_b = Agent(
    name="Agent B",
    instructions="Only speak in Haikus.",
)

response = client.run(
    agent=agent_a,
    messages=[{"role": "user", "content": "I want to talk to agent B."}],
)

print(response.messages[-1]["content"])
```

Result:
```
Hope glimmers brightly,
New paths converge gracefully,
What can I assist?
```

## Table of Contents

- [Overview](#overview)
- [Examples](#examples)
- [Documentation](#documentation)
  - [Running Swarm](#running-swarm)
  - [Agents](#agents)
  - [Functions](#functions)
  - [Streaming](#streaming)
- [Evaluations](#evaluations)
- [Utils](#utils)

## Overview

Swarm focuses on making agent coordination and execution lightweight, highly controllable, and easily testable.

It accomplishes this through two primitive abstractions: Agents and handoffs. An Agent encompasses instructions and tools, and can at any point choose to hand off a conversation to another Agent.

These primitives are powerful enough to express rich dynamics between tools and networks of agents, allowing you to build scalable, real-world solutions while avoiding a steep learning curve.

> **Note**
> 
> Swarm Agents are not related to Assistants in the Assistants API. They are named similarly for convenience, but are otherwise completely unrelated. Swarm is entirely powered by the Chat Completions API and is hence stateless between calls.

##Why Swarm
Swarm explores patterns that are lightweight, scalable, and highly customizable by design. Approaches similar to Swarm are best suited for situations dealing with a large number of independent capabilities and instructions that are difficult to encode into a single prompt.

The Assistants API is a great option for developers looking for fully-hosted threads and built in memory management and retrieval. However, Swarm is an educational resource for developers curious to learn about multi-agent orchestration. Swarm runs (almost) entirely on the client and, much like the Chat Completions API, does not store state between calls.

## Examples

Check out `/examples` for inspiration! Learn more about each one in its README.

- [basic](https://github.com/openai/swarm/blob/main/examples/basic): Simple examples of fundamentals like setup, function calling, handoffs, and context variables
- [triage_agent](https://github.com/openai/swarm/blob/main/examples/triage_agent): Simple example of setting up a basic triage step to hand off to the right agent
- [weather_agent](https://github.com/openai/swarm/blob/main/examples/weather_agent): Simple example of function calling
- [airline](https://github.com/openai/swarm/blob/main/examples/airline): A multi-agent setup for handling different customer service requests in an airline context
- [support_bot](https://github.com/openai/swarm/blob/main/examples/support_bot): A customer service bot which includes a user interface agent and a help center agent with several tools
- [personal_shopper](https://github.com/openai/swarm/blob/main/examples/personal_shopper): A personal shopping agent that can help with making sales and refunding orders

## Documentation

A diagram depicts a structured flow where different modules handle specific parts of a query to deliver a targeted response. It illustrates a system where a query about the weather is routed through different assistants. Here's a breakdown of the steps:

1. **User Query**: The user asks, "What's the weather in NY?"

2. **Triage Assistant**: The system routes this query to a "Triage Assistant," which determines the nature of the request. Recognizing it as a weather-related query, it triggers the function `transfer_to_weather_assistant()`.

3. **Weather Assistant**: After the transfer, the query is passed to the "Weather Assistant." This assistant uses the function `get_weather("New York City")` to retrieve the weather information for New York City.

4. **Weather Response**: The weather assistant retrieves a temperature of 67 degrees and returns the response: "It's 67 degrees in New York."

## Running Swarm

Start by instantiating a Swarm client (which internally just instantiates an OpenAI client).

```python
from swarm import Swarm

client = Swarm()
```
### client.run()

Swarm's `run()` function is analogous to the `chat.completions.create()` function in the Chat Completions API – it takes messages and returns messages and saves no state between calls. Importantly, however, it also handles Agent function execution, hand-offs, context variable references, and can take multiple turns before returning to the user.

At its core, Swarm's `client.run()` implements the following loop:

1. Get a completion from the current Agent
2. Execute tool calls and append results
3. Switch Agent if necessary
4. Update context variables, if necessary
5. If no new function calls, return

| Argument         | Type   | Description                                                                                       | Default          |
|------------------|--------|---------------------------------------------------------------------------------------------------|-------------------|
| agent            | Agent  | The (initial) agent to be called.                                                                 | (required)       |
| messages         | List   | A list of message objects, identical to Chat Completions messages                                 | (required)       |
| context_variables| dict   | A dictionary of additional context variables, available to functions and Agent instructions       | {}               |
| max_turns        | int    | The maximum number of conversational turns allowed                                                | float("inf")     |
| model_override   | str    | An optional string to override the model being used by an Agent                                   | None             |
| execute_tools    | bool   | If False, interrupt execution and immediately returns tool_calls message when an Agent tries to call a function | True |
| stream           | bool   | If True, enables streaming responses                                                              | False            |
| debug            | bool   | If True, enables debug logging                                                                    | False            |

Once `client.run()` is finished (after potentially multiple calls to agents and tools) it will return a `Response` containing all the relevant updated state. Specifically, the new messages, the last Agent to be called, and the most up-to-date `context_variables`. You can pass these values (plus new user messages) in to your next execution of `client.run()` to continue the interaction where it left off – much like `chat.completions.create()`. (The `run_demo_loop` function implements an example of a full execution loop in `/swarm/repl/repl.py`.)

| Field             | Type   | Description                                                                                                                          |
|-------------------|--------|--------------------------------------------------------------------------------------------------------------------------------------|
| messages          | List   | A list of message objects generated during the conversation. Very similar to Chat Completions messages, but with a sender field indicating which Agent the message originated from. |
| agent             | Agent  | The last agent to handle a message.                                                                                                  |
| context_variables | dict   | The same as the input variables, plus any changes.                                                                                   |

## Agents

An `Agent` simply encapsulates a set of instructions with a set of functions (plus some additional settings below), and has the capability to hand off execution to another `Agent`.

While it's tempting to personify an `Agent` as "someone who does X", it can also be used to represent a very specific workflow or step defined by a set of `instructions` and `functions` (e.g., a set of steps, a complex retrieval, single step of data transformation, etc.). This allows `Agents` to be composed into a network of "agents", "workflows", and "tasks", all represented by the same primitive.

## Agent Fields

| Field          | Type                | Description                                                                                     | Default                   |
|----------------|---------------------|-------------------------------------------------------------------------------------------------|---------------------------|
| name           | str                 | The name of the agent.                                                                          | "Agent"                   |
| model          | str                 | The model to be used by the agent.                                                              | "gpt-4d"                  |
| instructions   | str or func() => str | Instructions for the agent, can be a string or a callable returning a string.                   | "You are a helpful agent."|
| functions      | List                | A list of functions that the agent can call.                                                    | []                        |
| tool_choice    | str                 | The tool choice for the agent, if any.                                                          | None                      |

### Instructions

`Agent` instructions are directly converted into the system prompt of a conversation (as the first message). Only the instructions of the active `Agent` will be present at any given time (e.g., if there is an `Agent` handoff, the system prompt will change, but the chat history will not).

```python
agent = Agent(
   instructions="You are a helpful agent."
)
```

The `instructions` can either be a regular `str`, or a function that returns a `str`. The function can optionally receive a `context_variables` parameter, which will be populated by the `context_variables` passed into `client.run()`.

```python
def instructions(context_variables):
   user_name = context_variables["user_name"]
   return f"Help the user, {user_name}, do whatever they want."

agent = Agent(
   instructions=instructions
)
response = client.run(
   agent=agent,
   messages=[{"role":"user", "content": "Hi!"}],
   context_variables={"user_name":"John"}
)
print(response.messages[-1]["content"])
```

```
Hi John, how can I assist you today?
```

### Functions

- Swarm `Agent`s can call python functions directly.
- Function should usually return a `str` (values will be attempted to be cast as a `str`).
- If a function returns an `Agent`, execution will be transferred to that `Agent`.
- If a function defines a `context_variables` parameter, it will be populated by the `context_variables` passed into `client.run()`.

```python
def greet(context_variables, language):
   user_name = context_variables["user_name"]
   greeting = "Hola" if language.lower() == "spanish" else "Hello"
   print(f"{greeting}, {user_name}!")
   return "Done"

agent = Agent(
   functions=[greet]
)

client.run(
   agent=agent,
   messages=[{"role": "user", "content": "Usa greet() por favor."}],
   context_variables={"user_name": "John"}
)
```

```
Hola, John!
```

- If an `Agent` function call has an error (missing function, wrong argument, error) an error response will be appended to the chat so the `Agent` can recover gracefully.
- If multiple functions are called by the `Agent`, they will be executed in that order.

### Handoffs and Updating Context Variables

An `Agent` can hand off to another `Agent` by returning it in a `function`.

```python
sales_agent = Agent(name="Sales Agent")

def transfer_to_sales():
   return sales_agent

agent = Agent(functions=[transfer_to_sales])

response = client.run(agent, [{"role":"user", "content":"Transfer me to sales."}])
print(response.agent.name)
```

```
Sales Agent
```

It can also update the `context_variables` by returning a more complete `Result` object. This can also contain a value and an `Agent`, in case you want a single function to return a value, update the `Agent`, and update the `context_variables` (or any subset of the three).

```python
sales_agent = Agent(name="Sales Agent")

def talk_to_sales():
   print("Hello, World!")
   return Result(
       value="Done",
       agent=sales_agent,
       context_variables={"department": "sales"}
   )

agent = Agent(functions=[talk_to_sales])

response = client.run(
   agent=agent,
   messages=[{"role": "user", "content": "Transfer me to sales"}],
   context_variables={"user_name": "John"}
)
print(response.agent.name)
print(response.context_variables)
```

```
Sales Agent
{'department': 'sales', 'user_name': 'John'}
``` 

**Note**: If an `Agent` calls multiple functions to hand-off to an `Agent`, only the last handoff function will be used.

### Function Schemas

Swarm automatically converts functions into a JSON Schema that is passed into Chat Completions `tools`:

- Docstrings are turned into the function `description`
- Parameters without default values are set to `required`
- Type hints are mapped to the parameter's `type` (and default to `string`)
- Per-parameter descriptions are not explicitly supported, but should work similarly if just added in the docstring (in the future docstring argument parsing may be added)

```python
def greet(name, age: int, location: str = "New York"):
   """Greets the user. Make sure to get their name and age before calling.

   Args:
      name: Name of the user.
      age: Age of the user.
      location: Best place on earth.
   """
   print(f"Hello {name}, glad you are {age} in {location}!")
```

```json
{
   "type": "function",
   "function": {
      "name": "greet",
      "description": "Greets the user. Make sure to get their name and age before calling.\n\nArgs:\n   name: Name of the user.\n   age: Age of the user.\n   location: Best place on earth.",
      "parameters": {
         "type": "object",
         "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "location": {"type": "string"}
         },
         "required": ["name", "age"]
      }
   }
}
```

## Streaming

```python
stream = client.run(agent, messages, stream=True)
for chunk in stream:
   print(chunk)
```

Uses the same events as [Chat Completions API streaming](https://platform.openai.com/docs/api-reference/streaming). See `process_and_print_streaming_response` in `/swarm/repl/repl.py` as an example.

Two new event types have been added:

- `{"delim":"start"}` and `{"delim":"end"}`, to signal each time an `Agent` handles a single message (response or function call). This helps identify switches between `Agent`s.
- `{"response": Response}`, to return a `Response` object at the end of a stream with the aggregated (complete) response, for convenience.

## Evaluations

Evaluations are crucial to any project, and we encourage developers to bring their own eval suites to test the performance of their swarms. For reference, we have some examples for how to eval swarm in the `airline`, `weather_agent`, and `triage_agent` quickstart examples. See the READMEs for more details.

## Utils

Use the `run_demo_loop` to test out your swarm! This will run a REPL on your command line. Supports streaming.

```python
from swarm.repl import run_demo_loop
...
run_demo_loop(agent, stream=True)
```



---