"""Persistent, bounded scheduler for local EVOMIND jobs."""
import json,threading
from datetime import datetime,timezone,timedelta

def utcnow():
    return datetime.now(timezone.utc)

def iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

class JobScheduler:
    ALLOWED={"reflect","create_task","agent_run"}
    AGENT_IDS={"general","planner","researcher","writer","coder","analyst","organizer","tutor","translator","reviewer","architect","product","debugger","creative"}
    def __init__(self,db,assistant,agents,poll_seconds=5):
        self.db=db;self.assistant=assistant;self.agents=agents
        self.poll_seconds=max(2,int(poll_seconds));self._stop=threading.Event();self._thread=None
    def create(self,title,kind,payload,run_at,interval_seconds=0):
        title=str(title).strip()
        if not title or len(title)>160:raise ValueError("Title must be 1–160 characters")
        if kind not in self.ALLOWED:raise ValueError("Unsupported scheduled job type")
        if not isinstance(payload,dict):raise ValueError("Payload must be an object")
        if kind=="create_task":
            if not str(payload.get("title","")).strip():raise ValueError("Task title is required")
            payload={"title":str(payload["title"]).strip()[:180],"description":str(payload.get("description",""))[:4000]}
        elif kind=="agent_run":
            if payload.get("agent","general") not in self.AGENT_IDS:raise ValueError("Unknown agent")
            prompt=str(payload.get("text","")).strip()
            if not prompt or len(prompt)>12000:raise ValueError("Agent prompt must be 1–12,000 characters")
            payload={"agent":payload.get("agent","general"),"text":prompt}
        else:payload={}
        try:
            when=datetime.fromisoformat(str(run_at).replace("Z","+00:00"))
            if when.tzinfo is None:raise ValueError("run_at must include a timezone")
            when=when.astimezone(timezone.utc)
        except (TypeError,ValueError) as e:raise ValueError("run_at must be an ISO-8601 timestamp with timezone") from e
        interval=int(interval_seconds or 0)
        if interval and not 60<=interval<=2592000:raise ValueError("Repeat interval must be 60 seconds to 30 days")
        if interval and kind=="agent_run":raise ValueError("Recurring agent runs are disabled; schedule a one-time run to avoid unattended repeated model execution")
        i,_=self.db.execute("INSERT INTO scheduled_jobs(title,kind,payload,run_at,interval_seconds) VALUES(?,?,?,?,?)",(title,kind,json.dumps(payload),iso(when),interval))
        self.db.execute("INSERT INTO events(kind,detail) VALUES('job_scheduled',?)",(str(i),))
        return self.get(i)
    def get(self,job_id):
        return self.db.one("SELECT * FROM scheduled_jobs WHERE id=?",(job_id,))
    def list(self):
        return self.db.rows("SELECT * FROM scheduled_jobs ORDER BY enabled DESC,run_at ASC,id DESC LIMIT 200")
    def cancel(self,job_id):
        row=self.get(job_id)
        if not row:return False
        self.db.execute("UPDATE scheduled_jobs SET enabled=0,status='cancelled',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='scheduled'",(job_id,))
        return self.get(job_id)["status"]=="cancelled"
    def _execute(self,row):
        payload=json.loads(row["payload"])
        if row["kind"]=="reflect":
            result=self.assistant.reflect()
            return "Reflection completed; "+str(result.get("candidates",0))+" candidate memories queued for review."
        if row["kind"]=="create_task":
            task=self.assistant.add_task(payload["title"],payload.get("description",""))
            return "Created task #"+str(task["id"])+": "+task["title"]
        if row["kind"]=="agent_run":
            result=self.agents.run(payload["agent"],payload["text"])
            return result["reply"][:4000]
        raise ValueError("Unsupported job type")
    def run_due_once(self):
        now=iso(utcnow())
        due=self.db.rows("SELECT * FROM scheduled_jobs WHERE enabled=1 AND status='scheduled' AND run_at<=? ORDER BY run_at,id LIMIT 10",(now,))
        completed=[]
        for row in due:
            _,changed=self.db.execute("UPDATE scheduled_jobs SET status='running',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='scheduled' AND enabled=1",(row["id"],))
            if changed!=1:continue
            try:
                result=self._execute(row)
                if row["interval_seconds"]:
                    next_run=iso(utcnow()+timedelta(seconds=row["interval_seconds"]))
                    self.db.execute("UPDATE scheduled_jobs SET status='scheduled',run_at=?,last_run_at=?,last_result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(next_run,iso(utcnow()),result[:4000],row["id"]))
                else:
                    self.db.execute("UPDATE scheduled_jobs SET status='completed',enabled=0,last_run_at=?,last_result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(iso(utcnow()),result[:4000],row["id"]))
                self.db.execute("INSERT INTO events(kind,detail) VALUES('job_completed',?)",(str(row["id"]),))
                completed.append({"id":row["id"],"ok":True,"result":result})
            except Exception as e:
                self.db.execute("UPDATE scheduled_jobs SET status='error',enabled=0,last_run_at=?,last_result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(iso(utcnow()),str(e)[:4000],row["id"]))
                self.db.execute("INSERT INTO events(kind,detail) VALUES('job_failed',?)",(str(row["id"]),))
                completed.append({"id":row["id"],"ok":False,"error":str(e)})
        return completed
    def _loop(self):
        while not self._stop.is_set():
            try:self.run_due_once()
            except Exception as e:self.db.execute("INSERT INTO events(kind,detail) VALUES('scheduler_error',?)",(str(e)[:500],))
            self._stop.wait(self.poll_seconds)
    def start(self):
        if self._thread and self._thread.is_alive():return
        self.db.execute("UPDATE scheduled_jobs SET status='interrupted',enabled=0,last_result='Previous process stopped while this job was running; review and schedule it again.',updated_at=CURRENT_TIMESTAMP WHERE status='running'")
        self._stop.clear();self._thread=threading.Thread(target=self._loop,name="evomind-scheduler",daemon=True);self._thread.start()
    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():self._thread.join(timeout=3)
