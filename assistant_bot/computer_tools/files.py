from langchain.tools import Tool


def file_read(file_path: str) -> str:
    try:
        with open(file_path, "r") as file:
            return file.read()
    except Exception as e:
        return str(e)


def file_save(file_path: str, content: str) -> str:
    try:
        with open(file_path, "w") as file:
            file.write(content)
        return f"File saved successfully to {file_path}"
    except Exception as e:
        return str(e)


file_save_tool = Tool(
    name="file_save_tool",
    func=file_save,
    description="Save content to a file on the computer where the agent is running",
)

file_read_tool = Tool(
    name="file_read_tool",
    func=file_read,
    description="Read the content of a file from the computer where the agent is running",
)
