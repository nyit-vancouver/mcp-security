from langchain.tools import Tool


def execute_command(command: str) -> str:
    import subprocess

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return str(e)


execute_tool = Tool(
    name="execute_command_tool",
    func=execute_command,
    description="executes a shell command and returns the output or error message on the computer where the agent is running",
)
