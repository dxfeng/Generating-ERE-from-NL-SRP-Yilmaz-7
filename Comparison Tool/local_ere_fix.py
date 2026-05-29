import sys;
import time

args = sys.argv[1:]
import base64
import pandas as pd

import string
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA



def create_anonymization(ere:str):
    '''
    Generates and applies a mapping of the events to unique characters.
    This is done as regex comparison tools view "event" as 5 seperate entities, first the letter e,
    then the letter v, and so on.
    In ERE for TraceMOP, "event" is a single entity.
    The number of unique events is limited to 26 using this algorithm, the capital letters of the alphabet.
    The special epsilon events will be replaced with the "ϵ", a character.
    '''
    ere += " " # Append " " to the ERE so that if the final event has no operator it will still add it to the new ERE

    curr_replacement = "A" # This is the current replacement for the event. Note that this means there is at most 26 events, but that is enough for TraceMOP's dataset
    curr_event = "" # This is a string where we store the name of the current event
    event_dict = {"epsilon":"ϵ"} # This is a dictionary that stores the events that have been found so far. Epsilon, the empty event, is instantialized to the ~
    new_ere = "" # This is the new ere that we create after anonymization

    valid_char = [*range(ord('a'), ord('z')+1), *range(ord('0'), ord('9')+1), ord("_")]
    '''
    This is a list of all characters allowed in event names.
    None of these are operators so if a character is in this set it must be part of an event name.
    '''
    for c in ere: # Iterate over each character
        if ord(c) in valid_char:
            curr_event += c # If the character is in the valid_char list, add it to the back of the current event
        else:

            if curr_event:# If the character is not in the valid_char list, we first check if there was an event name that finished.
                if curr_event in event_dict: # if the event has occured before, we use the replacement character
                    new_ere += event_dict[curr_event]
                else: #If the event has not occured before:
                    event_dict[curr_event] = curr_replacement #1. We first add it to the event dictionary
                    new_ere += curr_replacement #2. we then add that character to the new ERE
                    curr_replacement = chr(ord(curr_replacement)+1) #3. Then we incremement the current replacement character

                curr_event = "" # We reset the current event back to the empty string as we have finished parsing that event

            new_ere += c # add the non-valid character
    return new_ere, event_dict #we return the new ERe, and the event dictionary to be used in anonymising the other ERE
def use_anonymization(ere:str, anonymization_map:dict):
    '''
    Takes an ere and a anonymization map as input.
    Uses the mapping generated from create_anonymization to replace the events
    with single unique characters.
    If an event in this ere is not in the anonymization_map, it replaces them starting with the lowercase alphabet.
    '''
    ere += " "

    curr_event = ""
    new_ere = ""
    curr_replacement = "a"
    '''
    We still need the curr_replacement string because there could be events found in this ERE that were not inside the previous ERE
    We start at "a" instead of "A" to differentiate.
    '''

    valid_char = [*range(ord('a'), ord('z') + 1), *range(ord('0'), ord('9') + 1), ord("_")]
    for c in ere:
        if ord(c) in valid_char:
            curr_event += c
        else:
            if curr_event:
                if curr_event not in anonymization_map: # If the event was not in the previous ERE, we perform the same steps as earlier.
                    anonymization_map[curr_event] = curr_replacement # 1. We add the new character into the anonymization_map
                    new_ere += curr_replacement # 2. We add the character to the new ERE
                    curr_replacement = chr(ord(curr_replacement)+1) # 3. We increment the current replacement character
                else: # If the event has been seen before, we add the replacement character to the new ERE
                    new_ere += anonymization_map[curr_event]

                curr_event = ""
            new_ere += c
    return new_ere # We return only the new_ere

