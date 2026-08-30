---
# ============================================================
# REQUIRED
# ============================================================
student: danish
date: 2026-08-29
title: 🧠 Making your code THINK

# ============================================================
# OPTIONAL — known keys
# ============================================================
subtitle: if / else — the magic that turns a boring script into a real game 🎮
course: python-fundamentals
format: slide
hint_seconds: 30
visible: false
time: "5:00 PM"
duration: 45 min

# ============================================================
# OPTIONAL — extra header pills
# ============================================================
lesson: 3 of 6
platform: direct
homework: finish the guessing game 🎲
difficulty: ⭐⭐☆☆☆
---

🤖 Right now your programs are robots. They do the **exact same thing** every
single time, no matter what. Boring!

Today that stops. 🔥

By the end of tonight your code will look at what is happening, ask a question,
and **choose** what to do next — just like every game you have ever played.


:::journey
- 🎈 Lesson 1 | Data types | string, integer, float, boolean | done
- 📋 Lesson 2 | Lists & dictionaries | One box that holds LOTS of stuff | done
- 🧠 Lesson 3 — TODAY | if / else | Your code makes its own choices | now
- 🔁 Lesson 4 — next | Loops | Do something 100 times without typing it 100 times
:::


:::objectives
1. 🤔 Write an `if` that only runs when something is true.
WHY — every game rule ever is an if. Health hits 0 → game over. That's it. That's the whole thing.
CHECK — you change ONE number and a totally different message pops up.

2. ⚖️ Know the difference between `=` and `==` without thinking about it.
WHY — this is the #1 Python mistake on planet Earth. You WILL do it tonight. 😄
CHECK — you spot the bug in `if age = 12:` in under two seconds.

3. 🔀 Use `if` + `elif` + `else` so your program has THREE different endings.
WHY — real choices are never just yes/no. Kids ticket, teen ticket, adult ticket.
CHECK — your ticket machine gives 3 different prices for 3 different ages.
:::


:::card title="🚀 Before you start"
1. Open **VS Code**
2. Make a new file → call it `lesson3.py`
3. Type your code, then smash **▶ Run**

⌨️ **Type everything by hand tonight.** No copy-paste! Your fingers remember
what your eyes forget. 🧠
:::


:::card title="🗺️ Your cheat sheet — everything you need tonight"
**Nothing below uses anything that isn't on this list.**
If you find something that isn't here, *I* messed up. Tell me and I'll fix it. 😅

| code | what it does |
|---|---|
| `print("...")` | 📣 shout something on the screen |
| `if score > 50:` | 🤔 do the indented lines ONLY if this is true |
| `else:` | 🛟 do THESE instead, when the if was false |
| `elif score > 20:` | 🔀 another question — only checked if the ones above failed |
| `==` | is the same as? |
| `!=` | is NOT the same as? |
| `>` `<` | bigger than, smaller than |
| `>=` `<=` | bigger-or-equal, smaller-or-equal |
| `and` | 🤝 BOTH must be true |
| `or` | 🎟️ ONE of them is enough |
| `not` | 🙃 flips true into false |
| `input("...")` | ⌨️ ask the player to type something |
| `int(...)` | 🔢 turn typed text into a real number |
:::


:::tip
🚨 **The colon and the indent are NOT decoration!**

Every `if`, `elif` and `else` line ends with `:` — and the line underneath gets
pushed in with one **TAB**. Miss either one and Python straight up refuses to run.

This will happen to you tonight. It happens to everybody. Even me. 😎
:::


## PART 1 — 🍴 A fork in the road

An `if` is a fork in the road. Python walks up to the question, works out if it's
true, and then either goes down the indented path… or steps right over it.


