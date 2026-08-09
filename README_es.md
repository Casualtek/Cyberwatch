# Cyberwatch

<!-- hy-mt2-i18n:start -->
[English](./README.md) | [中文](./README_zh-CN.md) | [日本語](./README_ja.md) | **Español**
<!-- hy-mt2-i18n:end -->

Hacer un seguimiento de los ciberataques

Este proyecto consta en varios scripts en Python que ayudan a monitorear las noticias para detectar menciones de ciberataques en los medios de todo el mundo.

*rss.py* recopila fuentes de noticias sobre el tema desde Google, elimina duplicados y traduce los titulares a inglés mediante la API del servicio de traducción de Azure. También se utiliza ChatGPT para determinar si el título indica que el artículo trata sobre un ciberataque o no.
La fuente RSS resultante está lista para ser consumida con tu lector de RSS favorito. Se actualiza con frecuencia mediante GitHub Actions.
*TODO*: agregar resultados de la API de búsqueda de Bing News. Ampliar la detección de duplicados.

*review-week.py* utiliza los datos de *cyberattacks.json* para generar un resumen semanal de los ciberataques. Es ejecutado por GitHub Actions.

*review-monthly.py* utiliza los datos de *cyberattacks.json* para generar un resumen mensual de los ciberataques. También es ejecutado por GitHub Actions.

¿Y qué contiene *cyberattacks.json*?
Un conjunto de ciberataques mencionados en los medios y detectados gracias a la fuente RSS de ciberataques.
Allí encontrarás el nombre de la víctima, el país, la fecha, una breve descripción de la situación y un enlace al artículo de noticias original.
Estos datos se extraen del artículo original con la ayuda de Claude, utilizando la API para desarrolladores de Anthropic.
La salida se verifica manualmente. Se utiliza cada semana para crear **Cyberhebdo**, publicado por **[LeMagIT](https://www.lemagit.fr/ressources/Securite)**.

¿Y qué hay en *cyberattaques.xml*?
Bueno, es una fuente RSS de los informes de ciberataques mencionados anteriormente, ordenada cronológicamente según la fecha de detección.

¡Disfrútalo y no dudes en proponer ideas para mejoras!
