# 🚄 铁路技能竞赛模拟考试系统

Railway Skills Competition Simulation Exam System

## 快速开始（开发模式）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python app.py
```

浏览器会自动打开 `http://127.0.0.1:5000`（或下一个空闲端口）。

## 打包为 .exe

### 方法一：使用 build.bat（推荐）

双击 `build.bat` 即可自动完成打包。

### 方法二：手动命令行

```bash
pyinstaller --onefile --noconsole ^
  --add-data "templates;templates" ^
  --add-data "data;data" ^
  --hidden-import flask ^
  --hidden-import jinja2.ext ^
  --hidden-import waitress ^
  --hidden-import flask_cors ^
  --name "RailwayExam" ^
  app.py
```

构建成功后，`dist\RailwayExam.exe` 就是可以分发的单文件程序。

### 方法三：使用 .spec 文件（高级）

如需自定义图标或额外配置，先生成 .spec 文件再构建：

```bash
pyi-makespec --onefile --noconsole ^
  --add-data "templates;templates" ^
  --add-data "data;data" ^
  --hidden-import flask ^
  --hidden-import jinja2.ext ^
  --hidden-import waitress ^
  --hidden-import flask_cors ^
  --name "RailwayExam" ^
  app.py

# 编辑 RailwayExam.spec 后：
pyinstaller RailwayExam.spec
```

## 使用说明

1. 双击 `RailwayExam.exe`（首次启动可能需要 5-15 秒解压）
2. 浏览器自动打开考试页面
3. 选择题库（通信工 / 信号工）
4. 设置各题型的抽题数量和分值
5. 设置考试时长，点击「开始考试」
6. 逐题作答，计时器倒计时
7. 提交后查看成绩，可保存到本地

### 注意事项

- **简答题和综合题**仅供学习参考，不计分，也不强制填写
- 同一时间只能运行一个考试实例（防止端口冲突）
- 关闭浏览器不会自动退出程序，请点击「退出程序」按钮
- 成绩保存在 `文档\RailwayExam\` 目录下

## 题库说明

| 题库 | 文件名 | 题目数 |
|------|--------|--------|
| 通信工 | 2026年职工技能竞赛技术文件-轨道交通通信工-理论.csv | ~796 |
| 信号工 | 第19届股份技能大赛题库-信号（最终版）.csv | ~817 |

### 题型

| 题型 | 代码 | 计分 | 作答方式 |
|------|------|------|----------|
| 填空题 | fill | ✓ | 文本输入，模糊匹配 |
| 单选题 | choice | ✓ | A/B/C/D 单选 |
| 判断题 | judge | ✓ | 对/错 单选 |
| 简答题 | short_answer | ✗ | 文本输入（参考） |
| 综合题 | comprehensive | ✗ | 文本输入（参考） |

## 技术架构

- **后端**: Python + Flask + Waitress
- **前端**: 单文件 HTML + CSS + JavaScript
- **打包**: PyInstaller（--onefile + --noconsole）
- **数据**: CSV（UTF-8 BOM 编码）

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 打包后无法找到 CSV | 确保 `--add-data "data;data"` 正确 |
| 中文乱码 | CSV 文件编码必须是 UTF-8-BOM |
| 端口被占用 | 程序会自动寻找空闲端口 |
| exe 启动很慢 | --onefile 模式需要解压，正常现象（5-15秒） |
| 杀毒软件报警 | PyInstaller 打包的程序可能被误报，添加白名单即可 |

## 许可证

内部使用
