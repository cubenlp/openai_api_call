import os, responses
from openai_api_call import Chat, load_chats, process_chats

def test_with_checkpoint():
    # save chats without chatid
    chat = Chat()
    checkpath = "tmp.log"
    chat.save(checkpath, mode="w")
    chat = Chat("hello!")
    chat.save(checkpath) # append
    chat.assistant("你好, how can I assist you today?")
    chat.save(checkpath) # append
    ## load chats
    chat_logs = load_chats(checkpath, chat_log_only=True)
    assert chat_logs == [[], [{'role': 'user', 'content': 'hello!'}],
                          [{'role': 'user', 'content': 'hello!'}, 
                           {'role': 'assistant', 'content': '你好, how can I assist you today?'}]]
    chat_msgs = load_chats(checkpath, last_message_only=True)
    assert chat_msgs == ["", "hello!", "你好, how can I assist you today?"]
    chats = load_chats(checkpath)
    assert chats == [Chat(log) for log in chat_logs]

    # save chats with chatid
    chat = Chat()
    checkpath = "tmp.log"
    chat.save(checkpath, mode="w", chatid=0)
    chat = Chat("hello!")
    chat.save(checkpath, chatid=3)
    chat.assistant("你好, how can I assist you today?")
    chat.save(checkpath, chatid=2)
    ## load chats
    chat_logs = load_chats(checkpath, chat_log_only=True)
    assert chat_logs == [[], None, 
                         [{'role': 'user', 'content': 'hello!'}, {'role': 'assistant', 'content': '你好, how can I assist you today?'}],
                           [{'role': 'user', 'content': 'hello!'}]]
    chat_msgs = load_chats(checkpath, last_message_only=True)
    assert chat_msgs == ["", None, "你好, how can I assist you today?", "hello!"]
    chats = load_chats(checkpath)
    assert chats == [Chat(log) if log is not None else None for log in chat_logs]

def test_process_chats():
    api_key = os.environ.get("OPENAI_API_KEY")
    # assert api_key is not None # TODO: Add the key to the environment variables
    def msg2chat(msg):
        chat = Chat(api_key=api_key)
        chat.system("You are a helpful translator for numbers.")
        chat.user(f"Please translate the digit to Roman numerals: {msg}")
        # chat.getresponse()
        chat.assistant("III")
        return chat
    checkpath = "tmp.log"
    # first call
    msgs = ["1", "2", "3"]
    chats = process_chats(msgs, msg2chat, checkpath, clearfile=True)
    for chat in chats:
        print(chat[-1])
    assert len(chats) == 3
    assert all([len(chat) == 3 for chat in chats])
    # continue call
    msgs = msgs + ["4", "5", "6"]
    continue_chats = process_chats(msgs, msg2chat, checkpath, clearfile=False)
    assert len(continue_chats) == 6
    assert all(c1 == c2 for c1, c2 in zip(chats, continue_chats[:3]))
    assert all([len(chat) == 3 for chat in continue_chats])

    # get the last message only
    last_msgs = process_chats(msgs, msg2chat, checkpath, clearfile=False, last_message_only=True)
    assert last_msgs == [chat[-1]['content'] for chat in continue_chats]
    last_msgs = process_chats(msgs[:3], msg2chat, checkpath, clearfile=False, last_message_only=True)
    assert last_msgs == [chat[-1]['content'] for chat in continue_chats[:3]]
    
    
    