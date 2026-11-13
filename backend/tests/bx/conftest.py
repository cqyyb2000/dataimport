# -*- coding: utf-8 -*-
"""报销台账规则测试使用独立的内存库，不连接业务数据库。"""
import pytest
from flask import Flask
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

from Model.base import db
from Model.bx import BxBudget, BxClaim, BxDepartment, BxDocSeq, BxProject  # noqa: F401


@pytest.fixture(scope='session')
def bx_app():
    app = Flask('bx-rules-test')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    }
    db.init_app(app)

    with app.app_context():
        engine = db.engine

        @event.listens_for(engine, 'connect')
        def _fk_on(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

    return app


@pytest.fixture
def db_ctx(bx_app):
    with bx_app.app_context():
        db.create_all()
        yield
        db.session.rollback()
        db.session.remove()
        with db.engine.begin() as conn:
            conn.exec_driver_sql('PRAGMA foreign_keys=OFF')
            db.metadata.drop_all(bind=conn)
            conn.exec_driver_sql('PRAGMA foreign_keys=ON')
