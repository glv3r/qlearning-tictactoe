# Ethics Writeup: Q-Learning Tic-Tac-Toe

## 1. Transparency

Our agent's "knowledge" is a nested Python dictionary — `q_table[state][action] → value` — persisted to disk with `pickle` via `save_q_table()`/`load_q_table()`. A trained run of 10,000 self-play episodes (`alpha=0.5, gamma=0.9`, epsilon decaying linearly from 1.0 to a floor of 0.05) produces a table covering exactly **4,431 distinct board states**, out of the roughly 5,478 that are reachable in tic-tac-toe, each mapped to a handful of numbers, one per legal move.

This means transparency isn't a metaphor here: for any board we can open the table and read off the exact value the agent assigned to every option it considered. If it played the center on an empty board, we can show the number that made the center beat the corners. There's no hidden layer translating "board" into "decision", the lookup is the decision. Contrast that with a black-box model that decides a loan or a diagnosis, where the closest you can get is a post-hoc explanation method that approximates the model's reasoning rather than exposing it directly.

We should be honest about why this works: it only works because tic-tac-toe's state space is small enough to enumerate and store in full. A table like this scales linearly with the number of distinct state, it works fine with the limited amount of states that tic-tac-toe has, but would be impossible with a game like chess, and meaningless for continuous, high-dimensional inputs like medical images or loan applicant records. That's exactly why real systems use neural networks that generalize from limited data instead of memorizing every case, and why the field trades transparency for scalability rather than getting both for free.

## 2. Reward Design as Value Alignment

The agent doesn't optimize what we average; it optimizes `reward_scheme`, a three-line dictionary: `{'win': 1, 'loss': -1, 'draw': 0}`. To test this in miniature, we changed one number — raising `draw` from `0` to `5` while leaving `win` and `loss` untouched — and retrained from the same seed with identical hyperparameters. The intuitive prediction is that an agent rewarded more for drawing would draw more often, especially against a strong opponent. The opposite happened:

| Opponent | Reward scheme | Wins | Losses | Draws |
|---|---|---|---|---|
| Random agent (200 games) | Baseline (`draw=0`) | 178 | 3 | 19 |
| Random agent (200 games) | Bad reward (`draw=5`) | 89 | 27 | 84 |
| Perfect minimax player (50 games) | Baseline (`draw=0`) | 0 | 0 | 50 |
| Perfect minimax player (50 games) | Bad reward (`draw=5`) | 0 | **50** | 0 |

Tic-tac-toe is a solved game: optimal play against a perfect opponent always ends in a draw, and the baseline agent reaches exactly that, 50 draws out of 50. The moment we overweighted the draw reward, the agent didn't draw more; it lost every single game it could have, at worst, tied. Against the random opponent its win rate roughly halved and its loss rate rose ninefold. One plausible reading, consistent with how Q-values bootstrap off downstream max estimates, is that inflating the terminal draw reward distorted values propagated back through the whole game tree, so the policy under-weighted defensive moves — the ones that matter most against a strong opponent, in favor of states that merely looked path-adjacent to a draw.

The point isn't the specific mechanism so much as the demonstration: a single number, changed with no other intent than "value draws a bit more," silently produced a strictly worse agent by every measure, including on the dimension we thought we were improving. That's the same failure mode behind engagement-maximizing recommender systems or clinical models optimizing a proxy metric the team didn't fully interrogate — reproduced here with a three-line dictionary and a 250-game evaluation instead of a production incident.

## 3. Reproducibility

`random.seed(6)` is fixed at the top of the training loop, and because both self-play move selection (epsilon-greedy) and every other random draw in a run pull from that single seeded stream, the entire 10,000-episode training run is deterministic end to end. We confirmed this isn't just a claim: rerunning the baseline training from scratch just now reproduced exactly 4,431 learned states — matching the `q_table_trained` file already committed to the repository.

Hyperparameters aren't buried in config files or magic defaults; they're explicit keyword arguments at the call site (`train(agent=q1, episodes=10000, alpha=0.5, gamma=0.9, epsilon_decay=0.0001, min_epsilon=0.05)`), so anyone reading `main.py` sees exactly what produced the shipped table. `pyproject.toml` together with the committed `uv.lock` pins the Python environment precisely, so `uv sync` gives the same interpreter and library versions on any machine — not a "works on my laptop" situation. The trained artifact itself is committed alongside the code, so a reviewer can verify our claims by diffing their own fresh run against ours, rather than taking our word for it.

We'd add one caveat in the interest of honesty: reproducibility is easy here specifically because the system is small, tabular, and free of the nondeterminism that plagues larger models — GPU-parallel floating-point summation, distributed data shuffling, asynchronous updates. Reproducing a 4,431-state lookup table is a much lower bar than reproducing a large neural network's training run, and we shouldn't imply otherwise. That caveat connects back to Part 1: the same small scale that makes this agent fully transparent is what makes it fully reproducible too, and both properties are things we'd have to give up, not just work harder to preserve, if we scaled this approach up.
