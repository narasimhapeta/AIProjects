from __future__ import annotations
from livekit import agents
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm
)
# from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import ( openai  )

from dotenv import load_dotenv
import os
from api import AssistantFnc
from prompts import WELCOME_MESSAGE, LOOKUP_VIN_MESSAGE
load_dotenv()

async def entrypoint(ctx: JobContext):
    ##Created room
    await ctx.connect(auto_subscribe= AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()
    # Creating AI Agent
       
    assistant_fnc = AssistantFnc()
    
    ##Agent joining livekit room
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="coral")
    )

    await session.start(
        room=ctx.room,
        agent=AssistantFnc(),
        room_input_options=RoomInputOptions(
            
        )
    )    

    await session.generate_reply(
        instructions=WELCOME_MESSAGE
    )

    @session.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        if isinstance(msg.content, list):
            msg.content = "\n".join("[image]" if isinstance(x, llm.ChatImage) else x for x in msg)
            
        if assistant_fnc.has_car():
            handle_query(msg)
        else:
            find_profile(msg)
        
    def find_profile(msg: llm.ChatMessage):
        session.conversation.item.create(
            llm.ChatMessage(
                role="system",
                content=LOOKUP_VIN_MESSAGE(msg)
            )
        )
        session.response.create()
        
    def handle_query(msg: llm.ChatMessage):
        session.conversation.item.create(
            llm.ChatMessage(
                role="user",
                content=msg.content
            )
        )
        session.response.create()

   


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
