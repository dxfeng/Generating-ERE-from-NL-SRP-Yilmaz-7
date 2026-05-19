import sys;
import base64

# for selenium (?)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

args = sys.argv[1:]

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

def standardize_to_dfa(ere:str, creation_events:list, driver):
    '''
    Use Cyberzhg tool to convert RE to min-DFA
    '''

    b64_regex = str(base64.b64encode(ere.encode("ascii")))[2:-1]

    driver.get(f"https://cyberzhg.github.io/toolbox/min_dfa?regex={b64_regex}")

    wait = WebDriverWait(driver, 10)
    table = wait.until(EC.presence_of_element_located((By.ID, "dfa_table")))
    headers = [th.text for th in table.find_elements(By.TAG_NAME, "th")]

    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if cols:  # skip header row
            data.append([col.text for col in cols])

    df = pd.DataFrame(data, columns=headers)
    #print(df)

    '''
    Turn the pandas dataframe that defines the min-DFA into a graph represented by an adjacency list
    '''
    crude_adj = []

    accepting = []
    for i, itm in enumerate(df.iterrows()):
        instance = itm[1]
        if instance['TYPE'] == 'accept':
            accepting.append(i)

        dct = dict(instance)
        del dct['DFA STATE']
        del dct['Min-DFA STATE']
        del dct['TYPE']

        to_remove = []
        for k in dct:
            if not dct[k]:
                to_remove.append(k)
            else:
                dct[k] = int(dct[k]) - 1

        for k in to_remove:
            del dct[k]

        crude_adj.append(dct)

    #print(crude_adj)
    #print(accepting)


    '''
    Split transitions into individual transitions
        a,b -> 0
        ~
        a -> 0
        b -> 0
    '''
    adj = []

    for u in crude_adj:
        v = {}
        for E in u:
            all_transitions = E.split(",")
            for transition in all_transitions:
                v[transition] = u[E]
        adj.append(v)

    #print(adj)

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
        number_not_creation = 0
        for E in adj[0]:
            if E not in creation_events:
                number_not_creation += 1
                continue

            new_first_node[E] = adj[0][E] + 1

        if number_not_creation > 0:
            adj.insert(0, new_first_node)
            for i in range(1, len(adj)):
                adj[i] = {u: adj[i][u] + 1 for u in adj[i]}

            if (0 in accepting):
                accepting.append(-1)
            accepting = [i + 1 for i in accepting]

    #print(adj)
    return adj, accepting


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

def compare_expressions(raw_ground:str, raw_generated:str, creation_events:list, driver):
    global ground_adj, ground_accepting, generated_adj, generated_accepting, equivalent_node, ground_visited, generated_visited
    ground, anom_dict = create_anonymization(raw_ground)
    generated = use_anonymization(raw_generated, anom_dict)

    # Remove all spaces -> they are unnecessary because every event is a single character
    ground = "".join(ground.split())
    generated = "".join(generated.split())
    creation_events = sorted([anom_dict[u] for u in creation_events])


    ground_adj, ground_accepting = standardize_to_dfa(ground, creation_events, driver)
    generated_adj, generated_accepting = standardize_to_dfa(generated, creation_events, driver)
    equivalent_node = {0:0}
    ground_visited = []
    generated_visited = []

    res = check_equivalence(0)

    return res

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

    driver = webdriver.Firefox()
    for i in range(len(ground_truth_ere_list)):
        generated_ere = generated_ere_list[i].split(";")
        ground_truth_ere = ground_truth_ere_list[i].split(";")
        creation_events = ground_truth_ere[2].strip().split(',')
        creation_events.sort()
        res = compare_expressions(ground_truth_ere[0], generated_ere[0], creation_events, driver)
        print(f"Test #{i}:\nGround: {ground_truth_ere[0]}\nGenerated: {generated_ere[0]}\nResult: {res}")

    driver.close()
    print("Driver Closed, Finished Tests")