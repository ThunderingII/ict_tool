# 实验室标注、分拆半自动协助脚本
## 一、说明
20181203更新

**请使用tool文件夹下面的split.py**

这个是为了加速实验室分派的任务完成的一套脚本，主要分为自动标注脚本、半自动分拆脚本，具体用法见各个文件夹。
## 二、依赖
本项目依赖[selenium](https://www.seleniumhq.org/)库，所以需要以下准备：
1. 安装selenium的python库,pip install selenium
2. 下载自己对应系统的[driver](https://www.seleniumhq.org/projects/webdriver/)文件，windows系统的已经下好了
3. 如果非windows系统，需要修改代码*spilt_tools/split_tool.py*的++45++行（相近位置，也许会变）