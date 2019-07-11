# PyEhViewer
由于 iOS 平台审查限制，App Store 没有好用的 exhentai.org 阅读器（虽有偷鸡摸狗上架的，但体验也很差），因此利用 Pythonista 3 这个万能平台自己创作，功能上对标 Andiord 平台的 EhViewer，同时也有自己的特色功能

## Features
- 自动翻页，让左酱右酱休息一下（原生的EhViewer做不到哦，另外不要抬杠，我知道安卓随便弄一下也就有了）
- 快捷搜索
- 高级搜索
- 边栏、搜索词收藏、直接打开url等快捷功能
- 标签翻译
- 打分、收藏、分享、阅读评论
- 可以导入已缓存的旧版本，或者将旧版本导到新版本，方便追更新
- 缓存，缓存内容也可以搜索
- 自适应屏幕
- 阅读页面可以使用手势操作
- 代码尽量模块化设计，所以你可以添加想要的任何功能！

## 前提
本程序本来是为了本人欣赏艺术才写的，因此很遗憾，可能不适合对艺术没有追求的人。  
适合熟悉Python、Pythonista 3、Exhentai.org 的人使用。  
你必须满足以下前提才能使用PyEhViewer:
1. (必要) 目前只支持 iPad 逻辑分辨率为 1024x768 的机型(即除了 iPad Pro 10.5 和 iPad Pro 12.9 以外的所有机型，比如iPad mini、iPad Air、iPad 2018)，iPad Pro 10.5 和 iPad Pro 12.9 应该也没问题，不过我没有条件测试，有条件的可以测试一下。**暂不支持iPhone。**
1. (必要) [Pythonista 3](https://apps.apple.com/cn/app/pythonista-3/id1085978097)
2. (必要) 第三方包 html2text，在 [stash](https://github.com/ywangd/stash) 中运行以下代码安装，未安装 stash 请先安装 stash

```
pip install html2text
```
3. (必要) 可以访问 e-hentai.org 和 exhentai.org 的网络环境。如果你使用代理，请注意可能需要设为全局代理或者手动添加以上两个网址，因为很多代理软件没有这两个网址。
4. (必要) 注册e-hentai.org账号，并确保可以访问 exhentai.org （刚注册的账号需要等待两星期左右才能访问 exhentai.org），然后请去 https://e-hentai.org/hathperks.php 点亮Multi-Page Viewer的Hath Perk，需要300Hath币（**最快方法：淘宝买币**。也可以各显神通，赚币方法很多）或捐款100美元
5. (必要) [设置界面](https://exhentai.org/uconfig.php)必须做以下设置：

- Front Page Settings 设为 Extended
- Thumbnail Settings 中的 Size 设为 Large

6. (可选) [设置界面](https://exhentai.org/uconfig.php)推荐做以下设置：

- Gallery Name Display 设为 Japanese Title (if available)
- Search Result Count 设为 50 results

## 使用方法
运行`main.py`即可。

## TO-DO
- [ ] CommentsView，可以发表评论，打分，打开链接
- [ ] 为 iPad Pro 10.5和 iPad Pro 12.9 调整测试UI适配
- [ ] 适配iPhone
- [ ] 让没有 Multi-Page Viewer 权限的账号也能使用（这需要调整网络模块和整个程序的多线程逻辑，还有UI也要调整，而且运行效率必然下降）
- [ ] 让游客也能使用

## 已知bugs
- 若放在iCloud文件夹中，本程序无法运作
- 首次运行如果出现`requests.exceptions.SSLError`: 检查代理软件，建议暂时设为全局模式，登录完成以后再改回来
- 如果出现数据库错误（多为程序卡死强制关闭造成），运行`troublefix.py`里的`rebuild_db()`即可

## 截图
![0.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/0.png)  
![1.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/1.png)  
![2.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/2.png)  
![3.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/3.png)