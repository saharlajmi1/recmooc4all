from app.models.agent_state import AgentState
from workflow import workflow
class ResponseGenerationServiceImpl:


    def generate_response(
        self, state
    ):
       
        app = workflow.create_workflow(AgentState)
        data = app.invoke(state)
        print(data)
