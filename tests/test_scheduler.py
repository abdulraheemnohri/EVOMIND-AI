from datetime import datetime,timezone,timedelta
import pytest
from evomind.database import Database
from evomind.scheduler import JobScheduler

class FakeAssistant:
    def __init__(self,db):self.db=db
    def reflect(self):return {"candidates":2}
class FakeAgents:
    def run(self,agent,text):return {"reply":agent+":"+text}

def build(tmp_path):
    db=Database(tmp_path/"scheduler.sqlite3")
    return db,JobScheduler(db,FakeAssistant(db),FakeAgents(),poll_seconds=2)

def test_scheduler_runs_due_reflection_once_and_persists_history(tmp_path):
    db,s=build(tmp_path)
    job=s.create("Reflect now","reflect",{},datetime.now(timezone.utc).isoformat())
    result=s.run_due_once()
    saved=s.get(job["id"])
    assert result[0]["ok"] is True
    assert saved["status"]=="completed" and saved["enabled"]==0
    assert "2 candidate memories" in saved["last_result"]
    assert s.run_due_once()==[]

def test_scheduler_creates_task_only_when_due(tmp_path):
    db,s=build(tmp_path)
    future=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    job=s.create("Make task","create_task",{"title":"Test scheduled task"},future)
    assert s.run_due_once()==[]
    assert db.count("tasks")==0
    db.execute("UPDATE scheduled_jobs SET run_at=? WHERE id=?",(datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),job["id"]))
    result=s.run_due_once()
    assert result[0]["ok"] is True
    assert db.count("tasks")==1

def test_scheduler_agent_run_is_one_shot(tmp_path):
    db,s=build(tmp_path)
    job=s.create("Agent review","agent_run",{"agent":"planner","text":"Plan a test"},datetime.now(timezone.utc).isoformat())
    assert s.run_due_once()[0]["result"]=="planner:Plan a test"
    assert s.get(job["id"])["status"]=="completed"

def test_scheduler_rejects_unknown_actions_bad_timezone_and_unsafe_repeats(tmp_path):
    db,s=build(tmp_path)
    with pytest.raises(ValueError):s.create("Shell","shell",{},datetime.now(timezone.utc).isoformat())
    with pytest.raises(ValueError):s.create("No timezone","reflect",{},"2030-01-01T00:00:00")
    with pytest.raises(ValueError):s.create("Repeat model","agent_run",{"agent":"general","text":"run"},datetime.now(timezone.utc).isoformat(),60)
    with pytest.raises(ValueError):s.create("Too fast","reflect",{},datetime.now(timezone.utc).isoformat(),10)

def test_scheduler_cancel_and_error_state(tmp_path):
    db,s=build(tmp_path)
    job=s.create("Cancel me","reflect",{},(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())
    assert s.cancel(job["id"]) is True
    assert s.get(job["id"])["status"]=="cancelled"
    assert s.cancel(99999) is False
