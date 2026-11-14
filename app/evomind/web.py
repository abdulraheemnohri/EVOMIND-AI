from pathlib import Path
from litestar import Litestar,get,post
from litestar.response import Response
from .config import settings
from .engine import EvoMind
from .agents import AgentHub
settings.prepare()
assistant=EvoMind(settings.db_path or settings.data_dir/"evomind.sqlite3",settings.models_dir)
agents=AgentHub(assistant.db,assistant.models)
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
@post("/api/hf/search")
async def hf_search(data:dict):
 try:return {"models":assistant.hf_models.search(str(data.get("query","litert-community")),int(data.get("limit",10)))}
 except Exception as e:return {"error":str(e)}
@post("/api/hf/files")
async def hf_files(data:dict):
 try:return {"files":assistant.hf_models.files(str(data.get("repo_id","")))}
 except Exception as e:return {"error":str(e)}
@post("/api/hf/download")
async def hf_download(data:dict):
 try:return assistant.hf_models.download(str(data.get("repo_id","")),str(data.get("filename","")))
 except Exception as e:return {"error":str(e)}
@get("/api/models")
async def models():return {"active":assistant.models.active.key,"inventory":assistant.models.inventory(),"error":assistant.models.last_error}
@post("/api/models/select")
async def select(data:dict):
 try:return assistant.models.select(str(data.get("key","demo")),data.get("filename"))
 except Exception as e:return {"error":str(e),"active":assistant.models.active.key}
@get("/api/agents")
async def agent_list():return {"agents":agents.list(),"tools":agents.tools()}
@post("/api/agents/run")
async def agent_run(data:dict):
 try:return agents.run(str(data.get("agent","general")),str(data.get("text","")))
 except Exception as e:return {"error":str(e)}
@post("/api/tools/{tool:str}")
async def tool_run(tool:str,data:dict):
 try:return agents.use_tool(tool,data)
 except Exception as e:return {"error":str(e)}
@get("/api/tasks")
async def task_list():return {"tasks":assistant.db.rows("SELECT * FROM tasks ORDER BY id DESC LIMIT 200")}
@post("/api/tasks")
async def task_create(data:dict):
 title=str(data.get("title","")).strip()
 if not title:return {"error":"Task title required"}
 if len(title)>180:return {"error":"Task title too long"}
 i,_=assistant.db.execute("INSERT INTO tasks(title,description) VALUES(?,?)",(title,str(data.get("description",""))[:4000]))
 return {"task":assistant.db.one("SELECT * FROM tasks WHERE id=?",(i,))}
@post("/api/tasks/{task_id:int}")
async def task_update(task_id:int,data:dict):
 row=assistant.db.one("SELECT * FROM tasks WHERE id=?",(task_id,))
 if not row:return {"error":"Task not found"}
 status=data.get("status",row["status"])
 if status not in ("pending","in_progress","done","cancelled"):return {"error":"Invalid task status"}
 assistant.db.execute("UPDATE tasks SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,task_id))
 return {"task":assistant.db.one("SELECT * FROM tasks WHERE id=?",(task_id,))}
@get("/api/system")
async def system_info():
 import os,platform,sys
 return {"platform":platform.platform(),"python":sys.version.split()[0],"architecture":platform.machine(),"host":settings.host,"port":settings.port,"data_dir":str(settings.data_dir),"models_dir":str(settings.models_dir),"pid":os.getpid(),"autostart":"Use scripts/install_autostart.sh (systemd) or Android Termux:Boot guide."}
app=Litestar(route_handlers=[index,chat,stats,memories,decision,reflect,skills,install,feedback,goals,add_goal,update_goal,hf_search,hf_files,hf_download,models,select,agent_list,agent_run,tool_run,task_list,task_create,task_update,system_info])
def main():
 import uvicorn
 uvicorn.run(app,host=settings.host,port=settings.port)
if __name__=="__main__":main()
