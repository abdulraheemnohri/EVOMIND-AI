from pathlib import Path
import pytest
from evomind.database import Database
from evomind.runtimes import ModelManager
from evomind.agents import AgentHub,safe_calculate

def make_hub(tmp_path:Path):
    db=Database(tmp_path/"agent-test.sqlite3")
    models=ModelManager(tmp_path/"models")
    return db,AgentHub(db,models)

def test_specialist_agents_run_and_persist(tmp_path):
    db,hub=make_hub(tmp_path)
    result=hub.run("planner","Plan a small offline notes app.")
    assert result["agent"]=="planner"
    assert result["reply"]
    assert db.count("agent_runs")==1
    assert len(hub.list())>=10

def test_agent_uses_approved_memory_and_goals_as_context(tmp_path):
    db,hub=make_hub(tmp_path)
    db.execute("INSERT INTO memories(content,source,status) VALUES(?,?,?)",("User prefers offline software","test","approved"))
    db.execute("INSERT INTO goals(title,status) VALUES(?,?)",("Build a local assistant","open"))
    assert hub.run("general","What should I focus on?")["reply"]

def test_safe_calculator():
    assert safe_calculate("(125 * 3) / 5")==75
    assert safe_calculate("2 ** 3")==8

@pytest.mark.parametrize("expression",[
    "__import__('os').system('id')",
    "open('/etc/passwd')",
    "2 ** 99",
    "1 / 0",
])
def test_calculator_rejects_unsafe_or_invalid_expressions(expression):
    with pytest.raises((ValueError,ZeroDivisionError,SyntaxError)):
        safe_calculate(expression)

def test_allowlisted_task_tool(tmp_path):
    db,hub=make_hub(tmp_path)
    result=hub.use_tool("task_create",{"title":"Review PR","description":"Check tests"})
    assert result["task"]["title"]=="Review PR"
    assert db.count("tasks")==1

def test_unknown_tool_is_rejected(tmp_path):
    _,hub=make_hub(tmp_path)
    with pytest.raises(ValueError):
        hub.use_tool("shell",{"command":"id"})