def standardize_to_dfa(ere:str, creation_events:list):
    '''
    Use automaton to convert to min-dfa
    '''

    alphabet = set(string.ascii_uppercase)|set(string.ascii_lowercase)
    nfa = NFA.from_regex(ere, input_symbols=alphabet)
    dfa = DFA.from_nfa(nfa)


    adj = dfa.transitions
    initial_state = dfa.initial_state
    accepting = dfa.final_states
    adj = {k: {c: adj[k][c] for c in adj[k]} for k in adj}

    '''
    Remove terminal state edges (only apply if @match type). Then run a dfs from the root node to see what nodes may have been impacted
        Determining if this will be included should be discussed
    '''
    # for x in accepting:
    #     adj[x] = {}

    '''
    Use this if creation events exist.
    '''
    if creation_events:
        new_first_node = {}
        num_not_creation = 0
        for E in adj[initial_state]:
            if E not in creation_events:
                num_not_creation += 1
                continue
            new_first_node[E] = adj[initial_state][E]
        if num_not_creation:
            mex = 0
            while mex in adj:
                mex += 1
            adj[mex] = new_first_node
            initial_state = mex

    #print(adj)
    all_transitions = set(string.ascii_lowercase)|set(string.ascii_uppercase)

    new_dfa = DFA(
        states={k for k in adj.keys()},
        input_symbols=all_transitions,
        transitions=adj,
        initial_state=initial_state,
        final_states=accepting,
        allow_partial=True
    )

    return new_dfa


ground_adj = []
ground_accepting = []
generated_adj = []
generated_accepting = []

equivalent_node = {0:0}
ground_visited = []
generated_visited = []

def check_equivalence(u: int):
    v = equivalent_node[u]
    ground_visited.append(u)
    generated_visited.append(v)

    accepting_difference = (u in ground_accepting) == (v in generated_accepting)
    size_difference = len(generated_adj) - len(ground_adj)
    equivalent_size_difference = len(generated_adj[v]) - sum(k in generated_adj[v] for k in ground_adj[u])

    if (not accepting_difference) or (size_difference != 0) or (equivalent_size_difference != 0):
        return False

    all_valid = []
    for s in ground_adj[u]:
        if ground_adj[u][s] in ground_visited and equivalent_node[ground_adj[u][s]] != generated_adj[v][s]:
            return False
        if generated_adj[v][s] in ground_visited and ground_adj[u][s] not in equivalent_node:
            return False

        if ground_adj[u][s] not in ground_visited and generated_adj[v][s] not in generated_visited:
            equivalent_node[ground_adj[u][s]] = generated_adj[v][s]
            all_valid.append(ground_adj[u][s])

    return not (False in all_valid)

def compare_expressions(raw_ground:str, raw_generated:str, creation_events:list):
    global ground_adj, ground_accepting, generated_adj, generated_accepting, equivalent_node, ground_visited, generated_visited
    ground, anom_dict = create_anonymization(raw_ground)
    generated = use_anonymization(raw_generated, anom_dict)

    # Remove all spaces -> they are unnecessary because every event is a single character
    ground = "".join(ground.split())
    generated = "".join(generated.split())
    ground = ground.replace("ϵ", "()")
    generated = generated.replace("ϵ", "()")
    creation_events = sorted([anom_dict[u] for u in creation_events])


    ground_dfa = standardize_to_dfa(ground, creation_events)
    generated_dfa = standardize_to_dfa(generated, creation_events)

    diff1 = ground_dfa.difference(generated_dfa)
    diff2 = generated_dfa.difference(ground_dfa)
    return diff1.isempty() and diff2.isempty()

if __name__ == "__main__":
    generated_ere_file = args[0] # ere
    ground_truth_ere_file = args[1] # ere;match/fail;creation_events

    f = open(generated_ere_file, 'r')
    generated_ere_list = []
    for l in f.readlines():
        generated_ere_list.append(l)
    f.close()

    f = open(ground_truth_ere_file, 'r')
    ground_truth_ere_list = []
    for l in f.readlines():
        ground_truth_ere_list.append(l)
    f.close()

    for i in range(len(ground_truth_ere_list)):
        generated_ere = generated_ere_list[i].split(";")
        ground_truth_ere = ground_truth_ere_list[i].split(";")
        creation_events = ground_truth_ere[2].strip().split(',')
        creation_events.sort()
        res = compare_expressions(ground_truth_ere[0].strip(), generated_ere[0].strip(), creation_events)
        print(f"Test #{i}:\nGround: {ground_truth_ere[0].strip()}\nGenerated: {generated_ere[0].strip()}")
        print(f"Result: {res}")
        print()

    print("Finished Tests")