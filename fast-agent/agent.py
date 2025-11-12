import asyncio

from fast_agent import FastAgent
from fast_agent.interfaces import AgentProtocol
from fast_agent.mcp.ui_agent import McpAgentWithUI

import requests
import json
from typing import List, Dict

# Create the application
fast = FastAgent("fast-agent example")

default_instruction = """You are a helpful AI Agent.

{{serverInstructions}}

{{agentSkills}}

The current date is {{currentDate}}."""


# Detection API configuration
DETECTION_API_URL = "http://localhost:5000/api/detect"

async def detect_tool(tool_name: str, description: str) -> Dict:
    """
    Call the MCP Tool Detection API to analyze a tool
    
    Args:
        tool_name: Name of the tool
        description: Tool description to analyze
    
    Returns:
        Detection result dictionary
    """
    try:
        response = requests.post(
            DETECTION_API_URL,
            json={
                "tool_name": tool_name,
                "description": description
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['result']
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP Error {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("⚠️  Make sure the detection API is running: uv run python app.py")
        return None

def print_detection_result(tool_name: str, result: Dict):
    """
    Pretty print the detection result
    
    Args:
        tool_name: Name of the tool
        result: Detection result dictionary
    """
    if not result:
        return
    
    # Color coding
    if result['result'] == 'Injection':
        color_emoji = "🚨"
        color_text = "\033[91m"  # Red
    elif result['result'] == 'Warning':
        color_emoji = "⚠️"
        color_text = "\033[93m"  # Yellow
    else:
        color_emoji = "✅"
        color_text = "\033[92m"  # Green
    
    reset_color = "\033[0m"
    
    print(f"\n{color_text}{'='*60}{reset_color}")
    print(f"{color_emoji} {color_text}Tool: {tool_name}{reset_color}")
    print(f"{color_text}Result: {result['result']}{reset_color}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Severity: {result['severity']}")
    
    if result.get('detected_patterns'):
        print(f"\n{color_text}Detected Patterns:{reset_color}")
        for pattern in result['detected_patterns']:
            print(f"  • {pattern['category']}: {', '.join(pattern['keywords'])} (score: {pattern['score']})")
    
    print(f"{color_text}{'='*60}{reset_color}")

# Define the agent
@fast.agent(instruction=default_instruction, 
            servers=["tool-poisoning","filesystem"])
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        default_agent = agent["default"]
        print(f"Agent type: {type(default_agent)}")

        # ✅ Use the list_tools() coroutine method
        try:
            result = await default_agent.list_tools()
            
            if hasattr(result, "tools"):
                tools = result.tools
                print(f"\n{'='*60}")
                print(f"🔍 Found {len(tools)} tools to analyze")
                print(f"{'='*60}\n")
                
                # Analyze each tool with the detection API
                detection_results = []
                
                for i, tool in enumerate(tools, 1):
                    print(f"\n[{i}/{len(tools)}] Analyzing: {tool.name}")
                    print(f"Description: {tool.description[:100]}{'...' if len(tool.description) > 100 else ''}")
                    
                    # Call detection API
                    detection_result = await detect_tool(tool.name, tool.description)
                    
                    if detection_result:
                        detection_results.append(detection_result)
                        print_detection_result(tool.name, detection_result)
                    else:
                        print(f"⚠️  Failed to analyze {tool.name}")
                
                # Summary
                print(f"\n{'='*60}")
                print("📊 DETECTION SUMMARY")
                print(f"{'='*60}")
                
                if detection_results:
                    injection_count = sum(1 for r in detection_results if r['result'] == 'Injection')
                    warning_count = sum(1 for r in detection_results if r['result'] == 'Warning')
                    normal_count = sum(1 for r in detection_results if r['result'] == 'Normal')
                    
                    print(f"Total Tools Analyzed: {len(detection_results)}")
                    print(f"🚨 Injections Detected: {injection_count}")
                    print(f"⚠️  Warnings: {warning_count}")
                    print(f"✅ Normal: {normal_count}")
                    
                    if injection_count > 0:
                        print(f"\n{'='*60}")
                        print("⚠️  CRITICAL: Malicious tools detected!")
                        print("⚠️  Review the detection results above before using these servers.")
                        print(f"{'='*60}")
                else:
                    print("No tools were successfully analyzed.")
                    
            else:
                print("No tools found or list_tools() returned no results.")
                
        except Exception as e:
            print(f"Error while listing tools: {e}")
            import traceback
            traceback.print_exc()
            
        # Interactive mode
        await agent.interactive()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

