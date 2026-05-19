<h1>Generating ERE from NL for Runtime-Verification</h1>

The major products of this research is:
1. A Python-based GUI built with tkinter that serves as the translation tool
2. A Python-based comparison tool that allows semantic comparison of two ERE

Install:
- Python 3.7+ (and tkinter, which should be preinstalled into any Python version >= 3.7)

**Using the GUI tool:**

Double click on the ```nl_to_ere_gui.pyw``` file; do not remove any of the other files inside of the folder as they are tied to the GUI and will be accessed by the GUI.

Place the full file path of the .MOP file, with the ERE removed, into modifiable row that has ```GEN``` on the right.

Click ```GEN```.

The GUI will then fill in the rest, the NL with clarified NL, the Parameter, the Events, the Handler, and then finally the generated ERE at the bottom-most row.

**Using the comparator tool:**

Inside the ```Comparison``` folder will contain three files. Two text files and one python file. Place the ground truth ERE inside the corresponding file, using the following form on each line:

```
ere;match/fail;creation_events
```

For example, here is what the file may look like:

```
(mark | read1 | readn | goodreset)* badreset+;match;mark
(mark | read1 | readn | goodreset)* badreset+;match;mark
read1 (mark | read1 | readn | goodreset)* badreset+;match;mark
```

Then, place the generated ERE inside the corresponding file, using the following form on each line:

```
ere
```

For example, here is what the file may look like:

```
mark (mark | read1 | readn | goodreset)* badreset+
(mark | read1 | readn | goodreset)+ badreset+
mark (mark | read1 | readn | goodreset)* badreset+
```

Finally, run the python file as follows:

```local_ere_fix.py generated_ere.txt ground_truth_ere.txt```

The output will look something like this:

```
Test #0:
Ground: (mark | read1 | readn | goodreset)* badreset+
Generated: mark (mark | read1 | readn | goodreset)* badreset+
Result: True

Test #1:
Ground: (mark | read1 | readn | goodreset)* badreset+
Generated: (mark | read1 | readn | goodreset)+ badreset+
Result: True

Test #2:
Ground: read1 (mark | read1 | readn | goodreset)* badreset+
Generated: mark (mark | read1 | readn | goodreset)* badreset+
Result: False

Finished Tests
```
