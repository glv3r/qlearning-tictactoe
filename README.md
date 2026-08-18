# Q-Learning Tic-Tac-Toe

A tabular Q-learning agent that learns tic-tac-toe from self-play alone — no hand-coded strategy, no opening book, no access to the rules beyond "here are the legal moves." After 10,000 games against itself it plays perfectly.

The point of the project isn't the agent. Tic-tac-toe is solved, so a perfect opponent already exists and can be used as a ruler: an agent that has genuinely learned optimal play must draw *every* game against minimax. That makes it possible to measure what a learner actually learned, rather than trusting a score against a weak baseline — which, as it turns out, is exactly the mistake the obvious metric invites.

There's also a playable pygame front-end, so you can lose to it yourself.

```
python main.py      # verify the environment and minimax
uv run play.py      # play against the trained agent
```

## Results

| Matchup | A wins | B wins | Draws | A win rate | Draw rate |
|---|---:|---:|---:|---:|---:|
| **Q-agent vs. minimax** | 0 | 0 | **1000** | 0.0% | **100.0%** |
| Q-agent vs. random | 920 | 4 | 76 | 92.0% | 7.6% |
| Minimax vs. random | 897 | 0 | 103 | 89.7% | 10.3% |
| Random vs. random | 410 | 472 | 118 | 41.0% | 11.8% |

1000 games per matchup, seed `20250816`, first move alternating every game. The trained agent draws 100% against perfect play, which is what optimal looks like in a solved game. It wins 0 games against minimax — that's the required result, not a shortfall. Any win there would mean minimax is broken.

The random-vs-random row is a sanity check: the near-even split confirms the harness isn't leaking first-move advantage into the numbers.

## Quickstart

Requires Python 3.10+.

```bash
git clone https://github.com/glv3r/qlearning-tictactoe.git
cd qlearning-tictactoe
uv sync
```

Then:

```bash
uv run play.py                              # graphical game
uv run main.py                              # verify environment + minimax
uv run python -m evaluation.checks          # verify the evaluation harness
uv run python -m evaluation.run_evaluation  # reproduce the results table
```

Without `uv`, a plain `pip install -e .` in a virtualenv works too.

The trained Q-table (`q_table_trained`, 4,431 states) is committed, so nothing needs training before you can play or evaluate.

## Playing

`uv run play.py` opens the menu. Two modes work today:

- **Player vs Player** — two humans, one keyboard, first to three wins.
- **Player vs Agent** — three difficulties: *Easy* plays random moves, *Medium* is the trained Q-agent at ε = 0.1, *Impossible* is minimax and cannot be beaten.

*Medium* runs the real trained agent, just with 10% random moves mixed in. At ε = 0 it never loses to anything, which makes it indistinguishable from *Impossible* and no fun; ε = 0.1 keeps its learned play while leaving a way in.

An **Agent vs Agent** demo mode is scaffolded on the menu but not yet wired up.

## Repo layout

```
environment/     board representation, rules, game loop, self-play training
  environment.py   immutable board, legal moves, win detection, play_game
  q_training.py    the self-play training loop and reward scheme
agents/          three interchangeable agents behind one interface
  random_agent.py  uniform random — the lower baseline
  minimax_agent.py full-depth search, memoised — the ground truth
  qtable_agent.py  ε-greedy tabular Q-learning
evaluation/      everything that produces a number
  harness.py       matchup runner, greedy evaluation, learning curves
  checks.py        sanity checks on the harness itself
  run_evaluation.py / hyperparameter_study.py / reward_scheme_experiment.py
  plots.py         draws the learning curves
  results/         committed CSVs and generated results.md
ui/              pygame front-end (screens, widgets, rendering)
main.py          verification harness (default), replay, retraining
play.py          graphical game entry point
q_table_trained  the committed Q-table
```

The dependency direction is one-way: `evaluation` depends on `environment` and `agents`, never the reverse. Nothing that gathers results can leak into the logic being measured.

## How it works

**Board.** An immutable 9-tuple of strings. Immutability isn't style — it makes a board hashable, which is what lets a board be a Q-table key *and* an argument to a memoised search. Whose turn it is is derived by counting marks rather than tracked separately, which removes a whole class of desync bug.

**Training.** One Q-learning instance plays both sides, so both marks share a single table. After each game the history is split by mark and replayed in reverse: the last move of each mark gets the terminal reward with no bootstrap, earlier moves get zero reward and bootstrap from the next state that mark faced. Going backwards propagates the outcome along the whole move sequence within one episode instead of one move per episode.

