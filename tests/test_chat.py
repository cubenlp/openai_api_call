# Test for the Chat class
from openai_api_call import Chat, Resp
import openai_api_call, json

# test for the chat class
def test_chat():
    # initialize
    chat = Chat()
    assert chat.chat_log == []
    chat = Chat([{"role": "user", "content": "hello!"}])
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat = Chat("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]

    # general usage
    chat = Chat()
    chat.user("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat.assistant("Hello, how can I assist you today?")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}
    ]
    chat.system("I am a system message")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"},
        {"role": "system", "content": "I am a system message"}
    ]
    chat.clear()
    assert chat.chat_log == []

    # user/assistant/system
    chat.user("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat.assistant("Hello, how can I assist you today?")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}
    ]
    chat.system("I am a system message")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"},
        {"role": "system", "content": "I am a system message"}
    ]
    # get index
    assert chat[0]['content'] == "hello!"
    assert chat[1]['content'] == "Hello, how can I assist you today?"
    assert chat[2]['content'] == "I am a system message"
    assert chat[-1]['content'] == "I am a system message"
    # pop/copy/clear
    chat.pop()
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}
    ]
    chat.pop()
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"}
    ]
    chat.pop()
    assert chat.chat_log == []
    chat.user("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat.assistant("Hello, how can I assist you today?")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2 = chat.copy()
    assert chat2.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2.user("hello!")
    assert chat2.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"},
        {"role": "user", "content": "hello!"}]
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2.pop()
    assert chat2.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2.clear()
    assert chat2.chat_log == []
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    
    # save json
    chat.save("test.log", mode="w")
    with open("test.log", "r") as f:
        data = json.loads(f.read())
    chat2 = Chat(data)
    assert chat2.chat_log == chat.chat_log

    # print log
    chat.print_log()
    chat.print_log(sep='\n')
    assert True
    print(chat)
    repr(chat)
    assert True

    # len
    assert len(chat) == 2
    chat.pop()
    assert len(chat) == 1

# test for long chatting
response = {
    "id":"chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls",
    "object":"chat.completion",
    "created":1679408728,
    "model":"gpt-3.5-turbo-0301",
    "usage":{
        "prompt_tokens":8,
        "completion_tokens":10,
        "total_tokens":18
    },
    "choices":[
        {
            "message":{
                "role":"assistant",
                "content":"Hello, how can I assist you today?"
            },
            "finish_reason":"stop",
            "index":0
        }
    ]
}

def test_long_talk():
    resp = Resp(response=response)
    msg = "hello!"
    chat = Chat(msg)
    chat.assistant(resp.content)
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    
def test_with_template():
    chat = Chat("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    openai_api_call.default_prompt = lambda msg: [
        {"role": "system", "content": "I am a system message"},
        {"role": "user", "content": msg}]
    chat = Chat("hello!")
    assert chat.chat_log == [
        {"role": "system", "content": "I am a system message"},
        {"role": "user", "content": "hello!"}]
    openai_api_call.default_prompt = None
    chat = Chat("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
