import asyncio, aiohttp
import time, random, warnings, json, os
from typing import List, Dict, Union
from openai_api_call import Chat, Resp, load_chats
import openai_api_call
from tqdm.asyncio import tqdm

async def async_post( session
                    , sem
                    , url
                    , data:str
                    , max_requests:int=1
                    , timeinterval=0
                    , timeout=0):
    """Asynchronous post request

    Args:
        session : aiohttp session
        sem : semaphore
        url (str): chat completion url
        data (str): payload of the request
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
    
    Returns:
        str: response text
    """
    async with sem:
        ntries = 0
        while max_requests > 0:
            try:    
                async with session.post(url, data=data, timeout=timeout) as response:
                    return await response.text()
            except Exception as e:
                max_requests -= 1
                ntries += 1
                time.sleep(random.random() * timeinterval)
                print(f"Request Failed({ntries}):{e}")
        else:
            warnings.warn("Maximum number of requests reached!")
            return None

async def async_process_msgs( chatlogs:List[List[Dict]]
                            , chkpoint:str
                            , api_key:str
                            , chat_url:str
                            , max_requests:int=1
                            , ncoroutines:int=1
                            , timeout:int=0
                            , timeinterval:int=0
                            , **options
                            )->List[bool]:
    """Process messages asynchronously

    Args:
        chatlogs (List[List[Dict]]): list of chat logs
        chkpoint (str): checkpoint file
        api_key (Union[str, None], optional): API key. Defaults to None.
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        ncoroutines (int, optional): number of coroutines. Defaults to 5.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.

    Returns:
        List[bool]: list of responses
    """
    # load from checkpoint
    chats = load_chats(chkpoint, withid=True) if os.path.exists(chkpoint) else []
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key
    }
    ncoroutines += 1 # add one for the main coroutine
    sem = asyncio.Semaphore(ncoroutines)
    locker = asyncio.Lock()

    async def chat_complete(ind, locker, chatlog, chkpoint, **options):
        payload = {"messages": chatlog}
        payload.update(options)
        data = json.dumps(payload)
        response = await async_post( session=session
                                   , sem=sem
                                   , url=chat_url
                                   , data=data
                                   , max_requests=max_requests
                                   , timeinterval=timeinterval
                                   , timeout=timeout)
        if response is None:return False
        resp = Resp(json.loads(response))
        if not resp.is_valid():
            warnings.warn(f"Invalid response: {resp.error_message}")
            return False
        ## saving files
        chatlog.append(resp.message)
        chat = Chat(chatlog)
        async with locker: # locker | not necessary for normal IO
            chat.savewithid(chkpoint, chatid=ind)
        return True

    async with sem, aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for ind, chatlog in enumerate(chatlogs):
            if ind < len(chats) and chats[ind] is not None: # skip completed chats
                continue
            tasks.append(
                asyncio.create_task(
                    chat_complete( ind=ind
                                 , locker=locker
                                 , chatlog=chatlog
                                 , chkpoint=chkpoint
                                 , **options)))
        if openai_api_call.platform == "macos":
            responses = await tqdm.gather(tasks)
        else: # not work for windows yet
            responses = await asyncio.gather(*tasks)
        return responses

def async_chat_completion( chatlogs:List[List[Dict]]
                         , chkpoint:str
                         , model:str='gpt-3.5-turbo'
                         , api_key:Union[str, None]=None
                         , chat_url:Union[str, None]=None
                         , max_requests:int=1
                         , ncoroutines:int=1
                         , timeout:int=0
                         , timeinterval:int=0
                         , clearfile:bool=False
                         , notrun:bool=False
                         , **options
                         ):
    """Asynchronous chat completion

    Args:
        chatlogs (List[List[Dict]]): list of chat logs
        chkpoint (str): checkpoint file
        model (str, optional): model to use. Defaults to 'gpt-3.5-turbo'.
        api_key (Union[str, None], optional): API key. Defaults to None.
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        ncoroutines (int, optional): number of coroutines. Defaults to 5.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.
        clearfile (bool, optional): whether to clear the checkpoint file. Defaults to False.

    Returns:
        List[Dict]: list of responses
    """
    if clearfile and os.path.exists(chkpoint):
        os.remove(chkpoint)
    if api_key is None:
        api_key = openai_api_call.api_key
    assert api_key is not None, "API key is not provided!"
    if chat_url is None:
        chat_url = os.path.join(openai_api_call.base_url, "v1/chat/completions")
    chat_url = openai_api_call.request.normalize_url(chat_url)
    # run async process
    assert ncoroutines > 0, "ncoroutines must be greater than 0!"
    args = {
        "chatlogs": chatlogs,
        "chkpoint": chkpoint,
        "api_key": api_key,
        "chat_url": chat_url,
        "max_requests": max_requests,
        "ncoroutines": ncoroutines,
        "timeout": timeout,
        "timeinterval": timeinterval,
        "model": model,
        **options
    }
    if notrun: # when use in Jupyter Notebook
        return async_process_msgs(**args) # return the async object
    else:
        return asyncio.run(async_process_msgs(**args))