:::figure caption="Python walks up, asks, and picks ONE road. 🚶"
                  age = 12
                     |
                     v
             +-------------------+
             |  is age >= 10 ?   |   <- the question
             +-------------------+
                 |           |
             ✅ TRUE      ❌ FALSE
                 |           |
                 v           v
        print("You can    (skips it
           play!") 🎮       completely)
                 |           |
                 +-----+-----+
                       |
                       v
                print("Bye!") 👋   <- ALWAYS runs. It's not indented!
:::

```python
age = 12

if age >= 10:
    print("You can play! 🎮")

print("Bye! 👋")
```


:::rule title="🗣️ Say these two OUT LOUD before you touch the keyboard"
1️⃣ THE ONE THAT TELLS
`age = 12`
"Put twelve INTO the box called age." 📦
It's an order. It changes something.
---
2️⃣ THE ONE THAT ASKS
`age == 12`
"Is the box called age the same as twelve?" 🤔
It's a question. The answer comes back True or False.
:::


:::task id=q1 type=choice
🕵️ Which line is ASKING a question?

NOTE
No timer on this one — go with your gut. 💪

OPTIONS
- `lives = 3` — Nope! 😄 One equals sign is you TELLING Python to shove 3 in the box.
- [x] `lives == 3` — 🎯 Nailed it. Two equals signs = a question, and the answer comes back True or False.
:::


:::task id=t1 type=code
🤔 Your very first if

NOTE
One box. One question. One message. That's the whole task.

🔮 **Guess first:** if `score` is 85, will the message print? {{t1_predict}}

```python
score = 85

# 👇 YOUR CODE HERE — one if, one print
```

DONE WHEN
✅ The winning message prints.
Then you change `score` to 20, run again, and **nothing happens at all.**

SOLUTION
```python
score = 85

if score > 50:
    print("You beat the level! 🏆")
```
With `score = 20` the question is false, so Python skips the indented line like
it isn't even there and the program just… ends. 🤷

That's not a bug — that IS the point!
:::


## PART 2 — 🛟 The other road

Right now, when the question is false, **nothing happens**. Usually you want
your program to say *something* instead. That's what `else` is for.


:::task id=t2 type=code
🏆 Win or lose

NOTE
`else` has NO question after it. Just `else:` sitting there on its own. 🛟
It means "everything that's left over."

```python
score = int(input("What is your score? "))

# 👇 YOUR CODE HERE — an if for winning, an else for losing
```

DONE WHEN
✅ You run it twice — once typing 80, once typing 20 — and get two totally
different messages.

SOLUTION
```python
score = int(input("What is your score? "))

if score >= 50:
    print("You win! 🏆")
else:
    print("Try again 😅")
```
Exactly ONE of those lines runs. Never both, never neither. 🎯

🔢 `int()` is there because `input()` always hands you **text**, and text can't
be compared with a number. (Remember Lesson 1? 😉)
:::


:::task id=t3 type=answer
🔍 Find the sneaky edge

NOTE
Keep your Task 2 program open. Change ONLY the score you type in, and fill this
in as you go. 📝

| you type | what prints |
|---|---|
| 90 | {{t3_90}} |
| 51 | {{t3_51}} |
| 50 | {{t3_50}} |
| 49 | {{t3_49}} |

😮 Now change `>=` to just `>` in your code and type **50** again.
What prints this time? {{t3_flip}}

🤯 One single character changed the answer. Why? {{t3_why|long}}

DONE WHEN
✅ Table is full, and you can explain `>` vs `>=` without peeking at the cheat sheet.
:::


## PART 3 — 🚪🚪🚪 More than two doors

Two roads isn't enough for a real game! `elif` lets you line up as many questions
as you want. Python reads them **top to bottom** and screeches to a halt at the
first true one. 🛑


:::figure caption="It stops at the FIRST true one. It never even looks at the rest. 🛑"
   score = 75
       |
       v
  is score >= 90 ?  -- ❌ FALSE --> keep going...
       |
       v
  is score >= 70 ?  -- ✅ TRUE ---> print "Grade B 🥈"  -->  🛑 STOP! Done.
       |
       v
  is score >= 50 ?      💤 never checked
       |
       v
     else                💤 never checked
:::


:::task id=q2 type=choice
🤨 `score` is 75. So why does it NOT print "Grade C", when 75 is bigger than 50?

NOTE
Peek at the diagram above first. 👆

OPTIONS
- Because 75 isn't really bigger than 50 — 😄 Have another look! 75 is definitely bigger than 50.
- [x] Because Python already found a true one and STOPPED — 🎯 Exactly! First TRUE wins. Everything below it gets ignored completely.
- Because `elif` only works twice — Nope! 😊 You can stack as many `elif` lines as you like.
:::


:::task id=t4 type=code
🎟️ Build a cinema ticket machine

NOTE
Three ages, three prices. That last `print` is NOT indented on purpose — so it
fires no matter which ticket you got. 🍿

```python
age = int(input("How old are you? "))

# 👇 YOUR CODE HERE — if / elif / else

print("Enjoy the film! 🍿")
```

🧒 Under 13 → Kids, 50 kr
🧑 Under 18 → Teen, 90 kr
🎩 Anyone else → Adult, 150 kr

DONE WHEN
✅ You run it three times — typing 9, then 15, then 40 — and get three different
prices. And "Enjoy the film!" shows up every single time.

SOLUTION
```python
age = int(input("How old are you? "))

if age < 13:
    print("Kids ticket 🎟️ 50 kr")
elif age < 18:
    print("Teen ticket 🎫 90 kr")
else:
    print("Adult ticket 🎩 150 kr")

print("Enjoy the film! 🍿")
```
🪜 **Order matters!** If you put `age < 18` first, a 9-year-old gets a TEEN
ticket — because 9 is under 18 too, and Python would stop right there. 😬
:::


## PART 4 — 🤝 Asking two things at once

Sometimes one question isn't enough. A boss door might need coins **AND** a key. 🗝️


:::grid
🤝 AND — BOTH must be true
`if coins >= 100 and has_key:`
Fails if EITHER one is false.
Think: a padlock with two keyholes. 🔒🔒
---
🎟️ OR — ONE is enough
`if is_vip or coins >= 500:`
Passes if EITHER one is true.
Think: two different doors into the same room. 🚪🚪
:::


:::task id=t5 type=code
🐉 The boss room

NOTE
`has_sword` is already a boolean, so you just write `has_sword` — NOT
`has_sword == True`. The `== True` bit does absolutely nothing. 😌

```python
coins = 250
has_sword = True

# 👇 YOUR CODE HERE — they get in only if BOTH are sorted
```

🗝️ They may enter only with **200 coins or more** AND **the sword**.

DONE WHEN
✅ It lets them in. Then you set `has_sword = False`, run again, and it kicks
them out — even though they're absolutely loaded with coins. 💰

SOLUTION
```python
coins = 250
has_sword = True

if coins >= 200 and has_sword:
    print("Welcome to the boss room! 🐉")
else:
    print("You are not ready yet 😬")
```
😮 Now swap `and` for `or` and run it again with `has_sword = False`.
They get in! One word, completely different rule.
:::


## PART 5 — 💥 Break it on purpose

Error messages aren't Python being angry at you. 😤 They're Python telling you
**exactly** what it wanted. Tonight you're going to smash two on purpose. 🔨


:::task id=t6 type=answer
🐞 Two deliberate crashes

NOTE
Run each one, read ONLY the **last line** of the red text, and write it down. 📝

💥 **Crash 1** — rip the colon off the end of the `if` line:

```python
lives = 2

if lives > 0
    print("Still alive!")
```

What's the last line of the error? {{t6_err1|wide}}

💥 **Crash 2** — use one equals sign instead of two:

```python
age = 12

if age = 12:
    print("You are twelve!")
```

What's the last line of the error? {{t6_err2|wide}}

:::tip
😌 Both of these say **SyntaxError**. That means "I couldn't even READ your code,
let alone run it" — so literally nothing happened.

Nothing is broken. Nothing is lost. Fix the line and run it again. 🔧
:::

🔧 Now fix them both. What did you have to change? {{t6_fix|long}}

DONE WHEN
✅ Both errors written down in your own words, and both programs run.
:::


## PART 6 — 🎲 Put it all together

Everything from tonight, squished into one little game.


:::task id=t7 type=code
🎲 Number guessing game

NOTE
Three possible endings: too low, too high, or spot on. 🎯
That's literally `if` / `elif` / `else`.

```python
secret = 7

guess = int(input("Guess my number (1-10): "))

# 👇 YOUR CODE HERE — three endings
```

DONE WHEN
✅ You play three times — guess low, guess high, then guess right — and get all
three messages.

SOLUTION
```python
secret = 7

guess = int(input("Guess my number (1-10): "))

if guess < secret:
    print("Too low! ⬇️")
elif guess > secret:
    print("Too high! ⬆️")
else:
    print("YOU GOT IT! 🎉")
```
🧠 You don't need a question on the `else`. If the guess isn't smaller and isn't
bigger… there's only one thing left it can possibly be!
:::


:::aside title="🔮 Why I keep making you guess before you run"
Anyone can smash Run and read what pops out. That teaches you basically nothing. 😴

Guessing first, being **wrong**, and then finding out *why* — THAT'S the bit that
sticks in your brain forever. 🧠

Being wrong on a guess costs you literally nothing and teaches you way more than
being right does.

So keep guessing out loud, even when you're not sure. **Especially** then. 💪
:::


:::push title="😬 Your game only gets ONE guess…"
Right now the player guesses once, gets told "too low", and the program just…
ends. That's a pretty rubbish game. 😅

**What would have to change so the player keeps guessing until they get it
right? You can't write it yet — but describe what the computer would need to do,
in normal English.** 🗣️

{{push|long}}

*🔁 That thing you just described has a name. It's called a **loop**, and it's the
whole of next lesson.* 😎
:::


:::checklist
- 🏃 Tasks 1–7 all run without errors
- 📝 Every blank filled in, including the table in Task 3
- 🗣️ You can say the difference between `=` and `==` out loud
- 💥 You crashed Python on purpose in Task 6 and read both messages
- 💾 Saved your file as `lesson3.py`
:::

🎯 **Check yourself against the three objectives at the top.** Can you do all
three? If not, tell me which one — that's exactly where next lesson starts.

⏱️ **Time:** about 45 minutes. If it's taking way longer, stop and message me.
That means *the document* is wrong, not you. 💪
