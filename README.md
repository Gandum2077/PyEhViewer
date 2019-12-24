# PyEhViewer

由于iOS平台审查限制，因此iOS平台在诸如看Pornhub、看Exhentai之类的功能上一直是缺失的。这是iOS让人难以忍受的地方，也是Android超越iOS的地方。  
一直以来，App Store没有好用的exhentai.org阅读器（虽有偷鸡摸狗上架的，但体验也很差），但是官方不提供，可以自己做嘛。利用Pythonista 3这个万能平台创作，功能上对标Android平台的EhViewer，同时也有自己的特色功能。

## Features

- 自动翻页，解放左酱右酱
- 快捷搜索
- 高级搜索
- 边栏、搜索词收藏、直接打开url等快捷功能
- 标签翻译
- 打分、收藏、分享、评论
- 可以导入已缓存的旧版本，或者将旧版本导到新版本，方便追更新
- 缓存，缓存内容也可以搜索
- 自适应屏幕
- 阅读页面可以使用手势操作
- 代码尽量模块化设计，所以你可以添加想要的任何功能！

## 前提

本来这是本人为了欣赏艺（工）术（口）才写的，因此很遗憾，可能不适合对艺（工）术（口）没有追求的人。  
本程序虽然前提设置有点复杂，但是程序本身的操作是一目了然的。

**你必须满足以下前提才能使用PyEhViewer:**

1. (必要) [Pythonista 3](https://apps.apple.com/cn/app/pythonista-3/id1085978097)
2. (必要) iPad。 **不支持iPhone。** 目前完美支持逻辑分辨率为1024x768的iPad机型（比如iPad mini 5、iPad Air 2、iPad 2018），更高逻辑分辨率的机型比如iPad Air 3和iPad Pro应该也没问题，布局可以自适应分辨率，但是我没有设备测试，有条件的同学可以测试并反馈一下。
3. (必要) 可以访问e-hentai.org和exhentai.org的网络环境。如果你使用代理，请注意可能需要设为全局代理或者手动添加以上两个网址，因为很多代理软件没有这两个网址。  
关于如何手动添加代理设置，举两个例子：  
例一 Quantumult：在配置文件加入`HOST-SUFFIX,e-hentai.org,PROXY,resolve-on-proxy`和`HOST-SUFFIX,exhentai.org,PROXY,resolve-on-proxy`。  
例二 Surge：在配置文件加入`DOMAIN-SUFFIX,e-hentai.org,Proxy`和`DOMAIN-SUFFIX,exhentai.org,Proxy`。
4. (必要) 注册[e-hentai.org](https://e-hentai.org)账号，并确保可以访问[exhentai.org](https://exhentai.org)（刚注册的账号需要等待两星期左右才能访问）。  
然后请去[Hath Perks页面](https://e-hentai.org/hathperks.php)点亮Multi-Page Viewer的Hath Perk，需要300Hath币或者在[捐款页面](https://e-hentai.org/bitcoin.php)捐价值100美元的Bitcoin或Bitcoin Cash。  

5. [设置界面](https://exhentai.org/uconfig.php)做以下设置：

- (必要)Front Page Settings 设为 Extended
- (必要)Thumbnail Settings 中的 Size 设为 Large
- (可选)Gallery Name Display 设为 Japanese Title (if available)
- (可选)Search Result Count 设为 50 results。此功能需要Paging Enlargement I的Hath Perk

## 安装和更新
建议安装[stash](https://github.com/ywangd/stash)，然后通过git来安装和更新。`stash`必须要运行在Python 2.7环境下。

- 安装

```
git clone https://github.com/Gandum2077/PyEhViewer.git  
```

请注意后面的.git不要漏了

- 更新

```
cd PyEhViewer; git pull
```

请注意需要先进入PyEhViewer的目录，如果你安装在别的地方，那么要对应的修改。  
此方法只保证在你没有过编辑行为，仅运行过`main.py`时可用，如果出现`WARNING: there are uncommitted modified files and/or staged changes. These could be overwritten by this command. Continue anyway? [y/n]`的提示，那么你应该修改过里面的文件，如果你认为自己的修改并不重要，可以输入y继续。  
更新完请看看Readme，**因为不能保证更新一定是平滑升级，说不定会需要一定的操作**（这个更新也许会很快到来，我已经在写了）
## 使用方法
运行`main.py`即可。

注意事项：

- 请注意所有的数据库写入操作都是在图库关闭的时候进行的，所以如果不关闭图库就直接退出Pythonista，那么这个图库就不会保存到数据库

## 更新
### 2019-12-05    版本：1.7 加入表示是否为隐藏图库的标记功能，bugfix
- 用删除线表示隐藏图库
- 修复各类Bug

### 2019-07-14    版本：1.6 加入评论功能，bugfix
- 此次更新加入评论功能，因此parse版本升级，兼容版本1.5的旧图库，
如果要全部升级，使用`troublefix`里的`update_infos()`即可。
- 修复评分以后的刷新bug

## TO-DO
- [x] CommentsView，可以发表评论，打分，打开链接
- [ ] 为逻辑分辨率更高的iPad调整测试UI适配
- [ ] 适配iPhone
- [ ] 让没有 Multi-Page Viewer 权限的账号也能使用
- [ ] 让游客也能使用
- [ ] 缓存搜索支持‘-’号过滤语法

## 已知bugs
- 若放在iCloud文件夹中，本程序无法运作
- 首次运行如果出现`requests.exceptions.SSLError`: 检查代理软件，最好将e-hentai.org和exhentai.org加入代理列表，或者可以暂时设为全局模式，登录完成以后再改回来
- 如果出现数据库错误（多为程序卡死强制关闭造成），运行`troublefix.py`里的`rebuild_db()`即可，如果App还能打开，也可以在设置里操作
- 如果之前因为关站风波下载了紧急更新版本，请运行`troublefix.py`里面的`fix_infos()`，否则旧图库将出现bug
- 由于对gif使用了webview这种折衷方案，所以观看gif的时候不宜过快翻页，否则容易内存告急而导致Pythonista崩溃。不过如果gif文件过大，即使你什么都不做App也会崩溃

## Contributing
- 针对不同设备调整UI需要大量的人力，所以如果你在逻辑分辨率不为1024*768的设备上使用，不要忘了调整UI并贡献代码
- 另一个重点问题是重构parse模块，使其适用于没有Multi-Page Viewer权限的账号

## 截图
![0.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/0.png)  
![1.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/1.png)  
![2.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/2.png)  
![3.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/3.png)
