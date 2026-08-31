---
student: demo_student
date: 2026-08-31
title: W5D1 — K-Means clustering
subtitle: Group nearby values into clusters
course: data-science
hint_seconds: 180
visible: false
week: 5
day: D1
---

## Teach — find groups by distance

K-Means starts with a few centres, assigns each point to its nearest centre,
then moves each centre to the average of its assigned points.

## Example — calculate a centre

```python
points = [2, 4, 6]
print(sum(points) / len(points))
```

:::task id=t1 type=code hint=180
Student practice — calculate a cluster centre

Write Python that stores `[3, 5, 7]` in `points` and prints their mean.

STARTER
points = [3, 5, 7]
# Print the mean of points.

EXPECTED
5.0

SOLUTION
```python
points = [3, 5, 7]
print(sum(points) / len(points))
```
:::

:::task id=sp1 type=code phase=self hint=60
Self-practice — a new cluster centre

Without copying the first answer, print the mean of `[4, 8, 12]`.

EXPECTED
8.0

SOLUTION
```python
points = [4, 8, 12]
print(sum(points) / len(points))
```
:::
