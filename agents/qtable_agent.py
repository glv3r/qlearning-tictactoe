import random

from environment.environment import Agent, legal_moves


class QTableAgent(Agent):
    def __init__(self, agent_name, epsilon):
        super().__init__(agent_name=agent_name)
        self.q_table = {}
        self.epsilon = epsilon

    def ensure_state(self, state):
        if state not in self.q_table:
            self.q_table[state] = {}

            for i in legal_moves(state):
                self.q_table[state][i] = 0
    

    def choose_move(self, board, mark) -> int:
        state = board

        self.ensure_state(state)
        if random.random() < self.epsilon:
            return random.choice(legal_moves(board))
        else:
            high = max(self.q_table[state].values())
            best_actions = []
            for action in self.q_table[state]:
                value = self.q_table[state][action]
                if value == high:
                    best_actions.append(action)
            return random.choice(best_actions)


    def update(self, state, action, reward, next_state, alpha, gamma):
        old_value = self.q_table[state][action]
        if next_state is None:
            future_value = 0
        else:
            self.ensure_state(next_state)
            future_value = max(self.q_table[next_state].values())

        target = reward + gamma * future_value

        new_value = old_value + alpha * (target - old_value)

        self.q_table[state][action] = new_value 
    


    

        
        
    
