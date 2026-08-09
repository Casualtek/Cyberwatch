# Cyberwatch

<!-- hy-mt2-i18n:start -->
[English](./README.md) | **中文** | [日本語](./README_ja.md) | [Español](./README_es.md)
<!-- hy-mt2-i18n:end -->

追踪网络攻击动态

该项目由若干个 Python 脚本组成，旨在帮助监控新闻，从而发现全球媒体中提及的网络攻击事件。

*rss.py* 会从谷歌获取与该主题相关的新闻源，去除重复内容，并利用 Azure Translation 服务的 API 将新闻标题翻译成英文。同时还会借助 ChatGPT 来判断标题是否表明该文章涉及网络攻击。最终生成的 RSS 源可直接在您常用的 RSS 阅读器中使用。该 RSS 源会通过 GitHub Actions 定期更新。
*待办事项*：接入 Bing News Search 的 API 以获取更多数据，并进一步完善重复内容的检测功能。

*review-week.py* 会使用 *cyberattacks.json* 中的数据来生成每周的网络攻击概要，它也是通过 GitHub Actions 运行的。

*review-monthly.py* 同样使用 *cyberattacks.json* 中的数据来生成每月的网络攻击概要，同样由 GitHub Actions 执行。

那么 *cyberattacks.json* 里包含什么内容呢？
它是通过元网络攻击 RSS 源发现的、在媒体中被提及的一系列网络攻击记录。其中包含了受害方的名称、所在国家、发生日期、对事件情况的简要描述，以及原始新闻报道的链接。这些数据是通过 Anthropic 的开发者 API，并借助 Claude 的帮助从原始新闻中提取出来的。之后会人工核对这些数据，它们会被用于每周制作由 **[LeMagIT](https://www.lemagit.fr/ressources/Securite)** 发行的 **Cyberhebdo** 报刊。

那 *cyberattaques.xml* 呢？
它其实就是上述网络攻击报告的 RSS 源，只是按照被发现的时间顺序进行了排序。

希望您能喜欢这个项目，也欢迎随时提出任何改进建议！
