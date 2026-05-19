import sys;
import base64
import requests
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

def standardize_ere_specs(ere1: list, ere2: list):
    ere1_string, anom_dict = create_anonymization(ere1[0])
    ere2_string = use_anonymization(ere2[0], anom_dict)

    # Remove all spaces -> they are unnecessary because every event is a single character
    ere1_string = "".join(ere1_string.split())
    ere2_string = "".join(ere2_string.split())

    ere1_b64 = str(base64.b64encode(ere1_string.encode("ascii")))[2:-1]
    ere2_b64 = str(base64.b64encode(ere2_string.encode("ascii")))[2:-1]


    return ere1_string, ere2_string

if __name__ == "__main__":
    generated_ere_file = args[0]
    ground_truth_ere_file = args[1]

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

    '''
    Each line in both files should be of format "{ERE};{Match/Fail};{List of Creation Events}"

    For example, for the Socket_InputStreamUnavailable specification 
    (https://github.com/SoftEngResearch/tracemop/blob/master/scripts/props/Socket_InputStreamUnavailable.mop)

    (create_connected | create_unconnected connect) get* (close | shutdown)*;fail;create_connected,create_unconnected
    '''

    n = len(generated_ere_list)
    generated_ere_new = []
    ground_truth_ere_new = []

    for i in range(n):
        generated_ere = generated_ere_list[i].split(";")
        ground_truth_ere = ground_truth_ere_list[i].split(";")

        a,b = standardize_ere_specs(generated_ere, ground_truth_ere)

        generated_ere_new.append(a)
        ground_truth_ere_new.append(b)

    f = open("standardized_" + generated_ere_file, 'w')
    f.write("\n".join(generated_ere_new))
    f.close()

    print("Created standardized_" + generated_ere_file + " containing standardized generated ere")
    f = open("standardized_" + ground_truth_ere_file, 'w')
    f.write("\n".join(ground_truth_ere_new))
    f.close()

    print("Created standardized_" + ground_truth_ere_file + " containing standardized ground-truth ere")

