---
student: demo_student
date: 2026-08-31
title: K-Means clustering
subtitle: Group nearby values into clusters
course: data-science
topics:
  - Distance and centres
  - Iterating to convergence
hint_seconds: 60
visible: false
week: 5
day: D1
---

## Find groups by distance

K-Means starts with a few centres, assigns each point to its nearest centre,
then moves each centre to the average of its assigned points.

:::example
```python
points = [2, 4, 6]
print(sum(points) / len(points))
```
:::

:::practice id=t1 hint=60
Write Python that stores `[3, 5, 7]` in `points` and prints their mean, on
your own computer.

EXPECTED
5.0

SOLUTION
```python
points = [3, 5, 7]
print(sum(points) / len(points))
```
:::

## A second cluster centre

:::practice id=sp1 hint=60
Without copying the first answer, print the mean of `[4, 8, 12]`.

EXPECTED
8.0

SOLUTION
```python
points = [4, 8, 12]
print(sum(points) / len(points))
```
:::
