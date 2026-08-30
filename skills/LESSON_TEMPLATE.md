---
# ============================================================
# REQUIRED
# ============================================================
student: andy                       # username — must already exist
date: 2026-08-26                    # YYYY-MM-DD — orders the timeline
title: One branch, and a function that calls itself

# ============================================================
# OPTIONAL — known keys, these change behaviour
# ============================================================
subtitle: Recursion — the idea the whole week rests on
course: blender-python              # groups lessons into a course
format: slide                       # document | slide, default document
hint_seconds: 240                   # default timer; per-task hint= overrides
visible: false                      # publish from the admin when ready
time: "7:00 PM"
duration: 45 min

# ============================================================
# OPTIONAL — anything else. Stored, and shown as header pills.
# Add whatever you like; no code change needed.
# ============================================================
week: 4
day: D3
platform: direct
homework: none
---

Opening paragraph. Plain Markdown works everywhere — **bold**, *italic*,
`inline code`, [links](https://example.com), lists and tables all render.

Use this space for the one sentence that says why today matters.


<!-- ===================================================================
     JOURNEY — the multi-day strip. Pipe-separated:
       label | focus | outcome | state       (state: now, done, or omit)
     Drop this block on single lessons.
=================================================================== -->

:::journey
- Day 1 — today | One branch, then recursion | A Y that becomes a 4-way split | now
- Day 2 — Thursday | Randomness and parameters | A whole tree, different every run
- Day 3 — Friday | Keyframes | The tree grows, or sways
:::


<!-- ===================================================================
     OBJECTIVES — one numbered item, then WHY and CHECK lines.
=================================================================== -->

:::objectives
1. Place a cylinder anywhere, at any angle, using only code.
WHY — a branch is a cylinder at an angle. Everything else is repetition.
CHECK — you make a branch leaning 30° and it lands where you predicted.

2. Write a function that calls itself, and say why it does not run forever.
WHY — this is the whole tree. Not a trick, the actual method.
CHECK — you change one number from 3 to 5 and get 31 branches instead of 7.
:::


<!-- ===================================================================
     CARD — a white panel. Use for setup, reference tables, anything
     that needs to sit apart from the flow without shouting.
=================================================================== -->

:::card title="Before you start"
1. Open Blender.
2. Click the **Scripting** tab.
3. Click **New** to make an empty script.
4. Type your code, then press **▶ Run Script**.

Every script starts with the same two lines:

```python
import bpy
from math import sin, cos, radians
```
:::


:::card title="Reference — every line you need tonight"
**Nothing in the tasks below uses a command that is not on this page.**
If you find one, that is a mistake in this document. Tell me and I will fix it.

| line | what it does |
|---|---|
| `primitive_cylinder_add()` | a cylinder at the centre |
| `primitive_cylinder_add(radius=0.2)` | a thin one |
| `primitive_cylinder_add(depth=3)` | a long one — `depth` means length |
| `radians(30)` | degrees → radians |
:::


<!-- ===================================================================
     TIP — the amber "!" bar. One idea. The thing they'll get wrong.
=================================================================== -->

:::tip
**z is UP.** Not y. This catches everybody once. Keep everything in the x–z
plane today — y is always 0, and your tree is flat, like a drawing on a wall.
:::


<!-- ===================================================================
     Headings become sections. ## is a section with an eyebrow;
     the text before the em dash becomes the eyebrow label.
=================================================================== -->

## PART 1 — Where does a branch end?

A branch starts somewhere, points in some direction, and has a length. You need
to know where its far end lands, because that is where the next branch starts.


<!-- ===================================================================
     FIGURE — monospace diagram, rendered verbatim on a dark panel.
     ASCII art is a first-class citizen. Use it instead of making images.
=================================================================== -->

:::figure caption="A branch is just a right-angled triangle."
            end point (ex, ez)
              /|
             / |
    length  /  |  length × cos(angle)
           /   |
          /    |
    start ‾‾‾‾‾
        length × sin(angle)
:::

```python
ex = x + length * sin(radians(angle))
ez = z + length * cos(radians(angle))
```


<!-- ===================================================================
     RULE — the dark teal panel. Columns split by a line of ---
     First line of each column is its label.
=================================================================== -->

:::rule title="Check it yourself before running anything"
IF THE ANGLE IS 0 — STRAIGHT UP
`sin(0) = 0`
So `ex = x` — it does not move sideways. Correct.
---
AND FOR THE HEIGHT
`cos(0) = 1`
So `ez = z + length` — straight up by its full length. Correct.
:::


<!-- ===================================================================
     TASK type=code — writes code somewhere else, self-marks.
     {{id}} is a saved blank. {{id|wide}} full width. {{id|long}} textarea.
=================================================================== -->

:::task id=t1 type=code hint=240
One branch, by hand

NOTE
Write a script that clears the scene and draws one **vertical** branch:
2 units long, radius 0.2, starting at the origin.

Work out its middle point on paper first — z = {{t1_z}}

```python
import bpy
from math import sin, cos, radians

# clear the scene
# YOUR CODE HERE
```

DONE WHEN
A thin post stands on the floor — not half-buried, and not floating.

SOLUTION
```python
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2, location=(0, 0, 1))
```
A branch 2 long starting at z = 0 ends at z = 2. Its middle is at z = 1.

If yours is half underground, you used location z = 0 — that puts the *middle*
at the floor.
:::


<!-- ===================================================================
     EXPECTED — use when the output is deterministic and comparable.
     Leave it out when every run differs (random, animated, visual).
=================================================================== -->

:::task id=t2 type=code hint=240
How many rows and columns are in this file?

NOTE
Attribute, not method. No brackets.

EXPECTED
(1002, 9)

SOLUTION
```python
df.shape
```
No brackets — shape is an attribute. Wrap it in `print()` if you want it inside
a bigger message.
:::


<!-- ===================================================================
     TASK type=choice — instant feedback, no timer, self-completing.
     - [x] marks the correct option.
     Text after the em dash is the feedback shown when that option is picked.
=================================================================== -->

:::task id=q1 type=choice
Which one gives you the number of rows and columns?

NOTE
No timer on this one — answer straight away.

OPTIONS
- [x] `df.shape` — Right. shape is an attribute, a fact the table already knows, so no brackets.
- `df.shape()` — Not that one. Ask yourself: is this thing DOING a job, or IS it a fact?
:::


<!-- ===================================================================
     TASK type=step — follow instructions in other software.
     Nothing to run, nothing to compare. Ticks done.
     Give these a longer timer: reading a wiring diagram takes longer
     than remembering a one-liner.
=================================================================== -->

:::task id=s1 type=step hint=90
Wire the LED to pin 13

NOTE
Open Tinkercad and build the circuit. Do not power it until the resistor is in.

DONE WHEN
The LED lights when you press Start Simulation, and stays lit.

SOLUTION
Long leg to pin 13. Short leg through a 220Ω resistor to GND.
If it does not light, the legs are the wrong way round — the long one is always
the positive side.
:::


<!-- ===================================================================
     TASK with NO SOLUTION — deliberately. The point is observing.
     No hint button renders. Do not add one.
     Blanks inside a Markdown table make a fill-in table.
=================================================================== -->

:::task id=t4 type=answer
Run it, and find the pattern

```python
branch(0, 0, 0, 2, 0.2, 3)
```

NOTE
Count the cylinders. Then try each depth and fill the table in.

| depth | branches |
|---|---|
| 1 | {{t4_d1}} |
| 2 | {{t4_d2}} |
| 3 | {{t4_d3}} |
| 4 | {{t4_d4}} |
| 5 | {{t4_d5}} |

What is the pattern? {{t4_pattern|wide}}

Now predict depth 8 **before** you run it: {{t4_d8}} branches. Then run it.

DONE WHEN
Your depth-8 prediction matches what Blender actually makes.
:::


<!-- ===================================================================
     Nested block — a tip inside a task. Valid, and useful for the
     "this is supposed to look broken" moment.
     {{id|long}} gives a textarea for written answers.
=================================================================== -->

:::task id=t5 type=answer
Break it on purpose

NOTE
Delete the `if depth == 0: return` lines and run it.

What happens? {{t5_what|long}}

Why? {{t5_why|long}}

:::tip
Blender may freeze. **That is the expected result.** Close it and reopen — you
have lost nothing. Then put the two lines back.
:::

DONE WHEN
You have written down why it never stopped, and the two lines are back in place.
:::


<!-- ===================================================================
     STEPS — big numbered items. For sequences where the order carries
     meaning. Not a substitute for an ordinary list.
=================================================================== -->

:::steps
1. Both wheels forward at the same speed = drives straight.
2. Left wheel fast, right wheel slow = curves to the right.
3. Left forward, right backward = spins on the spot.
4. Both wheels stopped = stands still.
:::


<!-- ===================================================================
     GRID — equal columns. First line of each is its label.
     For comparisons and "you give / it gives" splits.
=================================================================== -->

:::grid
WEBOTS GIVES YOU
The world — floor, walls, objects
The robot body — wheels, sensors
The physics — gravity, bumping
---
YOU GIVE IT
The controller — a Python file
Your decisions: go, stop, turn
:::


<!-- ===================================================================
     ASIDE — untimed collapsible. Optional depth, context, the
     "why this matters more than it looks" note.
     NEVER put an answer in here. Answers go in SOLUTION, behind a timer.
=================================================================== -->

:::aside title="Why I keep saying one number at a time"
If you change two things and the tree looks better, you do not know which one
did it. Change one, look, write it down, change it back.

This is slower for about ten minutes and faster for the rest of your life.
:::


<!-- ===================================================================
     RAW — the escape hatch, for the one-off the vocabulary can't do.
     Sanitised. If you reach for this repeatedly, that pattern should
     become a real block instead.
=================================================================== -->

:::raw
<p style="text-align:center"><em>Anything the blocks above cannot express.</em></p>
:::


<!-- ===================================================================
     PUSH — the closing question. Dark panel. Usually one |long blank.
=================================================================== -->

:::push title="Every tree it makes is identical"
Your recursion always splits into exactly two, always at exactly 30°, always
shrinking by exactly 0.7.

**Real trees are not identical. Name three things you would have to change to
make each tree different — and say which one would make the biggest difference.**

{{push|long}}

*This is Thursday's lesson, and you are going to design it before I teach it.*
:::


<!-- ===================================================================
     CHECKLIST — saved checkboxes. Positional ids, so reordering
     shifts them. Fine for checklists, not for answers.
=================================================================== -->

:::checklist
- Tasks 1–6 all run
- Every blank filled in, including the table in Task 4
- You can say out loud what `depth` is for, without reading it off the page
- Saved your file as `day1_branch.py`
:::

**Check yourself against the two objectives at the top.** Can you do both? If
not, say which one — that is where the next session starts.

**Time:** about 45 minutes. If it takes much longer, stop and message me. That
means the document is wrong, not you.
