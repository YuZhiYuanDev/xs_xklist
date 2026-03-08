# 浙江省普通高中选课管理系统 - 自动化选课程序

## 项目简介

这是一个用于浙江省普通高中选课管理系统的自动化选课程序，支持自动获取课程列表和批量报名课程。

## 功能特性

- 自动获取可选课程列表
- 根据关键词自动报名课程
- 支持配置文件管理
- 完整的日志记录
- 标准的Python项目结构

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/course-selector.git
cd course-selector

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 使用pip安装

```bash
pip install course-selector
```

## 使用方法

### 命令行使用

```bash
# 基本使用
python -m course_selector

# 指定配置文件
python -m course_selector --config /path/to/config.json

# 显示详细日志
python -m course_selector --verbose

# 显示帮助
python -m course_selector --help
```

### 作为库使用

```python
from course_selector import CourseSelector, ConfigManager

# 加载配置
config = ConfigManager().load()

# 创建选择器
selector = CourseSelector(config.cookies)

# 获取课程列表
courses = selector.get_course_list()

# 显示课程
selector.display_courses()

# 自动报名
results = selector.auto_enroll_by_keywords(["数学", "物理"])
print(results)
```

## 配置说明

### 配置文件格式 (config.json)

```json
{
    "cookies": "your_cookie_string_here",
    "target_courses": ["课程名称1", "课程名称2"],
    "semester": "2025/2026下",
    "request_interval": 1.0,
    "timeout": 30
}
```

### 配置项说明

- `cookies`: 从浏览器获取的Cookie字符串
- `target_courses`: 要报名的课程名称列表
- `semester`: 学期设置
- `request_interval`: 请求间隔时间（秒）
- `timeout`: 请求超时时间（秒）

### Cookie获取方法

1. 登录浙江省普通高中选课管理系统
2. 打开浏览器开发者工具（F12）
3. 切换到Network标签
4. 刷新页面，找到任意请求
5. 在请求头中找到Cookie字段，复制完整内容

## 项目结构

```
course_selector_project/
├── src/
│   └── course_selector/
│       ├── __init__.py           # 包入口
│       ├── __main__.py           # 命令行入口
│       ├── core/                 # 核心业务逻辑
│       │   ├── models.py         # 数据模型
│       │   └── selector.py       # 选课控制器
│       ├── http/                 # HTTP请求处理
│       │   └── client.py         # HTTP客户端
│       ├── parser/               # HTML解析
│       │   └── html_parser.py    # HTML解析器
│       ├── config/               # 配置管理
│       │   ├── manager.py        # 配置管理器
│       │   └── cookies.py        # Cookie管理器
│       └── utils/                # 工具函数
│           └── logger.py         # 日志工具
├── tests/                        # 测试目录
├── config/                       # 配置文件目录
├── pyproject.toml                # 项目配置
├── requirements.txt              # 运行时依赖
└── README.md                     # 项目说明
```

## 开发

### 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src/
isort src/
```

### 类型检查

```bash
mypy src/
```

## 注意事项

1. 请确保Cookie有效，过期后需要重新获取
2. 建议设置合理的请求间隔，避免频繁请求
3. 本程序仅供学习交流使用，请遵守学校相关规定

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
