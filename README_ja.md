# Cyberwatch

<!-- hy-mt2-i18n:start -->
[English](./README.md) | [中文](./README_zh-CN.md) | **日本語** | [Español](./README_es.md)
<!-- hy-mt2-i18n:end -->

サイバー攻撃の追跡

このプロジェクトは、世界中のメディアに掲載されたサイバー攻撃に関する記事を監視し、それらを発見するのに役立ついくつかのPythonスクリプトで構成されています。

*rss.py*はGoogleから該当トピックのニュースフィードを収集し、重複するものを削除した上で、Azure TranslationサービスのAPIを利用してニュースの見出しを英語に翻訳します。また、その見出しがサイバー攻撃に関する記事を示唆しているかどうかを判断するためにChatGPTも活用されています。
生成されたRSSフィードは、お気に入りのRSSリーダーで利用可能です。GitHub Actionsを使って定期的に更新されます。
*TODO*: Bing News SearchのAPIからの結果を追加する。重複検出機能を拡張する。

*review-week.py*は*cyberattacks.json*に含まれるデータを使って、週次のサイバー攻撃要約を作成します。これもGitHub Actionsによって実行されます。

*review-monthly.py*も同様に*cyberattacks.json*のデータを利用して週次のサイバー攻撃要約を作成し、GitHub Actionsによって実行されます。

では、*cyberattacks.json*には何が含まれているのでしょうか？
meta cyberattacks RSSフィードのおかげで発見された、メディアに掲載されたサイバー攻撃の一覧です。
そこには被害者の名称、国、日付、状況の簡単な説明、そして元のニュース記事へのリンクが記載されています。
このデータは、Anthropicの開発者向けAPIを利用し、Claudeの助けを借りて元のニュース記事から抽出されます。
出力内容は手動でチェックされ、毎週**[LeMagIT](https://www.lemagit.fr/ressources/Securite)**が発行する**Cyberhebdo**の作成に使用されます。

では、*cyberattaques.xml*はどうでしょうか？
これは前述のサイバー攻撃報告のRSSフィードで、発見日順に並べられています。

ぜひ楽しんでいただき、改善案があれば遠慮なくご提案ください！
