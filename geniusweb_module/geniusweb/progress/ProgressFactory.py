from datetime import datetime

from geniusweb.deadline.Deadline import Deadline
from geniusweb.deadline.DeadlineRounds import DeadlineRounds
from geniusweb.deadline.DeadlineTime import DeadlineTime
from geniusweb.deadline.DeadlineGauss import DeadlineGauss
from geniusweb.progress.Progress import Progress
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.progress.ProgressTime import ProgressTime
from geniusweb.progress.ProgressGauss import ProgressGauss

class ProgressFactory:
	@staticmethod
	def create( deadline: Deadline, nowms:int) -> Progress :
		'''
		@param deadline the deadline to create a progress for
		@param nowms    The time as from {@link System#currentTimeMillis()} that
		                is to be used as start time for the progress.
		@return new Progress matching the deadline type.
		'''
		assert isinstance(deadline, Deadline)
		if isinstance(deadline,DeadlineRounds):
			return ProgressRounds( deadline.getRounds(),
					0, datetime.fromtimestamp( (nowms + deadline.getDuration())/1000.))
		elif isinstance(deadline,DeadlineGauss):
			return ProgressGauss(deadline.getMeans(),
			        deadline.getStdevs(), deadline.getSeed(), 0.0, deadline.getEndtime(), datetime.fromtimestamp((nowms + deadline.getRealTimeDuration()) / 1000.))
		else:
			return ProgressTime(deadline.getDuration(),datetime.fromtimestamp(nowms/1000.))
