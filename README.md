# PyEhViewer
由于 iOS 平台审查限制，因此 iOS 平台在诸如看Pornhub、看e-hentai之类的功能上一直是缺失的。这是iOS让人难以忍受的地方，也是Android超越iOS的地方。  
一直以来，App Store没有好用的 exhentai.org 阅读器（虽有偷鸡摸狗上架的，但体验也很差），但是官方不提供，可以自己做嘛。因此利用Pythonista 3这个万能平台自己创作，功能上对标Android平台的EhViewer，同时也有自己的特色功能。

## 紧急更新：不再支持 exhentai.org，改为支持 e-hentai.org
之前的图库如果要继续使用，请运行`troublefix.py`里面的`fix_infos`，否则旧图库将出现bug


## Features
- 自动翻页，让左酱右酱休息一下（原生的EhViewer做不到哦，另外不要抬杠，我知道安卓随便弄一下也就有了）
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
本程序使用需要满足的前提比较多，本来这是本人为了欣赏艺（工）术（口）才写的，因此很遗憾，可能不适合对艺（工）术（口）没有追求的人。  
虽然前提设置有点复杂，但是程序本身的操作是很易懂、纯 GUI 操作的。  
适合熟悉Python、Pythonista 3、e-hentai.org 的人使用。  
你必须满足以下前提才能使用PyEhViewer:
1. (必要) 目前只支持 iPad 逻辑分辨率为 1024x768 的机型(即除了iPad Air 3和iPad Pro 10.5、11、12.9以外的所有机型，比如iPad mini、iPad Air、iPad 2018)，不过逻辑分辨率更高的机型应该也没问题，多数view的layout都已经调整好可以自适应分辨率，不过我没有条件测试，有条件的同学可以测试一下。**暂不支持iPhone。**
1. (必要) [Pythonista 3](https://apps.apple.com/cn/app/pythonista-3/id1085978097)
2. (必要) 第三方包 html2text，在 [stash](https://github.com/ywangd/stash) 中运行以下代码安装，未安装 stash 请先安装 stash

```
pip install html2text
```
3. (必要) 可以访问 e-hentai.org 的网络环境。如果你使用代理，请注意可能需要设为全局代理或者手动添加以上两个网址，因为很多代理软件没有这两个网址。
4. (必要) 注册 e-hentai.org 账号，然后请去 https://e-hentai.org/hathperks.php 点亮Multi-Page Viewer的Hath Perk，需要300Hath币（**最快方法：淘宝买币**。也可以各显神通，赚币方法很多）或捐款100美元
5. (必要) [设置界面](https://e-hentai.org/uconfig.php)必须做以下设置：

- Front Page Settings 设为 Extended
- Thumbnail Settings 中的 Size 设为 Large

6. (可选) [设置界面](https://e-hentai.org/uconfig.php)推荐做以下设置：

- Gallery Name Display 设为 Japanese Title (if available)
- Search Result Count 设为 50 results

## 使用方法
运行`main.py`即可。

## 更新
### 2019-07-14    版本：1.6 加入评论功能，bugfix
- 此次更新加入评论功能，因此parse版本升级，兼容版本1.5的旧图库，
如果要全部升级，使用`troublefix`里的`update_infos`即可。
- 修复评分以后的刷新bug

## TO-DO
- [x] CommentsView，可以发表评论，打分，打开链接
- [ ] 为 iPad Pro 10.5和 iPad Pro 12.9 调整测试UI适配
- [ ] 适配iPhone
- [ ] 让没有 Multi-Page Viewer 权限的账号也能使用（这需要调整网络模块和整个程序的多线程逻辑，还有UI也要调整，而且运行效率必然下降）
- [ ] 让游客也能使用

## 已知bugs
- 若放在iCloud文件夹中，本程序无法运作
- 首次运行如果出现`requests.exceptions.SSLError`: 检查代理软件，建议暂时设为全局模式，登录完成以后再改回来
- 如果出现数据库错误（多为程序卡死强制关闭造成），运行`troublefix.py`里的`rebuild_db()`即可

## Contributions
- 针对不同设备调整UI需要大量的人力，所以如果你在逻辑分辨率不为1024*768的设备上使用，不要忘了调整UI并贡献代码
- 另一个重点问题是重构parse模块，使其适用于没有Multi-Page Viewer权限的账号

## 截图
![0.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/0.png)  
![1.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/1.png)  
![2.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/2.png)  
![3.png](https://github.com/Gandum2077/PyEhViewer/blob/master/screenshots/3.png)
