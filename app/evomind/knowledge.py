"""Local, offline document ingestion and retrieval."""
import hashlib,re
class KnowledgeBase:
    MAX_DOCUMENT_CHARS=2_000_000
    CHUNK_SIZE=1400
    OVERLAP=220
    def __init__(self,db):self.db=db
    def _chunks(self,text):
        text=re.sub(r"\r\n?","\n",text).strip()
        if not text:return []
        out=[];start=0
        while start<len(text):
            end=min(start+self.CHUNK_SIZE,len(text))
            if end<len(text):
                boundary=max(text.rfind("\n",start,end),text.rfind(" ",start,end))
                if boundary>start+self.CHUNK_SIZE//2:end=boundary
            part=text[start:end].strip()
            if part:out.append(part)
            if end>=len(text):break
            start=max(end-self.OVERLAP,start+1)
        return out
    def add_text(self,title,content,source="pasted text"):
        title=(title or "").strip()[:180];content=(content or "").strip()
        if not title:raise ValueError("Document title is required")
        if not content:raise ValueError("Document text is empty")
        if len(content)>self.MAX_DOCUMENT_CHARS:raise ValueError("Document exceeds 2,000,000 characters")
        digest=hashlib.sha256(content.encode("utf-8")).hexdigest()
        existing=self.db.one("SELECT id,title FROM knowledge_documents WHERE content_hash=?",(digest,))
        if existing:return {"document":existing,"duplicate":True,"chunks":0}
        doc_id,_=self.db.execute("INSERT INTO knowledge_documents(title,source,content_hash) VALUES(?,?,?)",(title,(source or "pasted text")[:500],digest))
        chunks=self._chunks(content)
        for i,part in enumerate(chunks):self.db.execute("INSERT INTO knowledge_chunks(document_id,chunk_index,content) VALUES(?,?,?)",(doc_id,i,part))
        self.db.execute("INSERT INTO events(kind,detail) VALUES('knowledge_ingest',?)",(title,))
        return {"document":self.db.one("SELECT * FROM knowledge_documents WHERE id=?",(doc_id,)),"duplicate":False,"chunks":len(chunks)}
    def list(self):
        return self.db.rows("SELECT d.id,d.title,d.source,d.created_at,COUNT(c.id) chunks FROM knowledge_documents d LEFT JOIN knowledge_chunks c ON c.document_id=d.id GROUP BY d.id ORDER BY d.id DESC")
    def search(self,query,limit=6):
        terms=re.findall(r"[\w-]{2,}",(query or "").lower())[:10]
        if not terms:return []
        limit=max(1,min(int(limit),20))
        clauses=" OR ".join(["LOWER(c.content) LIKE ?" for _ in terms])
        params=["%"+t+"%" for t in terms]
        rows=self.db.rows("SELECT c.id,c.document_id,c.chunk_index,c.content,d.title,d.source FROM knowledge_chunks c JOIN knowledge_documents d ON d.id=c.document_id WHERE "+clauses+" ORDER BY d.id DESC LIMIT 100",params)
        for row in rows:
            low=row["content"].lower()
            row["score"]=sum(low.count(t) for t in terms)
        rows.sort(key=lambda x:(x["score"],x["document_id"]),reverse=True)
        return rows[:limit]
    def delete(self,document_id):
        row=self.db.one("SELECT id,title FROM knowledge_documents WHERE id=?",(document_id,))
        if not row:return False
        self.db.execute("DELETE FROM knowledge_documents WHERE id=?",(document_id,))
        self.db.execute("INSERT INTO events(kind,detail) VALUES('knowledge_delete',?)",(row["title"],))
        return True
