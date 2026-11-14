"""Declarative skills only; never execute user-provided source."""
import re
class SkillRegistry:
 ACTIONS={"greet","double_integer","word_count"}
 def __init__(self,db):
  self.db=db
  for x in [("greet","Friendly greeting","hello","greet"),("double","Double integer","double","double_integer"),("word_count","Count words","word count","word_count")]:self.install(*x,quiet=True)
 def install(self,name,description,trigger,action,quiet=False):
  name=name.strip().lower()
  if not name or action not in self.ACTIONS:raise ValueError("Unknown or unsafe action")
  self.db.execute("""INSERT INTO skills(name,description,trigger_text,action) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET description=excluded.description,trigger_text=excluded.trigger_text,action=excluded.action,enabled=1""",(name[:60],description[:240],trigger[:80].lower(),action))
  if not quiet:self.db.execute("INSERT INTO events(kind,detail) VALUES('skill_installed',?)",(name,))
  return self.db.one("SELECT * FROM skills WHERE name=?",(name,))
 def list(self):return self.db.rows("SELECT * FROM skills ORDER BY positive DESC,uses DESC")
 def run_match(self,q):
  hit=next((s for s in self.list() if s["enabled"] and s["trigger_text"] in q.lower()),None)
  if not hit:return None
  if hit["action"]=="greet":result="Hello! I'm EVOMIND. What shall we explore?"
  elif hit["action"]=="double_integer":
   nums=re.findall(r"-?\d+",q);result=str(int(nums[-1])*2) if nums else "Please include an integer."
  elif hit["action"]=="word_count":result="Word count: "+str(len(q.split()))
  else:return None
  self.db.execute("UPDATE skills SET uses=uses+1 WHERE id=?",(hit["id"],))
  return {"reply":result,"skill":hit["name"]}
 def feedback(self,name,positive):
  col="positive" if positive else "negative";self.db.execute("UPDATE skills SET "+col+"="+col+"+1 WHERE name=?",(name,))
