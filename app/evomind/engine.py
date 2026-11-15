from .database import Database
from .memory import MemoryStore
from .skills import SkillRegistry
from .runtimes import ModelManager
class EvoMind:
 def __init__(self,db_path,models_dir):
  self.db=Database(db_path);self.memory=MemoryStore(self.db);self.skills=SkillRegistry(self.db);self.models=ModelManager(models_dir)
 def stats(self):
  return {"messages":self.db.count("messages"),"memories":self.db.count("memories"),"pending_memories":len(self.memory.pending()),"skills":self.db.count("skills"),"goals":self.db.count("goals"),"events":self.db.count("events"),"tasks":self.db.count("tasks"),"agent_runs":self.db.count("agent_runs"),"runtime":self.models.active.key}
 def chat(self,text):
  text=(text or "").strip()
  if not text:return {"reply":"Please enter a message.","id":None,"via":"validation"}
  self.db.execute("INSERT INTO messages(role,content) VALUES('user',?)",(text,));skill=self.skills.run_match(text)
  if skill:reply,via=skill["reply"],"skill:"+skill["skill"]
  else:
   mem=self.memory.search(text,5);hist=self.db.rows("SELECT role,content FROM messages ORDER BY id DESC LIMIT 10");system="You are EVOMIND-AI, a truthful and helpful local personal assistant. Do not claim unavailable tools or external actions."
   if mem:system+="\nApproved memories:\n"+"\n".join("- "+m["content"] for m in mem)
   goals=self.db.rows("SELECT title,status,progress FROM goals WHERE status!='done' ORDER BY id DESC LIMIT 5")
   if goals:system+="\nOpen goals:\n"+"\n".join("- "+g["title"]+" ["+g["status"]+"] "+g["progress"] for g in goals)
   msgs=[{"role":"system","content":system}]+[{"role":m["role"],"content":m["content"]} for m in reversed(hist)]
   try:reply,via=self.models.generate(msgs),"model:"+self.models.active.key
   except Exception as e:reply,via="Local model error: "+str(e)+". Conversation was saved.","runtime-error"
  mid,_=self.db.execute("INSERT INTO messages(role,content,runtime) VALUES(?,?,?)",(reply,via));return {"reply":reply,"id":mid,"via":via}
 def reflect(self):
  rows=self.db.rows("SELECT content FROM messages WHERE role='user' ORDER BY id DESC LIMIT 300");n=self.memory.reflect_candidates([r["content"] for r in rows])
  self.db.execute("INSERT INTO events(kind,detail) VALUES('reflection',?)",(str(n)+" pending candidates",));return {"candidates":n,"pending":self.memory.pending()}
 def feedback(self,mid,positive):
  row=self.db.one("SELECT runtime FROM messages WHERE id=? AND role='assistant'",(mid,))
  if not row:return {"ok":False,"error":"Message not found"}
  self.db.execute("UPDATE messages SET feedback=? WHERE id=?",(1 if positive else -1,mid))
  if row["runtime"].startswith("skill:"):self.skills.feedback(row["runtime"].split(":",1)[1],positive)
  self.db.execute("INSERT INTO events(kind,detail) VALUES('feedback',?)",(str(mid),));return {"ok":True}
 def add_goal(self,title,details=""):
  i,_=self.db.execute("INSERT INTO goals(title,details) VALUES(?,?)",(title.strip(),details.strip()));return self.db.one("SELECT * FROM goals WHERE id=?",(i,))
 def update_goal(self,i,status=None,progress=None):
  row=self.db.one("SELECT * FROM goals WHERE id=?",(i,))
  if not row:return None
  status=status if status in ("open","done","paused") else row["status"];progress=row["progress"] if progress is None else progress
  self.db.execute("UPDATE goals SET status=?,progress=? WHERE id=?",(status,progress,i));return self.db.one("SELECT * FROM goals WHERE id=?",(i,))
