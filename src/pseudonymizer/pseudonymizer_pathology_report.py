import yaml
from dotenv import load_dotenv
load_dotenv()
from common.logger import log_debug

def load_patho_config(yml_path="config/pseudonynmization.yml"):
    with open(yml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("pathology_report", {})

if __name__ == "__main__":
    pr_cfg = load_patho_config()
    log_debug("test")
    log_debug(f"input_dir: {pr_cfg.get('input_dir')}")
    log_debug(f"output_dir: {pr_cfg.get('output_dir')}")