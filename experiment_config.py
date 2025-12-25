# experiment_config.py
# 仅放变量，不放函数

# 是否为开发者模式：
# True  = 开发者模式（有 sidebar，可以调模式和时间）
# False = 测试模式（隐藏 sidebar，所有参数固定）
DEV_MODE = False

# 必须提问的问题
REQUIRED_QUESTION = "is raw milk more nutritious than pasteurized milk?"

# 回答结束后再等待的秒数
END_DELAY = 3

# Qualtrics 验证码
VERIFY_CODE = "697395"

# 头像路径
USER_AVATAR_PATH = "avatar-user.jpg"
AGENT_AVATAR_PATH = "avatar-ai.jpg"

# 思考相关配置（测试模式直接用这里的值；
# 开发模式中作为默认值）
THINKING_ENABLED = True      # 是否显示“thinking”
THINKING_TIME = 15         # 实际思考时间（秒）
DISPLAY_TIME = 15     # 显示的思考时间（秒）
