# Interactive lesson input

Give this folder's `interactive_lesson_template.md` file to a lesson author or
another tool as the reference format for interactive coding lessons.

Keep the YAML front matter, especially the required `student:` field. Use the
following task pattern:

```markdown
:::task id=t1 type=code hint=180
Student practice — short task name

Describe the coding problem.

STARTER
# Optional small scaffold. Do not include the full solution.

EXPECTED
The exact output the learner's code should print

SOLUTION
```python
# Optional answer, hidden until the learner requests a hint.
```
:::
```

For a one-minute self-practice task, use `phase=self` and `hint=60`:

```markdown
:::task id=sp1 type=code phase=self hint=60
Self-practice — new problem on the same concept

EXPECTED
Expected output
:::
```

Replace every value in square brackets with the learner's details and lesson
content. The portal automatically provides the editable Python editor, Run
code, Output, Reset, Submit / check, sequential unlock, and countdown.
