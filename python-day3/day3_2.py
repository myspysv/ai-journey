def trim_chat_history(messages: list[str], max_messages: int = 5) -> list[str]:
    if max_messages <= 0:
        return []
    return messages[-max_messages:]

res = trim_chat_history(["Hey, are you free to talk later today?" ,
                         "Just saw the funniest video, sending it to you now!",
                         "Running about 10 minutes late, sorry!",
                         "Do we need anything from the grocery store?",
                         "Can't believe it's already Friday.",
                         "Did you end up watching that movie we talked about?",
                         "Let me know when you get home safe.",
                         "Coffee tomorrow morning?"], 5)
print(res)