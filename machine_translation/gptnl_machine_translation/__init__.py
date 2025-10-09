import os
from pathlib import Path

# keep datasets and models in project storage (does not fit in home folder default location)
hf_cache_path_parent = Path("/projects/prjs0986")
hf_cache_location = hf_cache_path_parent / ".hf_cache_dir"
current_hf_home = os.getenv("HF_HOME")
if not current_hf_home and hf_cache_path_parent.exists():
    os.environ["HF_HOME"] = str(hf_cache_location)
# otherwise, it will be at ~/.cache/huggingface
print(f"HF_HOME={os.getenv('HF_HOME')}")
