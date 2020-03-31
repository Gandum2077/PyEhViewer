# PyEhViewer

提升[exhentai.org](https://exhentai.org)在 iOS 平台的阅读体验，并尽情使用其强大的搜索、评分、收藏、评论等诸多功能！  
本应用基于 Pythonista 3 平台。在功能上对标 Android 平台的 EhViewer。另外，也选择在 JSBox 平台的孪生应用[JSEhViewer](https://github.com/Gandum2077/JSEhViewer)。

## Features

- 自动翻页，解放左酱右酱
- 快捷搜索
- 高级搜索
- 边栏、搜索词收藏、直接打开 url 等快捷功能
- 标签翻译
- 打分、收藏、分享、评论
- 可以导入已缓存的旧版本，或者将旧版本导到新版本，方便追更新
- 缓存，缓存内容也可以搜索
- 自适应屏幕
- 阅读页面可以使用手势操作
- 代码尽量模块化设计，所以你可以添加想要的任何功能！

## 前提

这是本人为了欣赏艺术、提升欣赏艺术的体验才写的，因此很遗憾，可能不适合对艺术没有追求的人。  
本程序虽然前提设置有点复杂，但是程序本身的操作是一目了然的。

**你必须满足以下前提才能使用 PyEhViewer:**

1. (必要) [Pythonista 3](https://apps.apple.com/cn/app/pythonista-3/id1085978097)
2. (必要) iPad。 **不支持 iPhone。**
3. (必要) 可以访问 e-hentai.org 和 exhentai.org 的网络环境，并且不可以使用 MITM 软件。如果你使用代理，请注意可能需要设为全局代理或者手动添加以上两个网址，因为很多代理软件没有这两个网址。  
   关于如何手动添加代理设置，举两个例子：  
   例一 Quantumult：在配置文件加入`HOST-SUFFIX,e-hentai.org,PROXY,resolve-on-proxy`和`HOST-SUFFIX,exhentai.org,PROXY,resolve-on-proxy`。  
   例二 Surge：在配置文件加入`DOMAIN-SUFFIX,e-hentai.org,Proxy`和`DOMAIN-SUFFIX,exhentai.org,Proxy`。
4. (必要) 注册[e-hentai.org](https://e-hentai.org)账号，并确保可以访问[exhentai.org](https://exhentai.org)，然后请去[Hath Perks 页面](https://e-hentai.org/hathperks.php)点亮 Multi-Page Viewer 的 Hath Perk
5. [设置界面](https://exhentai.org/uconfig.php)做以下设置：

   - (必要)Front Page Settings 设为 Extended
   - (必要)Thumbnail Settings 中的 Size 设为 Large
   - (可选)Gallery Name Display 设为 Japanese Title (if available)
   - (可选)Search Result Count 设为 50 results。此功能需要 Paging Enlargement I 的 Hath Perk

## 安装和更新

建议安装[stash](https://github.com/ywangd/stash)，然后通过 git 来安装和更新。`stash`必须要运行在 Python 2.7 环境下。

- 安装

```
git clone https://github.com/Gandum2077/PyEhViewer.git
```

请注意后面的.git 不要漏了

- 更新

```
cd PyEhViewer; git pull
```

请注意需要先进入 PyEhViewer 的目录，如果你安装在别的地方，那么要对应的修改。  
此方法只保证在你没有过编辑行为，仅运行过`main.py`时可用，如果出现`WARNING: there are uncommitted modified files and/or staged changes. These could be overwritten by this command. Continue anyway? [y/n]`的提示，那么你应该修改过里面的文件，如果你认为自己的修改并不重要，可以输入 y 继续。  
更新完请看看 Readme，**因为不能保证更新一定是平滑升级，尤其是大版本升级**

## 使用方法

运行`main.py`即可。

注意事项：

- 请注意所有的数据库写入操作都是在图库关闭的时候进行的，所以如果不关闭图库就直接退出 Pythonista，那么这个图库就不会保存到数据库

## 更新

### 2020-01-16 版本：2.0

- 此版本为大版本升级，不兼容之前的版本，请先运行`troublefix.py`，并选择“迁移到 2.0”
- 优化 downloads 页搜索速度
- 更新提示

### 2019-12-05 版本：1.7 加入表示是否为隐藏图库的标记功能，bugfix

- 用删除线表示隐藏图库
- 修复各类 Bug

### 2019-07-14 版本：1.6 加入评论功能，bugfix

- 此次更新加入评论功能，因此 parse 版本升级，兼容版本 1.5 的旧图库，
  如果要全部升级，使用`troublefix`里的`update_infos()`即可。
- 修复评分以后的刷新 bug

## TO-DO

- [ ] 为逻辑分辨率更高的 iPad 调整测试 UI 适配
- [ ] 适配 iPhone
- [ ] 让没有 Multi-Page Viewer 权限的账号也能使用
- [ ] 让游客也能使用
- [ ] 缓存搜索支持‘-’号过滤语法

## 已知 bugs

- 如果出现`requests.exceptions.SSLError`: 1. 不可以使用 MITM 软件；2. 请检查代理软件，最好将 e-hentai.org 和 exhentai.org 加入代理列表，或者可以暂时设为全局模式，登录完成以后再改回来
- 如果出现数据库错误（多为程序卡死强制关闭造成），运行`troublefix.py`里的“修复数据库”即可，如果 App 还能打开，也可以在设置里操作
- 本应用已经可以在 iCloud Drive 文件夹中运行。但是仍然强烈不推荐这么做，因为本应用在使用的时候需要频繁地的增删文件，iCloud Drive 会把版本冲突的文件在后面加“2”，“3”……这样的标识然后同时保留，这很可能导致本应用用于判断文件数量的函数运算出错，继而程序出错。
- 关于 MemoryError（参见[issue#3](https://github.com/Gandum2077/PyEhViewer/issues/3)）：Pythonista 自带的`html2text`有问题，请使用 stash 升级`html2text`

## Contributing

- 针对不同设备调整 UI 需要大量的人力，所以如果你在逻辑分辨率不为 1024\*768 的设备上使用，不要忘了调整 UI 并贡献代码
- 另一个重点问题是重构 parse 模块，使其适用于没有 Multi-Page Viewer 权限的账号

## 截图

![0.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/0.png)  
![1.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/1.png)  
![2.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/2.png)  
![3.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/3.png)
