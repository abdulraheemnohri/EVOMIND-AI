import re
class MemoryStore:
 def __init__(self,db):self.db=db
 def add(self,text,source="user",status="approved"):
  text=" ".join((text or "").strip().split())[:500]
  if not text:return None
  self.db.execute("INSERT OR IGNORE INTO memories(content,source,status) VALUES(?,?,?)",(text,source[:80],status))
  return self.db.one("SELECT * FROM memories WHERE content=?",(text,))
 def search(self,q,limit=8):
  terms=[x for x in re.findall(r"[\w'-]+",q.lower()) if len(x)>2][:12]
  rows=self.db.rows("SELECT * FROM memories WHERE status='approved' ORDER BY id DESC LIMIT 500")
  ranked=[(sum(t in r["content"].lower() for t in terms),r) for r in rows]
  ranked=[x for x in ranked if x[0]];ranked.sort(key=lambda x:(x[0],x[1]["id"]),reverse=True)
  return [r for _,r in ranked[:limit]] if terms else rows[:limit]
 def pending(self):return self.db.rows("SELECT * FROM memories WHERE status='pending' ORDER BY id DESC")
 def decide(self,i,approve):
  _,n=self.db.execute("UPDATE memories SET status=? WHERE id=? AND status='pending'",("approved" if approve else "rejected",i));return n==1
 def reflect_candidates(self,texts):
  pats=[r"\bremember that\s+([^.!?\n]{3,180})",r"\bmy name is\s+[^.!?\n]{2,80}",r"\bi (?:like|love|prefer|enjoy|work as|live in)\s+[^.!?\n]{2,120}"];n=0
  for text in texts:
   for p in pats:
    for m in re.finditer(p,text,re.I):
     if self.add(m.group(0).strip(" .!?"),"reflection","pending"):n+=1
  return n
