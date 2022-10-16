from __future__ import annotations
from datetime import datetime
from typing import List
from numpy.random import default_rng

from geniusweb.progress.Progress import Progress


class ProgressGauss (Progress):
	'''
	progress in terms of number of rounds. The round has to be updated by the
	user of this class, calling {@link #advance()}. immutable.
	'''

	def __init__(self, means:List[float], stdevs:List[float], seed:int, currenttime:float, endtime:float, endrealtime:datetime):
		'''
		@param endtime      length max number of rounds, must be positive (not 0)
		@param currenttime  the current round number (can be from 0 to deadlne).
		                    When = deadline, it means the progress has gone past
		                    the deadline.
		@param endrealtime  the termination time of this session. 
							WARNING due to a bug in python for windows, this value must be 
		             		at least 100000 seconds above jan. 1, 1970.
		'''
		if endtime <= 0:
			raise ValueError("deadline must be positive but is " + str(endtime))
		if currenttime < 0 or currenttime > endtime:
			raise ValueError("current round must be inside [0," + str(endtime) + "]")
		self._endTime = endtime
		self._seed = seed
		self._currentTime = currenttime
		self._endRealTime = endrealtime
		self._means = means
		self._stdevs = stdevs

	def getMeans(self) ->List[float]:
		return self._means

	def getStdevs(self) ->List[float]:
		return self._stdevs

	def getSeed(self) ->int:
		return self._seed

	def getEndRealTime(self) ->datetime:
		return self._endRealTime

	def getTerminationTime(self) -> datetime:
		return self._endRealTime

	def getDuration(self):
		'''
		@return time in ms of duration
		'''
		return self._endTime
	
	def getEndtime(self):
		return self._endTime

	def getCurrentTime(self) -> float:
		'''
		@return the current round. First round is 0. It is recommended that you
		        use the functions in {@link Progress} instead of this, to ensure
		        your code works with all implementations of Progress including
		        future developments.
		'''
		return self._currentTime

	def getTotalTime(self) -> int:
		'''
		@return total number of rounds. It is recommended that you use the
		        functions in {@link Progress} instead of this, to ensure your
		        code works with all implementations of Progress including future
		        developments.
		'''
		return self._endTime

	def get(self, currentTimeMs:int) -> float:
		# deadline and current both are limited to MAXINT is 32 bits; double
		# fits 52
		# bits so this should not result in accuracy issues
		ratio:float = self._currentTime / self._endTime;
		if ratio > 1.0:
			ratio = 1.0;
		elif ratio < 0.0:
			ratio = 0.0;
		return ratio;

	def isPastDeadline(self, currentTimeMs:int) -> bool:
		return self._currentTime >= self._endTime or \
			currentTimeMs > int(1000 * datetime.timestamp(self._endRealTime))

	def advance(self) -> "ProgressGauss":
		'''
		@return new ProgressRounds with round 1 advanced (or this, if
		        currentRound= duration). This is up to the user, as it is up to
		        the used protocol what exactly is a round.
		'''
		if self._endTime == self._currentTime:
			return self
		
		rng = default_rng(self._seed)
		increment = max(rng.normal(self._means[0], self._stdevs[0]), 0.0)
		newCurrentTime = self._currentTime + increment
		if newCurrentTime > self._endTime:
			newCurrentTime = self._endTime
		newMeans = list(self._means)
		if len(newMeans) > 1:
			newMeans = self._means[1:] + self._means[0:1]
		newStdevs = list(self._stdevs)
		if len(newStdevs) > 1:
			newStdevs = self._stdevs[1:] + self._stdevs[0:1]
		newSeed = rng.integers(0, (2 ** 63) - 1)
		return ProgressGauss(newMeans, newStdevs, newSeed, newCurrentTime, self._endTime, self._endRealTime)

	def __hash__(self):
		return hash((self._currentTime, self._endTime))
	
	def __eq__(self, other):
		return isinstance(other, self.__class__) \
			and self._currentTime == other._currentTime \
			and self._endTime == other._endTime \
			and self._endRealTime == other._endRealTime

	def __repr__(self):
		return "ProgressGauss[" + str(self._currentTime) \
			+" of " + str(self._endTime) + "]"
