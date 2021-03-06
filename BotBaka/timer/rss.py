#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    BotBaka.timer.rss
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    $END$

    :author:    lightless <root@lightless.me>
    :homepage:  None
    :license:   GPL-3.0, see LICENSE for more details.
    :copyright: Copyright (c) 2017-2020 lightless. All rights reserved
"""
from typing import List

import feedparser
import requests

from .engine.thread import SingleThreadEngine
from ..database.models import NewsModel, RssSourceModel
from ..utils.log import logger


class RSSTimer(SingleThreadEngine):

    def __init__(self):
        super(RSSTimer, self).__init__()

        self.name = "rss-timer"

        self.target_group = 672534169

        # todo 区分RSS和ATOM
        # self.rss_list = [
        #     "https://seclists.org/rss/oss-sec.rss"
        # ]

    def _worker(self):
        logger.debug("{} start.".format(self.name))

        while self.is_running():

            # 取出所有的rss
            all_sources = RssSourceModel.instance.all()

            for source in all_sources:
                logger.debug("Fetch {}({})...".format(source.name, source.url))
                url = source.url
                response = requests.get(url)
                rss = feedparser.parse(response.text)

                for e in rss.entries:
                    title = e.title
                    link = e.link

                    # 检查这个新闻是否已经入库了
                    news = NewsModel.instance.get_news_by_url(url=link)
                    if news is None:
                        # 库里没有
                        NewsModel.instance.create(url=link, title=title, has_send=0)

            # 把库里还没发过的新闻全都发出去
            all_news: List[NewsModel] = NewsModel.instance.get_not_send_news()
            for n in all_news:
                msg = n.title + "\n" + n.url
                self.CQApi.send_group_message(self.target_group, None, msg)

                n.has_send = 1
                n.save()

            # 5分钟查询一次
            self.ev.wait(300)
