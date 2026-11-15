import json
import pytest
from evomind.database import Database
from evomind.knowledge import KnowledgeBase
from evomind.system_tools import WorkspaceTools
from evomind.agents import AgentHub

def setup(tmp_path):
    db=Database(tmp_path/"evomind.sqlite3")
    return db

def test_knowledge_ingest_search_duplicate_and_delete(tmp_path):
    db=setup(tmp_path);kb=KnowledgeBase(db)
    text=("Solplanet ASW inverter zero export configuration and Modbus meter setup. "*80)
    result=kb.add_text("Solar notes",text,"manual")
    assert result["chunks"]>1
    assert kb.search("Solplanet inverter")
    duplicate=kb.add_text("Copy title",text,"other")
    assert duplicate["duplicate"] is True
    assert len(kb.list())==1
    assert kb.delete(result["document"]["id"]) is True
    assert kb.search("Solplanet")==[]

def test_knowledge_rejects_empty_and_oversized_documents(tmp_path):
    kb=KnowledgeBase(setup(tmp_path))
    with pytest.raises(ValueError):kb.add_text("Empty"," ")
    with pytest.raises(ValueError):kb.add_text("Huge","x"*(kb.MAX_DOCUMENT_CHARS+1))

def test_workspace_write_requires_explicit_approval(tmp_path):
    db=setup(tmp_path);tools=WorkspaceTools(db,tmp_path/"workspace")
    request=tools.run("workspace_write_request",{"path":"notes/plan.md","content":"Approved content"})
    target=tmp_path/"workspace"/"notes"/"plan.md"
    assert request["status"]=="pending"
    assert not target.exists()
    result=tools.decide(request["request_id"],True)
    assert result["status"]=="executed"
    assert target.read_text()=="Approved content"
    assert tools.decide(request["request_id"],True)["ok"] is False

def test_workspace_rejection_does_not_write(tmp_path):
    db=setup(tmp_path);tools=WorkspaceTools(db,tmp_path/"workspace")
    request=tools.run("workspace_write_request",{"path":"rejected.txt","content":"No"})
    result=tools.decide(request["request_id"],False)
    assert result["status"]=="rejected"
    assert not (tmp_path/"workspace"/"rejected.txt").exists()

@pytest.mark.parametrize("path",["../outside.txt","/etc/passwd","../../tmp/no.txt"])
def test_workspace_blocks_paths_outside_root(tmp_path,path):
    tools=WorkspaceTools(setup(tmp_path),tmp_path/"workspace")
    with pytest.raises(ValueError):
        tools.run("workspace_write_request",{"path":path,"content":"no"})

def test_workspace_read_is_limited_to_supported_text_files(tmp_path):
    root=tmp_path/"workspace";root.mkdir()
    (root/"hello.md").write_text("hello local")
    tools=WorkspaceTools(setup(tmp_path),root)
    assert tools.run("workspace_read",{"path":"hello.md"})["content"]=="hello local"
    with pytest.raises(ValueError):tools.run("workspace_read",{"path":"secret.bin"})

def test_agent_tool_registry_includes_workspace_and_approval_tools(tmp_path):
    db=setup(tmp_path);tools=WorkspaceTools(db,tmp_path/"workspace")
    class FakeModel:
        active=type("Runtime",(),{"key":"test"})()
        def generate(self,messages):return "ok"
    hub=AgentHub(db,FakeModel(),KnowledgeBase(db),tools)
    ids={x["id"] for x in hub.tools()}
    assert {"workspace_list","workspace_read","workspace_write_request"} <= ids
    assert hub.use_tool("workspace_list",{"path":"."})["items"]==[]

def test_workspace_rejects_symlink_escape(tmp_path):
    root=tmp_path/"workspace";root.mkdir()
    outside=tmp_path/"outside";outside.mkdir()
    (root/"link").symlink_to(outside,target_is_directory=True)
    tools=WorkspaceTools(new_db(tmp_path),root)
    with pytest.raises(ValueError):
        tools.run("workspace_write_request",{"path":"link/escape.md","content":"no"})

def test_agent_retrieves_local_knowledge(tmp_path):
    db=new_db(tmp_path);kb=KnowledgeBase(db)
    kb.add_text("Project note","EVOMIND uses offline local retrieval for private notes.")
    class Model:
        active=type("Runtime",(),{"key":"test"})()
        def __init__(self):self.messages=None
        def generate(self,messages):self.messages=messages;return "retrieved"
    model=Model();hub=AgentHub(db,model,kb,WorkspaceTools(db,tmp_path/"workspace"))
    result=hub.run("researcher","How does EVOMIND retrieve private notes?")
    assert result["reply"]=="retrieved"
    assert "offline local retrieval" in model.messages[0]["content"]

def test_workspace_rejects_symlink_escape(tmp_path):
    root=tmp_path/"workspace";root.mkdir()
    outside=tmp_path/"outside";outside.mkdir()
    (root/"link").symlink_to(outside,target_is_directory=True)
    tools=WorkspaceTools(new_db(tmp_path),root)
    with pytest.raises(ValueError):
        tools.run("workspace_write_request",{"path":"link/escape.md","content":"no"})

def test_agent_retrieves_local_knowledge(tmp_path):
    db=new_db(tmp_path);kb=KnowledgeBase(db)
    kb.add_text("Project note","EVOMIND uses offline local retrieval for private notes.")
    class Model:
        active=type("Runtime",(),{"key":"test"})()
        def __init__(self):self.messages=None
        def generate(self,messages):self.messages=messages;return "retrieved"
    model=Model();hub=AgentHub(db,model,kb,WorkspaceTools(db,tmp_path/"workspace"))
    result=hub.run("researcher","How does EVOMIND retrieve private notes?")
    assert result["reply"]=="retrieved"
    assert "offline local retrieval" in model.messages[0]["content"]
