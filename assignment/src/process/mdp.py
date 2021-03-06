# TODO: how to implement MDP "incrementally" based on MRP?

from typing import Generic, Union, Sequence, Tuple
from src.type_vars import S, A, SSf, SASf, SASTff, SATSff, Vf, Rf, Qf
from src.process.policy import Policy
from src.process.mrp import MRP


class MDP(Generic[S, A]):
    def __init__(self, mdp_input: Union[SASTff, SATSff], discount_factor: float) -> None:
        self.type_indicator: bool = MDP.input_type(mdp_input)
        self.gamma: float = discount_factor
        self.all_states, self.all_actions = self._get_all_states_and_actions(
            mdp_input)
        self.terminal_states, self.non_terminal_states = self._categorize_states(
            mdp_input)
        self.transition_matrix: Tuple[SASf, SASf] = self._assign_transition_matrix(
            mdp_input)

    # return True if SASTff, False if SATSff
    # TODO: unify with the same method in MRP
    @staticmethod
    def input_type(mdp_input: Union[SASTff, SATSff]) -> bool:
        first_value = mdp_input.get(next(iter(mdp_input)))
        return type(first_value) is dict

    def _get_all_states_and_actions(self, mdp_input: Union[SASTff, SATSff]) -> Tuple[Sequence[S], Sequence[A]]:
        state_list = []
        action_list = []
        for sa_tuple in mdp_input:
            if sa_tuple[0] not in state_list:
                state_list.append(sa_tuple[0])
            if sa_tuple[1] not in action_list:
                action_list.append(sa_tuple[1])
        # note that we also need to consider the case where a state s' only appears (s,a): {s': P(s, a, s')},
        # which implicitly states s' is a terminal state, this case is more convenient to be considered in
        # _categorize_states()
        return state_list, action_list

    def _categorize_states(self, mdp_input: Union[SASTff, SATSff]) -> Tuple[Sequence[S], Sequence[S]]:
        # list of terminal states
        terminal_states = self.all_states.copy()
        non_terminal_states = []
        temp = []
        for (s, a) in mdp_input:
            if self.type_indicator is True:
                for s1 in mdp_input.get((s, a)):
                    if (s1 not in self.all_states) and (s1 not in temp):
                        temp.append(s1)
                if mdp_input.get((s, a)).get(s) is None or mdp_input.get((s, a)).get(s)[0] != 1:
                    if s in terminal_states:
                        terminal_states.remove(s)
                        non_terminal_states.append(s)
            else:
                for s1 in mdp_input.get((s, a))[0]:
                    if (s1 not in self.all_states) and (s1 not in temp):
                        temp.append(s1)
                if mdp_input.get((s, a))[0].get(s, 0) != 1:
                    if s in terminal_states:
                        terminal_states.remove(s)
                        non_terminal_states.append(s)
        self.all_states += temp
        terminal_states += temp
        return terminal_states, non_terminal_states

    def _assign_transition_matrix(self, mdp_input: Union[SASTff, SATSff]):
        state_transition_matrix = {}
        reward_matrix = {}
        if self.type_indicator is True:
            for sa_tuple in mdp_input:
                if sa_tuple[0] not in self.terminal_states:
                    state_value = {}
                    reward_value = {}
                    for s2 in mdp_input.get(sa_tuple):
                        state_value.update(
                            {s2: mdp_input.get(sa_tuple).get(s2)[0]})
                        reward_value.update(
                            {s2: mdp_input.get(sa_tuple).get(s2)[1]})
                state_transition_matrix.update({sa_tuple: state_value})
                reward_matrix.update({sa_tuple: reward_value})
        else:
            for sa_tuple in mdp_input:
                if sa_tuple[0] not in self.terminal_states:
                    state_transition_matrix.update(
                        {sa_tuple: mdp_input.get(sa_tuple)[0]})
                    reward_value = {}
                    for s2 in mdp_input.get(sa_tuple)[0]:
                        reward_value.update({s2: mdp_input.get(sa_tuple)[1]})
                    reward_matrix.update({sa_tuple: reward_value})
        return state_transition_matrix, reward_matrix

    # convert MDP to MRP given policy
    # SASTff -> SSTff, SATSff -> STSff
    def get_mrp(self, policy: Policy) -> MRP:
        state_transition_matrix: SASf = self.transition_matrix[0]
        reward_matrix: SASf = self.transition_matrix[1]
        # convert transition matrix (SASf -> SSf)
        mrp_state_transition_matrix: SSf = {}
        mrp_reward_matrix: SSf = {}

        for s in self.all_states:
            for s1 in self.all_states:
                p_s_s1 = sum([state_transition_matrix[(
                    s, a, s1)] * policy.get_state_action_probability(s, a) for a in self.all_actions])
                mrp_state_transition_matrix.update({(s, s1): p_s_s1})
                r_s_s1 = sum([reward_matrix[(
                    s, a, s1)] * policy.get_state_action_probability(s, a) for a in self.all_actions])
                mrp_reward_matrix.update({(s, s1): r_s_s1})
        # TODO: return MRP class instance rather than two matrices
        return mrp_state_transition_matrix, mrp_reward_matrix

    def query_Pr(self, s: S, a: A, s1: S) -> float:
        return self.transition_matrix[0].get((s, a)).get(s1)

    def query_R(self, s: S, a: Union[A, None]) -> float:
        if a is None:
            a = self.all_actions[0]
        return self.transition_matrix[1].get((s, a))

    def query_successor(self, s: S, a: A) -> Sequence[S]:
        return [s1 for s1 in self.all_states if s1 in self.transition_matrix[0].get((s, a)).keys()]


