# 半自动分拆脚本
## 一、介绍
项目的主要思路很简单，人工找到导航栏的位置，代码自动在导航栏找到a标签，然后按照a标签路径，把结果写入文件。然后合并每个网站的结果，然后根据关键词做过滤。  

### 主要问题
很多时候，一个网站的导航栏对应的都是一个个分站，我们实际要的是进入分站，然后分拆分站的导航栏，本项目也是支持这样的，通过关键字"C"来触发。
## 二、使用说明
修改好了必要的位置（webdriver的路径）之后，可以直接*run split_tool.py* 了
### 2.1 基本使用
1. 先输入url，url一定是不带www、http等的纯净url，默认情况下脚本自动添加http://www.，**如果不希望脚本添加，请在url前面添加数字1**，例如：==1xmtfj.gov.cn==
2. 输入url之后等一下（有时很久，看网络），会提示输入nav的路径，这个时候粘贴nav的css selector
> 导航栏的css selector路径获取，chrome下面审查元素，选中导航栏元素，右键调出菜单，选择Copy->Copy selector，如果你自己会写直接写也是可以的
3. 完成上面两步之后，该导航栏上面的链接将会按照规则写入文件，url的名字会按照层级拼接，例如：*上海交通大学-新闻-院系频道-机械与动力工程学院*
4. 如果该网页有多处需要分拆的类导航栏结构，重复上述过程即可
<center>
<img src="https://note.youdao.com/yws/public/resource/05cbde4498bb988906b20eee74a87c1a/xmlnote/D2E6A377ADE44765AF70F15CE8CC1639/989" width="80%"/>
</center>

<center>
<img src="https://note.youdao.com/yws/public/resource/05cbde4498bb988906b20eee74a87c1a/xmlnote/5F350823C81B4FB997D580BF0506C919/992" width="80%"/>
</center>

### 2.2 完成导航页面分拆
很多时候，遇到的网站比较变态，比如：[遂宁新闻网](http://www.snxw.com/)这种恶心东西，其导航栏如图所示：

<center>
<img src="https://note.youdao.com/yws/public/resource/05cbde4498bb988906b20eee74a87c1a/xmlnote/20BB75C808C248E09AA53A1E4D0A2E4C/1039" width="80%"/>
</center>
导航栏上面每个item点进去都是一个独立网页，我们需要对那个独立网页进行分拆。   

遇到上述情况，请在url前面加“C”，表示该网站为复杂网站。例如：**Csnxw.*com***  
在你输入了nav位置之后，脚本不会把当前的nav元素写入文件，而是自动帮你点进去每个item，我们需要做的就是在进入一个item的时候提示输入nav，我们输入子网站的导航栏css
selector就行了，输入之后，系统会自动保存每个子网站的分拆结果，最后汇总到总站去。

## 三、代码说明
代码主要分为两部分：
1. 页面结果获取部分
2. 结果汇总过滤部分

控制两部分的主要变量是***PROCESS***，在290行左右

整体设计是每个网站均写入自己的csv文件，然后最后通过合并操作把所有的结果汇总，最后再进行过滤。所有数据操作使用pandas，主要是pandas操作数据方便快捷。