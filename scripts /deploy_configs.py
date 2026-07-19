import os
import copy
from ruamel.yaml import YAML

# 初始化 YAML 解析器，完美保留锚点与排版
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=2, offset=0)
yaml.width = 4096 

TEMPLATE_DIR = 'template'
OUTPUT_DIR = 'release/configs'

# 核心常量：需要从路由器/全托管 GUI 客户端中剥离的底层劫持模块
CORE_ROUTING_MODULES = ["dns", "tun", "sniffer"]
ALL_PORTS = ["mixed-port", "redir-port", "tproxy-port", "port", "socks-port", "allow-lan"]
CONTROLLER_KEYS = ["external-controller", "external-ui", "external-ui-url", "secret"]

# ==========================================
# 终极构建矩阵 (云端开关字典)
# ==========================================
config_matrix = {
    # ----------------------------------------
    # 1. 移动/桌面独立端 (保留全量底层网络，注入特定端口)
    # ----------------------------------------
    "surfing_smart": {
        "source": "base_smart.yaml",
        "ports": {"mixed-port": 7890, "redir-port": 7891, "tproxy-port": 1536},
        "controller": "0.0.0.0:9090",
        "remove_keys": [] # 全量保留
    },
    "box_smart": {
        "source": "base_smart.yaml",
        "ports": {"mixed-port": 7890, "redir-port": 9797, "tproxy-port": 9898},
        "controller": "0.0.0.0:9090",
        "remove_keys": [] 
    },
    "surfing_standard": {
        "source": "base_standard.yaml",
        "ports": {"mixed-port": 7890, "redir-port": 7891, "tproxy-port": 1536},
        "controller": "0.0.0.0:9090",
        "remove_keys": [] 
    },
    "box_standard": {
        "source": "base_standard.yaml",
        "ports": {"mixed-port": 7890, "redir-port": 9797, "tproxy-port": 9898},
        "controller": "0.0.0.0:9090",
        "remove_keys": [] 
    },

    # ----------------------------------------
    # 2. 路由器/强托管 GUI 端 (暴力剥离底层，化身为纯粹的策略分发清单)
    # ----------------------------------------
    "flclash_smart": {
        "source": "base_smart.yaml",
        "ports": "REMOVE_ALL", 
        "controller": "REMOVE",
        "remove_keys": CORE_ROUTING_MODULES
    },
    "flclash_standard": {
        "source": "base_standard.yaml",
        "ports": "REMOVE_ALL",
        "controller": "REMOVE",
        "remove_keys": CORE_ROUTING_MODULES
    },
    "openclash_smart": {
        "source": "base_smart.yaml",
        "ports": "REMOVE_ALL", # 路由器防火墙接管端口
        "controller": "127.0.0.1:9090", # 保留控制器供面板通信
        "remove_keys": CORE_ROUTING_MODULES # 防止 DNS 环路和 TUN 冲突
    },
    "openclash_standard": {
        "source": "base_standard.yaml",
        "ports": "REMOVE_ALL",
        "controller": "127.0.0.1:9090",
        "remove_keys": CORE_ROUTING_MODULES
    },
    "shellcrash_smart": {
        "source": "base_smart.yaml",
        "ports": "REMOVE_ALL",
        "controller": "127.0.0.1:9999",
        "remove_keys": CORE_ROUTING_MODULES
    },
    "shellcrash_standard": {
        "source": "base_standard.yaml",
        "ports": "REMOVE_ALL",
        "controller": "127.0.0.1:9999",
        "remove_keys": CORE_ROUTING_MODULES
    }
}

def build_configs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 预加载 2 个母版到内存字典
    templates = {}
    for template_name in ["base_smart.yaml", "base_standard.yaml"]:
        path = os.path.join(TEMPLATE_DIR, template_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                templates[template_name] = yaml.load(f)
        else:
            print(f"Warning: Base template {template_name} not found in {TEMPLATE_DIR}/.")

    for app_name, settings in config_matrix.items():
        source_file = settings["source"]
        if source_file not in templates:
            continue
            
        print(f"Building {app_name}.yaml...")
        data = copy.deepcopy(templates[source_file])

        # 1. 处理端口
        if settings["ports"] == "REMOVE_ALL":
            for key in ALL_PORTS:
                data.pop(key, None)
        elif isinstance(settings["ports"], dict):
            data.update(settings["ports"])

        # 2. 处理控制器
        if settings["controller"] == "REMOVE":
            for key in CONTROLLER_KEYS:
                data.pop(key, None)
        elif settings["controller"]:
            data["external-controller"] = settings["controller"]

        # 3. 处理底层模块 (DNS, TUN, Sniffer 等)
        for key in settings["remove_keys"]:
            data.pop(key, None)

        output_path = os.path.join(OUTPUT_DIR, f"{app_name}.yaml")
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        print(f"  -> Generated: {output_path}")

if __name__ == "__main__":
    build_configs()
