"""
Device Management System - Agent Runtime with AgentCore Memory

This version extends the runtime to include persistent memory using Amazon Bedrock AgentCore Memory,
allowing the agent to retain context and user preferences between sessions.
"""
import os
import json
import logging
import requests
from dotenv import load_dotenv
import access_token

# Import Strands Agents SDK
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import AgentMemory

# Load environment variables
load_dotenv()

# Initialize the AgentCore Runtime App
app = BedrockAgentCoreApp()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize AgentCore Memory
memory_store_path = os.getenv("AGENT_MEMORY_STORE", "./agent_memory.json")
agent_memory = AgentMemory(
    storage_path=memory_store_path,
    retention="long_term",  # can be "session", "short_term", or "long_term"
)
logger.info(f"AgentCore Memory initialized at: {memory_store_path}")

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
logger.info(f"MCP_SERVER_URL set to: {MCP_SERVER_URL}")

# Configure conversation management
conversation_manager = SlidingWindowConversationManager(window_size=25)

def check_mcp_server():
    try:
        jwt_token = os.getenv("BEARER_TOKEN")
        logger.info(f"Checking MCP server at URL: {MCP_SERVER_URL}")

        if not jwt_token:
            try:
                jwt_token = access_token.get_gateway_access_token()
                logger.info(f"Cognito token obtained: {'Yes' if jwt_token else 'No'}")
            except Exception as e:
                logger.error(f"Error getting Cognito token: {str(e)}", exc_info=True)

        headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"} if jwt_token else {"Content-Type": "application/json"}
        payload = {"jsonrpc": "2.0", "id": "test", "method": "tools/list", "params": {}}

        try:
            response = requests.post(f"{MCP_SERVER_URL}/mcp", headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"MCP server response status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception when checking MCP server: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error checking MCP server: {str(e)}", exc_info=True)
        return False

def initialize_agent():
    try:
        logger.info("Starting agent initialization...")
        jwt_token = os.getenv("BEARER_TOKEN") or access_token.get_gateway_access_token()

        gateway_endpoint = os.getenv("gateway_endpoint", MCP_SERVER_URL)
        headers = {"Authorization": f"Bearer {jwt_token}"} if jwt_token else {}

        mcp_client = MCPClient(lambda: streamablehttp_client(url=f"{gateway_endpoint}/mcp", headers=headers))
        mcp_client.__enter__()
        tools = mcp_client.list_tools_sync()
        logger.info(f"Loaded {len(tools)} tools from MCP server")

        model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")

        agent = Agent(
            model=model,
            tools=tools,
            conversation_manager=conversation_manager,
            memory=agent_memory,
            system_prompt="""
            You are an AI assistant for Device Remote Management. Help the user with their query.
            You have access to tools that can retrieve real data from the Device Remote Management system.

            Remember important context and user preferences between interactions,
            such as devices frequently queried or users mentioned earlier.

            Available tools:
            - list_devices: List all devices in the system
            - get_device_settings: Get settings for a specific device
            - list_wifi_networks: List all WiFi networks for a specific device
            - list_users: List all users in the system
            - query_user_activity: Query user activity within a time period
            - update_wifi_ssid: Update the SSID of a Wi-Fi network on a device
            - update_wifi_security: Update the security type of a Wi-Fi network on a device
            """
        )
        logger.info("Agent created successfully with memory support.")
        return agent, mcp_client

    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}", exc_info=True)
        return None, None

agent, mcp_client = (None, None)
if check_mcp_server():
    agent, mcp_client = initialize_agent()

@app.entrypoint
async def process_request(payload):
    global agent, mcp_client
    try:
        user_message = payload.get("prompt", "No prompt found in input, please provide a message")
        logger.info(f"Received user message: {user_message}")

        if not agent:
            if check_mcp_server():
                agent, mcp_client = initialize_agent()
                if not agent:
                    yield {"error": "Failed to initialize agent."}
                    return
            else:
                yield {"error": "MCP server unavailable."}
                return

        stream = agent.stream_async(user_message)
        async for event in stream:
            if "data" in event:
                yield {"type": "chunk", "data": event["data"]}
            elif "result" in event:
                yield {"type": "complete", "final_response": event["result"]}

        # Save memory after each interaction
        try:
            agent_memory.save()
            logger.info("Agent memory saved successfully.")
        except Exception as e:
            logger.error(f"Error saving agent memory: {str(e)}", exc_info=True)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        yield {"error": str(e)}

if __name__ == "__main__":
    app.run()