if __name__ == '__main__':
    # the following example is from the sample code
    input1 = {
        (1, 'a'): ({1: 0.3, 2: 0.6, 3: 0.1}, 5.0),
        (1, 'b'): ({2: 0.3, 3: 0.7}, 2.8),
        (1, 'c'): ({1: 0.2, 2: 0.4, 3: 0.4}, -7.2),
        (2, 'a'): ({1: 0.3, 2: 0.6, 3: 0.1}, 5.0),
        (2, 'c'): ({1: 0.2, 2: 0.4, 3: 0.4}, -7.2),
        (3, 'a'): ({3: 1.0}, 0.0),
        (3, 'b'): ({3: 1.0}, 0.0)
    }

    input2 = {
        (1, 'a'): {1: (0.3, 5.0), 2: (0.6, 5.0), 3: (0.1, 5.0)},
        (1, 'b'): {2: (0.3, 2.8), 3: (0.7, 2.8)},
        (1, 'c'): {1: (0.2, -7.2), 2: (0.4, -7.2), 3: (0.4, -7.2)},
        (2, 'a'): {1: (0.3, 5.0), 2: (0.6, 5.0), 3: (0.1, 5.0)},
        (2, 'c'): {1: (0.2, -7.2), 2: (0.4, -7.2), 3: (0.4, -7.2)},
        (3, 'a'): {3: (1.0, 0.0)},
        (3, 'b'): {3: (1.0, 0.0)}
    }

    # the following is the Student MDP example in David Silver's slides
    student_mdp = {
        ('Class 1', 'Study'): ({'Class 2': 1.0}, -2),
        ('Class 1', 'Facebook'): ({'Facebook': 1.0}, -1),
        ('Facebook', 'Facebook'): ({'Facebook': 1.0}, -1),
        ('Facebook', 'quit'): ({'Class 1': 1.0}, 0),
        ('Class 2', 'Study'): ({'Class 3': 1.0}, -2),
        ('Class 2', 'Sleep'): ({'Sleep': 1.0}, 0),
        ('Class 3', 'Study'): ({'Sleep': 1.0}, +10),
        ('Class 3', 'Pub'): ({'Class 1': 0.2, 'Class 2': 0.4, 'Class 3': 0.4}, 1),
    }

    mdp_obj = MDP(student_mdp, 1.0)
    print("all states: ", mdp_obj.all_states)
    print("terminal states: ", mdp_obj.terminal_states)
    print("non-terminal states: ", mdp_obj.non_terminal_states)
    print("all actions: ", mdp_obj.all_actions)
    print(mdp_obj.transition_matrix[0])
    print(mdp_obj.transition_matrix[1])
