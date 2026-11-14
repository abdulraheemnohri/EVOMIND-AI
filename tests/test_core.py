from evomind.engine import EvoMind
def make(tmp):return EvoMind(tmp/"db.sqlite",tmp/"models")
def test_chat_persists(tmp_path):
 a=make(tmp_path);r=a.chat("hello");assert r["id"];assert a.stats()["messages"]==2
def test_safe_skill(tmp_path):
 a=make(tmp_path);r=a.chat("double 21");assert r["reply"]=="42";assert r["via"]=="skill:double"
def test_reflection_approval(tmp_path):
 a=make(tmp_path);a.chat("remember that I like jazz");r=a.reflect();assert r["candidates"]>=1
 p=a.memory.pending();assert p and a.memory.decide(p[0]["id"],True);assert a.memory.search("jazz")
def test_unsafe_action_rejected(tmp_path):
 a=make(tmp_path)
 try:a.skills.install("bad","x","bad","python_exec")
 except ValueError:pass
 else:raise AssertionError("unsafe action accepted")
def test_goal_lifecycle(tmp_path):
 a=make(tmp_path);g=a.add_goal("Learn Python");assert a.update_goal(g["id"],"done","complete")["status"]=="done"
