# provide this for backwards compatibility:
def tool_api(*args, **kwargs):
	from .api import tool_api
	return tool_api(*args, **kwargs)