```
Q(s, a) ← Q(s, a) + α · [ r + γ · max Q(s′, a′) − Q(s, a) ]
```

Rewards are `{win: +1, loss: -1, draw: 0}`. Epsilon anneals linearly from 1.0 to a floor of 0.05 — kept off zero so the agent keeps visiting states it would otherwise stop reaching.

**Minimax** is memoised with an LRU cache. Unmemoised it re-searches the tree every move, about 0.7 s per game, which makes a single 1000-game matchup take ~12 minutes. The search is a pure function of two hashable arguments, so caching changes runtime by three orders of magnitude and changes no result.

**Verification comes first.** Every result in this repo is measured against minimax, so minimax and the environment are checked before any learning number is believed. `main.py` plays 6,050 games asserting that replayed histories reproduce every recorded state, that every action was legal where taken, that final boards agree with reported results, and that minimax never loses. `evaluation/checks.py` then checks the harness itself — that seeds reproduce, that different seeds diverge, that exploration is actually off during evaluation.

## What we found

**The obvious metric is useless.** Win rate against a random opponent ranged 85.7%–94.8% across nine hyper-parameter configurations and told us nothing about whether the agent had actually learned to play. The worst configuration in the study scored *higher* against random (91.0%) than the baseline (89.6%) while losing 500 of 1000 games against perfect play. Beating a random opponent only requires taking wins when offered and avoiding blunders, so the metric saturates early and stops carrying information.

**Only γ broke it.** With γ = 0.1 the agent never reaches optimal play. All reward here is terminal, so a discount that steep attenuates the win/loss signal roughly a thousandfold before it reaches the opening move — the agent never learns which early moves set up a win. Predictions about α and ε didn't reproduce: extreme values of both still finished at a 100% draw rate, most likely because 5,478 states is small enough to visit repeatedly, which papers over update rules that would be fatal in a larger space.

![learning curves for gamma](evaluation/plots/gamma.png)

Top panel: win rate vs. random — every setting looks fine. Bottom panel: draw rate vs. minimax — γ = 0.1 never gets there. Same runs, same axes.

**A perfect final score isn't convergence.** Two configurations ended at a 100% draw rate while being optimal on only 70% and 30% of their final ten training probes. The slow-ε-decay run was still ~60% exploratory when training stopped; its perfect score records where the last measurement happened to land, not where the policy sat.

**One integer broke the agent completely.** We raised the terminal draw reward from 0 to 5 — everything else identical, same seed — expecting an agent that draws more.

| Reward scheme | vs. random W/L/D | Win rate | vs. minimax W/L/D | Draw rate |
|---|---|---:|---|---:|
| `draw = 0` | 920/4/76 | 92.0% | 0/0/1000 | 100.0% |
| `draw = 5` | 478/144/378 | 47.8% | **0/1000/0** | **0.0%** |

It drew *nothing*. It lost all 1000 games to an opponent it had previously drawn with perfectly, in a game where a draw was always available. Inflating the draw reward raised the value of any state a draw was reachable from — including states a loss was also reachable from — while the loss penalty stayed at −1. We raised the value of a draw without raising the cost of failing to get one, and the agent optimised exactly what it was told to.

## Reproducing

Every experiment fixes a seed. Retraining the baseline from seed 6 reproduces the committed table exactly — 4,431 states with identical values on every one.

```bash
uv run python -m evaluation.run_evaluation           # results table
uv run python -m evaluation.hyperparameter_study     # 9-run parameter study
uv run python -m evaluation.plots                    # learning curves
uv run python -m evaluation.reward_scheme_experiment # the draw-reward experiment
uv run main.py --retrain                             # regenerate q_table_trained
```

Baseline: `episodes=10000, α=0.5, γ=0.9, ε: 1.0 → 0.05 by 0.0001/episode`, training seed `6`, evaluation seed `20250816`.

`--retrain` is deliberately not the default action of `main.py` — the committed Q-table is what every number here is computed from, and overwriting it shouldn't be a thing that happens by accident.

## Full report

`Final_Project_Documentation.pdf` has the complete write-up: methodology, the full hyper-parameter study with all three learning curves, ethical analysis, and limitations.

## Team

Daniel Glover · Akosua Twumwaa Boateng-Mensah · Tetteh Quaye Quayenortey · Naa Addai Torto

CS254: Introduction to Artificial Intelligence, Ashesi University
