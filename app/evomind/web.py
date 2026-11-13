from pathlib import Path
from litestar import Litestar,get,post
from litestar.response import Response
from .config import settings
from .engine import EvoMind
settings.prepare()
assistant=EvoMind(settings.db_path or settings.data_dir/"evomind.sqlite3",settings.models_dir)
@get("/")
async def index():return Response((Path(__file__).parent/"static"/"index.html").read_text(),media_type="text/html")
@post("/api/chat")
async def chat(data:dict):return assistant.chat(str(data.get("text","")))
@get("/api/stats")
async def stats():return assistant.stats()
@get("/api/memories")
async def memories():return {"approved":assistant.db.rows("SELECT * FROM memories WHERE status='approved' ORDER BY id DESC"),"pending":assistant.memory.pending()}
@post("/api/memories/{memory_id:int}/decision")
async def decision(memory_id:int,data:dict):return {"ok":assistant.memory.decide(memory_id,bool(data.get("approve",False)))}
@post("/api/reflect")
async def reflect():return assistant.reflect()
@get("/api/skills")
async def skills():return assistant.skills.list()
@post("/api/skills")
async def install(data:dict):
 try:return {"ok":True,"skill":assistant.skills.install(str(data.get("name","")),str(data.get("description","")),str(data.get("trigger","")).lower(),str(data.get("action","")))}
 except ValueError as e:return {"ok":False,"error":str(e)}
@post("/api/feedback")
async def feedback(data:dict):return assistant.feedback(int(data.get("id",0)),bool(data.get("positive",True)))
@get("/api/goals")
async def goals():return assistant.db.rows("SELECT * FROM goals ORDER BY id DESC")
@post("/api/goals")
async def add_goal(data:dict):
 title=str(data.get("title","")).strip()
 return assistant.add_goal(title,str(data.get("details",""))) if title else {"error":"Goal title required"}
@post("/api/goals/{goal_id:int}")
async def update_goal(goal_id:int,data:dict):return assistant.update_goal(goal_id,data.get("status"),data.get("progress")) or {"error":"Goal not found"}
@get("/api/models")
async def models():return {"active":assistant.models.active.key,"inventory":assistant.models.inventory(),"error":assistant.models.last_error}
@post("/api/models/select")
async def select(data:dict):
 try:return assistant.models.select(str(data.get("key","demo")),data.get("filename"))
 except Exception as e:return {"error":str(e),"active":assistant.models.active.key}
app=Litestar(route_handlers=[index,chat,stats,memories,decision,reflect,skills,install,feedback,goals,add_goal,update_goal,models,select])
def main():
 import uvicorn
 uvicorn.run(app,host=settings.host,port=settings.port)
if __name__=="__main__":main()
