# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Form data parser customization.

Flask and Werkzeug by default checks a request's content length against
``MAX_CONTENT_LENGTH`` configuration variable as soon as *any* content type is
specified in the request and not only when a form data content type is
specified. This behavior prevents both setting a MAX_CONTENT_LENGTH for form
data *and* allowing streaming uploads of large binary files.

In order to allow for both max content length checking and streaming uploads
of large files, we provide a custom form data parser which only checks the
content length if a form data content type is specified. The custom form data
parser is installed by using the custom Flask application class provided
provided in this module.
"""

from __future__ import absolute_import, print_function


import time # TODO:テスト用 後で消す
import typing as t
import typing_extensions as te
from flask import abort, current_app
from flask import Flask as FlaskBase
from flask.wrappers import Request as RequestBase
from invenio_files_rest import app
from invenio_files_rest.formparser import FormDataParser
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import cached_property

from .utils import sanitize_input_data

class Request(RequestBase):
    """Custom request class needed for using custom form data parser."""

    form_data_parser_class = FormDataParser

    @cached_property
    def form(self) -> "ImmutableMultiDict[str, str]":
        print(f"========================= form =========================")
        super().form
        start = time.perf_counter() #計測開始 TODO: 後で消す
        cleaned_data = sanitize_input_data(self.form)
        end = time.perf_counter() #計測終了 TODO: 後で消す
        print(f'入力 form 処理時間：{end-start:.6f}') #処理時間 TODO: 後で消す
        return ImmutableMultiDict(cleaned_data)

    @t.overload
    def get_json(
        self, force: bool = ..., silent: "te.Literal[False]" = ..., cache: bool = ...
    ) -> t.Any:
        ...

    @t.overload
    def get_json(
        self, force: bool = ..., silent: bool = ..., cache: bool = ...
    ) -> t.Optional[t.Any]:
        ...

    def get_json(
        self, force: bool = False, silent: bool = False, cache: bool = True
    ) -> t.Optional[t.Any]:

        print(f"========================= get_json() =========================")
        rv = super().get_json(force, silent, cache)
        if not isinstance(rv, dict):
            current_app.logger.error("Invalid request data.")
            abort(400)
        start = time.perf_counter() #計測開始 TODO: 後で消す
        rv = sanitize_input_data(rv)
        end = time.perf_counter() #計測終了 TODO: 後で消す
        print(f'入力 json 処理時間：{end-start:.6f}') #処理時間 TODO: 後で消す
        return rv


class Flask(FlaskBase):
    """Flask application class needed to use custom request class."""

    request_class = Request


app.Flask = Flask
