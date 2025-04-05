import raysim

class MyState(raysim.AgentState):
    @staticmethod
    def agent():
        return MyAgent
    
    funds: int
    position: tuple[int, int]


class MyAgent(raysim.Agent):
    def move(self):
        pass