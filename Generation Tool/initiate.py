from openai import OpenAI
import regex as re
import sys;
import base64
import requests
args = sys.argv[1:]

if __name__ == "__main__":
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )

    with open(args[0], "r") as file:
        testmop = file.read()

    # get the comment
    match = re.search(r"/\*\*.*?\*/", testmop, re.DOTALL)
    no_asterisks = match.group(0).replace("*", "")
    NL_COMMENT = " ".join(no_asterisks.split())

    # get the parameterization
    match = re.search(r".*?{", testmop)
    PARAMS = match.group(0)[:-2]

    # get the events
    EVENTS = []
    remove_from_ere = testmop[:re.search(r"ere\s*:", testmop).span(0)[0]]
    while ((u:=re.search(r"(?:creation )?event (?!.*(?:creation )?event).*", remove_from_ere, re.DOTALL))):
        start_ind = u.span(0)[0]
        EVENTS.append(remove_from_ere[start_ind:].strip())
        remove_from_ere = remove_from_ere[:start_ind]
    # get the handler
    HANDLER = re.search(r"@(match|fail)", testmop, re.DOTALL).group(0)

    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": """You are an expert in understanding the MOP (monitoring-oriented programming) framework. This includes understanding AspectJ and pointcuts format well. For each event, describe its properties in at most 5 sentences. It must include the following: 1. Is it a creation event? 2. Under what circumstances will this event trigger? 3. When this event triggers, is there attached java code that will trigger? If so what does that code do? The output must be in the following format: event1:..... \n event2:.... and so on. For example, the following event:
            event add before(Deque q) :
    		(
    			call(* Deque+.addFirst(..)) ||
    			call(* Deque+.addLast(..)) ||
    			call(* Deque+.add(..)) ||
    			call(* Deque+.push(..))
    		) && target(q) {}

    		would be listed as follows:

    		add: This event is not a creation event. It activates whenever the Deque q has addFirst, addLast, add, and push called. No java code is executed when this event is incurred.

            """},
            {"role": "user", "content": f"{EVENTS}"}
        ]
    )
    TRANSLATED_EVENTS = response.choices[0].message.content

    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": f"""You are an expert in generating Extended Regular Expressions for the Monitoring-Oriented Programming (MOP) framework. The special regular expression only uses some of the syntax from Regex, which are "(" and ")" to group events, "|" to signify "or", "*" to signify match as many as possible, and "+" to signify match as many as possible but at least once. On the otherhand, operators like "?" and "{{a,b}}" do not exist and should not be used. For example, the expression "(A|B)+" means match either event A or event B as many times as possible but at least once. Furthermore, this special form of Regex has added an event called "epsilon", which represents the event of nothing. For example, the expression "(A|epsilon)" would match both the trace "A" and an empty trace. This can be used as a replacement to the "?" operator. Further, the "." catch-all term does not exist. The regular expression you create should be as specific as possible. For example, when dealing with an object(s), it should begin from the creation of the object(s) in question. In the regular expression, do not pass arguments to the events and only put the event name. The result of the regular expression will fall into two categories: match, meaning the expression matches the entire relevant trace, or fail, meaning the expression does not match onto the entire relevant trace. It should be indicated for the final expression which one of these results maps to a violation of the runtime property. To be able to match the relevant trace, analyze how the events in the natural language interact with each other at all times from creation. For example, even if the natural language specifies that event A cannot occur after event B, make sure to consider event A occurring before event B in order to consider the entire trace. To do this generation, you will be provided with the rest of the MOP file.

            For example, if this mop file was provided:
            package mop;

            import java.util.*;
            import java.util.concurrent.*;
            import com.runtimeverification.rvmonitor.java.rt.RVMLogging;
            import com.runtimeverification.rvmonitor.java.rt.RVMLogging.Level;

            /**
             * Warns if a capacity-restricted deque performs a less preferable operation.
             *
             * According to the documentation, when using a capacity-restricted deque, it
             * is generally preferable to use offerFirst(), offerLast() and offer()
             * instead of addFirst(), addLast() and add(). Since push() is equivalent to
             * addFirst(), push() is not perferable either.
             * http://docs.oracle.com/javase/6/docs/api/java/util/Deque.html
             *
             * This property warns if addFirst(), addLast(), add() or push() is invoked on
             * a capacity-restricted deque. Since there is no general way to detect whether
             * or not a deque is capacity-restricted, this property warns only when the
             * object is of LinkedBlockingDeque type and it is created with a specific
             * capacity.
             *
             * @severity suggestion
             */

            Deque_OfferRatherThanAdd(Deque q) {{
                creation event create after() returning(Deque q) :
                    call(LinkedBlockingDeque+.new(int)) {{}}

                event add before(Deque q) :
                    (
                        call(* Deque+.addFirst(..)) ||
                        call(* Deque+.addLast(..)) ||
                        call(* Deque+.add(..)) ||
                        call(* Deque+.push(..))
                    ) && target(q) {{}}

                ere : create add+

                @match {{
                    RVMLogging.out.println(Level.CRITICAL, __DEFAULT_MESSAGE);
                    RVMLogging.out.println(Level.CRITICAL, "When using a capacity-restricted deque, it is generally preferable to use offerFirst(), offerLast() and offer() instead of addFirt(), addLast() and add().");
                }}
            }}

            You would want to generate:

            create add+

            This is because we are dealing with an @match handler. So, if we ever invoke the create event and then at least one add event, this means we are trying to use add instead of offer, which violates the natural language specification.
                    """},
            {"role": "user",
             "content": f"Translate the following natural language into a special regular expression, or ERE, for java runtime-verification: {NL_COMMENT}. Use this information from the file to assist: {testmop}. Here is an explanation of the events in natural language: {TRANSLATED_EVENTS}. This ERE must be suited for {HANDLER} handler type. Output only the generated ERE."}
        ]
    )
    OUTPUT = response.choices[0].message.content

    with open("../translation.txt", "w", encoding='utf-8') as file:
        file.write("@$#%\n")
        file.write(f"{NL_COMMENT}\n")
        file.write("@$#%\n")
        file.write(f"{PARAMS}\n")
        file.write("@$#%\n")
        file.write(f"{TRANSLATED_EVENTS}\n")
        file.write("@$#%\n")
        file.write(f"{HANDLER}\n")
        file.write("@$#%\n")
        file.write(f"{OUTPUT}\n")
        file.write("@$#%\n")