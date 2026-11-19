
from crewai.types.streaming import StreamChunkType
from market_research_agent.crew import MarketResearchAgent
from market_research_agent.events import event_queue


def run(inputs):
    crew = MarketResearchAgent().crew()
    streaming = crew.kickoff(inputs=inputs)

    final_task_index = len(crew.tasks) - 1

    for chunk in streaming:
        if (
            chunk.task_index == final_task_index
            and chunk.chunk_type == StreamChunkType.TEXT
            and chunk.content
        ):
            event_queue.put({
                "type": "brd_stream_chunk",
                "content": chunk.content,
            })

    return streaming.result
