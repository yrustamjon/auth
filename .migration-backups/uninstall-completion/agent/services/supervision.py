"""Restart only the installed agent; permissions and process identity are injected."""


class Supervisor:
    def __init__(self,find,launch,record,last_exit):
        self.find,self.launch,self.record,self.last_exit=find,launch,record,last_exit
        self.process=None;self.next_start=0;self.failures=0;self.explicit_exit=False
        self.started_at=None

    def tick(self,now,*,allowed,paused):
        if self.process is not None:
            code=self.process.poll()
            if code is None:
                if self.started_at is not None and now-self.started_at>=30:self.failures=0
                return
            pid=self.process.pid;self.process.close();self.process=None
            previous=self.last_exit()
            if previous.get('pid')==pid and previous.get('reason')=='prerelease_exit' and not previous.get('running'):
                self.explicit_exit=True
            elif paused:
                self.record('local_pause_reported',{'previous_pid':pid,'exit_code':code,'reason':'Server ruxsat bergan tanaffus davomida jarayon yopildi'})
            else:
                self.record('agent_unexpected_exit',{'previous_pid':pid,'exit_code':code,'reason':'Jarayon tugadi; sabab yoki shaxs aniqlanmagan'})
                if self.started_at is not None and now-self.started_at<30:
                    self.failures+=1;self.next_start=now+min(300,5*2**min(self.failures,6))
                else:self.failures=0
            self.started_at=None
        existing=self.find()
        if existing is not None:
            self.process=existing;self.explicit_exit=False;return
        if not allowed or paused or self.explicit_exit or now<self.next_start:return
        try:
            self.record('restart_attempted',{'reason':'Kuzatuvchi agentni ishga tushirishga urindi'})
            self.process=self.launch();self.started_at=now;self.next_start=now+5
        except Exception as error:
            self.failures+=1;self.next_start=now+min(300,5*2**min(self.failures,6))
            self.record('restart_failed',{'error_type':type(error).__name__})
