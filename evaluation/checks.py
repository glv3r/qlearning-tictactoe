## Sanity checks on the harness itself.
##
## The point of these is that the harness is the thing producing every number in the
## report, so it needs to be checked before the numbers are trusted. In particular the
## minimax checks are our ground truth: if minimax ever loses, or the Q-agent ever beats
## it, then minimax or the win checker is broken and every result downstream is void.
##
## Run with:  python -m evaluation.checks

from agents.minimax_agent import MinimaxAgent
from agents.random_agent import RandomAgent

from evaluation.compat import enable_minimax_cache
from evaluation.harness import evaluate, run_matchup
from evaluation.run_evaluation import load_q_agent

results = []


def check(name, condition, detail=""):
    results.append(condition)
    status = "PASS" if condition else "FAIL"
    print(f"{status}  {name}" + (f"  {detail}" if detail else ""))


def main():
    enable_minimax_cache()

    # --- the harness reports coherent, reproducible numbers
    first = run_matchup(RandomAgent('a'), RandomAgent('b'), 1000, seed=1)
    repeat = run_matchup(RandomAgent('a'), RandomAgent('b'), 1000, seed=1)
    other = run_matchup(RandomAgent('a'), RandomAgent('b'), 1000, seed=2)

    total_rate = first['a_win_rate'] + first['b_win_rate'] + first['draw_rate']
    check("rates sum to 1.0", abs(total_rate - 1.0) < 1e-9)
    check("same seed reproduces the same counts", first['counts'] == repeat['counts'])
    check("a different seed gives different counts", first['counts'] != other['counts'])

    # --- minimax is perfect, which is what the whole project is measured against
    vs_random = run_matchup(MinimaxAgent('mm'), RandomAgent('r'), 1000, seed=7)
    check("minimax never loses to random", vs_random['counts']['b_wins'] == 0,
          str(vs_random['counts']))

    mirror = run_matchup(MinimaxAgent('a'), MinimaxAgent('b'), 100, seed=7)
    check("minimax vs minimax always draws", mirror['counts']['draw'] == 100,
          str(mirror['counts']))

    # --- evaluation really does switch exploration off, and puts it back afterwards
    agent = load_q_agent()
    agent.epsilon = 0.7
    scored = evaluate(agent, RandomAgent('r'), 300, seed=3)
    check("epsilon is restored after evaluate", agent.epsilon == 0.7, f"epsilon={agent.epsilon}")

    agent.epsilon = 0.7
    rescored = evaluate(agent, RandomAgent('r'), 300, seed=3)
    check("evaluate ignores the training epsilon", scored['counts'] == rescored['counts'],
          str(scored['counts']))

    passthrough = evaluate(MinimaxAgent('m'), RandomAgent('r'), 10, seed=1)
    check("agents without an epsilon pass through", 'a_win_rate' in passthrough)

    # --- the headline claim, on a seed other than the one the report quotes
    trained = evaluate(load_q_agent(), MinimaxAgent('m'), 1000, seed=11)
    check("Q-agent never beats minimax", trained['counts']['a_wins'] == 0, str(trained['counts']))
    check("Q-agent draws 100% against minimax", trained['draw_rate'] == 1.0)

    passed = sum(1 for r in results if r)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
