"""Optional Hugging Face model discovery and safe file downloads."""
from pathlib import Path
class HuggingFaceModels:
    ALLOWED_SUFFIXES={".gguf",".litertlm"}
    def __init__(self,directory):self.directory=Path(directory).resolve()
    def search(self,query,limit=10):
        try:from huggingface_hub import HfApi
        except ImportError as e:raise RuntimeError("Install optional dependency: pip install -e '.[hf]'") from e
        api=HfApi();items=api.list_models(search=query or "litert-community",limit=max(1,min(int(limit),20)),sort="downloads",direction=-1)
        return [{"id":m.id,"downloads":m.downloads,"likes":m.likes,"pipeline_tag":m.pipeline_tag} for m in items]
    def files(self,repo_id):
        try:from huggingface_hub import HfApi
        except ImportError as e:raise RuntimeError("Install optional dependency: pip install -e '.[hf]'") from e
        names=HfApi().list_repo_files(repo_id)
        return [n for n in names if Path(n).suffix.lower() in self.ALLOWED_SUFFIXES]
    def download(self,repo_id,filename):
        from huggingface_hub import hf_hub_download
        if Path(filename).suffix.lower() not in self.ALLOWED_SUFFIXES:raise ValueError("Only .gguf and .litertlm model files are accepted")
        if filename.startswith("/") or ".." in Path(filename).parts:raise ValueError("Invalid model filename")
        self.directory.mkdir(parents=True,exist_ok=True)
        result=Path(hf_hub_download(repo_id=repo_id,filename=filename,local_dir=str(self.directory))).resolve()
        if result.parent!=self.directory and self.directory not in result.parents:raise ValueError("Download escaped model directory")
        return {"repo_id":repo_id,"filename":filename,"path":str(result),"bytes":result.stat().st_size}
