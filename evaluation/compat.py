## Workarounds that let the evaluation code drive Role 1's and Role 2's modules without
## editing their files. Everything here is deliberately contained to evaluation/ so that
## our branch doesn't collide with theirs. Both of these are papering over something that
## would be better fixed at the source, so each one says exactly what it's working around.

import functools
import random
from contextlib import contextmanager

import agents.minimax_agent as minimax_module


@contextmanager
def stable_rng(seed):
    """Seed the RNG once, then stop anything inside the block from re-seeding it.

    Works around environment/q_training.py:8, where train() calls random.seed(6) at the
    top of every call. That's fine when you train once, but the learning curve trains in
    chunks (train a bit, measure, train a bit more), so every chunk would restart the
    exact same random stream and our curve would be measuring a repeated sequence instead
    of continuous training.

    We seed once here and neutralise random.seed for the duration, which means the whole
    run is still fully reproducible from this one seed. Role 2 should eventually make the
    seed a parameter of train() and then this can go away.
    """
    random.seed(seed)

    original_seed = random.seed
    random.seed = lambda *args, **kwargs: None
    try:
        yield
    finally:
        random.seed = original_seed


_cache_enabled = False


def enable_minimax_cache():
    """Memoise the minimax search so the evaluation matchups finish in reasonable time.

    Un-cached, minimax re-searches the whole game tree from scratch on every move, which
    measures at roughly 0.7s per game as X. At the 1000 games per matchup the spec asks
    for, that's ~10 minutes for a single matchup.

    minimax(board, player) is a pure function of two hashable arguments, so caching it
    changes nothing about the result. Because the recursive calls inside minimax resolve
    the name through the module's globals, patching the module attribute means the
    recursion hits the cache too, not just the top-level call.
    """
    global _cache_enabled

    if not _cache_enabled:
        minimax_module.minimax = functools.lru_cache(maxsize=None)(minimax_module.minimax)
        _cache_enabled = True

    return minimax_module.minimax
