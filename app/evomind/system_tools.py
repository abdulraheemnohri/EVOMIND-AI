"""Approval-gated, workspace-scoped computer tools. No shell execution."""
import json,platform,sys,os
from pathlib import Path
class WorkspaceTools:
    MAX_FILE_BYTES=1_000_000
    ALLOWED_READ={".txt",".md",".json",".csv",".py",".toml",".yaml",".yml",".ini",".log",".html",".css",".js"}
    def __init__(self,db,workspace):
        self.db=db;self.root=Path(workspace).resolve();self.root.mkdir(parents=True,exist_ok=True)
    def _path(self,relative):
        if not isinstance(relative,str) or not relative.strip():raise ValueError("A workspace-relative path is required")
        candidate=(self.root/relative).resolve()
        try:candidate.relative_to(self.root)
        except ValueError:raise ValueError("Path escapes the EVOMIND workspace")
        return candidate
    def tools(self):
        return [
          {"id":"system_info","name":"System information","approval":False,"description":"Read OS and Python version."},
          {"id":"workspace_list","name":"List workspace","approval":False,"description":"List files inside the EVOMIND workspace only."},
          {"id":"workspace_read","name":"Read workspace file","approval":False,"description":"Read supported text files inside the EVOMIND workspace."},
          {"id":"workspace_write_request","name":"Write workspace file","approval":True,"description":"Create a pending write request; user approval is required before the file is written."}
        ]
    def run(self,tool,args=None):
        args=args or {}
        if tool=="system_info":
            return {"platform":platform.platform(),"python":sys.version.split()[0],"architecture":platform.machine(),"pid":os.getpid(),"workspace":str(self.root)}
        if tool=="workspace_list":
            folder=self._path(args.get("path","."))
            if not folder.exists() or not folder.is_dir():raise ValueError("Workspace directory not found")
            items=[]
            for p in sorted(folder.iterdir(),key=lambda x:x.name.lower())[:200]:
                if p.is_symlink():continue
                items.append({"name":p.name,"type":"directory" if p.is_dir() else "file","size":p.stat().st_size if p.is_file() else None})
            return {"path":str(folder.relative_to(self.root)),"items":items}
        if tool=="workspace_read":
            path=self._path(args.get("path",""))
            if path.suffix.lower() not in self.ALLOWED_READ:raise ValueError("File extension is not allowed for reading")
            if path.is_symlink() or not path.is_file():raise ValueError("Workspace file not found")
            if path.stat().st_size>self.MAX_FILE_BYTES:raise ValueError("File exceeds 1 MB")
            try:return {"path":str(path.relative_to(self.root)),"content":path.read_text(encoding="utf-8")}
            except UnicodeDecodeError:raise ValueError("File is not UTF-8 text")
        if tool=="workspace_write_request":
            relative=args.get("path","");content=args.get("content","")
            path=self._path(relative)
            if path.suffix.lower() not in self.ALLOWED_READ:raise ValueError("File extension is not allowed for writing")
            if not isinstance(content,str) or len(content.encode("utf-8"))>self.MAX_FILE_BYTES:raise ValueError("Content exceeds 1 MB")
            payload=json.dumps({"path":str(path.relative_to(self.root)),"content":content},ensure_ascii=False)
            request_id,_=self.db.execute("INSERT INTO tool_requests(tool,payload,status) VALUES(?,?,'pending')",(tool,payload))
            self.db.execute("INSERT INTO events(kind,detail) VALUES('tool_request',?)",(str(request_id),))
            return {"request_id":request_id,"status":"pending","message":"Nothing has been written. Review and approve this request to execute it."}
        raise ValueError("Tool is not allow-listed")
    def requests(self):
        return self.db.rows("SELECT id,tool,payload,status,result,created_at,updated_at FROM tool_requests ORDER BY id DESC LIMIT 100")
    def decide(self,request_id,approve):
        row=self.db.one("SELECT * FROM tool_requests WHERE id=?",(request_id,))
        if not row:return {"ok":False,"error":"Request not found"}
        if row["status"]!="pending":return {"ok":False,"error":"Request has already been decided"}
        if not approve:
            self.db.execute("UPDATE tool_requests SET status='rejected',result='Rejected by user',updated_at=CURRENT_TIMESTAMP WHERE id=?",(request_id,))
            return {"ok":True,"status":"rejected"}
        if row["tool"]!="workspace_write_request":return {"ok":False,"error":"Unsupported approval action"}
        try:
            payload=json.loads(row["payload"]);path=self._path(payload["path"])
            if path.suffix.lower() not in self.ALLOWED_READ:raise ValueError("File extension is not allowed")
            path.parent.mkdir(parents=True,exist_ok=True)
            # Resolve again after creating parent folders to prevent path traversal.
            path=self._path(payload["path"])
            if path.exists() and path.is_symlink():raise ValueError("Refusing to overwrite a symbolic link")
            temp=path.with_name(path.name+".evomind-tmp")
            temp.write_text(payload["content"],encoding="utf-8")
            temp.replace(path)
            result="Wrote "+str(path.relative_to(self.root))
            self.db.execute("UPDATE tool_requests SET status='executed',result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(result,request_id))
            self.db.execute("INSERT INTO events(kind,detail) VALUES('tool_executed',?)",(str(request_id),))
            return {"ok":True,"status":"executed","result":result}
        except Exception as e:
            self.db.execute("UPDATE tool_requests SET status='error',result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(str(e)[:500],request_id))
            return {"ok":False,"status":"error","error":str(e)}
