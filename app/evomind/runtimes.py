"""Optional local inference adapters, loaded only when selected."""
import gc,os
from pathlib import Path
class RuntimeErrorBase(RuntimeError):pass
class DemoRuntime:
 key="demo"
 def generate(self,msgs):
  q=next((m["content"] for m in reversed(msgs) if m["role"]=="user"),"")
  return "EVOMIND demo mode. Select a local GGUF or LiteRT-LM model in Model Manager. Saved message: "+q[:160]
 def close(self):pass
class GGUFRuntime:
 key="gguf"
 def __init__(self,path):
  try:from llama_cpp import Llama
  except ImportError as e:raise RuntimeErrorBase("Install optional dependency: pip install -e '.[gguf]'") from e
  self.model=Llama(model_path=str(path),n_ctx=4096,n_threads=max(1,(os.cpu_count() or 2)//2),verbose=False)
 def generate(self,msgs):
  r=self.model.create_chat_completion(messages=msgs,max_tokens=700,temperature=.65);return (r["choices"][0]["message"].get("content") or "").strip()
 def close(self):
  m=getattr(self,"model",None);c=getattr(m,"close",None)
  if callable(c):c()
  self.model=None;gc.collect()
class LiteRTLMRuntime:
 key="litertlm"
 def __init__(self,path):
  try:import litert_lm
  except ImportError as e:raise RuntimeErrorBase("Install compatible litert-lm-api for this platform.") from e
  self.lm=litert_lm
  try:self.engine=litert_lm.Engine(str(path),backend=litert_lm.Backend.CPU())
  except Exception as e:raise RuntimeErrorBase("LiteRT-LM model/API incompatible: "+str(e)) from e
 def generate(self,msgs):
  try:
   lm=self.lm;sysm=[lm.Message.system(m["content"]) for m in msgs if m["role"]=="system"];turns=[m for m in msgs if m["role"]!="system"]
   prompt="\n\n".join(m["role"].upper()+": "+m["content"] for m in turns)
   with self.engine.create_conversation(messages=sysm,max_output_tokens=700) as conv:out=conv.send_message(prompt)
   return "".join(x.get("text","") for x in out.get("content",[]) if isinstance(x,dict)).strip()
  except Exception as e:raise RuntimeErrorBase("LiteRT-LM generation failed: "+str(e)) from e
 def close(self):
  c=getattr(self.engine,"close",None)
  if callable(c):c()
  self.engine=None;gc.collect()
class ModelManager:
 def __init__(self,d):self.directory=d;self.active=DemoRuntime();self.last_error=None
 def inventory(self):
  g=sorted(self.directory.glob("*.gguf"));l=sorted(self.directory.glob("*.litertlm"))
  return [{"key":"demo","ready":True,"files":[]},{"key":"gguf","ready":bool(g),"files":[x.name for x in g]},{"key":"litertlm","ready":bool(l),"files":[x.name for x in l]}]
 def select(self,key,filename=None):
  if key=="demo":new=DemoRuntime()
  elif key in ("gguf","litertlm"):
   fs=sorted(self.directory.glob("*.gguf" if key=="gguf" else "*.litertlm"));p=self.directory/filename if filename else (fs[0] if fs else None)
   if p is None or p.resolve().parent!=self.directory.resolve() or not p.is_file():raise RuntimeErrorBase("No model file found in models directory.")
   new=GGUFRuntime(p) if key=="gguf" else LiteRTLMRuntime(p)
  else:raise RuntimeErrorBase("Unknown runtime")
  old,self.active=self.active,new;old.close();self.last_error=None;return {"active":key}
 def generate(self,msgs):
  try:return self.active.generate(msgs)
  except Exception as e:self.last_error=str(e);raise
