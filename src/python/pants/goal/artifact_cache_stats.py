# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from collections import defaultdict, namedtuple

from pants.cache.artifact_cache import UnreadableArtifact
from pants.util.dirutil import safe_mkdir


# Lists of target addresses.
CacheStat = namedtuple('CacheStat', ['hit_targets', 'miss_targets'])


class ArtifactCacheStats(object):
  """Tracks the hits and misses in the artifact cache.

  If dir is specified, writes the hits and misses to files in that dir."""

  def __init__(self, dir=None):
    def init_stat():
      return CacheStat([], [])
    self.stats_per_cache = defaultdict(init_stat)
    self._dir = dir
    safe_mkdir(self._dir)

  def add_hits(self, cache_name, targets):
    self._add_stat(0, cache_name, targets, None)

  # any cache misses, each target is paired with its cause for the miss.
  def add_misses(self, cache_name, targets, causes):
    self._add_stat(1, cache_name, targets, causes)

  def get_all(self):
    """Returns the cache stats as a list of dicts."""
    ret = []
    for cache_name, stat in self.stats_per_cache.items():
      ret.append({
        'cache_name': cache_name,
        'num_hits': len(stat.hit_targets),
        'num_misses': len(stat.miss_targets),
        'hits': stat.hit_targets,
        'misses': stat.miss_targets
      })
    return ret

  # hit_or_miss is the appropriate index in CacheStat, i.e., 0 for hit, 1 for miss.
  def _add_stat(self, hit_or_miss, cache_name, targets, causes):
    def format_vts(tgt, cause):
      """Format into (target, cause) tuple."""
      target_address = tgt.address.reference()
      if isinstance(cause, UnreadableArtifact):
        return (target_address, str(cause.err))
      elif cause == False:
        return (target_address, 'uncached')
      else:
        return (target_address, '')

    causes = causes or [True] * len(targets)
    target_with_causes = [format_vts(tgt, cause) for tgt, cause in zip(targets, causes)]
    self.stats_per_cache[cache_name][hit_or_miss].extend(target_with_causes)
    suffix = 'misses' if hit_or_miss else 'hits'
    if self._dir and os.path.exists(self._dir):  # Check existence in case of a clean-all.
      with open(os.path.join(self._dir, '{}.{}'.format(cache_name, suffix)), 'a') as f:
        f.write('\n'.join([' '.join(target_with_cause).strip()
                           for target_with_cause in target_with_causes]))
        f.write('\n')
