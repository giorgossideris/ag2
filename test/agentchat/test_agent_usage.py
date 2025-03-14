# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
# !/usr/bin/env python3 -m pytest

import io
from contextlib import redirect_stdout

from autogen import AssistantAgent, UserProxyAgent, gather_usage_summary
from autogen.import_utils import run_for_optional_imports

from ..conftest import Credentials


@run_for_optional_imports("openai", "openai")
def test_gathering(credentials_gpt_4o: Credentials, credentials_gpt_4o_mini: Credentials):
    assistant1 = AssistantAgent(
        "assistant",
        system_message="You are a helpful assistant.",
        llm_config=credentials_gpt_4o_mini.llm_config,
    )
    assistant2 = AssistantAgent(
        "assistant",
        system_message="You are a helpful assistant.",
        llm_config=credentials_gpt_4o_mini.llm_config,
    )
    assistant3 = AssistantAgent(
        "assistant",
        system_message="You are a helpful assistant.",
        llm_config=credentials_gpt_4o.llm_config,
    )

    assistant1.client.total_usage_summary = {
        "total_cost": 0.1,
        "gpt-4o-mini": {"cost": 0.1, "prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    }
    assistant2.client.total_usage_summary = {
        "total_cost": 0.2,
        "gpt-4o-mini": {"cost": 0.2, "prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    }
    assistant3.client.total_usage_summary = {
        "total_cost": 0.3,
        "gpt-4o": {"cost": 0.3, "prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    }

    total_usage = gather_usage_summary([assistant1, assistant2, assistant3])

    assert round(total_usage["usage_including_cached_inference"]["total_cost"], 8) == 0.6
    assert round(total_usage["usage_including_cached_inference"]["gpt-4o-mini"]["cost"], 8) == 0.3
    assert round(total_usage["usage_including_cached_inference"]["gpt-4o"]["cost"], 8) == 0.3

    # test when agent doesn't have client
    user_proxy = UserProxyAgent(
        name="ai_user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=2,
        code_execution_config=False,
        default_auto_reply="That's all. Thank you.",
    )

    total_usage = gather_usage_summary([user_proxy])
    total_usage_summary = total_usage["usage_including_cached_inference"]

    print("Total usage summary:", total_usage_summary)


@run_for_optional_imports("openai", "openai")
def test_agent_usage(credentials: Credentials):
    config_list = credentials.config_list
    assistant = AssistantAgent(
        "assistant",
        system_message="You are a helpful assistant.",
        llm_config={
            "cache_seed": None,
            "config_list": config_list,
        },
    )

    ai_user_proxy = UserProxyAgent(
        name="ai_user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config=False,
        llm_config={
            "config_list": config_list,
        },
        # In the system message the "user" always refers to the other agent.
        system_message="You ask a user for help. You check the answer from the user and provide feedback.",
    )

    math_problem = "$x^3=125$. What is x?"
    res = ai_user_proxy.initiate_chat(
        assistant,
        message=math_problem,
        summary_method="reflection_with_llm",
    )
    print("Result summary:", res.summary)

    # test print
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        ai_user_proxy.print_usage_summary()
    output = captured_output.getvalue()
    assert "Usage summary excluding cached usage:" in output

    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        assistant.print_usage_summary()
    output = captured_output.getvalue()
    assert "All completions are non-cached:" in output

    # test get
    print("Actual usage summary (excluding completion from cache):", assistant.get_actual_usage())
    print("Total usage summary (including completion from cache):", assistant.get_total_usage())

    print("Actual usage summary (excluding completion from cache):", ai_user_proxy.get_actual_usage())
    print("Total usage summary (including completion from cache):", ai_user_proxy.get_total_usage())


if __name__ == "__main__":
    # test_gathering()
    test_agent_usage()
