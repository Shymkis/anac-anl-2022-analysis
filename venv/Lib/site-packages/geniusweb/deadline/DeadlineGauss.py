from typing import List
from geniusweb.deadline.DeadlineTime import DeadlineTime

class DeadlineGauss (DeadlineTime):
	'''
	The number of rounds that a session will be allowed to run. This extends
	DeadlineTime because a rounds deadline is an ADDITIONAL deadline on top of a
	normal time deadline. It is not hard defined what a round is, this is up to
	the protocol.
	'''

	def __init__(self, means:List[float], stdevs:List[float], seed: int, endtime:float, durationms:int):
		'''
		@param rounds     the max number of rounds for the session
		@param durationms the maximum time in milliseconds the session is allowed
		                  to run.
		'''
		super().__init__(durationms)
		if endtime <= 0:
			raise ValueError("deadline must have at least 1 round")
		self._endtime = endtime
		self._means = means
		self._stdevs = stdevs
		self._seed = seed

	def getMeans(self) ->List[float]:
		return self._means
	
	def getStdevs(self) ->List[float]:
		return self._stdevs

	def getEndtime(self) -> float:
		return self._endtime

	def getSeed(self) ->int:
		return self._seed

	def getRealTimeDuration(self) ->int:
		return self.getDuration()
		
	def __hash__(self):
		prime = 31
		result = super().__hash__()
		result = prime * result + hash(tuple(self._rounds))
		return result

	def __key(self):
		return (self._means, self._stdevs, self._endtime)

	def __eq__(self, other):
		return isinstance(other, self.__class__) and \
				super().__eq__(other) and self.__key() == other.__key()

	def __repr__(self)->str:
		return "DeadlineGauss["+ str(self._means) + "," + str(self._stdevs) + "," + str(self._endtime) + "," + str(self._durationms) + "]";

